"""Owner dashboard numbers (slice 6). Definitions (PLAN.md slice 6):

- pending (awaiting email confirmation) and expired requests are left out everywhere.
- today: non-cancelled bookings starting on the chosen day; expected revenue is their
  total; confirmation rate is the share whose customer confirmed.
- last 30 days = the 30 local days ending on the chosen day, by appointment start:
  - no-show rate = no_show / (done + no_show)
  - refilled from waitlist = waitlist bookings / cancelled bookings (capped at 100%)
  - revenue recovered = total of waitlist bookings
  - online share = online / non-cancelled bookings
- weekly chart: no-shows and late cancellations for the 8 weeks (Mon–Sun) up to and
  including the chosen day's week.

A rate with nothing to divide by is None, never a division by zero.
Targets come from the blueprint's "how you will know it is working".
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.logic.availability import day_bounds_utc
from app.logic.owner_bookings import REPEAT_NO_SHOW_THRESHOLD
from app.models import Booking

WINDOW_DAYS = 30
CHART_WEEKS = 8
TARGETS = {"no_show_rate": 0.05, "refill_rate": 0.50, "online_share": 0.60}


@dataclass
class WeekCounts:
    week_start: date
    no_shows: int = 0
    late_cancellations: int = 0


@dataclass
class Dashboard:
    day: date
    window_start: date
    today: list[Booking]
    today_bookings: int
    expected_revenue_today: Decimal
    confirmation_rate_today: float | None
    no_show_rate: float | None
    refill_rate: float | None
    revenue_recovered: Decimal
    online_share: float | None
    weeks: list[WeekCounts] = field(default_factory=list)


def _rate(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def _bookings_between(db: Session, first: date, last: date) -> list[Booking]:
    start, _ = day_bounds_utc(first)
    _, end = day_bounds_utc(last)
    return list(db.scalars(
        select(Booking)
        .where(Booking.start_at >= start, Booking.start_at < end)
        .options(selectinload(Booking.items), selectinload(Booking.customer),
                 selectinload(Booking.therapist))
        .order_by(Booking.start_at, Booking.therapist_id)
    ).all())


def _local_day(booking: Booking) -> date:
    from app import clock

    return booking.start_at.astimezone(clock.BERLIN).date()


def build(db: Session, day: date) -> Dashboard:
    window_start = day - timedelta(days=WINDOW_DAYS - 1)
    first_week = day - timedelta(days=day.weekday()) - timedelta(weeks=CHART_WEEKS - 1)
    bookings = _bookings_between(db, min(window_start, first_week), day)

    # Unconfirmed (pending) and never-confirmed (expired) requests aren't bookings yet.
    bookings = [b for b in bookings if b.status not in ("pending", "expired")]
    today = [b for b in bookings if _local_day(b) == day]
    today_active = [b for b in today if b.status != "cancelled"]

    window = [b for b in bookings if window_start <= _local_day(b) <= day]
    active = [b for b in window if b.status != "cancelled"]
    done = sum(b.status == "done" for b in window)
    no_shows = sum(b.status == "no_show" for b in window)
    cancelled = sum(b.status == "cancelled" for b in window)
    from_waitlist = [b for b in active if b.source == "waitlist"]
    refill = _rate(len(from_waitlist), cancelled)

    weeks = [WeekCounts(first_week + timedelta(weeks=i)) for i in range(CHART_WEEKS)]
    for b in bookings:
        local = _local_day(b)
        if local < first_week:
            continue
        week = weeks[(local - first_week).days // 7]
        if b.status == "no_show":
            week.no_shows += 1
        elif b.status == "cancelled" and b.late_cancellation:
            week.late_cancellations += 1

    return Dashboard(
        day=day,
        window_start=window_start,
        today=today,
        today_bookings=len(today_active),
        expected_revenue_today=sum((b.total_price for b in today_active), Decimal(0)),
        confirmation_rate_today=_rate(
            sum(b.confirmed_at is not None for b in today_active), len(today_active)),
        no_show_rate=_rate(no_shows, done + no_shows),
        refill_rate=min(refill, 1.0) if refill is not None else None,
        revenue_recovered=sum((b.total_price for b in from_waitlist), Decimal(0)),
        online_share=_rate(sum(b.source == "online" for b in active), len(active)),
        weeks=weeks,
    )


def appointment_rows(dashboard: Dashboard) -> list[dict]:
    from app import clock

    return [
        {
            "id": b.id,
            "time": b.start_at.astimezone(clock.BERLIN).strftime("%H:%M"),
            "customer_name": f"{b.customer.first_name} {b.customer.last_name}",
            "repeat_no_show": b.customer.no_show_count >= REPEAT_NO_SHOW_THRESHOLD,
            "therapist_name": b.therapist.display_name,
            "services": [i.name_snapshot for i in b.items if i.item_type == "service"],
            "total_price": b.total_price,
            "status": b.status,
        }
        for b in dashboard.today
    ]
