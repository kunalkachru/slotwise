"""Availability rules. Frozen now: Sat 10 Oct 2026 12:00 Berlin.
Lena: Mon–Fri 10–19, Sat 10–14 (massages, reflexology). Sofia: Tue–Sat 9–17 (facials,
relaxation massage). Buffers are 10 minutes."""

from datetime import date, time

from app.models import DayOff, WorkingHours
from tests.conftest import book, menu_ids, slots, therapist_id

TUESDAY = "2026-10-13"


def times(response):
    assert response.status_code == 200, response.json()
    return [s["time"] for s in response.json()["slots"]]


def test_therapists_who_offer_every_chosen_service(empty_calendar):
    client = empty_calendar
    ids = menu_ids(client)

    def names(*services):
        r = client.get("/public/therapists", params={
            "service_ids": ",".join(str(ids[s]) for s in services)})
        return r

    assert [t["display_name"] for t in names("Deep tissue massage").json()] == ["Lena"]
    assert [t["display_name"] for t in names("Relaxation massage").json()] == ["Lena", "Sofia"]
    combo = names("Deep tissue massage", "Classic facial")
    assert combo.status_code == 404
    assert combo.json()["detail"] == (
        "No therapist offers this combination. Please remove a service."
    )


def test_fifteen_minute_steps_that_fit_inside_working_hours(empty_calendar):
    found = times(slots(empty_calendar, ["Deep tissue massage"], TUESDAY, "Lena"))
    assert found[0] == "10:00"
    assert found[1] == "10:15"
    assert found[-1] == "18:00"  # 60 min ends exactly at 19:00
    assert len(found) == 33


def test_add_ons_lengthen_the_appointment(empty_calendar):
    response = slots(empty_calendar, ["Deep tissue massage"], TUESDAY, "Lena",
                     add_ons=[("Deep tissue massage", "Hot stones")])
    assert response.json()["total_minutes"] == 75
    assert times(response)[-1] == "17:45"


def test_existing_booking_blocks_its_time_plus_buffer(empty_calendar):
    client = empty_calendar
    assert book(client, ["Deep tissue massage"], TUESDAY, "12:00", "Lena").status_code == 200
    found = times(slots(client, ["Deep tissue massage"], TUESDAY, "Lena"))
    # Blocked 12:00–13:10. A 70-minute block (60 + 10 buffer) starting at 11:00 would
    # overlap; 10:45 ends at 11:55 and still fits.
    assert "10:45" in found
    assert not {"11:00", "12:00", "12:45", "13:00"} & set(found)
    assert "13:15" in found


def test_cancelled_bookings_free_their_time(empty_calendar, db):
    from app.models import Booking

    client = empty_calendar
    book(client, ["Deep tissue massage"], TUESDAY, "12:00", "Lena")
    db.query(Booking).update({"status": "cancelled"})
    db.commit()
    assert "12:00" in times(slots(client, ["Deep tissue massage"], TUESDAY, "Lena"))


def test_two_hours_notice_today(empty_calendar):
    # Saturday 12:00 now; Sofia works until 17:00.
    found = times(slots(empty_calendar, ["Classic facial"], "2026-10-10", "Sofia"))
    assert found[0] == "14:00"
    assert found[-1] == "16:15"


def test_dates_outside_the_booking_window_are_rejected(empty_calendar):
    for day in ("2026-10-09", "2026-12-10"):  # yesterday, 61 days ahead
        response = slots(empty_calendar, ["Classic facial"], day)
        assert response.status_code == 422
        assert response.json()["detail"] == "Please choose a date within the next 60 days."
    assert slots(empty_calendar, ["Classic facial"], "2026-12-09").status_code == 200


def test_therapist_day_off_and_studio_closure(empty_calendar, db):
    client = empty_calendar
    lena = therapist_id(client, "Lena")
    db.add(DayOff(therapist_id=lena, date=date(2026, 10, 13), reason="Holiday"))
    db.commit()
    assert times(slots(client, ["Deep tissue massage"], TUESDAY)) == []
    # Sofia still offers relaxation massage that day
    assert {s["therapist_name"] for s in slots(client, ["Relaxation massage"], TUESDAY)
            .json()["slots"]} == {"Sofia"}

    db.add(DayOff(therapist_id=None, date=date(2026, 10, 14), reason="Studio closed"))
    db.commit()
    assert times(slots(client, ["Relaxation massage"], "2026-10-14")) == []


def test_sunday_is_closed(empty_calendar):
    assert times(slots(empty_calendar, ["Relaxation massage"], "2026-10-11")) == []


def test_no_preference_picks_fewest_bookings_then_lowest_id(empty_calendar):
    client = empty_calendar
    # Tie (no bookings): Lena has the lower id.
    by_time = {s["time"]: s["therapist_name"]
               for s in slots(client, ["Relaxation massage"], TUESDAY).json()["slots"]}
    assert by_time["10:00"] == "Lena"

    # Lena gets a booking, so Sofia (0 bookings) wins wherever both are free...
    book(client, ["Deep tissue massage"], TUESDAY, "10:00", "Lena")
    by_time = {s["time"]: s["therapist_name"]
               for s in slots(client, ["Relaxation massage"], TUESDAY).json()["slots"]}
    assert by_time["14:00"] == "Sofia"
    assert by_time["09:00"] == "Sofia"  # only Sofia works at 9
    assert by_time["17:30"] == "Lena"  # Sofia stops at 17:00

    # ...and the saved booking follows the same rule.
    response = book(client, ["Relaxation massage"], TUESDAY, "14:00",
                    email="tom.becker@example.com")
    assert response.json()["therapist_name"] == "Sofia"


def test_times_are_correct_across_the_october_dst_change(empty_calendar, db):
    client = empty_calendar
    lena = therapist_id(client, "Lena")
    db.add(WorkingHours(therapist_id=lena, weekday=6, start_time=time(10), end_time=time(19)))
    db.commit()

    dst_day = slots(client, ["Deep tissue massage"], "2026-10-25", "Lena")  # clocks go back
    assert times(dst_day)[0] == "10:00"
    assert len(times(dst_day)) == 33  # no duplicated or missing hour
    assert dst_day.json()["slots"][0]["start_at"].startswith("2026-10-25T09:00:00")  # CET

    summer = slots(client, ["Deep tissue massage"], "2026-10-20", "Lena")
    assert summer.json()["slots"][0]["start_at"].startswith("2026-10-20T08:00:00")  # CEST
