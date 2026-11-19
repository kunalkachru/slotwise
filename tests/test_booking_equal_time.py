"""Regression test for bookings whose end time equals their start time."""

import pytest
from sqlalchemy import select

from app.models import Booking
from tests.conftest import CUSTOMER, menu_ids


@pytest.mark.parametrize("acceptance_check", ["AC-1"], ids=["AC-1"])
def test_booking_rejects_end_time_equal_to_start_time(empty_calendar, db, acceptance_check):
    client = empty_calendar
    ids = menu_ids(client)

    response = client.post("/public/bookings", json={
        "service_ids": [ids["Classic facial"]],
        "add_on_ids": [],
        "therapist_id": None,
        "date": "2026-10-13",
        "start_time": "12:00",
        "end_time": "12:00",
        **CUSTOMER,
    })

    assert response.status_code == 422
    assert response.json()["detail"] == "End time must be after start time."
    assert db.scalar(select(Booking.id)) is None
