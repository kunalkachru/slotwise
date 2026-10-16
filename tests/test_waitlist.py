"""Slice 5: waitlist join, offers on cancellation, claim/decline/expiry, run-jobs."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app import clock
from app.models import Booking, Customer, WaitlistEntry
from tests.conftest import book, login, manage_token, menu_ids, slots, therapist_id

TUESDAY = "2026-10-13"
JOBS = {"X-Jobs-Secret": "test-jobs-secret"}


def at(monkeypatch, *args):
    moment = datetime(*args, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: moment)


def confirm_waitlist(client, name):
    """Click the double opt-in link for this person's newest waitlist request."""
    with client.app.state.session_factory() as session:
        customer = session.scalar(select(Customer).where(Customer.first_name == name))
        token = session.scalar(select(WaitlistEntry.confirm_token).where(
            WaitlistEntry.customer_id == customer.id).order_by(WaitlistEntry.id.desc()))
    return client.post(f"/public/waitlist/confirm/{token}")


def join(client, name, services=("Foot reflexology",), day=TUESDAY, earliest="09:00",
         latest="18:00", therapist=None, add_ons=(), confirm=True):
    ids = menu_ids(client)
    response = client.post("/public/waitlist", json={
        "service_ids": [ids[s] for s in services], "add_on_ids": [ids[a] for a in add_ons],
        "therapist_id": therapist_id(client, therapist) if therapist else None,
        "preferred_date": day, "earliest_time": earliest, "latest_time": latest,
        "first_name": name, "last_name": "Waiting", "email": f"{name.lower()}@example.com",
        "phone": "+49 151 0000 0100"})
    if confirm and response.status_code == 200:
        confirm_waitlist(client, name)
    return response


def offers_sent(client):
    return [e for e in client.app.state.mailer.outbox if e.subject.startswith("A time is free")]


def offer_token(db, name):
    db.expire_all()
    customer = db.scalar(select(Customer).where(Customer.first_name == name))
    return db.scalar(select(WaitlistEntry.offer_token).where(
        WaitlistEntry.customer_id == customer.id))


def entry_status(db, name):
    db.expire_all()
    customer = db.scalar(select(Customer).where(Customer.first_name == name))
    return db.scalar(select(WaitlistEntry.status).where(WaitlistEntry.customer_id == customer.id))


@pytest.fixture
def lena_booked(empty_calendar):
    """Lena: foot reflexology Tue 13 Oct 15:00 (30 min), booked by Priya."""
    response = book(empty_calendar, ["Foot reflexology"], TUESDAY, "15:00", "Lena",
                    first_name="Priya", email="priya.shah@example.com")
    assert response.status_code == 200
    return empty_calendar, manage_token(empty_calendar, response.json()["id"])


# ---------- joining ----------

def joined_mails(client):
    return [e for e in client.app.state.mailer.outbox if e.subject.startswith("Waitlist for")]


def test_join_emails_the_position_and_the_response_reveals_nothing(empty_calendar, db):
    client = empty_calendar
    first = join(client, "Tom")
    assert first.status_code == 200
    assert first.json() == {"status": "received", "preferred_date": TUESDAY}
    join(client, "Mia")
    [tom, mia] = joined_mails(client)
    assert tom.to == "tom@example.com" and "number 1" in tom.text
    assert mia.to == "mia@example.com" and "number 2" in mia.text

    # Joining again for the same day: same response, no new entry, an email to the owner.
    again = join(client, "Tom", services=("Back and neck massage",))
    assert again.status_code == 200 and again.json() == first.json()
    assert db.query(WaitlistEntry).count() == 2
    assert "already on the waitlist" in joined_mails(client)[-1].text
    assert join(client, "Tom", day="2026-10-14").status_code == 200  # another day is fine
    assert db.query(WaitlistEntry).count() == 3


def test_joins_are_limited_per_inbox(empty_calendar):
    """Security review finding: nobody can sign a stranger up for many days of emails."""
    client = empty_calendar
    ids = menu_ids(client)
    for i, day in enumerate(("2026-10-13", "2026-10-14", "2026-10-15")):
        response = client.post("/public/waitlist", headers={"X-Forwarded-For": f"203.0.113.{i}"},
                               json={"service_ids": [ids["Foot reflexology"]], "add_on_ids": [],
                                     "preferred_date": day, "earliest_time": "09:00",
                                     "latest_time": "18:00", "first_name": "Victim",
                                     "last_name": "X", "email": f"victim+{i}@example.com",
                                     "phone": "+49 151 0000 0100"})
        assert response.status_code == 200
    blocked = client.post("/public/waitlist", headers={"X-Forwarded-For": "203.0.113.99"},
                          json={"service_ids": [ids["Foot reflexology"]], "add_on_ids": [],
                                "preferred_date": "2026-10-16", "earliest_time": "09:00",
                                "latest_time": "18:00", "first_name": "Victim", "last_name": "X",
                                "email": "VICTIM@example.com", "phone": "+49 151 0000 0100"})
    assert blocked.status_code == 429


def test_open_entries_per_customer_are_capped(empty_calendar, db):
    from app.logic import waitlist as wl

    client = empty_calendar
    limiter = client.app.state.booking_limiter
    for day in ("2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17",
                "2026-10-19"):
        limiter._events.clear()  # isolate the cap from the daily join limit
        assert join(client, "Tom", day=day).status_code == 200
    assert db.query(WaitlistEntry).count() == wl.MAX_OPEN_ENTRIES_PER_CUSTOMER
    # Security review finding: the join that changed nothing is not silent.
    last = client.app.state.mailer.outbox[-1]
    assert last.to == "tom@example.com"
    assert "could not add you to the waitlist" in last.text
    assert "already has 5 open waitlist requests" in last.text


def test_join_validation(empty_calendar):
    client = empty_calendar
    assert join(client, "Tom", earliest="15:00", latest="10:00").status_code == 422
    assert join(client, "Tom", day="2026-12-31").status_code == 422
    # Lena doesn't do facials (a combination of Lena + Sofia is fine: option B).
    assert join(client, "Tom", services=("Deep tissue massage", "Classic facial"),
                therapist="Lena").status_code == 404
    closed = join(client, "Tom", day="2026-10-11")  # Sunday
    assert closed.status_code == 422
    assert closed.json()["detail"] == (
        "Nobody offers this treatment on that day, so no time can free up.")
    assert join(client, "Tom", services=("Classic facial",), day="2026-10-12").status_code \
        == 422  # Sofia (facials) doesn't work Mondays


# ---------- offers ----------

def test_cancellation_offers_the_slot_in_join_order_to_fitting_entries(lena_booked, db):
    client, token = lena_booked
    join(client, "Wrongday", day="2026-10-14")
    join(client, "Late", earliest="16:00", latest="18:00")  # window doesn't include 15:00
    join(client, "Sofiaonly", services=("Relaxation massage",), therapist="Sofia")
    join(client, "Toolong", services=("Deep tissue massage",))  # 60 min won't fit? (fits)
    join(client, "Tom")  # foot reflexology, any therapist, 09–18
    # Make the 60-min treatment not fit: Lena is busy right after the freed slot.
    book(client, ["Back and neck massage"], TUESDAY, "15:45", "Lena",
         email="other@example.com", first_name="Other")

    client.post(f"/public/bookings/{token}/cancel")
    [mail] = offers_sent(client)
    assert mail.to == "tom@example.com"
    assert "Tue 13 Oct, 15:00 with Lena (30 min)" in mail.text
    assert entry_status(db, "Tom") == "offered"
    for name in ("Wrongday", "Late", "Sofiaonly", "Toolong"):
        assert entry_status(db, name) == "waiting", name


def test_only_one_open_offer_per_slot(lena_booked, db):
    from app.logic.waitlist import offer_slot

    client, token = lena_booked
    join(client, "Tom")
    join(client, "Mia")
    client.post(f"/public/bookings/{token}/cancel")
    booking = db.scalar(select(Booking))
    again = offer_slot(db, client.app.state.mailer, "http://x", booking.therapist_id,
                       booking.start_at)
    assert again is None
    assert entry_status(db, "Mia") == "waiting"


def test_offer_page_shows_the_slot_but_no_customer_details(lena_booked, db):
    client, token = lena_booked
    join(client, "Tom")
    client.post(f"/public/bookings/{token}/cancel")
    response = client.get(f"/public/waitlist/offers/{offer_token(db, 'Tom')}")
    assert response.status_code == 200
    body = response.json()
    assert (body["status"], body["date"], body["time"], body["therapist_name"]) == (
        "open", TUESDAY, "15:00", "Lena")
    assert body["total_price"] == "42.00"
    assert "tom@example.com" not in response.text and "Waiting" not in response.text
    assert client.get("/public/waitlist/offers/unknown").status_code == 404


def test_claiming_books_the_slot_with_source_waitlist(lena_booked, db):
    client, token = lena_booked
    join(client, "Tom")
    client.post(f"/public/bookings/{token}/cancel")
    claimed = client.post(f"/public/waitlist/offers/{offer_token(db, 'Tom')}/claim")
    assert claimed.status_code == 200, claimed.json()
    body = claimed.json()
    assert (body["source"], body["time"], body["therapist_name"]) == ("waitlist", "15:00", "Lena")
    assert entry_status(db, "Tom") == "booked"
    assert "15:00" not in [s["time"] for s in slots(client, ["Foot reflexology"], TUESDAY,
                                                    "Lena").json()["slots"]]
    twice = client.post(f"/public/waitlist/offers/{offer_token(db, 'Tom')}/claim")
    assert twice.status_code == 400
    confirmation = client.app.state.mailer.outbox[-1]
    assert confirmation.to == "tom@example.com" and confirmation.subject.startswith("Booking")


def test_expired_offer_passes_to_the_next_person(lena_booked, db, monkeypatch):
    client, token = lena_booked
    join(client, "Tom")
    join(client, "Mia")
    client.post(f"/public/bookings/{token}/cancel")
    tom_token = offer_token(db, "Tom")
    at(monkeypatch, 2026, 10, 10, 12, 31)  # 31 minutes later

    run = client.post("/internal/run-jobs", headers=JOBS).json()
    assert run["offers_expired"] == 1 and run["offers_passed_on"] == 1
    assert entry_status(db, "Tom") == "expired"
    assert entry_status(db, "Mia") == "offered"
    assert [m.to for m in offers_sent(client)] == ["tom@example.com", "mia@example.com"]

    late = client.post(f"/public/waitlist/offers/{tom_token}/claim")
    assert late.status_code == 410
    assert late.json()["detail"] == "Sorry, this offer has expired."
    assert client.get(f"/public/waitlist/offers/{tom_token}").status_code == 410


def test_claim_after_deadline_expires_immediately_even_before_run_jobs(lena_booked, db,
                                                                        monkeypatch):
    client, token = lena_booked
    join(client, "Tom")
    join(client, "Mia")
    client.post(f"/public/bookings/{token}/cancel")
    at(monkeypatch, 2026, 10, 10, 12, 45)
    assert client.post(f"/public/waitlist/offers/{offer_token(db, 'Tom')}/claim") \
        .status_code == 410
    assert entry_status(db, "Mia") == "offered"


def test_declining_passes_the_slot_on(lena_booked, db):
    client, token = lena_booked
    join(client, "Tom")
    join(client, "Mia")
    client.post(f"/public/bookings/{token}/cancel")
    assert client.post(f"/public/waitlist/offers/{offer_token(db, 'Tom')}/decline") \
        .status_code == 204
    assert entry_status(db, "Tom") == "removed"
    assert entry_status(db, "Mia") == "offered"


def test_owner_cancellation_also_offers_the_slot(lena_booked, db):
    client, _ = lena_booked
    login(client)
    join(client, "Tom")
    booking_id = db.scalar(select(Booking.id))
    client.put(f"/owner/bookings/{booking_id}/status", json={"status": "cancelled"})
    assert entry_status(db, "Tom") == "offered"


def test_owner_waitlist_page_data_and_removal(lena_booked, db):
    client, _ = lena_booked
    login(client)
    join(client, "Tom", add_ons=())
    entries = client.get("/owner/waitlist", params={"date": TUESDAY}).json()
    assert [(e["customer_name"], e["services"], e["status"]) for e in entries] == [
        ("Tom Waiting", ["Foot reflexology"], "waiting")]
    assert client.delete(f"/owner/waitlist/{entries[0]['id']}").status_code == 204
    assert entry_status(db, "Tom") == "removed"


# ---------- run-jobs ----------

def test_run_jobs_needs_the_secret(empty_calendar):
    client = empty_calendar
    assert client.post("/internal/run-jobs").status_code == 401
    assert client.post("/internal/run-jobs", headers={"X-Jobs-Secret": "wrong"}).status_code == 401
    assert client.post("/internal/run-jobs", headers=JOBS).status_code == 200


def test_run_jobs_without_a_configured_secret_is_closed(make_client, frozen_now):
    client = make_client(jobs_secret=None)
    assert client.post("/internal/run-jobs", headers={"X-Jobs-Secret": ""}).status_code == 401


def test_reminders_are_sent_once_within_24_hours(empty_calendar, monkeypatch, db):
    client = empty_calendar
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia")  # booked Sat 10 Oct
    client.app.state.mailer.outbox.clear()

    at(monkeypatch, 2026, 10, 12, 9, 0)  # 25 h before: too early
    assert client.post("/internal/run-jobs", headers=JOBS).json()["reminders_sent"] == 0
    at(monkeypatch, 2026, 10, 12, 10, 15)  # 23 h 45 min before
    assert client.post("/internal/run-jobs", headers=JOBS).json()["reminders_sent"] == 1
    assert client.post("/internal/run-jobs", headers=JOBS).json()["reminders_sent"] == 0
    [reminder] = client.app.state.mailer.outbox
    assert reminder.subject.startswith("Reminder:")
    assert "&action=confirm" in reminder.text and "&action=cancel" in reminder.text


def test_no_reminder_for_bookings_made_less_than_24_hours_ahead(empty_calendar, monkeypatch):
    client = empty_calendar
    at(monkeypatch, 2026, 10, 12, 18, 0)
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia")  # 16 h ahead
    client.app.state.mailer.outbox.clear()
    assert client.post("/internal/run-jobs", headers=JOBS).json()["reminders_sent"] == 0
    assert list(client.app.state.mailer.outbox) == []


def test_customers_are_anonymized_two_years_after_their_last_booking(client, db, monkeypatch):
    ben = db.scalar(select(Customer).where(Customer.first_name == "Ben"))
    ben_id = ben.id
    last = max(b.start_at for b in ben.bookings)
    monkeypatch.setattr(clock, "now", lambda: last + timedelta(days=731))
    result = client.post("/internal/run-jobs", headers=JOBS).json()
    assert result["customers_anonymized"] >= 1
    db.expire_all()
    ben = db.get(Customer, ben_id)
    assert (ben.first_name, ben.phone, ben.anonymized_at is not None) == ("Anonymized", "", True)
    assert ben.email == f"anonymized-{ben_id}@invalid.example"
    assert all(b.total_price is not None for b in ben.bookings)  # bookings and receipts kept
