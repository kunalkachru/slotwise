"""GDPR requests: the owner can export a customer's data or erase it."""

import json
from decimal import Decimal

import pytest

from app.models import Booking
from tests.conftest import book, login, manage_token

TUESDAY = "2026-10-13"


@pytest.fixture
def booked(empty_calendar):
    client = empty_calendar
    booking = book(client, ["Deep tissue massage"], TUESDAY, "17:00", "Lena",
                   add_ons=[("Deep tissue massage", "Hot stones")], note="Shoulders, please").json()
    login(client)
    detail = client.get(f"/owner/bookings/{booking['id']}").json()
    return client, booking, detail["customer"]["id"]


def test_export_has_the_customers_data_but_no_link_tokens(booked):
    client, booking, customer_id = booked
    response = client.get(f"/owner/customers/{customer_id}/export")
    assert response.status_code == 200
    assert 'filename="customer-' in response.headers["content-disposition"]
    assert response.headers["cache-control"] == "no-store"
    data = json.loads(response.text)
    assert data["customer"] == {
        "first_name": "Anna",
        "last_name": "Müller",
        "email": "anna.mueller@example.com",
        "phone": "+49 151 0000 0001",
        "no_shows": 0,
        "anonymized_at": None,
    }
    [entry] = data["bookings"]
    booked_at = entry["booked_at"]
    assert entry == {
        "start": "2026-10-13T17:00+02:00",
        "end": "2026-10-13T18:15+02:00",
        "status": "booked",
        "therapist": "Lena",
        "source": "online",
        "items": [
            {"name": "Deep tissue massage", "quantity": 1, "unit_price": "70.00"},
            {"name": "Hot stones", "quantity": 1, "unit_price": "12.00"},
        ],
        "total_price": "82.00",
        "receipt_number": None,
        "note": "Shoulders, please",
        "booked_at": booked_at,
    }
    assert [i["name"] for i in entry["items"]] == ["Deep tissue massage", "Hot stones"]
    assert entry["note"] == "Shoulders, please"
    assert data["waitlist"] == []
    assert data["summary"] == {
        "total_bookings": 1,
        "completed_visits": 0,
        "no_shows": 0,
        "total_spent_on_completed_bookings": "0.00",
        "last_completed_visit": None,
    }
    assert manage_token(client, booking["id"]) not in response.text  # keys aren't data


def test_export_includes_customer_booking_summary(booked):
    client, booking, customer_id = booked
    second = book(client, ["Deep tissue massage"], "2026-10-14", "17:00", "Lena").json()
    third = book(client, ["Deep tissue massage"], "2026-10-15", "17:00", "Lena").json()

    with client.app.state.session_factory() as session:
        first_booking = session.get(Booking, booking["id"])
        second_booking = session.get(Booking, second["id"])
        third_booking = session.get(Booking, third["id"])
        first_booking.status = "done"
        first_booking.total_price = Decimal("82.00")
        second_booking.status = "no_show"
        second_booking.total_price = Decimal("50.00")
        third_booking.status = "done"
        third_booking.total_price = Decimal("99.00")
        session.commit()

    data = client.get(f"/owner/customers/{customer_id}/export").json()

    assert data["summary"] == {
        "total_bookings": 3,
        "completed_visits": 2,
        "no_shows": 1,
        "total_spent_on_completed_bookings": "181.00",
        "last_completed_visit": "2026-10-15",
    }


def test_erase_anonymizes_but_keeps_amounts_and_is_idempotent(booked):
    client, booking, customer_id = booked
    assert client.post(f"/owner/customers/{customer_id}/erase").status_code == 200
    detail = client.get(f"/owner/bookings/{booking['id']}").json()
    assert detail["customer"]["first_name"] == "Anonymized"
    assert detail["customer"]["email"].endswith("@invalid.example")
    assert detail["customer_note"] is None
    assert detail["total_price"] == "82.00"  # tax law: amounts and dates stay
    assert client.post(f"/owner/customers/{customer_id}/erase").status_code == 200  # again: fine
    exported = client.get(f"/owner/customers/{customer_id}/export").json()
    assert exported["customer"]["anonymized_at"] is not None


def test_customer_data_needs_the_owner(empty_calendar):
    assert empty_calendar.get("/owner/customers/1/export").status_code == 401
    assert empty_calendar.post("/owner/customers/1/erase").status_code == 401


def test_unknown_customer_is_404(empty_calendar):
    login(empty_calendar)
    assert empty_calendar.get("/owner/customers/999/export").status_code == 404
