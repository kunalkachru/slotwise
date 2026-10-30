from collections import Counter
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import clock
from app.models import Booking, BookingItem

COUNTED_STATUSES = {"pending", "booked", "confirmed", "done", "no_show"}


def popular_service_ids(db: Session) -> set[int]:
    """Return service ids that are most popular in the last 30 days by bookings created_at.
    Only bookings with statuses in COUNTED_STATUSES count. Each booking contributes one
    count for each service item it contains (item_type == 'service')."""
    window_start = clock.now() - timedelta(days=30)
    # join bookings and items, start from bookings and join their items so we can filter by
    # booking.created_at and booking.status reliably.
    stmt = (
        select(BookingItem.service_id)
        .select_from(Booking)
        .join(BookingItem, Booking.id == BookingItem.booking_id)
        .where(Booking.created_at >= window_start)
        .where(Booking.status.in_(list(COUNTED_STATUSES)))
        .where(BookingItem.item_type == "service")
    )
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return set()
    counts = Counter(rows)
    if not counts:
        return set()
    max_count = max(counts.values())
    return {sid for sid, cnt in counts.items() if cnt == max_count}
