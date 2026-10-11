"""Waitlist (slice 5): join, offer a freed slot, claim, decline, expire.

Rules (blueprint + PLAN.md decisions):
- A freed slot is offered to waiting entries in join order whose date, start-time
  window, therapist preference and total duration fit it. "Fits" uses the same free-slot
  check as booking (working hours, other bookings, buffers).
- Only one open offer per slot at a time; an offer lasts `waitlist_offer_minutes`.
- Each entry gets one offer. Expired -> "expired", declined -> "removed"; the slot then
  goes to the next entry. Customers can join again [decision].
- Offers and claims skip the 2-hour notice, so late cancellations can be refilled.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.emails import Mailer, waitlist_offer_email
from app.errors import (
    DATE_OUT_OF_RANGE,
    INVALID_TIME_WINDOW,
    OFFER_ALREADY_CLAIMED,
    OFFER_EXPIRED,
    OFFER_NOT_FOUND,
    AppError,
)
from app.logic.availability import free_slots_by_therapist, get_studio
from app.logic.booking import CustomerDetails, create_booking, find_or_create_customer
from app.logic.selection import Selection, qualified_therapists, resolve_selection
from app.models import Customer, DayOff, Therapist, WaitlistEntry
from app.security import new_token

OPEN = ("waiting", "offered")
NOBODY_WORKS_THAT_DAY = "Nobody offers this treatment on that day, so no time can free up."


def _anyone_works(db: Session, therapists: list[Therapist], day: date) -> bool:
    """A waitlist entry only makes sense if a qualified therapist works that day."""
    rows = db.execute(select(DayOff.therapist_id).where(DayOff.date == day)).all()
    if any(r.therapist_id is None for r in rows):
        return False  # whole studio closed
    off = {r.therapist_id for r in rows}
    return any(t.id not in off and any(h.weekday == day.weekday() for h in t.working_hours)
               for t in therapists)


@dataclass
class JoinRequest:
    service_ids: list[int]
    add_on_ids: list[int]
    therapist_id: int | None
    preferred_date: date
    earliest_time: time
    latest_time: time
    details: CustomerDetails


MAX_OPEN_ENTRIES_PER_CUSTOMER = 5


@dataclass
class JoinResult:
    outcome: str  # "created" | "already" (waiting that day) | "limit" (cap reached)
    customer: Customer
    entry: WaitlistEntry | None = None
    position: int | None = None

    @property
    def created(self) -> bool:
        return self.outcome == "created"


def join(db: Session, request: JoinRequest) -> JoinResult:
    """Add an entry, or report the existing one. The caller must give the same response
    either way, so the API never reveals who is on the waitlist (security review)."""
    selection = resolve_selection(db, request.service_ids, request.add_on_ids)
    therapists = qualified_therapists(db, selection)
    if request.therapist_id is not None:
        therapists = [t for t in therapists if t.id == request.therapist_id]
    if not therapists:
        from app.errors import NO_THERAPIST_FOR_COMBINATION

        raise AppError(404, NO_THERAPIST_FOR_COMBINATION)
    today = clock.now().date()
    if not today <= request.preferred_date <= today + timedelta(
        days=get_studio(db).booking_window_days
    ):
        raise AppError(422, DATE_OUT_OF_RANGE, field="preferred_date")
    if request.earliest_time >= request.latest_time:
        raise AppError(422, INVALID_TIME_WINDOW, field="earliest_time")
    if not _anyone_works(db, therapists, request.preferred_date):
        raise AppError(422, NOBODY_WORKS_THAT_DAY, field="preferred_date")

    details = request.details.cleaned()
    customer = find_or_create_customer(db, details)
    db.flush()
    existing = db.scalar(select(WaitlistEntry).where(
        WaitlistEntry.customer_id == customer.id,
        WaitlistEntry.preferred_date == request.preferred_date,
        WaitlistEntry.status.in_(OPEN),
    ))
    if existing is not None:
        db.commit()
        return JoinResult("already", customer, existing, queue_position(db, existing))
    open_entries = db.scalar(select(func.count()).select_from(WaitlistEntry).where(
        WaitlistEntry.customer_id == customer.id, WaitlistEntry.status.in_(OPEN)))
    if open_entries >= MAX_OPEN_ENTRIES_PER_CUSTOMER:
        db.commit()  # the caller emails the address owner: never a silent no-op
        return JoinResult("limit", customer)
    entry = WaitlistEntry(
        customer=customer,
        therapist_id=request.therapist_id,
        service_ids=selection.service_ids,
        add_on_ids=[a.id for a in selection.add_ons],
        preferred_date=request.preferred_date,
        earliest_time=request.earliest_time,
        latest_time=request.latest_time,
        status="waiting",
    )
    db.add(entry)
    db.commit()
    return JoinResult("created", customer, entry, queue_position(db, entry))


def queue_position(db: Session, entry: WaitlistEntry) -> int:
    return db.scalar(select(func.count()).select_from(WaitlistEntry).where(
        WaitlistEntry.preferred_date == entry.preferred_date,
        WaitlistEntry.status.in_(OPEN),
        WaitlistEntry.id <= entry.id,
    ))


def _selection_for(db: Session, entry: WaitlistEntry) -> Selection | None:
    try:
        return resolve_selection(db, list(entry.service_ids), list(entry.add_on_ids))
    except AppError:
        return None  # a chosen service was deactivated since joining


def _slot_has_open_offer(db: Session, therapist_id: int, start_at: datetime) -> bool:
    return db.scalar(select(func.count()).select_from(WaitlistEntry).where(
        WaitlistEntry.status == "offered",
        WaitlistEntry.offer_therapist_id == therapist_id,
        WaitlistEntry.offer_start_at == start_at,
        WaitlistEntry.offer_expires_at > clock.now(),
    )) > 0


def offer_slot(db: Session, mailer: Mailer, public_url: str, therapist_id: int,
               start_at: datetime) -> WaitlistEntry | None:
    """Offer the freed slot to the first fitting waiting entry. Returns the entry offered."""
    if start_at <= clock.now() or _slot_has_open_offer(db, therapist_id, start_at):
        return None
    therapist = db.get(Therapist, therapist_id)
    if therapist is None or not therapist.active:
        return None
    local = start_at.astimezone(clock.BERLIN)
    candidates = db.scalars(
        select(WaitlistEntry)
        .where(
            WaitlistEntry.status == "waiting",
            WaitlistEntry.preferred_date == local.date(),
            WaitlistEntry.earliest_time <= local.time(),
            WaitlistEntry.latest_time >= local.time(),
        )
        .order_by(WaitlistEntry.created_at, WaitlistEntry.id)
    ).all()
    studio = get_studio(db)
    for entry in candidates:
        if entry.therapist_id not in (None, therapist_id):
            continue
        selection = _selection_for(db, entry)
        if selection is None or therapist not in qualified_therapists(db, selection):
            continue
        free = free_slots_by_therapist(db, local.date(), selection, [therapist], for_owner=True)
        if start_at not in free[therapist_id]:
            continue  # their treatment doesn't fit into this gap
        now = clock.now()
        entry.status = "offered"
        entry.offer_token = new_token()
        entry.offer_start_at = start_at
        entry.offer_therapist_id = therapist_id
        entry.offered_at = now
        entry.offer_expires_at = now + timedelta(minutes=studio.waitlist_offer_minutes)
        db.commit()
        when = local.strftime("%a %-d %b, %H:%M")
        mailer.send(waitlist_offer_email(entry, studio, public_url, when,
                                         therapist.display_name, selection.total_minutes))
        return entry
    return None


def get_offer(db: Session, token: str) -> WaitlistEntry:
    entry = db.scalar(select(WaitlistEntry).where(WaitlistEntry.offer_token == token)) \
        if token else None
    if entry is None:
        raise AppError(404, OFFER_NOT_FOUND)
    return entry


def is_expired(entry: WaitlistEntry) -> bool:
    return entry.status in ("expired", "removed") or (
        entry.status == "offered" and entry.offer_expires_at <= clock.now()
    )


def expire_offer(db: Session, mailer: Mailer, public_url: str, entry: WaitlistEntry,
                 status: str = "expired") -> WaitlistEntry | None:
    """Close an offer and pass the slot to the next entry. Returns the new offer, if any."""
    if entry.status != "offered":
        return None
    therapist_id, start_at = entry.offer_therapist_id, entry.offer_start_at
    entry.status = status
    db.commit()
    return offer_slot(db, mailer, public_url, therapist_id, start_at)


def claim(db: Session, mailer: Mailer, public_url: str, token: str):
    entry = get_offer(db, token)
    if entry.status == "booked":
        raise AppError(400, OFFER_ALREADY_CLAIMED)
    if is_expired(entry):
        expire_offer(db, mailer, public_url, entry)  # no-op unless still "offered"
        raise AppError(410, OFFER_EXPIRED)
    selection = _selection_for(db, entry)
    if selection is None:
        expire_offer(db, mailer, public_url, entry)
        raise AppError(410, OFFER_EXPIRED)
    customer = entry.customer
    local = entry.offer_start_at.astimezone(clock.BERLIN)
    booking = create_booking(
        db, selection, local.date(), local.strftime("%H:%M"), entry.offer_therapist_id,
        CustomerDetails(customer.first_name, customer.last_name, customer.email,
                        customer.phone or "000000"),
        source="waitlist",
    )
    entry.status = "booked"
    entry.booking_id = booking.id
    db.commit()
    return entry, booking


def decline(db: Session, mailer: Mailer, public_url: str, token: str) -> WaitlistEntry:
    entry = get_offer(db, token)
    if entry.status == "booked":
        raise AppError(400, OFFER_ALREADY_CLAIMED)
    if is_expired(entry):
        expire_offer(db, mailer, public_url, entry)
        raise AppError(410, OFFER_EXPIRED)
    expire_offer(db, mailer, public_url, entry, status="removed")
    return entry


def remove_entry(db: Session, entry_id: int) -> None:
    """Owner removes an entry. An open offer is withdrawn (not passed on: the owner
    decides what to do with that time)."""
    entry = db.get(WaitlistEntry, entry_id)
    if entry is None:
        raise AppError(404, "Not found.")
    if entry.status in OPEN:
        entry.status = "removed"
        db.commit()


def list_entries(db: Session, day: date | None) -> list[WaitlistEntry]:
    stmt = select(WaitlistEntry).order_by(
        WaitlistEntry.preferred_date, WaitlistEntry.created_at, WaitlistEntry.id)
    if day is not None:
        stmt = stmt.where(WaitlistEntry.preferred_date == day)
    else:
        stmt = stmt.where(WaitlistEntry.preferred_date >= clock.now().date())
    return list(db.scalars(stmt).all())
