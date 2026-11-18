"""T1: token-scoped customer booking list and cancellation behavior."""

from datetime import datetime

import pytest

from app import clock
from tests.conftest import book, manage_token, slots

TUESDAY = "2026-10-13"


@pytest.mark.parametrize("_ac", [pytest.param(None, id="AC-1")])
def test_verified_manage_link_lists_customer_bookings_with_cancel_action_for_each_upcoming(
    empty_calendar, _ac
):
    client = empty_calendar
    first = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    second = book(client, ["Deep tissue massage"], TUESDAY, "17:00", "Lena").json()
    token = manage_token(client, first["id"])

    response = client.get(f"/public/bookings/{token}/list")

    assert response.status_code == 200
    listed = response.json()["bookings"]
    assert {booking["id"] for booking in listed} == {first["id"], second["id"]}
    assert all(booking["can_cancel"] for booking in listed)
    assert all("Cancel" not in booking for booking in listed)


@pytest.mark.parametrize("_ac", [pytest.param(None, id="AC-2")])
def test_customer_cancel_marks_booking_cancelled_and_frees_slot(empty_calendar, _ac):
    client = empty_calendar
    created = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    token = manage_token(client, created["id"])
    assert "10:00" not in [
        s["time"] for s in slots(client, ["Classic facial"], TUESDAY, "Sofia").json()["slots"]
    ]

    response = client.post(f"/public/bookings/{token}/list/{created['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["booking"]["status"] == "cancelled"
    listed = client.get(f"/public/bookings/{token}/list").json()["bookings"]
    assert next(b for b in listed if b["id"] == created["id"])["status"] == "cancelled"
    assert "10:00" in [
        s["time"] for s in slots(client, ["Classic facial"], TUESDAY, "Sofia").json()["slots"]
    ]


@pytest.mark.parametrize("_ac", [pytest.param(None, id="AC-3")])
def test_customer_cannot_cancel_started_booking_shows_started_message(
    empty_calendar, monkeypatch, _ac
):
    client = empty_calendar
    created = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    token = manage_token(client, created["id"])
    monkeypatch.setattr(clock, "now", lambda: datetime(2026, 10, 13, 10, 1, tzinfo=clock.BERLIN))

    response = client.post(f"/public/bookings/{token}/list/{created['id']}/cancel")

    assert response.status_code == 400
    assert "already started" in response.json()["detail"]
    assert client.get(f"/public/bookings/{token}/list").json()["bookings"][0]["can_cancel"] is False


@pytest.mark.parametrize("_ac", [pytest.param(None, id="AC-4")])
def test_customer_cannot_cancel_cancelled_booking_shows_already_cancelled_message(
    empty_calendar, _ac
):
    client = empty_calendar
    created = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    token = manage_token(client, created["id"])
    assert client.post(f"/public/bookings/{token}/cancel").status_code == 200

    response = client.post(f"/public/bookings/{token}/list/{created['id']}/cancel")

    assert response.status_code == 400
    assert "already cancelled" in response.json()["detail"]
    booking = client.get(f"/public/bookings/{token}/list").json()["bookings"][0]
    assert booking["status"] == "cancelled" and booking["can_cancel"] is False
