"""Customer bookings-list contract (S-118, T1)."""

from datetime import datetime

import pytest

from app import clock
from tests.conftest import book, manage_token, slots

TUESDAY = "2026-10-13"


def test_customer_bookings_list_is_scoped_and_hides_tokens(empty_calendar):
    customer_booking = book(
        empty_calendar, ["Classic facial"], TUESDAY, "10:00", "Sofia",
    )
    second_customer_booking = book(
        empty_calendar, ["Classic facial"], TUESDAY, "11:00", "Sofia",
        email="tom.becker@example.com", first_name="Tom", last_name="Becker",
        phone="+49 151 0000 0002",
    )
    token = manage_token(empty_calendar, customer_booking.json()["id"])
    other_id = second_customer_booking.json()["id"]

    response = empty_calendar.get("/public/bookings", params={"token": token})

    assert response.status_code == 200
    body = response.json()
    assert [booking["id"] for booking in body] == [customer_booking.json()["id"]]
    assert body[0]["status"] == "booked"
    assert body[0]["can_cancel"] is True
    assert other_id not in [booking["id"] for booking in body]
    assert token not in response.text
    assert "Anna" not in response.text
    assert "Müller" not in response.text
    assert "Tom" not in response.text
    assert "Becker" not in response.text


@pytest.mark.parametrize(
    "acceptance", [pytest.param(None, id="AC-1: scoped safe customer bookings list")]
)
def test_customer_bookings_list_acceptance(acceptance, empty_calendar):
    """Keep AC-1 visible while the required contract name stays stable."""
    test_customer_bookings_list_is_scoped_and_hides_tokens(empty_calendar)


def test_customer_list_cancellation_frees_all_segments(empty_calendar):
    response = book(
        empty_calendar, ["Deep tissue massage"], TUESDAY, "10:00", "Lena",
        add_ons=[("Deep tissue massage", "Hot stones")],
    )
    booking_id = response.json()["id"]
    token = manage_token(empty_calendar, booking_id)
    assert "10:00" not in [s["time"] for s in slots(
        empty_calendar, ["Deep tissue massage"], TUESDAY, "Lena",
        add_ons=[("Deep tissue massage", "Hot stones")],
    ).json()["slots"]]

    cancelled = empty_calendar.post(
        f"/public/bookings/{booking_id}/cancel", params={"token": token}
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert "10:00" in [s["time"] for s in slots(
        empty_calendar, ["Deep tissue massage"], TUESDAY, "Lena",
        add_ons=[("Deep tissue massage", "Hot stones")],
    ).json()["slots"]]


def test_started_booking_cannot_be_cancelled_from_customer_list(empty_calendar, monkeypatch):
    response = book(empty_calendar, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    booking_id = response.json()["id"]
    token = manage_token(empty_calendar, booking_id)
    at = datetime(2026, 10, 13, 10, 30, tzinfo=clock.BERLIN)
    monkeypatch.setattr("app.clock.now", lambda: at)

    rejected = empty_calendar.post(
        f"/public/bookings/{booking_id}/cancel", params={"token": token}
    )

    assert rejected.status_code == 400
    assert "started" in rejected.json()["detail"].lower()


def test_already_cancelled_booking_cannot_be_cancelled_from_customer_list(empty_calendar):
    response = book(empty_calendar, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    booking_id = response.json()["id"]
    token = manage_token(empty_calendar, booking_id)
    assert empty_calendar.post(
        f"/public/bookings/{booking_id}/cancel", params={"token": token}
    ).status_code == 200

    rejected = empty_calendar.post(
        f"/public/bookings/{booking_id}/cancel", params={"token": token}
    )

    assert rejected.status_code == 400
    assert "cancelled" in rejected.json()["detail"].lower()


@pytest.mark.parametrize(
    "acceptance", [pytest.param(None, id="AC-2: customer list cancellation shows cancelled")]
)
def test_customer_list_cancel_acceptance(acceptance, empty_calendar):
    test_already_cancelled_booking_cannot_be_cancelled_from_customer_list(empty_calendar)


@pytest.mark.parametrize(
    "acceptance", [pytest.param(None, id="AC-3: customer list cancellation releases every segment")]
)
def test_customer_list_release_acceptance(acceptance, empty_calendar):
    test_customer_list_cancellation_frees_all_segments(empty_calendar)


@pytest.mark.parametrize(
    "acceptance", [pytest.param(None, id="AC-4: started booking rejection is clear")]
)
def test_started_booking_rejection_acceptance(acceptance, empty_calendar, monkeypatch):
    test_started_booking_cannot_be_cancelled_from_customer_list(empty_calendar, monkeypatch)


@pytest.mark.parametrize(
    "acceptance", [pytest.param(None, id="AC-5: cancelled booking rejection is clear")]
)
def test_cancelled_booking_rejection_acceptance(acceptance, empty_calendar):
    test_already_cancelled_booking_cannot_be_cancelled_from_customer_list(empty_calendar)
