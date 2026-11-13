"""S-24: a late confirmation click must still refill the released slot."""

from datetime import datetime

from sqlalchemy import select

from app import clock
from app.models import Booking, WaitlistEntry
from tests.conftest import book, manage_token
from tests.test_waitlist import JOBS, join

TUESDAY = "2026-10-13"


def test_late_confirmation_releases_slot_to_waitlist(empty_calendar, monkeypatch, db):
    client = empty_calendar
    join(client, "Tom", services=("Classic facial",))
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia",
                confirm=False).json()
    token = manage_token(client, body["id"])

    monkeypatch.setattr(
        clock, "now", lambda: datetime(2026, 10, 10, 12, 45, tzinfo=clock.BERLIN)
    )
    late = client.post(f"/public/bookings/{token}/verify")

    assert late.status_code == 410
    db.expire_all()
    assert db.get(Booking, body["id"]).status == "expired"
    assert db.scalar(select(WaitlistEntry.status)) == "offered"
    assert any(message.subject.startswith("A time is free")
               for message in client.app.state.mailer.outbox)

    result = client.post("/internal/run-jobs", headers=JOBS).json()
    assert result["unconfirmed_bookings_expired"] == 1
