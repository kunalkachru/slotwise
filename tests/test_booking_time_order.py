"""Regression test for bookings with an end time before their start time."""

from tests.conftest import CUSTOMER, menu_ids


def test_booking_rejects_end_time_before_start_time(empty_calendar):
    client = empty_calendar
    ids = menu_ids(client)

    response = client.post("/public/bookings", json={
        "service_ids": [ids["Classic facial"]],
        "add_on_ids": [],
        "therapist_id": None,
        "date": "2026-10-13",
        "start_time": "12:00",
        "end_time": "11:00",
        **CUSTOMER,
    })

    assert response.status_code == 422
    assert response.json()["detail"] == "End time must be after start time."
