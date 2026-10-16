"""Background work, run only through POST /internal/run-jobs (called every 15 minutes by
.github/workflows/jobs.yml, because the free host sleeps and has no scheduler).

Every step is idempotent: running twice, or late, sends nothing twice.
"""

import threading
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.emails import Mailer, reminder_email
from app.logic.availability import get_studio
from app.logic.waitlist import expire_offer
from app.models import Booking, Customer, WaitlistEntry

REMINDER_HOURS = 24
RETENTION_DAYS = 730  # keep bookings 2 years, then anonymize the customer (blueprint)

_run_lock = threading.Lock()


def send_due_reminders(db: Session, mailer: Mailer, public_url: str) -> int:
    """Reminder within 24 h of the start, once, with one-click confirm/cancel. Bookings
    made less than 24 h ahead get none: the customer has just booked [decision]."""
    now = clock.now()
    due = db.scalars(select(Booking).where(
        Booking.status.in_(("booked", "confirmed")),
        Booking.reminder_sent_at.is_(None),
        Booking.start_at > now,
        Booking.start_at <= now + timedelta(hours=REMINDER_HOURS),
    )).all()
    studio = get_studio(db)
    sent = 0
    for booking in due:
        if booking.start_at - booking.created_at < timedelta(hours=REMINDER_HOURS):
            booking.reminder_sent_at = now  # mark as handled; no reminder needed
            db.commit()
            continue
        booking.reminder_sent_at = now  # mark first, so a crash can't cause a resend loop
        db.commit()
        mailer.send(reminder_email(booking, studio, public_url))
        sent += 1
    return sent


def expire_offers(db: Session, mailer: Mailer, public_url: str) -> tuple[int, int]:
    """Close offers past their deadline and pass each slot on. Returns (expired, offered)."""
    overdue = db.scalars(select(WaitlistEntry).where(
        WaitlistEntry.status == "offered",
        WaitlistEntry.offer_expires_at <= clock.now(),
    ).order_by(WaitlistEntry.offer_expires_at)).all()
    offered = 0
    for entry in overdue:
        if expire_offer(db, mailer, public_url, entry) is not None:
            offered += 1
    return len(overdue), offered


def expire_unconfirmed(db: Session, mailer: Mailer, public_url: str) -> tuple[int, int]:
    """Online bookings not confirmed within the hold, and waitlist requests not confirmed
    within a day, expire. A released booking slot goes to the waitlist.
    Returns (bookings expired, waitlist requests expired)."""
    from app.logic.availability import BOOKING_HOLD_MINUTES
    from app.logic.waitlist import WAITLIST_CONFIRM_HOURS, freed_times, offer_freed

    now = clock.now()
    stale = db.scalars(select(Booking).where(
        Booking.status == "pending",
        Booking.created_at <= now - timedelta(minutes=BOOKING_HOLD_MINUTES),
    )).all()
    for booking in stale:
        booking.status = "expired"
        db.commit()
        offer_freed(db, mailer, public_url, freed_times(booking))
    requests = db.scalars(select(WaitlistEntry).where(
        WaitlistEntry.status == "pending",
        WaitlistEntry.created_at <= now - timedelta(hours=WAITLIST_CONFIRM_HOURS),
    )).all()
    for entry in requests:
        entry.status = "expired"
    db.commit()
    return len(stale), len(requests)


def anonymize_customer(db: Session, customer: Customer) -> None:
    """Remove personal details but keep bookings and receipts (amounts, dates).
    Reusable for "delete a customer on request" later (PLAN.md, nice to have)."""
    customer.first_name = "Anonymized"
    customer.last_name = "Customer"
    customer.email = f"anonymized-{customer.id}@invalid.example"
    customer.phone = ""
    customer.anonymized_at = clock.now()
    for booking in customer.bookings:
        booking.customer_note = None
    for entry in db.scalars(select(WaitlistEntry).where(WaitlistEntry.customer_id == customer.id)):
        if entry.status in ("pending", "waiting", "offered"):
            entry.status = "removed"


def anonymize_old_customers(db: Session) -> int:
    cutoff = clock.now() - timedelta(days=RETENTION_DAYS)
    last_booking = (
        select(Booking.customer_id, func.max(Booking.start_at).label("last"))
        .group_by(Booking.customer_id).subquery()
    )
    customers = db.scalars(
        select(Customer).join(last_booking, last_booking.c.customer_id == Customer.id)
        .where(last_booking.c.last < cutoff, Customer.anonymized_at.is_(None))
    ).all()
    for customer in customers:
        anonymize_customer(db, customer)
    db.commit()
    return len(customers)


def run_jobs(db: Session, mailer: Mailer, public_url: str) -> dict:
    if not _run_lock.acquire(blocking=False):
        return {"skipped": "another run is in progress"}
    try:
        unconfirmed_bookings, unconfirmed_requests = expire_unconfirmed(db, mailer, public_url)
        expired, offered = expire_offers(db, mailer, public_url)
        return {
            "unconfirmed_bookings_expired": unconfirmed_bookings,
            "unconfirmed_waitlist_expired": unconfirmed_requests,
            "reminders_sent": send_due_reminders(db, mailer, public_url),
            "offers_expired": expired,
            "offers_passed_on": offered,
            "customers_anonymized": anonymize_old_customers(db),
        }
    finally:
        _run_lock.release()
