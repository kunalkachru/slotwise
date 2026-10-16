"""GDPR requests: the owner can export a customer's data or erase it."""

import json

import pytest

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
    assert data["customer"]["email"] == "anna.mueller@example.com"
    [entry] = data["bookings"]
    assert entry["start"] == "2026-10-13T17:00+02:00" and entry["total_price"] == "82.00"
    assert [i["name"] for i in entry["items"]] == ["Deep tissue massage", "Hot stones"]
    assert entry["note"] == "Shoulders, please"
    assert manage_token(client, booking["id"]) not in response.text  # keys aren't data


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
