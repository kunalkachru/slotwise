from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.clock import BERLIN
from app.models import Booking, BookingSegment, Customer
from tests.conftest import login


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


def _report(client, start="2026-10-10", end="2026-10-10"):
    assert login(client).status_code == 200
    return client.get("/owner/reports/therapists", params={"from": start, "to": end})


def test_therapist_report_returns_one_exact_row_per_therapist(db, client, report_therapists):
    therapists = report_therapists
    _booking(db, therapists, datetime(2026, 10, 10, 12, tzinfo=BERLIN), "12.50")

    response = _report(client)
    assert response.status_code == 200
    rows = response.json()

    assert len(rows) == len(therapists)
    assert all(
        set(row) == {
            "therapist_id", "therapist_name", "booking_count", "revenue",
            "no_show_count", "no_show_rate", "average_booking_value",
        }
        for row in rows
    )
    assert {row["booking_count"] for row in rows} == {0, 1}


def test_therapist_report_counts_qualifying_bookings_by_segments(
    db, client, report_therapists
):
    therapists = report_therapists
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(
        db, therapists, start, "20.00",
        segment_ids=[therapists[0].id, therapists[1].id, therapists[0].id],
    )
    for offset, status in enumerate(("pending", "expired", "cancelled"), 1):
        _booking(db, therapists, start + timedelta(hours=offset), "99.00", status=status)

    response = _report(client)
    assert response.status_code == 200
    rows = response.json()
    by_id = {row["therapist_id"]: row for row in rows}

    assert by_id[therapists[0].id]["booking_count"] == 1
    assert by_id[therapists[1].id]["booking_count"] == 1
    assert by_id[therapists[0].id]["no_show_count"] == 0
    assert by_id[therapists[1].id]["no_show_count"] == 0
    assert all(row["booking_count"] == 0 for row in rows[2:])


def test_therapist_report_no_show_metrics(db, client, report_therapists):
    therapists = report_therapists
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "20.00", status="done")
    _booking(db, therapists, start + timedelta(hours=1), "30.00", status="no_show")
    _booking(db, therapists, start + timedelta(hours=2), "40.00", status="no_show")

    response = _report(client)
    assert response.status_code == 200
    by_id = {row["therapist_id"]: row for row in response.json()}

    assert by_id[therapists[0].id]["no_show_count"] == 2
    assert by_id[therapists[0].id]["no_show_rate"] == 2 / 3
    assert by_id[therapists[1].id]["no_show_count"] == 0
    assert by_id[therapists[1].id]["no_show_rate"] is None


def test_therapist_report_average_booking_value(db, client, report_therapists):
    therapists = report_therapists
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "10.11")
    _booking(db, therapists, start + timedelta(hours=1), "2.35")

    response = _report(client)
    assert response.status_code == 200
    by_id = {row["therapist_id"]: row for row in response.json()}

    assert by_id[therapists[0].id]["average_booking_value"] == "6.23"
    assert by_id[therapists[1].id]["average_booking_value"] is None


def test_therapist_report_sums_and_formats_revenue(db, client, report_therapists):
    therapists = report_therapists
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "10.10")
    _booking(db, therapists, start + timedelta(hours=1), "2.35")

    response = _report(client)
    assert response.status_code == 200
    row = next(row for row in response.json() if row["therapist_id"] == therapists[0].id)

    assert row["booking_count"] == 2
    assert row["revenue"] == "12.45"


def test_therapist_report_uses_inclusive_berlin_date_boundaries(db, client, report_therapists):
    therapists = report_therapists
    _booking(db, therapists, datetime(2026, 10, 9, 22, tzinfo=UTC), "1.00")
    _booking(db, therapists, datetime(2026, 10, 11, 21, 59, tzinfo=UTC), "2.00")
    _booking(db, therapists, datetime(2026, 10, 11, 22, tzinfo=UTC), "4.00")

    response = _report(client, end="2026-10-11")
    assert response.status_code == 200
    row = next(row for row in response.json() if row["therapist_id"] == therapists[0].id)

    assert row["booking_count"] == 2
    assert row["revenue"] == "3.00"


def test_therapist_report_is_deterministically_ordered(db, client, report_therapists):
    therapists = report_therapists
    start = datetime(2026, 10, 10, 12, tzinfo=BERLIN)
    _booking(db, therapists, start, "10.00", segment_ids=[therapists[1].id])
    _booking(db, therapists, start + timedelta(hours=1), "10.00", segment_ids=[therapists[0].id])

    first = _report(client)
    assert first.status_code == 200
    rows = first.json()

    assert [row["therapist_id"] for row in rows[:2]] == [therapists[0].id, therapists[1].id]
    assert _report(client).json() == rows


def test_therapist_report_requires_owner_session(client):
    response = client.get("/owner/reports/therapists", params={
        "from": "2026-10-10", "to": "2026-10-10",
    })

    assert response.status_code == 401


def test_therapist_report_matches_owner_booking_range_rules(client):
    assert login(client).status_code == 200

    assert client.get("/owner/reports/therapists").status_code == 200
    assert client.get("/owner/reports/therapists", params={
        "from": "2026-10-10",
    }).status_code == 200
    assert client.get("/owner/reports/therapists", params={
        "to": "2026-10-16",
    }).status_code == 200
    assert client.get("/owner/reports/therapists", params={
        "from": "2026-10-11", "to": "2026-10-10",
    }).status_code == 422
    assert client.get("/owner/reports/therapists", params={
        "from": "2026-01-01", "to": "2026-12-31",
    }).status_code == 422
