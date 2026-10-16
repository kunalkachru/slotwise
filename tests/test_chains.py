"""Several therapists per visit (option B, slice 2): chains in availability and booking.
Frozen now: Sat 10 Oct 2026 12:00 Berlin. Tuesday 13 Oct: Lena 10–19 (massages,
reflexology), Sofia 9–17 (facials, relaxation massage). Buffers are 10 minutes."""

import threading
from datetime import date, time

from sqlalchemy import select

from app.models import Booking, BookingSegment, DayOff, WorkingHours
from tests.conftest import CUSTOMER, book, menu_ids, therapist_id

TUESDAY = "2026-10-13"
MASSAGE_AND_FACIAL = ["Deep tissue massage", "Classic facial"]  # Lena only, Sofia only


def chains(client, services, day=TUESDAY, choices=None, add_ons=(), **params):
    """Availability with per-treatment choices, e.g. {"Relaxation massage": "Lena"}."""
    ids = menu_ids(client)
    choice = ",".join(f"{ids[s]}:{therapist_id(client, n) if n else 'any'}"
                      for s, n in (choices or {}).items())
    response = client.get("/public/availability", params={
        "date": day, "service_ids": ",".join(str(ids[s]) for s in services),
        "add_on_ids": ",".join(str(ids[a]) for a in add_ons),
        "therapist_choices": choice, **params})
    assert response.status_code == 200, response.json()
    return response.json()["slots"]


def plan(slot):
    """'10:00 Lena, 11:00 Sofia' style summary of a slot's steps."""
    return [f"{s['time']} {s['therapist_name']}" for s in slot["steps"]]


def book_chain(client, services, start, choices=None, break_before=None, **customer):
    ids = menu_ids(client)
    body = {
        "service_ids": [ids[s] for s in services], "add_on_ids": [], "date": TUESDAY,
        "start_time": start, "break_before": break_before,
        "therapist_choices": {str(ids[s]): therapist_id(client, n) if n else None
                              for s, n in (choices or {}).items()},
        **CUSTOMER, **customer,
    }
    return client.post("/public/bookings", json=body)


def segments(db, booking_id):
    rows = db.scalars(select(BookingSegment).where(BookingSegment.booking_id == booking_id)
                      .order_by(BookingSegment.position)).all()
    return [(s.therapist.display_name,
             s.start_at.strftime("%H:%M"), s.end_at.strftime("%H:%M"),
             s.blocked_until.strftime("%H:%M")) for s in rows]  # UTC: Berlin is UTC+2


def test_a_combination_nobody_offers_alone_gets_a_chain(empty_calendar):
    found = chains(empty_calendar, MASSAGE_AND_FACIAL)
    assert plan(found[0]) == ["10:00 Lena", "11:00 Sofia"]
    assert found[0]["steps"][1]["end_time"] == "11:45"
    assert found[0]["break_before"] is None
    # The facial must end by Sofia's 17:00 closing: it starts at 16:15 at the latest.
    assert plan(found[-1]) == ["15:15 Lena", "16:15 Sofia"]
    assert [s["time"] for s in found] == [s["time"] for s in found if s["time"] <= "15:15"]


def test_the_order_is_the_customers(empty_calendar):
    # Facial first: Sofia from 9:00, but Lena only starts at 10:00, so 9:15 is the first.
    found = chains(empty_calendar, ["Classic facial", "Deep tissue massage"])
    assert plan(found[0]) == ["09:15 Sofia", "10:00 Lena"]


def test_booking_a_chain_creates_one_segment_per_therapist(empty_calendar, db):
    client = empty_calendar
    response = book_chain(client, MASSAGE_AND_FACIAL, "10:00")
    assert response.status_code == 200, response.json()
    booking = db.get(Booking, response.json()["id"])
    assert segments(db, booking.id) == [("Lena", "08:00", "09:00", "09:10"),
                                        ("Sofia", "09:00", "09:45", "09:55")]
    assert booking.total_price == 129  # 70 + 59: one booking, one total
    assert (booking.start_at.strftime("%H:%M"), booking.end_at.strftime("%H:%M")) == (
        "08:00", "09:45")
    assert {i.name_snapshot: i.segment.therapist.display_name for i in booking.items} == {
        "Deep tissue massage": "Lena", "Classic facial": "Sofia"}


def test_each_segment_blocks_only_its_own_therapist(empty_calendar):
    client = empty_calendar
    assert book_chain(client, MASSAGE_AND_FACIAL, "10:00").status_code == 200
    lena = [s["time"] for s in chains(client, ["Deep tissue massage"])]
    sofia = [s["time"] for s in chains(client, ["Classic facial"])]
    assert "10:00" not in lena and "11:15" in lena  # 10:00–11:00 + buffer
    assert "10:00" in sofia  # Sofia is free while Lena works: ends 10:45 + 10 < 11:00
    assert "10:15" not in sofia and "11:00" not in sofia and "12:00" in sofia


def test_the_second_therapist_busy_or_off_means_no_chain(empty_calendar, db):
    client = empty_calendar
    assert book(client, ["Classic facial"], TUESDAY, "11:00", "Sofia").status_code == 200
    times = [s["time"] for s in chains(client, MASSAGE_AND_FACIAL)]
    assert "10:00" not in times  # the facial would start at 11:00
    db.add(DayOff(therapist_id=therapist_id(client, "Sofia"), date=date(2026, 10, 13)))
    db.commit()
    assert chains(client, MASSAGE_AND_FACIAL) == []


def test_no_preference_keeps_the_same_therapist(empty_calendar):
    """Relaxation (Lena or Sofia) + facial (Sofia): Sofia does both, one segment, even
    though Lena has fewer bookings that day."""
    client = empty_calendar
    assert book(client, ["Express facial"], TUESDAY, "15:00", "Sofia").status_code == 200
    found = chains(client, ["Relaxation massage", "Classic facial"])
    assert plan(next(s for s in found if s["time"] == "10:00")) == ["10:00 Sofia", "11:00 Sofia"]
    # Fewest bookings when there's no handover to save: Lena has none, Sofia has one.
    at_ten = next(s for s in chains(client, ["Relaxation massage"]) if s["time"] == "10:00")
    assert at_ten["therapist_name"] == "Lena"


def test_a_chosen_therapist_is_always_honoured(empty_calendar):
    client = empty_calendar
    found = chains(client, ["Relaxation massage", "Classic facial"],
                   choices={"Relaxation massage": "Lena"})
    assert plan(found[0]) == ["10:00 Lena", "11:00 Sofia"]
    # Lena doesn't do facials: no times rather than someone else.
    assert chains(client, ["Classic facial"], choices={"Classic facial": "Lena"}) == []
    # The old single therapist_id still means one therapist for everything.
    old = client.get("/public/availability", params={
        "date": TUESDAY, "therapist_id": therapist_id(client, "Lena"),
        "service_ids": ",".join(str(menu_ids(client)[s]) for s in MASSAGE_AND_FACIAL)})
    assert old.status_code == 200 and old.json()["slots"] == []


def test_the_same_therapist_twice_in_one_visit(empty_calendar, db):
    client = empty_calendar
    visit = ["Foot reflexology", "Express facial", "Back and neck massage"]
    found = chains(client, visit)
    assert plan(found[0]) == ["10:00 Lena", "10:30 Sofia", "11:00 Lena"]
    response = book_chain(client, visit, "10:00")
    assert response.status_code == 200
    assert [s[0] for s in segments(db, response.json()["id"])] == ["Lena", "Sofia", "Lena"]


def _no_gapless_day(db, client):
    """Lena works 10–11 and Sofia from 11:15 on Tuesday: only a break joins them."""
    lena, sofia = therapist_id(client, "Lena"), therapist_id(client, "Sofia")
    for hours in db.scalars(select(WorkingHours).where(WorkingHours.weekday == 1)):
        if hours.therapist_id == lena:
            hours.start_time, hours.end_time = time(10), time(11)
        if hours.therapist_id == sofia:
            hours.start_time, hours.end_time = time(11, 15), time(17)
    db.commit()


def test_a_break_is_offered_only_when_no_gapless_chain_fits(empty_calendar, db):
    client = empty_calendar
    assert all(s["break_before"] is None for s in chains(client, MASSAGE_AND_FACIAL))
    _no_gapless_day(db, client)
    [slot] = chains(client, MASSAGE_AND_FACIAL)
    assert plan(slot) == ["10:00 Lena", "11:15 Sofia"]
    assert slot["break_before"] == 1
    assert book_chain(client, MASSAGE_AND_FACIAL, "10:00").status_code == 400  # no break
    response = book_chain(client, MASSAGE_AND_FACIAL, "10:00", break_before=1)
    assert response.status_code == 200
    assert segments(db, response.json()["id"]) == [("Lena", "08:00", "09:00", "09:10"),
                                                   ("Sofia", "09:15", "10:00", "10:10")]


def test_choosing_times_myself_also_lists_breaks(empty_calendar):
    found = chains(empty_calendar, MASSAGE_AND_FACIAL, choose_myself="true")
    at_ten = [s for s in found if s["time"] == "10:00"]
    assert [plan(s) for s in at_ten] == [["10:00 Lena", "11:00 Sofia"],
                                         ["10:00 Lena", "11:15 Sofia"]]
    assert [s["break_before"] for s in at_ten] == [None, 1]
    # A single treatment never has a break.
    assert all(s["break_before"] is None
               for s in chains(empty_calendar, ["Classic facial"], choose_myself="true"))


def test_availability_and_booking_agree(empty_calendar, db):
    client = empty_calendar
    assert book(client, ["Express facial"], TUESDAY, "15:00", "Sofia").status_code == 200
    services = ["Relaxation massage", "Classic facial"]
    shown = next(s for s in chains(client, services) if s["time"] == "10:00")
    response = book_chain(client, services, shown["time"],
                          choices={"Relaxation massage": None})
    assert [s[0] for s in segments(db, response.json()["id"])] == [
        s["therapist_name"] for s in shown["steps"][:1]]  # Sofia does both: one segment


def test_a_part_taken_meanwhile_fails_the_whole_chain(empty_calendar, db):
    client = empty_calendar
    assert chains(client, MASSAGE_AND_FACIAL)[0]["time"] == "10:00"
    assert book(client, ["Classic facial"], TUESDAY, "11:00", "Sofia",
                email="tom.becker@example.com").status_code == 200
    response = book_chain(client, MASSAGE_AND_FACIAL, "10:00")
    assert response.status_code == 400
    assert response.json()["detail"] == "That time was just taken. Please pick another."
    assert db.scalar(select(Booking).where(Booking.therapist_id == therapist_id(
        client, "Lena"))) is None  # nothing half-booked


def test_concurrent_chains_sharing_a_therapist_book_once(make_client, frozen_now, tmp_path):
    client = make_client(database_url=f"sqlite:///{tmp_path / 'race.db'}")
    with client.app.state.session_factory() as db:
        db.query(BookingSegment).delete()
        db.query(Booking).delete()
        db.commit()
    results: list[int] = []
    barrier = threading.Barrier(2)

    def attempt(services, n):
        barrier.wait()
        results.append(book_chain(client, services, "10:00",
                                  email=f"race{n}@example.com").status_code)

    # Both want Lena at 10:00 and Sofia right after; only one can have them.
    threads = [threading.Thread(target=attempt, args=(MASSAGE_AND_FACIAL, 1)),
               threading.Thread(target=attempt, args=(["Back and neck massage",
                                                       "Express facial"], 2))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(results) == [200, 400]
