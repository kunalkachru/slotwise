"""Studio settings: details shown publicly and in emails, and the booking rules."""

import pytest

from tests.conftest import book, login, manage_token, slots

TUESDAY = "2026-10-13"


@pytest.fixture
def owner(empty_calendar):
    login(empty_calendar)
    return empty_calendar


def settings(owner, **changes):
    current = owner.get("/owner/studio").json()
    return owner.put("/owner/studio", json={**current, **changes})


def test_settings_need_a_session(client):
    assert client.get("/owner/studio").status_code == 401
    assert client.put("/owner/studio", json={}).status_code in (401, 422)


def test_details_update_the_home_page_and_emails(owner):
    response = settings(owner, name="Isar Wellness Studio",
                        address="Lindwurmstraße 5, 80337 München",
                        phone="+49 89 123 456 78", email=" Hello@Isar-Wellness.de ")
    assert response.status_code == 200, response.json()
    assert response.json()["email"] == "hello@isar-wellness.de"
    studio = owner.get("/public/studio").json()
    assert (studio["name"], studio["phone"]) == ("Isar Wellness Studio", "+49 89 123 456 78")

    book(owner, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    email = owner.app.state.mailer.outbox[-1]
    assert email.reply_to == "hello@isar-wellness.de"
    assert "Lindwurmstraße 5, 80337 München" in email.text
    assert "Isar Wellness Studio" in email.subject


def test_booking_rules_take_effect_and_messages_follow_them(owner):
    assert settings(owner, min_notice_hours=24, booking_window_days=30).status_code == 200
    # Saturday 12:00 now: Monday is fine with 24 h notice, but nothing 31 days ahead.
    too_far = slots(owner, ["Classic facial"], "2026-11-10")
    assert too_far.status_code == 422
    assert too_far.json()["detail"] == "Please choose a date within the next 30 days."
    soon = book(owner, ["Classic facial"], "2026-10-10", "15:00", "Sofia")
    assert soon.status_code == 422
    assert soon.json()["detail"] == "Please choose a time between 24 hours and 30 days from now."


def test_receipt_prefix_and_free_cancellation_are_used(owner, monkeypatch):
    from datetime import datetime

    from app import clock

    settings(owner, receipt_prefix="iws", free_cancellation_hours=48)
    booking = book(owner, ["Classic facial"], TUESDAY, "10:00", "Sofia").json()
    token = manage_token(owner, booking["id"])
    assert "Free cancellation until Sun 11 Oct, 10:00" in owner.app.state.mailer.outbox[-1].text
    moment = datetime(2026, 10, 12, 9, 0, tzinfo=clock.BERLIN)  # 25 h before: now late
    monkeypatch.setattr(clock, "now", lambda: moment)
    assert owner.post(f"/public/bookings/{token}/cancel").json()["late_cancellation"] is True
    assert owner.get("/owner/studio").json()["receipt_prefix"] == "IWS"


@pytest.mark.parametrize("change, field", [
    ({"name": " "}, "name"),
    ({"address": ""}, "address"),
    ({"phone": "12"}, "phone"),
    ({"email": "not-an-email"}, "email"),
    ({"min_notice_hours": 100}, "min_notice_hours"),
    ({"booking_window_days": 0}, "booking_window_days"),
    ({"free_cancellation_hours": -1}, "free_cancellation_hours"),
    ({"waitlist_offer_minutes": 2}, "waitlist_offer_minutes"),
    ({"receipt_prefix": "IW-2026"}, "receipt_prefix"),
    ({"vat_mode": "16"}, "vat_mode"),
    ({"tax_number": "1" * 41}, "tax_number"),
])
def test_invalid_settings_are_rejected_with_the_field(owner, change, field):
    response = settings(owner, **change)
    assert response.status_code == 422
    assert response.json()["fields"][0]["field"] == field


def test_vat_settings_are_saved_and_shown_on_receipts(owner):
    assert owner.get("/owner/studio").json()["vat_mode"] == "19"  # the default
    response = settings(owner, vat_mode="7", tax_number="  143/123/45678 ")
    assert response.status_code == 200, response.json()
    studio = owner.get("/public/studio").json()
    assert (studio["vat_mode"], studio["tax_number"]) == ("7", "143/123/45678")
    settings(owner, tax_number="")
    assert owner.get("/public/studio").json()["tax_number"] is None
