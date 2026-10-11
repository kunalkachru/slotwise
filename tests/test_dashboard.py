"""Slice 6: dashboard numbers against a hand-computed scenario.
Frozen now: Sat 10 Oct 2026 12:00 Berlin. 30-day window: 11 Sep – 10 Oct 2026."""

from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app import clock
from app.models import Booking, BookingItem, Customer, Therapist
from tests.conftest import login


def add_booking(db, n, day, at, status="done", source="online", late=False, price="50.00",
                confirmed=False, therapist="Sofia"):
    therapist_id = db.scalar(select(Therapist.id).where(Therapist.display_name == therapist))
    customer = Customer(first_name="Guest", last_name=f"N{'ABCDEFGHIJKLMNOP'[n]}",
                        email=f"guest{n}@example.com", phone="+49 151 0000 0000")
    start = datetime.combine(day, at, clock.BERLIN)
    booking = Booking(
        customer=customer, therapist_id=therapist_id, start_at=start,
        end_at=start + timedelta(minutes=30), blocked_until=start + timedelta(minutes=40),
        status=status, source=source, late_cancellation=late, total_price=Decimal(price),
        manage_token=f"token-{n}-" + "x" * 30,
        confirmed_at=start - timedelta(hours=20) if confirmed else None,
        items=[BookingItem(item_type="service", name_snapshot="Express facial",
                           minutes_snapshot=30, unit_price_snapshot=Decimal(price), quantity=1)],
    )
    db.add(booking)
    db.commit()



@pytest.fixture
def scenario(empty_calendar, db):
    from datetime import date

    rows = [
        # past bookings inside the 30-day window
        (date(2026, 10, 1), "done", "online", False, "50.00"),
        (date(2026, 10, 2), "done", "online", False, "50.00"),
        (date(2026, 10, 5), "done", "online", False, "50.00"),
        (date(2026, 10, 6), "done", "online", False, "50.00"),
        (date(2026, 10, 7), "done", "phone", False, "50.00"),
        (date(2026, 10, 8), "done", "waitlist", False, "70.00"),
        (date(2026, 10, 3), "no_show", "online", False, "50.00"),
        (date(2026, 9, 29), "no_show", "online", False, "50.00"),
        (date(2026, 10, 8), "cancelled", "online", False, "50.00"),
        (date(2026, 10, 9), "cancelled", "online", True, "50.00"),
        # outside the 30-day window, but inside the 8-week chart
        (date(2026, 9, 1), "no_show", "online", False, "50.00"),
    ]
    for n, (day, status, source, late, price) in enumerate(rows):
        add_booking(db, n, day, time(10), status, source, late, price)
    today = date(2026, 10, 10)
    add_booking(db, 11, today, time(13), "confirmed", "online", price="59.00", confirmed=True)
    add_booking(db, 12, today, time(15), "booked", "phone", price="39.00")
    add_booking(db, 13, today, time(16), "cancelled", "online", late=True, price="42.00")
    login(empty_calendar)
    return empty_calendar


def test_dashboard_numbers_match_the_hand_computed_scenario(scenario):
    body = scenario.get("/owner/dashboard").json()
    assert body["date"] == "2026-10-10" and body["window_start"] == "2026-09-11"
    # Today: 13:00 confirmed (59) + 15:00 booked (39); the cancelled 16:00 doesn't count.
    assert body["today_bookings"] == 2
    assert body["expected_revenue_today"] == "98.00"
    assert body["confirmation_rate_today"] == 0.5
    # 30 days: 6 done, 2 no-shows -> 2/8
    assert body["no_show_rate"] == 0.25
    # 3 cancellations (8 Oct, 9 Oct late, today late), 1 waitlist booking -> 1/3
    assert body["refill_rate"] == pytest.approx(0.3333)
    assert body["revenue_recovered"] == "70.00"
    # non-cancelled: 8 past + 2 today = 10, of which online: 4 done + 2 no-show + 1 today = 7
    assert body["online_share"] == 0.7
    assert body["targets"] == {"no_show_rate": 0.05, "refill_rate": 0.5, "online_share": 0.6}

    weeks = {w["week_start"]: (w["no_shows"], w["late_cancellations"]) for w in body["weeks"]}
    assert len(body["weeks"]) == 8 and body["weeks"][0]["week_start"] == "2026-08-17"
    assert weeks["2026-08-31"] == (1, 0)   # 1 Sep no-show (outside the 30 days, in the chart)
    assert weeks["2026-09-28"] == (2, 0)   # 29 Sep and 3 Oct no-shows
    assert weeks["2026-10-05"] == (0, 2)   # 9 Oct and 10 Oct late cancellations
    assert sum(n + c for n, c in weeks.values()) == 5

    assert [(a["time"], a["status"]) for a in body["appointments"]] == [
        ("13:00", "confirmed"), ("15:00", "booked"), ("16:00", "cancelled")]
    assert body["appointments"][0]["total_price"] == "59.00"


def test_refill_rate_is_capped_at_100_percent(empty_calendar, db):
    from datetime import date

    add_booking(db, 0, date(2026, 10, 5), time(10), "done", "waitlist")
    add_booking(db, 1, date(2026, 10, 6), time(10), "done", "waitlist")
    add_booking(db, 2, date(2026, 10, 7), time(10), "cancelled", "online")
    login(empty_calendar)
    assert empty_calendar.get("/owner/dashboard").json()["refill_rate"] == 1.0


def test_empty_data_gives_no_rates_and_no_errors(empty_calendar):
    login(empty_calendar)
    body = empty_calendar.get("/owner/dashboard").json()
    assert body["today_bookings"] == 0 and body["expected_revenue_today"] == "0.00"
    for rate in ("confirmation_rate_today", "no_show_rate", "refill_rate", "online_share"):
        assert body[rate] is None, rate
    assert body["revenue_recovered"] == "0.00"
    assert [(w["no_shows"], w["late_cancellations"]) for w in body["weeks"]] == [(0, 0)] * 8
    assert body["appointments"] == []


def test_dashboard_for_another_day_and_needs_login(scenario):
    other = scenario.get("/owner/dashboard", params={"date": "2026-10-08"}).json()
    assert other["date"] == "2026-10-08" and other["window_start"] == "2026-09-09"
    assert [a["status"] for a in other["appointments"]] == ["done", "cancelled"]
    scenario.post("/auth/logout")
    assert scenario.get("/owner/dashboard").status_code == 401
