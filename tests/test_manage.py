"""Slice 3: confirmation email, manage link, confirm and cancel."""

import json
from datetime import datetime

import pytest

from app import clock
from app.emails import Mailer, reminder_email
from app.models import Booking, Studio
from tests.conftest import book, manage_token, slots

TUESDAY = "2026-10-13"


def outbox(client):
    return list(client.app.state.mailer.outbox)


def emails(client, subject_start):
    return [e for e in client.app.state.mailer.outbox if e.subject.startswith(subject_start)]


@pytest.fixture
def booked(empty_calendar):
    """Deep tissue + Hot stones with Lena, Tue 13 Oct 2026 at 17:00 (€82)."""
    response = book(empty_calendar, ["Deep tissue massage"], TUESDAY, "17:00", "Lena",
                    add_ons=[("Deep tissue massage", "Hot stones")])
    assert response.status_code == 200
    return empty_calendar, manage_token(empty_calendar, response.json()["id"])


def at(monkeypatch, year, month, day, hour, minute=0):
    moment = datetime(year, month, day, hour, minute, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: moment)


def test_booking_sends_an_itemized_confirmation_email(booked):
    client, token = booked
    [email] = emails(client, "Booking confirmed")
    assert email.to == "anna.mueller@example.com"
    assert email.subject.startswith("Booking confirmed: Tuesday 13 October 2026, 17:00")
    for text in (email.text, email.html):
        assert "Deep tissue massage" in text and "Hot stones" in text
        assert "€70.00" in text and "€12.00" in text and "€82.00" in text
        assert "Pay at the studio" in text
        assert f"http://localhost:8000/manage.html?token={token}" in text
    assert "Free cancellation until Mon 12 Oct, 17:00" in email.text
    assert email.reply_to == "hello@isar-wellness.example.com"


def test_email_html_escapes_customer_input(empty_calendar):
    book(empty_calendar, ["Classic facial"], TUESDAY, "10:00", "Sofia", first_name="O'Neil")
    [email] = emails(empty_calendar, "Booking confirmed")
    assert "Hello O&#x27;Neil" in email.html
    assert "O'Neil" not in email.html


def test_logs_never_contain_tokens_or_full_addresses(booked, caplog):
    import logging

    from app.logs import RedactTokens, redact

    client, token = booked
    assert token not in redact(f"GET /public/bookings/{token}/cancel and ?token={token}&x=1")
    access = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1,
                               '%s - "%s %s HTTP/%s" %d',
                               ("10.0.0.1:1", "GET", f"/public/bookings/{token}", "1.1", 200),
                               None)
    RedactTokens().filter(access)
    assert token not in access.getMessage() and "/public/bookings/<token>" in access.getMessage()

    with caplog.at_level(logging.INFO, logger="app.emails"):
        book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", email="tom.becker@example.com")
    logged = caplog.text
    assert "EMAIL (log only, not sent) to=to***@example.com" in logged
    assert "tom.becker@example.com" not in logged
    assert "token=<redacted>" in logged


def test_manage_link_shows_the_booking_without_customer_details(booked):
    client, token = booked
    response = client.get(f"/public/bookings/{token}")
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["date"], body["time"], body["therapist_name"]) == (
        "booked", TUESDAY, "17:00", "Lena")
    assert body["total_price"] == "82.00" and body["total_minutes"] == 75
    assert body["can_confirm"] and body["can_cancel"]
    assert body["free_cancellation_until"].startswith("2026-10-12T15:00:00")  # 17:00 CEST
    for private in ("Anna", "Müller", "anna.mueller", "+49", "manage_token"):
        assert private not in response.text


def test_unknown_token_is_404(empty_calendar):
    for path in ("/public/bookings/nope", "/public/bookings/nope/confirm",
                 "/public/bookings/nope/cancel"):
        response = (empty_calendar.get if path.count("/") == 3 else empty_calendar.post)(path)
        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Booking not found. Please check the link in your email.")


def test_confirm(booked, db):
    client, token = booked
    response = client.post(f"/public/bookings/{token}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    assert response.json()["can_confirm"] is False
    assert client.post(f"/public/bookings/{token}/confirm").status_code == 200  # idempotent
    booking = db.query(Booking).one()
    assert booking.confirmed_at is not None


def test_free_cancellation_up_to_24_hours_before(booked, monkeypatch, db):
    client, token = booked
    at(monkeypatch, 2026, 10, 12, 16, 59)  # 24 h 1 min before 17:00
    response = client.post(f"/public/bookings/{token}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["late_cancellation"] is False
    booking = db.query(Booking).one()
    assert booking.cancelled_at is not None and booking.late_cancellation is False


def test_exactly_24_hours_before_is_still_free(booked, monkeypatch):
    client, token = booked
    at(monkeypatch, 2026, 10, 12, 17, 0)
    assert client.post(f"/public/bookings/{token}/cancel").json()["late_cancellation"] is False


def test_later_cancellation_is_allowed_but_flagged_late(booked, monkeypatch):
    client, token = booked
    at(monkeypatch, 2026, 10, 12, 17, 1)  # 23 h 59 min before
    response = client.post(f"/public/bookings/{token}/cancel")
    assert response.status_code == 200
    assert response.json()["late_cancellation"] is True


def test_cancelling_twice_or_after_the_start_is_rejected(booked, monkeypatch, empty_calendar):
    client, token = booked
    assert client.post(f"/public/bookings/{token}/cancel").status_code == 200
    again = client.post(f"/public/bookings/{token}/cancel")
    assert again.status_code == 400
    assert again.json()["detail"] == "This booking is already cancelled or finished."
    confirm = client.post(f"/public/bookings/{token}/confirm")
    assert confirm.status_code == 400
    assert confirm.json()["detail"] == "This booking can no longer be confirmed."

    other = manage_token(client, book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
                                      email="tom.becker@example.com").json()["id"])
    at(monkeypatch, 2026, 10, 13, 10, 30)  # appointment already started
    assert client.post(f"/public/bookings/{other}/cancel").status_code == 400
    assert client.post(f"/public/bookings/{other}/confirm").status_code == 400


def test_cancelling_frees_the_slot(booked):
    client, token = booked
    assert "17:00" not in [s["time"] for s in slots(client, ["Deep tissue massage"], TUESDAY,
                                                    "Lena").json()["slots"]]
    client.post(f"/public/bookings/{token}/cancel")
    assert "17:00" in [s["time"] for s in slots(client, ["Deep tissue massage"], TUESDAY,
                                                "Lena").json()["slots"]]


def test_reminder_email_has_one_click_confirm_and_cancel(booked, db):
    client, token = booked
    booking = db.query(Booking).one()
    email = reminder_email(booking, db.query(Studio).one(), "https://slotwise.example.com")
    assert f"https://slotwise.example.com/manage.html?token={token}&action=confirm" in email.text
    assert f"https://slotwise.example.com/manage.html?token={token}&action=cancel" in email.text
    assert "Hot stones" in email.html


def test_mailer_posts_to_resend_when_a_key_is_set(monkeypatch):
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout):
        captured.update(url=request.full_url, headers=dict(request.headers),
                        body=json.loads(request.data), timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    from app.emails import Email

    ok = Mailer("re_test_key", "Slotwise <hello@example.com>").send(
        Email(to="a@example.com", subject="Hi", text="t", html="<p>h</p>",
              reply_to="r@example.com"))
    assert ok
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer re_test_key"
    assert captured["body"] == {"from": "Slotwise <hello@example.com>", "to": ["a@example.com"],
                                "subject": "Hi", "text": "t", "html": "<p>h</p>",
                                "reply_to": "r@example.com"}


def test_a_failing_email_service_does_not_break_booking(empty_calendar, monkeypatch):
    import urllib.error

    def broken(*args, **kwargs):
        raise urllib.error.URLError("down")

    monkeypatch.setattr("urllib.request.urlopen", broken)
    empty_calendar.app.state.mailer.api_key = "re_test_key"
    response = book(empty_calendar, ["Classic facial"], TUESDAY, "10:00", "Sofia")
    assert response.status_code == 200


def test_booking_as_calendar_file(booked):
    client, token = booked
    response = client.get(f"/public/bookings/{token}/calendar.ics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert response.headers["cache-control"] == "no-store"
    assert 'filename="booking-2026-10-13.ics"' in response.headers["content-disposition"]
    body = response.text
    assert body.startswith("BEGIN:VCALENDAR\r\n") and body.endswith("END:VCALENDAR\r\n")
    assert "DTSTART:20261013T150000Z" in body  # 17:00 in Munich (summer time)
    assert "DTEND:20261013T161500Z" in body  # 75 minutes: Deep tissue + Hot stones
    assert "SUMMARY:Deep tissue massage · Isar Wellness" in body
    assert "LOCATION:Isarstraße 12\\, 80469 München" in body  # commas escaped
    assert all(len(line.encode()) <= 75 for line in body.split("\r\n"))  # folded
    [email] = emails(client, "Booking confirmed")
    assert f"/public/bookings/{token}/calendar.ics" in email.text  # "Add to your calendar"
    assert client.get("/public/bookings/nope/calendar.ics").status_code == 404
