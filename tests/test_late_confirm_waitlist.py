"""Regression test for a late booking confirmation releasing a waitlist slot."""

from tests.conftest import book, manage_token
from tests.test_email_confirmation import at
from tests.test_waitlist import JOBS, join


def test_late_confirmation_releases_slot_to_waitlist(empty_calendar, monkeypatch):
    client = empty_calendar
    join(client, "Tom", services=("Classic facial",))
    booking = book(client, ["Classic facial"], "2026-10-13", "10:00", "Sofia",
                   confirm=False).json()

    at(monkeypatch, 2026, 10, 10, 12, 45)
    token = manage_token(client, booking["id"])
    late = client.post(f"/public/bookings/{token}/verify")
    assert late.status_code == 410

    result = client.post("/internal/run-jobs", headers=JOBS).json()
    assert result["unconfirmed_bookings_expired"] == 1
    assert any(mail.subject.startswith("A time is free") for mail in client.app.state.mailer.outbox)
