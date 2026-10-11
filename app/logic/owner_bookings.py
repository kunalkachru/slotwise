"""Owner side of bookings (slice 4): list, status, final items, receipts, CSV."""

import csv
import io
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app import clock
from app.errors import AppError
from app.logic.availability import day_bounds_utc, get_studio
from app.logic.booking import cancel_booking
from app.models import BOOKING_STATUSES, AddOn, Booking, BookingItem, Customer, Service

STATUS_NOT_ALLOWED = "This status change is not allowed."
NOT_STARTED_YET = "A booking can only be marked done or no-show after it starts."
RECEIPT_ALREADY_SENT = "The receipt was already sent; this booking can't be changed."
RECEIPT_ONLY_WHEN_DONE = "Only bookings marked done can get a receipt."
CANCELLED_CANT_CHANGE = "Cancelled bookings can't be changed."
BOOKING_NOT_FOUND_OWNER = "Booking not found."
INVALID_ITEMS = "Please check the item lines."

REPEAT_NO_SHOW_THRESHOLD = 2  # highlighted for the owner, never blocked (blueprint)

_receipt_lock = threading.Lock()


def _with_details():
    return (
        selectinload(Booking.items),
        selectinload(Booking.customer),
        selectinload(Booking.therapist),
    )


def get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.id == booking_id).options(*_with_details()))
    if booking is None:
        raise AppError(404, BOOKING_NOT_FOUND_OWNER)
    return booking


def list_bookings(
    db: Session,
    start_day: date,
    end_day: date,
    therapist_id: int | None = None,
    status: str | None = None,
    query: str | None = None,
) -> list[Booking]:
    """Bookings starting on local days start_day..end_day (inclusive)."""
    start, _ = day_bounds_utc(start_day)
    _, end = day_bounds_utc(end_day)
    stmt = (
        select(Booking)
        .join(Booking.customer)
        .where(Booking.start_at >= start, Booking.start_at < end)
        .options(*_with_details())
        .order_by(Booking.start_at, Booking.therapist_id)
    )
    if therapist_id is not None:
        stmt = stmt.where(Booking.therapist_id == therapist_id)
    if status:
        if status not in BOOKING_STATUSES:
            raise AppError(422, "Unknown status.", field="status")
        stmt = stmt.where(Booking.status == status)
    if query and query.strip():
        needle = f"%{query.strip().lower()}%"
        digits = "".join(ch for ch in query if ch.isdigit())
        conditions = [
            func.lower(Customer.first_name + " " + Customer.last_name).like(needle),
            func.lower(Customer.email).like(needle),
        ]
        if len(digits) >= 3:
            # Phone numbers are stored as typed; compare digits only.
            phone_digits = func.replace(func.replace(func.replace(
                Customer.phone, " ", ""), "+", ""), "-", "")
            conditions.append(phone_digits.like(f"%{digits}%"))
        stmt = stmt.where(or_(*conditions))
    return list(db.scalars(stmt).unique().all())


def has_started(booking: Booking) -> bool:
    return booking.start_at <= clock.now()


def change_status(db: Session, booking: Booking, new_status: str) -> Booking:
    """Owner status changes. done / no_show only after the start; no_show counts
    against the customer (and is undone if corrected); nothing changes after a receipt."""
    old = booking.status
    if new_status not in BOOKING_STATUSES:
        raise AppError(422, STATUS_NOT_ALLOWED, field="status")
    if new_status == old:
        return booking
    if booking.receipt_sent_at is not None:
        raise AppError(400, RECEIPT_ALREADY_SENT)
    if old in ("cancelled", "expired"):
        raise AppError(400, CANCELLED_CANT_CHANGE)
    if new_status in ("pending", "expired"):
        raise AppError(400, STATUS_NOT_ALLOWED)  # set by the system, not by hand
    if old == "pending" and new_status in ("done", "no_show"):
        raise AppError(400, STATUS_NOT_ALLOWED)  # confirm it first

    if new_status == "cancelled":
        return cancel_booking(db, booking)  # same 24 h late-cancellation rule
    if new_status in ("done", "no_show"):
        if not has_started(booking):
            raise AppError(400, NOT_STARTED_YET)
    elif new_status in ("booked", "confirmed"):
        if has_started(booking) and old in ("done", "no_show"):
            pass  # correcting a mistaken done/no-show is allowed
        elif has_started(booking):
            raise AppError(400, STATUS_NOT_ALLOWED)

    if old == "no_show":
        booking.customer.no_show_count = max(0, booking.customer.no_show_count - 1)
    if new_status == "no_show":
        booking.customer.no_show_count += 1
    if new_status == "confirmed" and booking.confirmed_at is None:
        booking.confirmed_at = clock.now()
    booking.status = new_status
    db.commit()
    return booking


@dataclass
class ItemInput:
    item_type: str
    name: str
    minutes: int
    unit_price: Decimal
    quantity: int
    service_id: int | None = None
    add_on_id: int | None = None


def replace_items(db: Session, booking: Booking, items: list[ItemInput]) -> Booking:
    """Final itemized lines for what happened on the day. Changes the total and the
    receipt, not the calendar times [decision]."""
    if booking.status in ("cancelled", "expired"):
        raise AppError(400, CANCELLED_CANT_CHANGE)
    if booking.receipt_sent_at is not None:
        raise AppError(400, RECEIPT_ALREADY_SENT)
    if not items:
        raise AppError(422, INVALID_ITEMS, field="items")
    for item in items:
        name = item.name.strip()
        if (
            item.item_type not in ("service", "add_on", "extra")
            or not name or len(name) > 120
            or not 0 <= item.minutes <= 480
            or not Decimal(0) <= item.unit_price <= Decimal(10000)
            or item.unit_price != item.unit_price.quantize(Decimal("0.01"))
            or not 1 <= item.quantity <= 99
        ):
            raise AppError(422, INVALID_ITEMS, field="items")
        if item.service_id is not None and db.get(Service, item.service_id) is None:
            raise AppError(422, INVALID_ITEMS, field="items")
        if item.add_on_id is not None and db.get(AddOn, item.add_on_id) is None:
            raise AppError(422, INVALID_ITEMS, field="items")

    booking.items.clear()
    db.flush()
    for item in items:
        booking.items.append(BookingItem(
            item_type=item.item_type,
            service_id=item.service_id if item.item_type == "service" else None,
            add_on_id=item.add_on_id if item.item_type == "add_on" else None,
            name_snapshot=item.name.strip(),
            minutes_snapshot=item.minutes,
            unit_price_snapshot=item.unit_price,
            quantity=item.quantity,
        ))
    booking.total_price = sum(
        (i.unit_price_snapshot * i.quantity for i in booking.items), Decimal(0)
    )
    db.commit()
    return booking


def assign_receipt_number(db: Session, booking: Booking) -> Booking:
    """IW-2026-0042: studio prefix, year of the appointment, running number per year.
    Kept when a receipt is re-sent."""
    if booking.status != "done":
        raise AppError(400, RECEIPT_ONLY_WHEN_DONE)
    with _receipt_lock:
        if booking.receipt_number is None:
            prefix = get_studio(db).receipt_prefix
            year = booking.start_at.astimezone(clock.BERLIN).year
            stem = f"{prefix}-{year}-"
            existing = db.scalars(
                select(Booking.receipt_number).where(Booking.receipt_number.like(f"{stem}%"))
            ).all()
            numbers = [int(n[len(stem):]) for n in existing if n[len(stem):].isdigit()]
            booking.receipt_number = f"{stem}{max(numbers, default=0) + 1:04d}"
        booking.receipt_sent_at = clock.now()
        db.commit()
    return booking


# ---------- CSV export ----------

CSV_COLUMNS = [
    "booking_id", "date", "time", "therapist", "status", "source", "customer",
    "email", "phone", "item_type", "item", "minutes", "unit_price", "quantity",
    "line_total", "booking_total", "late_cancellation", "receipt_number",
]


def _safe_cell(value) -> str:
    """Stop spreadsheet formula injection: cells starting with = + - @ (or tab/CR)
    are prefixed with an apostrophe, so Excel shows them as text."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def bookings_csv(bookings: list[Booking]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(CSV_COLUMNS)
    for b in bookings:
        local = b.start_at.astimezone(clock.BERLIN)
        base = [
            b.id, local.date().isoformat(), local.strftime("%H:%M"), b.therapist.display_name,
            b.status, b.source, f"{b.customer.first_name} {b.customer.last_name}",
            b.customer.email, b.customer.phone,
        ]
        for item in b.items:
            writer.writerow([_safe_cell(v) for v in base + [
                item.item_type, item.name_snapshot, item.minutes_snapshot,
                f"{item.unit_price_snapshot:.2f}", item.quantity,
                f"{item.unit_price_snapshot * item.quantity:.2f}", f"{b.total_price:.2f}",
                "yes" if b.late_cancellation else "no", b.receipt_number or "",
            ]])
    return out.getvalue()


def default_range(today: date) -> tuple[date, date]:
    return today, today + timedelta(days=6)
