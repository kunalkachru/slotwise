"""Regression test for a late confirmation releasing a waitlisted slot."""

from app.models import Booking
from tests.conftest import book, manage_token
from tests.test_email_confirmation import HOLD_ERROR, TUESDAY, at, times
from tests.test_waitlist import JOBS, entry_status, join, offers_sent


def test_late_confirmation_releases_slot_to_waitlist(empty_calendar, monkeypatch, db):
    client = empty_calendar
    join(client, "Tom", services=("Classic facial",))
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
                confirm=False).json()
    token = manage_token(client, body["id"])

    at(monkeypatch, 2026, 10, 10, 12, 45)
    late = client.post(f"/public/bookings/{token}/verify")
    assert late.status_code == 410 and late.json()["detail"] == HOLD_ERROR
    db.expire_all()
    assert db.get(Booking, body["id"]).status == "expired"
    assert "10:00" in times(client)

    result = client.post("/internal/run-jobs", headers=JOBS).json()
    assert result["unconfirmed_bookings_expired"] == 1
    db.expire_all()
    assert db.get(Booking, body["id"]).status == "expired"
    assert entry_status(db, "Tom") == "offered"
    [mail] = offers_sent(client)
    assert mail.to == "tom@example.com" and mail.subject.startswith("A time is free")

    again = client.post("/internal/run-jobs", headers=JOBS).json()
    assert again["unconfirmed_bookings_expired"] == 0
    assert len(offers_sent(client)) == 1
