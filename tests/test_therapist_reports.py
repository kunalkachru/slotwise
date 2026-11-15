from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete

from app.clock import BERLIN
from app.logic.owner_bookings import therapist_report
from app.models import Booking, BookingItem, BookingSegment, Customer, Therapist
from app.schemas import TherapistReportOut


def _therapists(db):
    db.execute(delete(BookingItem))
    db.execute(delete(BookingSegment))
    db.execute(delete(Booking))
    db.execute(delete(Customer))
    db.commit()
    return db.query(Therapist).order_by(Therapist.id).all()


def _booking(db, therapists, start, price, status="booked", segment_ids=None):
    customer = Customer(
        first_name="Report", last_name="Customer",
        email=f"report-{start.timestamp()}-{price}@example.com",
        phone="+49 151 0000 0000",
    )
    db.add(customer)
    db.flush()
    segment_ids = segment_ids or [therapists[0].id]
    booking = Booking(
        customer=customer, therapist_id=segment_ids[0], start_at=start,
        end_at=start + timedelta(minutes=30), blocked_until=start + timedelta(minutes=40),
        status=status, total_price=Decimal(price), source="phone",
        manage_token=f"report-token-{start.timestamp()}-{price}-{status}",
    )
    booking.segments = [
        BookingSegment(
            position=position, therapist_id=therapist_id,
            start_at=start + timedelta(minutes=position * 30),
            end_at=start + timedelta(minutes=(position + 1) * 30),
            blocked_until=start + timedelta(minutes=(position + 1) * 30 + 10),
        )
        for position, therapist_id in enumerate(segment_ids)
    ]
    db.add(booking)
    db.commit()


def _json_row(row):
    return TherapistReportOut.model_validate(row).model_dump(mode="json")


def test_therapist_report_returns_one_exact_row_per_therapist(db):
    therapists = _therapists(db)
    _booking(db, therapists, datetime(2026, 10, 10, 12, tzinfo=BERLIN), "12.50")

    rows = therapist_report(db, date(2026, 10, 10), date(2026, 10, 10))

    assert len(rows) == len(therapists)
    assert {tuple(row) for row in rows}  # rows are mapping-like report records
    assert all(
        set(row) == {"therapist_id", "therapist_name", "booking_count", "revenue"}
        for row in rows
    )
    assert {row["booking_count"] for row in rows} == {0, 1}


def test_therapist_report_counts_qualifying_bookings_by_segments(db):
    therapists = _therapists(db)
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(
        db, therapists, start, "20.00",
        segment_ids=[therapists[0].id, therapists[1].id, therapists[0].id],
    )
    for offset, status in enumerate(("pending", "expired", "cancelled"), 1):
        _booking(db, therapists, start + timedelta(hours=offset), "99.00", status=status)

    rows = therapist_report(db, date(2026, 10, 10), date(2026, 10, 10))
    by_id = {row["therapist_id"]: row for row in rows}

    assert by_id[therapists[0].id]["booking_count"] == 1
    assert by_id[therapists[1].id]["booking_count"] == 1
    assert all(row["booking_count"] == 0 for row in rows[2:])


def test_therapist_report_sums_and_formats_revenue(db):
    therapists = _therapists(db)
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "10.10")
    _booking(db, therapists, start + timedelta(hours=1), "2.35")

    row = next(row for row in therapist_report(db, date(2026, 10, 10), date(2026, 10, 10))
               if row["therapist_id"] == therapists[0].id)

    assert row["booking_count"] == 2
    assert _json_row(row)["revenue"] == "12.45"


def test_therapist_report_uses_inclusive_berlin_date_boundaries(db):
    therapists = _therapists(db)
    _booking(db, therapists, datetime(2026, 10, 9, 22, tzinfo=UTC), "1.00")
    _booking(db, therapists, datetime(2026, 10, 11, 21, 59, tzinfo=UTC), "2.00")
    _booking(db, therapists, datetime(2026, 10, 11, 22, tzinfo=UTC), "4.00")

    row = next(row for row in therapist_report(db, date(2026, 10, 10), date(2026, 10, 11))
               if row["therapist_id"] == therapists[0].id)

    assert row["booking_count"] == 2
    assert _json_row(row)["revenue"] == "3.00"


def test_therapist_report_is_deterministically_ordered(db):
    therapists = _therapists(db)
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "10.00", segment_ids=[therapists[1].id])
    _booking(db, therapists, start + timedelta(hours=1), "10.00", segment_ids=[therapists[0].id])

    rows = therapist_report(db, date(2026, 10, 10), date(2026, 10, 10))

    assert [row["therapist_id"] for row in rows[:2]] == [therapists[0].id, therapists[1].id]
    assert therapist_report(db, date(2026, 10, 10), date(2026, 10, 10)) == rows
