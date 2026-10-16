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

Several therapists per visit (option B, PLAN.md): each treatment can have its own
therapist. A visit is a chain of segments, one per therapist, run back to back in the
order the customer chose. A 15-minute break at a handover is offered only when no gapless
chain fits that day (or when the customer picks times themselves).
"""

from dataclasses import dataclass, field
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



# ---------- Chains: one therapist per segment (option B) ----------

BREAK = timedelta(minutes=15)
MAX_CHAINS_TRIED = 5000  # per start time; far above what a small studio's menu needs


@dataclass(frozen=True)
class Step:
    """One chosen treatment (with its add-ons) inside a chain."""
    service_id: int
    therapist: Therapist
    start_at: datetime
    end_at: datetime


@dataclass(frozen=True)
class SegmentPlan:
    """One therapist's part of a visit: consecutive treatments with the same therapist.
    Its cleanup buffer (largest of its treatments) only blocks that therapist."""
    therapist: Therapist
    start_at: datetime
    end_at: datetime
    blocked_until: datetime
    service_ids: tuple[int, ...]


@dataclass(frozen=True)
class Slot:
    start_at: datetime  # UTC
    steps: tuple[Step, ...]
    segments: tuple[SegmentPlan, ...]
    break_before: int | None = None  # index of the treatment that follows the break
    rank: tuple = field(default=(), compare=False)

    @property
    def therapist(self) -> Therapist:
        return self.steps[0].therapist

    @property
    def end_at(self) -> datetime:
        return self.steps[-1].end_at

    @property
    def local_time(self) -> str:
        return self.start_at.astimezone(clock.BERLIN).strftime("%H:%M")


class DayPlanner:
    """Everything needed to plan chains on one day, read once: busy times, working hours,
    days off and the "fewest bookings" counts. Availability and booking creation (inside
    the lock) both plan with this class, so they always agree."""

    def __init__(self, db: Session, day: date, selection: Selection,
                 candidates: dict[int, list[Therapist]], for_owner: bool = False):
        self.day = day
        self.services = selection.services
        self.minutes = [selection.step_minutes(s) for s in self.services]
        self.buffers = [s.buffer_minutes for s in self.services]
        studio_closed, off = _closed_therapist_ids(db, day)
        self.candidates = [
            [] if studio_closed else [t for t in candidates[s.id] if t.id not in off]
            for s in self.services
        ]
        ids = sorted({t.id for options in self.candidates for t in options})
        self.busy = _busy_ranges(db, ids, day) if ids else {}
        self.counts = bookings_per_therapist(db, ids, day) if ids else {}
        self.limits = booking_limits(db, for_owner)
        self.windows = {
            t.id: [(local_to_utc(day, h.start_time), local_to_utc(day, h.end_time))
                   for h in t.working_hours if h.weekday == day.weekday()]
            for options in self.candidates for t in options
        }

    def starts(self) -> list[datetime]:
        found = {start for t in self.candidates[0]
                 for start in _candidate_starts(t, self.day, self.minutes[0])}
        return sorted(start for start in found if self.limits.allows(start))

    def _works(self, therapist: Therapist, start: datetime, end: datetime) -> bool:
        return any(w_start <= start and end <= w_end for w_start, w_end in
                   self.windows[therapist.id])

    def _free(self, therapist: Therapist, start: datetime, end: datetime) -> bool:
        return not any(start < b_end and b_start < end for b_start, b_end in
                       self.busy[therapist.id])

    def _step_times(self, start: datetime, break_before: int | None):
        times, at = [], start
        for index, minutes in enumerate(self.minutes):
            if index == break_before:
                at += BREAK
            times.append((at, at + timedelta(minutes=minutes)))
            at = times[-1][1]
        return times

    def _segments(self, assigned: list[Therapist], times) -> list[SegmentPlan] | None:
        segments: list[SegmentPlan] = []
        first = 0
        for index in range(1, len(assigned) + 1):
            if index < len(assigned) and assigned[index] is assigned[first] and (
                    times[index][0] == times[index - 1][1]):
                continue
            therapist, start, end = assigned[first], times[first][0], times[index - 1][1]
            blocked = end + timedelta(minutes=max(self.buffers[first:index]))
            if not (self._works(therapist, start, end) and self._free(therapist, start, blocked)):
                return None
            # The same therapist twice in one visit (Lena, Sofia, Lena): her own parts,
            # buffer included, must not overlap either.
            if any(s.therapist is therapist and start < s.blocked_until for s in segments):
                return None
            segments.append(SegmentPlan(therapist, start, end, blocked,
                                        tuple(s.id for s in self.services[first:index])))
            first = index
        return segments

    def chain(self, start: datetime, break_before: int | None = None) -> Slot | None:
        """The best chain starting at `start`: fewest handovers first, then per treatment
        the therapist with the fewest bookings that day, then the lower id. A break only
        sits at a handover."""
        count = len(self.services)
        if not self.limits.allows(start) or (
                break_before is not None and not 0 < break_before < count):
            return None
        times = self._step_times(start, break_before)
        best: tuple[tuple, list[SegmentPlan], list[Therapist]] | None = None
        tried = 0

        def walk(assigned: list[Therapist], handovers: int) -> None:
            nonlocal best, tried
            index = len(assigned)
            if tried >= MAX_CHAINS_TRIED or (best and handovers > best[0][0] - 1):
                return
            if index == count:
                tried += 1
                segments = self._segments(assigned, times)
                if segments is None:
                    return
                rank = (len(segments),
                        tuple((self.counts.get(t.id, 0), t.id) for t in assigned))
                if best is None or rank < best[0]:
                    best = (rank, segments, list(assigned))
                return
            for therapist in self.candidates[index]:
                handover = bool(assigned) and therapist is not assigned[-1]
                if index == break_before and not handover:
                    continue
                if not (self._works(therapist, *times[index])
                        and self._free(therapist, *times[index])):
                    continue
                walk(assigned + [therapist], handovers + handover)

        walk([], 0)
        if best is None:
            return None
        rank, segments, assigned = best
        steps = tuple(Step(s.id, t, *times[i])
                      for i, (s, t) in enumerate(zip(self.services, assigned, strict=True)))
        return Slot(start_at=start, steps=steps, segments=tuple(segments),
                    break_before=break_before, rank=(*rank, break_before or 0))


def chain_slots(
    db: Session, day: date, selection: Selection, candidates: dict[int, list[Therapist]],
    for_owner: bool = False, choose_myself: bool = False,
) -> list[Slot]:
    """Free chains on a day, by start time.

    Suggested (default): one chain per start time, gapless; only when no gapless chain
    fits all day, one chain with a 15-minute break per start time.
    Choose myself: every gapless chain plus, per start time, the best chain with a break
    at each possible handover, so the customer can pick each treatment's time."""
    planner = DayPlanner(db, day, selection, candidates, for_owner)
    starts = planner.starts()
    gapless = [slot for slot in map(planner.chain, starts) if slot]
    if len(selection.services) == 1 or (gapless and not choose_myself):
        return gapless
    with_break = [slot for start in starts for k in range(1, len(selection.services))
                  if (slot := planner.chain(start, k))]
    if choose_myself:
        return sorted(gapless + with_break, key=lambda s: (s.start_at, s.break_before or 0))
    best: dict[datetime, Slot] = {}
    for slot in with_break:
        if slot.start_at not in best or slot.rank < best[slot.start_at].rank:
            best[slot.start_at] = slot
    return [best[start] for start in sorted(best)]
