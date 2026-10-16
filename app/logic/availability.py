"""Free start times (PLAN.md section 2, "Core calculations").

All arithmetic is done in UTC so durations stay correct across DST changes; local
Europe/Berlin time is only used to read working hours and to show times.

Rules:
- start times on 15-minute steps (local time)
- the appointment (total minutes) must end inside the therapist's working hours;
  the cleanup buffer may run past closing [decision]
- at least `min_notice_hours` ahead, at most `booking_window_days` ahead
- no overlap with the therapist's non-cancelled bookings, buffer included:
  a.start < b.blocked_until AND b.start < a.blocked_until
- therapist days off and whole-studio closures are excluded
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app import clock
from app.errors import AppError, date_out_of_range
from app.logic.selection import Selection
from app.models import Booking, BookingSegment, DayOff, Studio, Therapist

STEP = timedelta(minutes=15)
BOOKING_HOLD_MINUTES = 30  # an unconfirmed online booking holds its slot this long [decision]


def occupies_slot():
    """SQL condition: the booking blocks its time. Cancelled and expired bookings don't;
    a pending (unconfirmed) one does only while its hold lasts."""
    hold_start = clock.now() - timedelta(minutes=BOOKING_HOLD_MINUTES)
    return and_(
        Booking.status.notin_(("cancelled", "expired")),
        or_(Booking.status != "pending", Booking.created_at > hold_start),
    )


@dataclass(frozen=True)
class Slot:
    start_at: datetime  # UTC
    therapist: Therapist

    @property
    def local_time(self) -> str:
        return self.start_at.astimezone(clock.BERLIN).strftime("%H:%M")


def local_to_utc(day: date, at: time) -> datetime:
    return datetime.combine(day, at, clock.BERLIN).astimezone(UTC)


def day_bounds_utc(day: date) -> tuple[datetime, datetime]:
    return local_to_utc(day, time(0)), local_to_utc(day + timedelta(days=1), time(0))


def get_studio(db: Session) -> Studio:
    return db.scalar(select(Studio).limit(1))


def check_date_in_range(db: Session, day: date) -> None:
    studio = get_studio(db)
    today = clock.now().date()
    if day < today or day > today + timedelta(days=studio.booking_window_days):
        raise AppError(422, date_out_of_range(studio.booking_window_days), field="date")


@dataclass(frozen=True)
class BookingLimits:
    earliest: datetime  # now + min notice
    latest_day: date  # today + booking window

    def allows(self, start_at: datetime) -> bool:
        return (
            start_at >= self.earliest
            and start_at.astimezone(clock.BERLIN).date() <= self.latest_day
        )


def booking_limits(db: Session, for_owner: bool = False) -> BookingLimits:
    """Customers need `min_notice_hours`; the owner (phone bookings) only needs a future
    start time [decision]. Both are limited to the booking window."""
    studio = get_studio(db)
    now = clock.now()
    return BookingLimits(
        earliest=now if for_owner else now + timedelta(hours=studio.min_notice_hours),
        latest_day=now.date() + timedelta(days=studio.booking_window_days),
    )


def _closed_therapist_ids(db: Session, day: date) -> tuple[bool, set[int]]:
    rows = db.execute(select(DayOff.therapist_id).where(DayOff.date == day)).all()
    studio_closed = any(r.therapist_id is None for r in rows)
    return studio_closed, {r.therapist_id for r in rows if r.therapist_id is not None}


def _busy_ranges(db: Session, therapist_ids: list[int], day: date):
    """Each therapist's busy time that touches the day, as (start, blocked_until): the
    segments of bookings that occupy their slot (one per therapist part of a booking)."""
    start, end = day_bounds_utc(day)
    rows = db.execute(
        select(BookingSegment.therapist_id, BookingSegment.start_at, BookingSegment.blocked_until)
        .join(Booking, Booking.id == BookingSegment.booking_id)
        .where(
            BookingSegment.therapist_id.in_(therapist_ids),
            occupies_slot(),
            BookingSegment.start_at < end + timedelta(hours=12),
            BookingSegment.blocked_until > start - timedelta(hours=12),
        )
    ).all()
    busy: dict[int, list[tuple[datetime, datetime]]] = {t: [] for t in therapist_ids}
    for row in rows:
        busy[row.therapist_id].append((row.start_at, row.blocked_until))
    return busy


def _candidate_starts(therapist: Therapist, day: date, total_minutes: int):
    for hours in therapist.working_hours:
        if hours.weekday != day.weekday():
            continue
        window_start = local_to_utc(day, hours.start_time)
        window_end = local_to_utc(day, hours.end_time)
        # Align the first start up to a quarter hour of local time.
        local = window_start.astimezone(clock.BERLIN)
        offset = (15 - local.minute % 15) % 15
        start = window_start + timedelta(minutes=offset) - timedelta(seconds=local.second)
        while start + timedelta(minutes=total_minutes) <= window_end:
            yield start
            start += STEP


def free_slots_by_therapist(
    db: Session, day: date, selection: Selection, therapists: list[Therapist],
    for_owner: bool = False,
) -> dict[int, list[datetime]]:
    studio_closed, off = _closed_therapist_ids(db, day)
    if studio_closed:
        return {t.id: [] for t in therapists}
    busy = _busy_ranges(db, [t.id for t in therapists], day)
    limits = booking_limits(db, for_owner)
    blocked = timedelta(minutes=selection.blocked_minutes)
    result: dict[int, list[datetime]] = {}
    for therapist in therapists:
        if therapist.id in off:
            result[therapist.id] = []
            continue
        starts = []
        for start in _candidate_starts(therapist, day, selection.total_minutes):
            if not limits.allows(start):
                continue
            end = start + blocked
            if any(start < b_end and b_start < end for b_start, b_end in busy[therapist.id]):
                continue
            starts.append(start)
        result[therapist.id] = starts
    return result


def bookings_per_therapist(db: Session, therapist_ids: list[int], day: date) -> dict[int, int]:
    start, end = day_bounds_utc(day)
    rows = db.execute(  # bookings in which the therapist has a part that day
        select(BookingSegment.therapist_id, func.count(func.distinct(BookingSegment.booking_id)))
        .join(Booking, Booking.id == BookingSegment.booking_id)
        .where(
            BookingSegment.therapist_id.in_(therapist_ids),
            occupies_slot(),
            BookingSegment.start_at >= start,
            BookingSegment.start_at < end,
        )
        .group_by(BookingSegment.therapist_id)
    ).all()
    counts = {t: 0 for t in therapist_ids}
    counts.update({row[0]: row[1] for row in rows})
    return counts


def pick_therapist(candidates: list[Therapist], counts: dict[int, int]) -> Therapist:
    """'No preference' rule: fewest non-cancelled bookings that day, then lower id."""
    return min(candidates, key=lambda t: (counts.get(t.id, 0), t.id))


def free_slots(
    db: Session, day: date, selection: Selection, therapists: list[Therapist],
    for_owner: bool = False,
) -> list[Slot]:
    """One slot per start time. With several therapists ("no preference") each time is
    listed once, with the therapist `pick_therapist` would assign."""
    by_therapist = free_slots_by_therapist(db, day, selection, therapists, for_owner)
    counts = bookings_per_therapist(db, [t.id for t in therapists], day)
    by_id = {t.id: t for t in therapists}
    free_at: dict[datetime, list[Therapist]] = {}
    for therapist_id, starts in by_therapist.items():
        for start in starts:
            free_at.setdefault(start, []).append(by_id[therapist_id])
    return [
        Slot(start_at=start, therapist=pick_therapist(free_at[start], counts))
        for start in sorted(free_at)
    ]
