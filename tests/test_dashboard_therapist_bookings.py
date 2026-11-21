from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app import clock
from app.logic.dashboard import build
from app.models import Booking, BookingItem, BookingSegment, Customer, Service, Therapist
from tests.conftest import login

ANCHOR = date(2026, 10, 10)


def add_booking(db, number, day, therapist, service, status="booked"):
    start = datetime.combine(day, time(10), clock.BERLIN)
    customer = Customer(
        first_name="Guest", last_name=str(number), email=f"guest-{number}@example.com",
        phone="+49 151 0000 0000",
    )
    booking = Booking(
        customer=customer, therapist_id=therapist.id, start_at=start,
        end_at=start + timedelta(minutes=30), blocked_until=start + timedelta(minutes=40),
        status=status, source="online", total_price=Decimal("50.00"),
        manage_token=f"dashboard-token-{number}-" + "x" * 20,
        items=[BookingItem(
            item_type="service", service_id=service.id, name_snapshot=service.name,
            minutes_snapshot=30, unit_price_snapshot=Decimal("50.00"), quantity=1,
        )],
    )
    db.add(booking)
    db.commit()


def roster(db):
    therapists = db.scalars(
        select(Therapist).where(Therapist.active.is_(True)).order_by(Therapist.id)
    ).all()
    services = db.scalars(
        select(Service).where(Service.active.is_(True)).order_by(Service.id)
    ).all()
    return therapists, services


def test_dashboard_returns_seven_day_counts_for_every_active_therapist(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 1, ANCHOR, therapists[0], services[0])
    login(empty_calendar)

    response = empty_calendar.get("/owner/dashboard", params={"date": ANCHOR.isoformat()})
    assert response.status_code == 200
    dashboard = response.json()

    assert [row["therapist_id"] for row in dashboard["therapist_bookings"]] == [
        therapist.id for therapist in therapists
    ]
    assert all(len(row["days"]) == 7 for row in dashboard["therapist_bookings"])
    assert all([day["date"] for day in row["days"]] == [
        (ANCHOR + timedelta(days=i)).isoformat() for i in range(7)
    ] for row in dashboard["therapist_bookings"])
    assert dashboard["therapist_bookings"][0]["days"][0]["count"] == 1
    assert all(day["count"] == 0 for day in dashboard["therapist_bookings"][1]["days"])


def test_dashboard_counts_qualifying_bookings_by_therapist_and_local_date(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 2, ANCHOR, therapists[0], services[0], "confirmed")
    add_booking(db, 3, ANCHOR + timedelta(days=1), therapists[0], services[0], "done")
    add_booking(db, 4, ANCHOR + timedelta(days=2), therapists[0], services[0], "cancelled")
    add_booking(db, 5, ANCHOR + timedelta(days=3), therapists[0], services[0], "pending")
    add_booking(db, 6, ANCHOR + timedelta(days=4), therapists[0], services[0], "expired")

    row = build(db, ANCHOR).therapist_bookings.rows[0]

    assert [day.count for day in row.days] == [1, 1, 0, 0, 0, 0, 0]

    # A chain booking is counted once for each participating therapist.
    booking = db.scalar(
        select(Booking).where(Booking.manage_token.startswith("dashboard-token-2-"))
    )
    therapists, _ = roster(db)
    booking.segments = [
        BookingSegment(position=0, therapist_id=therapists[0].id,
                       start_at=booking.start_at, end_at=booking.end_at,
                       blocked_until=booking.blocked_until),
        BookingSegment(position=1, therapist_id=therapists[1].id,
                       start_at=booking.start_at, end_at=booking.end_at,
                       blocked_until=booking.blocked_until),
    ]
    db.commit()
    schedule = build(db, ANCHOR).therapist_bookings
    assert schedule.rows[0].days[0].count == 1
    assert schedule.rows[1].days[0].count == 1


def test_dashboard_service_filter_limits_therapist_counts(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 7, ANCHOR, therapists[0], services[0])
    add_booking(db, 8, ANCHOR + timedelta(days=1), therapists[0], services[1])

    login(empty_calendar)
    all_services = empty_calendar.get(
        "/owner/dashboard", params={"date": ANCHOR.isoformat()}
    ).json()
    filtered = empty_calendar.get(
        "/owner/dashboard", params={"date": ANCHOR.isoformat(), "service_id": services[0].id}
    ).json()
    all_services = all_services["therapist_bookings"][0]
    filtered = filtered["therapist_bookings"][0]

    assert [day["count"] for day in all_services["days"]][:2] == [1, 1]
    assert [day["count"] for day in filtered["days"]][:2] == [1, 0]
    assert empty_calendar.get(
        "/owner/dashboard", params={"date": ANCHOR.isoformat()}
    ).json()["weekly_total"] == 2
    assert empty_calendar.get(
        "/owner/dashboard", params={"date": ANCHOR.isoformat(), "service_id": services[0].id}
    ).json()["weekly_total"] == 1


def test_dashboard_uses_inclusive_seven_day_local_date_window(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 9, ANCHOR, therapists[0], services[0])
    add_booking(db, 10, ANCHOR + timedelta(days=6), therapists[0], services[0])
    add_booking(db, 11, ANCHOR + timedelta(days=7), therapists[0], services[0])

    login(empty_calendar)
    row = empty_calendar.get(
        "/owner/dashboard", params={"date": ANCHOR.isoformat()}
    ).json()["therapist_bookings"][0]

    assert [day["date"] for day in row["days"]] == [
        (ANCHOR + timedelta(days=i)).isoformat() for i in range(7)
    ]
    assert [day["count"] for day in row["days"]] == [1, 0, 0, 0, 0, 0, 1]
    assert empty_calendar.get(
        "/owner/dashboard", params={"date": (ANCHOR + timedelta(days=7)).isoformat()}
    ).json()["therapist_bookings"][0]["days"][0]["count"] == 1


def test_dashboard_schedule_preserves_anchor_date_and_selected_day_content(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 14, ANCHOR + timedelta(days=1), therapists[0], services[0])
    login(empty_calendar)

    response = empty_calendar.get(
        "/owner/dashboard", params={"date": (ANCHOR + timedelta(days=1)).isoformat()}
    )

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["date"] == (ANCHOR + timedelta(days=1)).isoformat()
    assert dashboard["appointments"][0]["time"] == "10:00"
    assert [day["date"] for day in dashboard["therapist_bookings"][0]["days"]] == [
        (ANCHOR + timedelta(days=1 + i)).isoformat() for i in range(7)
    ]
    assert dashboard["therapist_bookings"][0]["days"][0]["count"] == 1


def test_dashboard_therapist_schedule_requires_owner_session(empty_calendar):
    response = empty_calendar.get("/owner/dashboard", params={"date": ANCHOR.isoformat()})

    assert response.status_code == 401
    assert "therapist_bookings" not in response.json()


def test_dashboard_includes_combined_weekly_total(empty_calendar, db):
    therapists, services = roster(db)
    add_booking(db, 12, ANCHOR, therapists[0], services[0])
    add_booking(db, 13, ANCHOR + timedelta(days=1), therapists[1], services[0])

    dashboard = build(db, ANCHOR).therapist_bookings

    assert dashboard.weekly_total == 2
    assert dashboard.weekly_total == sum(day.count for row in dashboard.rows for day in row.days)

    login(empty_calendar)
    response = empty_calendar.get("/owner/dashboard", params={"date": ANCHOR.isoformat()})
    assert response.json()["weekly_total"] == 2


def test_dashboard_renders_no_bookings_state_for_zero_cells():
    root = Path(__file__).parents[1] / "app" / "static"
    javascript = (root / "js" / "owner-dashboard.js").read_text(encoding="utf-8")

    assert '"No bookings"' in javascript
    assert 'day.count === 0' in javascript
    assert "no-bookings" in javascript
    assert 'aria-label' in javascript


def test_dashboard_page_renders_service_filter_and_applies_it():
    root = Path(__file__).parents[1] / "app" / "static"
    html = (root / "owner" / "dashboard.html").read_text(encoding="utf-8")
    javascript = (root / "js" / "owner-dashboard.js").read_text(encoding="utf-8")

    assert 'id="dash-service"' in html
    assert 'ownerApi("/owner/services")' in javascript
    assert "service_id" in javascript
    assert "weekly_total" in javascript
    assert "selected" in javascript
    assert 'service.onchange = () => load()' in javascript


def test_dashboard_page_renders_seven_day_schedule_date_range_heading():
    root = Path(__file__).parents[1] / "app" / "static"
    javascript = (root / "js" / "owner-dashboard.js").read_text(encoding="utf-8")

    assert "Therapist bookings" in javascript
    assert "[days[0], days[days.length - 1]]" in javascript
    assert "const dateRange = `${dayLabel(rangeDays[0])} – ${dayLabel(rangeDays[1])}`" in javascript
    assert " – " in javascript
    assert "therapistSchedule(d.therapist_bookings, d.weekly_total, d.date)" in javascript


def test_dashboard_highlights_today_column():
    root = Path(__file__).parents[1] / "app" / "static"
    javascript = (root / "js" / "owner-dashboard.js").read_text(encoding="utf-8")
    styles = (root / "css" / "styles.css").read_text(encoding="utf-8")
    calm = (root / "css" / "calm.css").read_text(encoding="utf-8")

    assert 'const today = isoDay.format(new Date())' in javascript
    assert 'day.date === today ? " today" : ""' in javascript
    assert "table.schedule th.today" in styles
    assert "table.schedule td.today" in styles
    assert "table.schedule th.today" in calm
    assert "table.schedule td.today" in calm
    assert "font-weight: 700" in styles


def test_dashboard_highlight_uses_current_local_date_not_anchor():
    root = Path(__file__).parents[1] / "app" / "static"
    javascript = (root / "js" / "owner-dashboard.js").read_text(encoding="utf-8")

    assert 'const today = isoDay.format(new Date())' in javascript
    assert 'day.date === today ? " today" : ""' in javascript
    assert 'day.date === anchorDate' not in javascript


def test_dashboard_schedule_date_range_data_matches_two_anchor_dates(empty_calendar):
    login(empty_calendar)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    def day_label(day):
        return f"{weekdays[day.weekday()]} {day.day} {months[day.month - 1]}"

    for anchor in (ANCHOR, ANCHOR + timedelta(days=3)):
        dashboard = empty_calendar.get(
            "/owner/dashboard", params={"date": anchor.isoformat()}
        ).json()
        days = dashboard["therapist_bookings"][0]["days"]
        expected_days = [anchor + timedelta(days=i) for i in range(7)]

        actual_days = [date.fromisoformat(day["date"]) for day in days]
        assert actual_days == expected_days
        assert f"{day_label(actual_days[0])} – {day_label(actual_days[-1])}" == (
            f"{day_label(anchor)} – {day_label(anchor + timedelta(days=6))}"
        )
