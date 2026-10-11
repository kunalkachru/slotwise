"""Email confirmation: online bookings and waitlist requests only count once the
address owner clicks the emailed link. Frozen now: Sat 10 Oct 2026 12:00 Berlin."""

from datetime import datetime

from sqlalchemy import select

from app import clock
from app.models import Booking, Customer, WaitlistEntry
from tests.conftest import book, login, manage_token, slots
from tests.test_waitlist import JOBS, confirm_waitlist, join

TUESDAY = "2026-10-13"
HOLD_ERROR = ("This booking request has expired because it wasn't confirmed in time. "
              "Please book again.")


def at(monkeypatch, *args):
    moment = datetime(*args, tzinfo=clock.BERLIN)
    monkeypatch.setattr(clock, "now", lambda: moment)


def subjects(client):
    return [e.subject for e in client.app.state.mailer.outbox]


def times(client, service="Classic facial", therapist="Sofia"):
    return [s["time"] for s in slots(client, [service], TUESDAY, therapist).json()["slots"]]


# ---------- bookings ----------

def test_online_booking_waits_for_the_email_click(empty_calendar, db):
    client = empty_calendar
    response = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False)
    body = response.json()
    assert body["status"] == "pending" and "manage_token" not in body
    [mail] = client.app.state.mailer.outbox
    assert mail.subject.startswith("Please confirm your booking")
    token = manage_token(client, body["id"])
    assert f"/manage.html?token={token}&action=verify" in mail.text
    assert "holding the time for you until 12:30" in mail.text
    assert "10:00" not in times(client)  # the slot is held while pending

    view = client.get(f"/public/bookings/{token}").json()
    assert view["awaiting_email_confirmation"] is True and view["can_confirm"] is False

    verified = client.post(f"/public/bookings/{token}/verify")
    assert verified.status_code == 200 and verified.json()["status"] == "booked"
    assert subjects(client)[-1].startswith("Booking confirmed")
    again = client.post(f"/public/bookings/{token}/verify")
    assert again.status_code == 200
    assert sum(s.startswith("Booking confirmed") for s in subjects(client)) == 1


def test_unconfirmed_hold_expires_and_frees_the_slot(empty_calendar, monkeypatch, db):
    client = empty_calendar
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False).json()
    token = manage_token(client, body["id"])
    at(monkeypatch, 2026, 10, 10, 12, 31)  # 31 minutes later
    assert "10:00" in times(client)  # free again, even before run-jobs runs
    late = client.post(f"/public/bookings/{token}/verify")
    assert late.status_code == 410 and late.json()["detail"] == HOLD_ERROR
    db.expire_all()
    assert db.get(Booking, body["id"]).status == "expired"


def test_run_jobs_expires_stale_holds_and_offers_the_slot(empty_calendar, monkeypatch, db):
    client = empty_calendar
    join(client, "Tom", services=("Classic facial",))  # confirmed waitlist entry
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False).json()
    at(monkeypatch, 2026, 10, 10, 12, 45)
    result = client.post("/internal/run-jobs", headers=JOBS).json()
    assert result["unconfirmed_bookings_expired"] == 1
    db.expire_all()
    assert db.get(Booking, body["id"]).status == "expired"
    assert any(s.startswith("A time is free") for s in subjects(client))


def test_withdrawing_an_unconfirmed_booking_is_not_a_cancellation(empty_calendar, db):
    client = empty_calendar
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False).json()
    token = manage_token(client, body["id"])
    assert client.post(f"/public/bookings/{token}/cancel").json()["status"] == "expired"
    login(client)
    dashboard = client.get("/owner/dashboard", params={"date": TUESDAY}).json()
    assert dashboard["today_bookings"] == 0 and dashboard["refill_rate"] is None


def test_phone_bookings_and_waitlist_claims_need_no_email_click(empty_calendar):
    client = empty_calendar
    login(client)
    from tests.conftest import menu_ids

    ids = menu_ids(client)
    phone = client.post("/owner/bookings", json={
        "service_ids": [ids["Classic facial"]], "add_on_ids": [], "therapist_id": None,
        "date": TUESDAY, "start_time": "11:00", "first_name": "Jonas", "last_name": "Klein",
        "email": "jonas.klein@example.com", "phone": "+49 151 0000 0002"})
    assert phone.json()["status"] == "booked"


def test_owner_can_confirm_a_pending_booking_by_hand(empty_calendar, monkeypatch):
    client = empty_calendar
    body = book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False).json()
    login(client)
    path = f"/owner/bookings/{body['id']}/status"
    assert client.put(path, json={"status": "expired"}).status_code == 400
    assert client.put(path, json={"status": "booked"}).json()["status"] == "booked"


def test_reminders_skip_unconfirmed_bookings(empty_calendar, monkeypatch):
    client = empty_calendar
    book(client, ["Classic facial"], TUESDAY, "10:00", "Sofia", confirm=False)
    at(monkeypatch, 2026, 10, 10, 12, 20)  # still inside the hold
    assert client.post("/internal/run-jobs", headers=JOBS).json()["reminders_sent"] == 0


# ---------- waitlist double opt-in ----------

def test_unconfirmed_waitlist_requests_get_no_offers(empty_calendar, db):
    client = empty_calendar
    booked = book(client, ["Foot reflexology"], TUESDAY, "15:00", "Lena",
                  email="priya.shah@example.com", first_name="Priya").json()
    join(client, "Tom", confirm=False)
    [confirm_mail] = [e for e in client.app.state.mailer.outbox
                      if e.subject.startswith("Please confirm: waitlist")]
    assert "/waitlist-confirm.html?token=" in confirm_mail.text
    client.post(f"/public/bookings/{manage_token(client, booked['id'])}/cancel")
    assert not any(e.subject.startswith("A time is free") for e in client.app.state.mailer.outbox)

    response = confirm_waitlist(client, "Tom")
    assert response.json() == {"status": "waiting", "preferred_date": TUESDAY, "position": 1}
    assert client.app.state.mailer.outbox[-1].subject.startswith("Waitlist for")
    assert confirm_waitlist(client, "Tom").json()["status"] == "waiting"  # idempotent


def test_unconfirmed_waitlist_requests_expire_after_a_day(empty_calendar, monkeypatch, db):
    client = empty_calendar
    join(client, "Tom", confirm=False)
    at(monkeypatch, 2026, 10, 11, 12, 1)
    assert client.post("/internal/run-jobs", headers=JOBS).json()[
        "unconfirmed_waitlist_expired"] == 1
    late = confirm_waitlist(client, "Tom")
    assert late.status_code == 410
    customer = db.scalar(select(Customer).where(Customer.first_name == "Tom"))
    db.expire_all()
    assert db.scalar(select(WaitlistEntry.status).where(
        WaitlistEntry.customer_id == customer.id)) == "expired"


def test_a_stranger_cannot_fill_someones_waitlist_places(empty_calendar):
    """Unconfirmed requests don't count toward the 5-entry cap (closes the accepted risk)."""
    client = empty_calendar
    limiter = client.app.state.booking_limiter
    days = ("2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17", "2026-10-19")
    for day in days:
        limiter._events.clear()
        join(client, "Tom", day=day, confirm=False)  # a stranger, without the inbox
    limiter._events.clear()
    join(client, "Tom", day="2026-10-20")  # the real Tom confirms
    with client.app.state.session_factory() as session:
        statuses = session.scalars(select(WaitlistEntry.status)).all()
    assert statuses.count("waiting") == 1


def test_confirm_links_are_redacted_in_logs():
    from app.logs import redact

    token = "A" * 43
    assert token not in redact(f"POST /public/waitlist/confirm/{token} HTTP/1.1")


def test_confirming_cannot_go_past_the_cap(empty_calendar, db):
    """Security review finding: pending requests don't count when joining, so the cap
    must be checked again at confirmation."""
    from app.logic.waitlist import MAX_OPEN_ENTRIES_PER_CUSTOMER

    client = empty_calendar
    limiter = client.app.state.booking_limiter
    days = ("2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-17",
            "2026-10-19", "2026-10-20")
    for day in days:  # all pending: none counts toward the cap yet
        limiter._events.clear()
        join(client, "Tom", day=day, confirm=False)
    with client.app.state.session_factory() as session:
        tokens = session.scalars(select(WaitlistEntry.confirm_token).order_by(
            WaitlistEntry.id)).all()
    results = [client.post(f"/public/waitlist/confirm/{t}") for t in tokens]
    assert [r.status_code for r in results].count(200) == MAX_OPEN_ENTRIES_PER_CUSTOMER
    rejected = [r for r in results if r.status_code == 409]
    assert len(rejected) == 2
    assert rejected[0].json()["detail"] == (
        "You already have 5 open waitlist requests. Please call the studio to change them.")
    with client.app.state.session_factory() as session:
        statuses = session.scalars(select(WaitlistEntry.status)).all()
    assert statuses.count("waiting") == MAX_OPEN_ENTRIES_PER_CUSTOMER
