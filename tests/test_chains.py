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


def test_requests_are_limited_in_size(empty_calendar):
    response = empty_calendar.get("/public/availability", params={
        "date": TUESDAY, "service_ids": ",".join(str(i) for i in range(1, 12))})
    assert response.status_code == 422


def test_the_search_budget_is_shared_by_the_whole_request(empty_calendar, monkeypatch):
    from app.logic import availability

    monkeypatch.setattr(availability, "SEARCH_BUDGET", 10)
    found = chains(empty_calendar, MASSAGE_AND_FACIAL)
    assert 0 < len(found) < 10  # stops early instead of searching every start time


# ---------- Slice 3: what the customer sees ----------

def _booked_chain(client, **customer):
    response = book_chain(client, MASSAGE_AND_FACIAL, "10:00", **customer)
    assert response.status_code == 200
    from tests.conftest import manage_token

    token = manage_token(client, response.json()["id"])
    assert client.post(f"/public/bookings/{token}/verify").status_code == 200
    return response.json(), token


def test_the_booking_shows_who_does_what(empty_calendar):
    booking, token = _booked_chain(empty_calendar)
    assert booking["therapist_name"] == "Lena, Sofia"
    assert [(v["time"], v["names"], v["therapist_name"]) for v in booking["visit"]] == [
        ("10:00", ["Deep tissue massage"], "Lena"), ("11:00", ["Classic facial"], "Sofia")]
    manage = empty_calendar.get(f"/public/bookings/{token}").json()
    assert [v["therapist_name"] for v in manage["visit"]] == ["Lena", "Sofia"]
    assert manage["visit"][1]["end_time"] == "11:45"


def test_emails_list_each_part_of_the_visit(empty_calendar):
    _booked_chain(empty_calendar)
    [email] = [e for e in empty_calendar.app.state.mailer.outbox
               if e.subject.startswith("Booking confirmed")]
    for body in (email.text, email.html):
        assert "10:00  Deep tissue massage — Lena" in body
        assert "11:00  Classic facial — Sofia" in body
        assert "with Lena" not in body
    assert "Tuesday 13 October 2026, 10:00 (105 min)" in email.text


def test_a_break_shows_as_its_own_line_in_german_too(empty_calendar, db):
    client = empty_calendar
    _no_gapless_day(db, client)
    ids = menu_ids(client)
    response = client.post("/public/bookings", headers={"X-Lang": "de"}, json={
        "service_ids": [ids[s] for s in MASSAGE_AND_FACIAL], "date": TUESDAY,
        "start_time": "10:00", "break_before": 1, **CUSTOMER})
    assert response.status_code == 200
    assert [v["is_break"] for v in response.json()["visit"]] == [False, True, False]
    [email] = client.app.state.mailer.outbox
    assert "11:00  15 Min. Pause" in email.text
    assert "11:15  Klassische Gesichtsbehandlung — Sofia" in email.text


def test_cancelling_frees_every_part(empty_calendar):
    client = empty_calendar
    _, token = _booked_chain(client)
    assert "10:00" not in [s["time"] for s in chains(client, ["Deep tissue massage"])]
    assert "11:00" not in [s["time"] for s in chains(client, ["Classic facial"])]
    assert client.post(f"/public/bookings/{token}/cancel").status_code == 200
    assert "10:00" in [s["time"] for s in chains(client, ["Deep tissue massage"])]
    assert "11:00" in [s["time"] for s in chains(client, ["Classic facial"])]


def test_late_cancellation_counts_from_the_first_part(empty_calendar, monkeypatch):
    from datetime import datetime

    from app import clock

    client = empty_calendar
    _, token = _booked_chain(client)
    moment = datetime(2026, 10, 12, 10, 30, tzinfo=clock.BERLIN)  # 23.5 h before 10:00
    monkeypatch.setattr(clock, "now", lambda: moment)
    assert client.post(f"/public/bookings/{token}/cancel").json()["late_cancellation"] is True


def test_the_calendar_file_covers_the_whole_visit(empty_calendar):
    _, token = _booked_chain(empty_calendar)
    body = empty_calendar.get(f"/public/bookings/{token}/calendar.ics").text
    unfolded = body.replace("\r\n ", "")
    assert "DTSTART:20261013T080000Z" in body and "DTEND:20261013T094500Z" in body
    assert "10:00 Deep tissue massage — Lena\\n11:00 Classic facial — Sofia" in unfolded


# ---------- Slice 4: the owner area ----------

def _owner_chain(client):
    from tests.conftest import login

    booking, _ = _booked_chain(client)
    assert login(client).status_code == 200
    return booking["id"]


def test_the_owner_sees_each_part_and_can_filter_by_any_therapist(empty_calendar):
    client = empty_calendar
    booking_id = _owner_chain(client)
    detail = client.get(f"/owner/bookings/{booking_id}").json()
    assert [(s["position"], s["therapist_name"], s["time"], s["end_time"])
            for s in detail["segments"]] == [(0, "Lena", "10:00", "11:00"),
                                             (1, "Sofia", "11:00", "11:45")]
    assert [i["segment_position"] for i in detail["items"]] == [0, 1]
    for name in ("Lena", "Sofia"):
        listed = client.get("/owner/bookings", params={
            "from": TUESDAY, "to": TUESDAY, "therapist_id": therapist_id(client, name)}).json()
        assert [b["id"] for b in listed] == [booking_id]


def test_csv_names_the_therapist_of_each_line(empty_calendar):
    import csv
    import io

    client = empty_calendar
    _owner_chain(client)
    text = client.get("/owner/bookings/export.csv", params={"from": TUESDAY, "to": TUESDAY}).text
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    assert [(r[3], r[10]) for r in rows[1:]] == [("Lena", "Deep tissue massage"),
                                                 ("Sofia", "Classic facial")]


def test_adjusted_items_keep_their_therapist(empty_calendar, db):
    client = empty_calendar
    booking_id = _owner_chain(client)
    response = client.put(f"/owner/bookings/{booking_id}/items", json={"items": [
        {"item_type": "service", "name": "Deep tissue massage", "minutes": 60,
         "unit_price": "70.00", "quantity": 1, "segment_position": 0},
        {"item_type": "service", "name": "Classic facial", "minutes": 45,
         "unit_price": "59.00", "quantity": 1, "segment_position": 1},
        {"item_type": "extra", "name": "Face oil", "minutes": 0, "unit_price": "18.00",
         "quantity": 1},
    ]})
    assert response.status_code == 200
    assert [i["segment_position"] for i in response.json()["items"]] == [0, 1, None]
    assert [v["names"] for v in response.json()["visit"]] == [
        ["Deep tissue massage"], ["Classic facial"]]


def test_phone_bookings_choose_a_therapist_per_treatment(empty_calendar, db):
    from tests.conftest import login

    client = empty_calendar
    assert login(client).status_code == 200
    ids = menu_ids(client)
    services = ["Relaxation massage", "Classic facial"]
    lena = therapist_id(client, "Lena")
    found = client.get("/owner/availability", params={
        "date": TUESDAY, "service_ids": ",".join(str(ids[s]) for s in services),
        "therapist_choices": f"{ids['Relaxation massage']}:{lena}"}).json()["slots"]
    assert plan(found[0]) == ["10:00 Lena", "11:00 Sofia"]
    response = client.post("/owner/bookings", json={
        "service_ids": [ids[s] for s in services], "date": TUESDAY, "start_time": "10:00",
        "therapist_choices": {str(ids["Relaxation massage"]): lena}, **CUSTOMER})
    assert response.status_code == 200
    assert [s["therapist_name"] for s in response.json()["segments"]] == ["Lena", "Sofia"]
    assert response.json()["status"] == "booked"


# ---------- Slice 5: waitlist chains ----------

def wait_for(client, name, services, choices=None, earliest="09:00", latest="18:00"):
    """Join Tuesday's waitlist and click the opt-in link."""
    from app.models import Customer, WaitlistEntry

    ids = menu_ids(client)
    response = client.post("/public/waitlist", json={
        "service_ids": [ids[s] for s in services], "preferred_date": TUESDAY,
        "therapist_choices": {str(ids[s]): therapist_id(client, n) if n else None
                              for s, n in (choices or {}).items()},
        "earliest_time": earliest, "latest_time": latest, "first_name": name,
        "last_name": "Waiting", "email": f"{name.lower()}@example.com",
        "phone": "+49 151 0000 0100"})
    assert response.status_code == 200, response.json()
    with client.app.state.session_factory() as session:
        customer = session.scalar(select(Customer).where(Customer.first_name == name))
        token = session.scalar(select(WaitlistEntry.confirm_token).where(
            WaitlistEntry.customer_id == customer.id))
    assert client.post(f"/public/waitlist/confirm/{token}").status_code == 200


def waitlist_entry(db, name):
    from app.models import Customer, WaitlistEntry

    db.expire_all()
    customer = db.scalar(select(Customer).where(Customer.first_name == name))
    return db.scalar(select(WaitlistEntry).where(WaitlistEntry.customer_id == customer.id))


def cancel(client, booking_id):
    from tests.conftest import manage_token

    assert client.post(f"/public/bookings/{manage_token(client, booking_id)}/cancel") \
        .status_code == 200


def test_a_freed_part_is_offered_as_a_whole_visit_and_claimed(empty_calendar, db):
    client = empty_calendar
    facial = book(client, ["Classic facial"], TUESDAY, "11:00", "Sofia",
                  email="mia.wagner@example.com", first_name="Mia")
    wait_for(client, "Anna", MASSAGE_AND_FACIAL, latest="10:00")
    cancel(client, facial.json()["id"])

    entry = waitlist_entry(db, "Anna")
    assert entry.status == "offered"
    assert [(s[0], s[1][11:16]) for s in entry.offer_plan["segments"]] == [
        (therapist_id(client, "Lena"), "08:00"), (therapist_id(client, "Sofia"), "09:00")]
    [mail] = [e for e in client.app.state.mailer.outbox if e.subject.startswith("A time is")]
    assert "Tue 13 Oct, 10:00 with Lena, Sofia (105 min)" in mail.text

    offer = client.get(f"/public/waitlist/offers/{entry.offer_token}").json()
    assert [(v["time"], v["therapist_name"]) for v in offer["visit"]] == [
        ("10:00", "Lena"), ("11:00", "Sofia")]
    claimed = client.post(f"/public/waitlist/offers/{entry.offer_token}/claim")
    assert claimed.status_code == 200, claimed.json()
    assert claimed.json()["source"] == "waitlist"
    assert segments(db, claimed.json()["id"]) == [("Lena", "08:00", "09:00", "09:10"),
                                                  ("Sofia", "09:00", "09:45", "09:55")]


def test_join_order_skips_visits_that_do_not_fit(empty_calendar, db):
    client = empty_calendar
    facial = book(client, ["Classic facial"], TUESDAY, "11:00", "Sofia",
                  email="mia.wagner@example.com", first_name="Mia")
    wait_for(client, "Early", MASSAGE_AND_FACIAL, earliest="12:00")  # visit starts 10:00
    wait_for(client, "Picky", MASSAGE_AND_FACIAL, choices={"Classic facial": None,
                                                           "Deep tissue massage": None},
             latest="09:30")
    wait_for(client, "Fits", ["Express facial"])
    cancel(client, facial.json()["id"])
    assert [waitlist_entry(db, n).status for n in ("Early", "Picky", "Fits")] == [
        "waiting", "waiting", "offered"]


def test_one_open_offer_per_therapist_time_and_expiry_passes_every_part_on(
        empty_calendar, db, monkeypatch):
    from datetime import datetime

    from app import clock

    client = empty_calendar
    visit = book_chain(client, MASSAGE_AND_FACIAL, "10:00", email="mia.wagner@example.com")
    from tests.conftest import manage_token

    client.post(f"/public/bookings/{manage_token(client, visit.json()['id'])}/verify")
    wait_for(client, "Chain", MASSAGE_AND_FACIAL)
    wait_for(client, "Foot", ["Foot reflexology"])
    wait_for(client, "Face", ["Express facial"])
    cancel(client, visit.json()["id"])
    # The first in line takes both parts; nobody else may be offered those times.
    assert [waitlist_entry(db, n).status for n in ("Chain", "Foot", "Face")] == [
        "offered", "waiting", "waiting"]

    later = datetime(2026, 10, 10, 12, 31, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: later)
    run = client.post("/internal/run-jobs", headers={"X-Jobs-Secret": "test-jobs-secret"})
    assert run.json()["offers_expired"] == 1
    assert [waitlist_entry(db, n).status for n in ("Chain", "Foot", "Face")] == [
        "expired", "offered", "offered"]
    assert waitlist_entry(db, "Foot").offer_start_at.strftime("%H:%M") == "08:00"  # 10:00
    assert waitlist_entry(db, "Face").offer_start_at.strftime("%H:%M") == "09:00"  # 11:00


def test_waitlist_choices_per_treatment_are_honoured(empty_calendar, db):
    client = empty_calendar
    relax = book(client, ["Relaxation massage"], TUESDAY, "11:00", "Sofia",
                 email="mia.wagner@example.com", first_name="Mia")
    wait_for(client, "Lenafan", ["Relaxation massage"], choices={"Relaxation massage": "Lena"})
    wait_for(client, "Anyone", ["Relaxation massage"])
    entry = waitlist_entry(db, "Lenafan")
    assert entry.therapist_choices == {str(menu_ids(client)["Relaxation massage"]):
                                       therapist_id(client, "Lena")}
    cancel(client, relax.json()["id"])  # Sofia's time frees up
    assert waitlist_entry(db, "Lenafan").status == "waiting"
    assert waitlist_entry(db, "Anyone").status == "offered"
