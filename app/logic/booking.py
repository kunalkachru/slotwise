"""Creating bookings (slice 2). Later slices add confirm / cancel / status / items."""

import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import (
    INVALID_EMAIL,
    MISSING_FIRST_NAME,
    MISSING_LAST_NAME,
    MISSING_PHONE,
    NOT_AN_OFFERED_TIME,
    NOTE_TOO_LONG,
    OUTSIDE_BOOKING_WINDOW,
    TIME_TAKEN,
    AppError,
)
from app.logic.availability import (
    booking_limits,
    bookings_per_therapist,
    free_slots_by_therapist,
    local_to_utc,
    pick_therapist,
)
from app.logic.selection import Selection, require_therapists
from app.models import Booking, Customer, Therapist
from app.security import new_token

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# One Render instance: a process-wide lock makes "check the slot is free, then insert"
# atomic even on SQLite. On PostgreSQL the therapist rows are also locked FOR UPDATE.
_booking_lock = threading.Lock()


@dataclass
class CustomerDetails:
    first_name: str
    last_name: str
    email: str
    phone: str
    note: str | None = None

    def cleaned(self) -> "CustomerDetails":
        first = self.first_name.strip()
        last = self.last_name.strip()
        email = self.email.strip().lower()
        phone = self.phone.strip()
        note = (self.note or "").strip() or None
        if not first:
            raise AppError(422, MISSING_FIRST_NAME, field="first_name")
        if not last:
            raise AppError(422, MISSING_LAST_NAME, field="last_name")
        if not EMAIL_RE.match(email) or len(email) > 255:
            raise AppError(422, INVALID_EMAIL, field="email")
        if sum(ch.isdigit() for ch in phone) < 6 or len(phone) > 40:
            raise AppError(422, MISSING_PHONE, field="phone")
        if note and len(note) > 300:
            raise AppError(422, NOTE_TOO_LONG, field="note")
        return CustomerDetails(first, last, email, phone, note)


def parse_start(day: date, start_time: str) -> datetime:
    try:
        hours, minutes = (int(p) for p in start_time.split(":"))
        local = time(hours, minutes)
    except ValueError:
        raise AppError(422, NOT_AN_OFFERED_TIME, field="start_time") from None
    if local.minute % 15:
        raise AppError(422, NOT_AN_OFFERED_TIME, field="start_time")
    return local_to_utc(day, local)


def find_or_create_customer(db: Session, details: CustomerDetails) -> Customer:
    """Match returning customers by email, without changing their saved details.

    Booking needs no login, so anyone could type someone else's email. Overwriting the
    stored name or phone from that request would let a stranger change another
    customer's contact details (security review, slice 2).
    """
    customer = db.scalar(select(Customer).where(Customer.email == details.email))
    if customer is None:
        customer = Customer(
            email=details.email,
            first_name=details.first_name,
            last_name=details.last_name,
            phone=details.phone,
        )
        db.add(customer)
    return customer


def _lock_therapists(db: Session, therapist_ids: list[int]) -> None:
    """PostgreSQL row locks so concurrent workers can't double-book (no-op on SQLite)."""
    if db.bind.dialect.name == "postgresql":
        db.execute(
            select(Therapist.id).where(Therapist.id.in_(therapist_ids)).with_for_update()
        ).all()


def create_booking(
    db: Session,
    selection: Selection,
    day: date,
    start_time: str,
    therapist_id: int | None,
    details: CustomerDetails,
    source: str = "online",
) -> Booking:
    details = details.cleaned()
    start_at = parse_start(day, start_time)
    if not booking_limits(db).allows(start_at):
        raise AppError(422, OUTSIDE_BOOKING_WINDOW, field="start_time")

    candidates = require_therapists(db, selection)
    if therapist_id is not None:
        candidates = [t for t in candidates if t.id == therapist_id]
        if not candidates:
            raise AppError(400, TIME_TAKEN)

    with _booking_lock:
        _lock_therapists(db, [t.id for t in candidates])
        # Re-check inside the lock with the same rules the availability endpoint uses.
        free = free_slots_by_therapist(db, day, selection, candidates)
        free_now = [t for t in candidates if start_at in free[t.id]]
        if not free_now:
            db.rollback()
            raise AppError(400, TIME_TAKEN)
        counts = bookings_per_therapist(db, [t.id for t in free_now], day)
        therapist = pick_therapist(free_now, counts)

        items = selection.snapshot_items()
        end_at = start_at + timedelta(minutes=selection.total_minutes)
        booking = Booking(
            customer=find_or_create_customer(db, details),
            therapist=therapist,
            start_at=start_at,
            end_at=end_at,
            blocked_until=end_at + timedelta(minutes=selection.buffer_minutes),
            status="booked",
            total_price=selection.total_price,
            source=source,
            manage_token=new_token(),
            customer_note=details.note,
            items=items,
        )
        db.add(booking)
        db.commit()
    db.refresh(booking)
    return booking
