"""Waitlist (slice 5): join, offer a freed slot, claim, decline, expire.

Rules (blueprint + PLAN.md decisions):
- A freed slot is offered to waiting entries in join order whose date, start-time
  window, therapist preference and total duration fit it. "Fits" uses the same chain
  planner as booking (working hours, other bookings, buffers).
- Several therapists per visit (option B): an entry has a therapist choice per treatment.
  It fits freed time when one of its treatments can start exactly then, with that
  therapist, as part of a whole visit that starts inside its window (gapless first, a
  15-minute break as the fallback). The offer is that exact visit.
- Only one open offer may include a given therapist time; an offer lasts
  `waitlist_offer_minutes`.
- Each entry gets one offer. Expired -> "expired", declined -> "removed"; the slot then
  goes to the next entry. Customers can join again [decision].
- Offers and claims skip the 2-hour notice, so late cancellations can be refilled.
"""

import threading
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.emails import Mailer, waitlist_offer_email
from app.errors import (
    INVALID_TIME_WINDOW,
    OFFER_ALREADY_CLAIMED,
    OFFER_EXPIRED,
    OFFER_NOT_FOUND,
    WAITLIST_LIMIT_REACHED,
    WAITLIST_REQUEST_EXPIRED,
    AppError,
    date_out_of_range,
)
from app.logic.availability import DayPlanner, Slot, get_studio
from app.logic.booking import CustomerDetails, create_booking, find_or_create_customer
from app.logic.selection import Selection, resolve_selection, therapist_candidates
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
    language: str = "en"
    therapist_choices: dict[int, int | None] | None = None


MAX_OPEN_ENTRIES_PER_CUSTOMER = 5


WAITLIST_CONFIRM_HOURS = 24  # unconfirmed waitlist requests expire after this [decision]


@dataclass
class JoinResult:
    # "created" (pending; confirmation email) | "unconfirmed" (pending already; resend it)
    # | "already" (waiting/offered that day) | "limit" (cap of confirmed entries reached)
    outcome: str
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
    candidates = therapist_candidates(db, selection, request.therapist_id,
                                      request.therapist_choices)
    if not all(candidates.values()):
        from app.errors import NO_THERAPIST_FOR_COMBINATION

        raise AppError(404, NO_THERAPIST_FOR_COMBINATION)
    today = clock.now().date()
    window = get_studio(db).booking_window_days
    if not today <= request.preferred_date <= today + timedelta(days=window):
        raise AppError(422, date_out_of_range(window), field="preferred_date")
    if request.earliest_time >= request.latest_time:
        raise AppError(422, INVALID_TIME_WINDOW, field="earliest_time")
    if not all(_anyone_works(db, options, request.preferred_date)
               for options in candidates.values()):
        raise AppError(422, NOBODY_WORKS_THAT_DAY, field="preferred_date")

    details = request.details.cleaned()
    customer = find_or_create_customer(db, details)
    db.flush()
    existing = db.scalar(select(WaitlistEntry).where(
        WaitlistEntry.customer_id == customer.id,
        WaitlistEntry.preferred_date == request.preferred_date,
        WaitlistEntry.status.in_(OPEN + ("pending",)),
    ).order_by(WaitlistEntry.id.desc()))
    if existing is not None and existing.status == "pending" and not _confirm_expired(existing):
        db.commit()
        return JoinResult("unconfirmed", customer, existing)
    if existing is not None and existing.status in OPEN:
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
        therapist_choices={str(k): v for k, v in (request.therapist_choices or {}).items()
                           if k in selection.service_ids and v is not None},
        service_ids=selection.service_ids,
        add_on_ids=[a.id for a in selection.add_ons],
        preferred_date=request.preferred_date,
        earliest_time=request.earliest_time,
        latest_time=request.latest_time,
        status="pending",  # counts only after the email confirmation (double opt-in)
        confirm_token=new_token(),
        language=request.language,
    )
    db.add(entry)
    db.commit()
    return JoinResult("created", customer, entry)


def get_entry_by_confirm_token(db: Session, token: str) -> WaitlistEntry | None:
    if not token:
        return None
    return db.scalar(select(WaitlistEntry).where(WaitlistEntry.confirm_token == token))


def _confirm_expired(entry: WaitlistEntry) -> bool:
    return clock.now() >= entry.created_at + timedelta(hours=WAITLIST_CONFIRM_HOURS)


# One Render instance: a process-wide lock makes "count open entries, then confirm"
# atomic; on PostgreSQL the customer row is also locked (security review: race).
_confirm_lock = threading.Lock()


def confirm_entry(db: Session, token: str) -> tuple[WaitlistEntry, int | None]:
    """Double opt-in link. Returns the entry and its queue position once waiting."""
    with _confirm_lock:
        return _confirm_entry(db, token)


def _confirm_entry(db: Session, token: str) -> tuple[WaitlistEntry, int | None]:
    entry = db.scalar(select(WaitlistEntry).where(WaitlistEntry.confirm_token == token)) \
        if token else None
    if entry is None:
        raise AppError(404, "Waitlist request not found. Please check the link in your email.")
    if db.bind.dialect.name == "postgresql":
        db.execute(select(Customer.id).where(Customer.id == entry.customer_id)
                   .with_for_update()).all()
        db.refresh(entry)
    if entry.status == "pending":
        if _confirm_expired(entry):
            entry.status = "expired"
            db.commit()
            raise AppError(410, WAITLIST_REQUEST_EXPIRED)
        # The cap is checked again here: pending requests don't count when joining, so
        # several could otherwise be confirmed past it (security review).
        open_entries = db.scalar(select(func.count()).select_from(WaitlistEntry).where(
            WaitlistEntry.customer_id == entry.customer_id,
            WaitlistEntry.status.in_(OPEN),
        ))
        if open_entries >= MAX_OPEN_ENTRIES_PER_CUSTOMER:
            entry.status = "removed"
            db.commit()
            raise AppError(409, WAITLIST_LIMIT_REACHED)
        entry.status = "waiting"
        db.commit()
    elif entry.status in ("expired", "removed"):
        raise AppError(410, WAITLIST_REQUEST_EXPIRED)
    position = queue_position(db, entry) if entry.status in OPEN else None
    return entry, position


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


def _choices(entry: WaitlistEntry) -> dict[int, int | None]:
    return {int(k): v for k, v in (entry.therapist_choices or {}).items()}


def _iso(moment: datetime) -> str:
    return moment.isoformat()


def _plan_of(slot: Slot) -> dict:
    return {
        "choices": {str(step.service_id): step.therapist.id for step in slot.steps},
        "break_before": slot.break_before,
        "segments": [[seg.therapist.id, _iso(seg.start_at), _iso(seg.end_at),
                      _iso(seg.blocked_until), list(seg.service_ids)] for seg in slot.segments],
    }


def offer_segments(db: Session, entry: WaitlistEntry) -> list[tuple[int, datetime, datetime]]:
    """The therapist times an offer holds: (therapist id, start, blocked until)."""
    if entry.offer_plan:
        return [(tid, datetime.fromisoformat(start), datetime.fromisoformat(blocked))
                for tid, start, _end, blocked, _services in entry.offer_plan["segments"]]
    # Offers made before option B: one therapist for the whole visit.
    selection = _selection_for(db, entry)
    minutes = selection.blocked_minutes if selection else 0
    return [(entry.offer_therapist_id, entry.offer_start_at,
             entry.offer_start_at + timedelta(minutes=minutes))]


def _open_offer_times(db: Session) -> list[tuple[int, datetime, datetime]]:
    offers = db.scalars(select(WaitlistEntry).where(
        WaitlistEntry.status == "offered", WaitlistEntry.offer_expires_at > clock.now())).all()
    return [part for entry in offers for part in offer_segments(db, entry)]


def _clashes(slot: Slot, taken: list[tuple[int, datetime, datetime]]) -> bool:
    return any(seg.therapist.id == tid and seg.start_at < blocked and start < seg.blocked_until
               for seg in slot.segments for tid, start, blocked in taken)


def _chain_for(db: Session, entry: WaitlistEntry, selection: Selection, therapist_id: int,
               start_at: datetime, taken) -> Slot | None:
    """The entry's earliest whole visit in which one treatment starts at `start_at` with
    that therapist (the freed time), inside its window. Gapless first, then a break."""
    try:
        candidates = therapist_candidates(db, selection, entry.therapist_id, _choices(entry))
    except AppError:
        return None
    day = start_at.astimezone(clock.BERLIN).date()
    planner = DayPlanner(db, day, selection, candidates, for_owner=True)
    starts = set(planner.starts())
    for break_before in [None, *range(1, len(selection.services))]:
        offsets = planner.step_offsets(break_before)
        found = []
        for index, service in enumerate(selection.services):
            therapist = next((t for t in candidates[service.id] if t.id == therapist_id), None)
            start = start_at - offsets[index]
            local = start.astimezone(clock.BERLIN).time()
            if therapist is None or start not in starts or not (
                    entry.earliest_time <= local <= entry.latest_time):
                continue
            slot = planner.chain(start, break_before, fixed=(index, therapist))
            if slot is not None and not _clashes(slot, taken):
                found.append(slot)
        if found:
            return min(found, key=lambda slot: slot.start_at)
    return None


def freed_times(booking) -> list[tuple[int, datetime]]:
    """Where a cancelled or expired booking frees time: each part's therapist and start."""
    return [(s.therapist_id, s.start_at) for s in booking.segments] or [
        (booking.therapist_id, booking.start_at)]


def offer_freed(db: Session, mailer: Mailer, public_url: str,
                freed: list[tuple[int, datetime]]) -> list[WaitlistEntry]:
    """Offer each freed therapist time to the first fitting entry. Returns those offered."""
    offered = [offer_slot(db, mailer, public_url, therapist_id, start_at)
               for therapist_id, start_at in freed]
    return [entry for entry in offered if entry is not None]


def offer_slot(db: Session, mailer: Mailer, public_url: str, therapist_id: int,
               start_at: datetime) -> WaitlistEntry | None:
    """Offer the freed time to the first fitting waiting entry. Returns the entry offered."""
    if start_at <= clock.now():
        return None
    therapist = db.get(Therapist, therapist_id)
    if therapist is None or not therapist.active:
        return None
    taken = _open_offer_times(db)
    if any(tid == therapist_id and start <= start_at < blocked for tid, start, blocked in taken):
        return None  # already part of an open offer
    local = start_at.astimezone(clock.BERLIN)
    candidates = db.scalars(
        select(WaitlistEntry)
        .where(WaitlistEntry.status == "waiting", WaitlistEntry.preferred_date == local.date())
        .order_by(WaitlistEntry.created_at, WaitlistEntry.id)
    ).all()
    studio = get_studio(db)
    for entry in candidates:
        selection = _selection_for(db, entry)
        if selection is None:
            continue
        slot = _chain_for(db, entry, selection, therapist_id, start_at, taken)
        if slot is None:
            continue  # their visit doesn't fit into this gap
        now = clock.now()
        entry.status = "offered"
        entry.offer_token = new_token()
        entry.offer_start_at = slot.start_at
        entry.offer_therapist_id = slot.therapist.id
        entry.offer_plan = _plan_of(slot)
        entry.offered_at = now
        entry.offer_expires_at = now + timedelta(minutes=studio.waitlist_offer_minutes)
        db.commit()
        names = ", ".join(dict.fromkeys(seg.therapist.display_name for seg in slot.segments))
        mailer.send(waitlist_offer_email(entry, studio, public_url,
                                         slot.start_at.astimezone(clock.BERLIN), names,
                                         selection.total_minutes))
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
    freed = [(tid, start) for tid, start, _ in offer_segments(db, entry)]
    entry.status = status
    db.commit()
    offered = offer_freed(db, mailer, public_url, freed)
    return offered[0] if offered else None


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
    plan = entry.offer_plan or {}
    booking = create_booking(
        db, selection, local.date(), local.strftime("%H:%M"),
        None if plan else entry.offer_therapist_id,  # offers before option B: one therapist
        CustomerDetails(customer.first_name, customer.last_name, customer.email,
                        customer.phone or "000000"),
        source="waitlist",
        language=entry.language,
        therapist_choices={int(k): v for k, v in plan.get("choices", {}).items()} or None,
        break_before=plan.get("break_before"),
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
    if entry.status in OPEN + ("pending",):
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
