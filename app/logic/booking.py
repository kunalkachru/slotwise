"""Creating bookings (slice 2). Later slices add confirm / cancel / status / items."""

import re
import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.errors import (
    ALREADY_CANCELLED_OR_FINISHED,
    BOOKING_NOT_FOUND,
    CANNOT_CONFIRM,
    INVALID_EMAIL,
    MISSING_FIRST_NAME,
    MISSING_LAST_NAME,
    MISSING_PHONE,
    NAME_CHARACTERS,
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
    get_studio,
    local_to_utc,
    pick_therapist,
)
from app.logic.selection import Selection, require_therapists
from app.models import Booking, Customer, Therapist
from app.security import new_token

LOCAL_PART_RE = re.compile(r"^[a-z0-9_%+-]+(?:\.[a-z0-9_%+-]+)*$")
DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}$")


def canonical_email(raw: str) -> str | None:
    """The one form of an address used everywhere: validation, storage, sending and
    rate limiting, so no two spellings of an inbox can be treated differently.

    ASCII only, and the only change made is trimming and lower-casing ASCII letters.
    No Unicode mapping of any kind: Python's IDNA 2003 codec turns "straße.de" into
    "strasse.de" (possibly someone else's domain), and str.lower() turns some
    non-ASCII characters into ASCII (Kelvin sign -> "k"). Internationalised domains
    can be entered in their xn-- form (security reviews, slice 3)."""
    raw = raw.strip()
    if not raw.isascii() or len(raw) > 254:
        return None
    local, at, domain = raw.lower().partition("@")
    if not at or not LOCAL_PART_RE.match(local) or not DOMAIN_RE.match(domain):
        return None
    return f"{local}@{domain}"
NAME_PUNCTUATION = set(" -'’.")


DOT_INSIDE_WORD = re.compile(r"\.\S")


def _is_plain_name(name: str) -> bool:
    """Letters (any alphabet), spaces, hyphens, apostrophes, and dots only before a space
    or at the end ("Jr.", "J. R."). Names end up in emails we send, so no URLs, domains
    like "evil.com", digits, @ or markup (security reviews, slice 3)."""
    return all(ch.isalpha() or ch in NAME_PUNCTUATION for ch in name) and not (
        DOT_INSIDE_WORD.search(name)
    )


def mailbox_key(email: str) -> str:
    """One key per real inbox, for rate limiting. Takes a canonical_email() result and
    also drops +tags and, for Gmail, dots (anna+1@x and a.nna@gmail.com reach the
    same person)."""
    local, _, domain = email.partition("@")
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local, domain = local.replace(".", ""), "gmail.com"
    return f"{local}@{domain}"

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
        email = canonical_email(self.email)
        phone = self.phone.strip()
        note = (self.note or "").strip() or None
        if not first:
            raise AppError(422, MISSING_FIRST_NAME, field="first_name")
        if not last:
            raise AppError(422, MISSING_LAST_NAME, field="last_name")
        if not _is_plain_name(first):
            raise AppError(422, NAME_CHARACTERS, field="first_name")
        if not _is_plain_name(last):
            raise AppError(422, NAME_CHARACTERS, field="last_name")
        if email is None:
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


# ---------- Manage link (slice 3) ----------


def get_by_token(db: Session, token: str) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.manage_token == token)) if token else None
    if booking is None:
        raise AppError(404, BOOKING_NOT_FOUND)
    return booking


def free_cancellation_until(db: Session, booking: Booking) -> datetime:
    return booking.start_at - timedelta(hours=get_studio(db).free_cancellation_hours)


def can_confirm(booking: Booking) -> bool:
    return booking.status in ("booked", "confirmed") and booking.start_at > clock.now()


def can_cancel(booking: Booking) -> bool:
    return booking.status in ("booked", "confirmed") and booking.start_at > clock.now()


def confirm_booking(db: Session, booking: Booking) -> Booking:
    if not can_confirm(booking):
        raise AppError(400, CANNOT_CONFIRM)
    if booking.status == "booked":  # confirming twice is harmless
        booking.status = "confirmed"
        booking.confirmed_at = clock.now()
        db.commit()
    return booking


def cancel_booking(db: Session, booking: Booking) -> Booking:
    """Free up to `free_cancellation_hours` before the start; later is allowed but flagged."""
    if not can_cancel(booking):
        raise AppError(400, ALREADY_CANCELLED_OR_FINISHED)
    now = clock.now()
    booking.status = "cancelled"
    booking.cancelled_at = now
    booking.late_cancellation = now > free_cancellation_until(db, booking)
    db.commit()
    return booking
