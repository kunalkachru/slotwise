"""Regression coverage for owner day-off validation."""

from tests.conftest import book, login, therapist_id


def test_owner_rejects_past_and_booked_therapist_days_off(empty_calendar):
    client = empty_calendar
    assert login(client).status_code == 200

    past = client.post("/owner/days-off", json={
        "therapist_id": None,
        "date": "2026-10-09",
        "reason": "Backdated closure",
    })

    lena = therapist_id(client, "Lena")
    assert book(client, ["Deep tissue massage"], "2026-10-13", "12:00", "Lena").status_code == 200
    booked = client.post("/owner/days-off", json={
        "therapist_id": lena,
        "date": "2026-10-13",
        "reason": "Personal day",
    })
    assert (
        past.status_code == 422
        and "past" in past.json().get("detail", "").lower()
        and booked.status_code == 422
        and "booking" in booked.json().get("detail", "").lower()
    )
    assert client.get("/owner/days-off").json() == []


def test_owner_rejects_studio_day_off_with_affected_booking_count(empty_calendar):
    client = empty_calendar
    assert login(client).status_code == 200

    assert book(client, ["Deep tissue massage"], "2026-10-13", "12:00", "Lena").status_code == 200
    assert book(client, ["Classic facial"], "2026-10-13", "12:00", "Sofia",
                email="sofia.booking@example.com").status_code == 200

    rejected = client.post("/owner/days-off", json={
        "therapist_id": None,
        "date": "2026-10-13",
        "reason": "Studio closure",
    })

    assert rejected.status_code == 422
    assert "2 bookings are affected" in rejected.json().get("detail", "").lower()
    assert client.get("/owner/days-off").json() == []
