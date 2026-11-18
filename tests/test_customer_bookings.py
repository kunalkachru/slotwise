"""Customer bookings-list contract (S-118, T1)."""

import pytest

from tests.conftest import book, manage_token

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
