from datetime import timedelta

from app import clock
from tests.conftest import FROZEN_NOW, book, manage_token, menu_ids

TUESDAY = "2026-10-13"


def test_only_recent_booking_counts(empty_calendar, client, frozen_now, monkeypatch):
    # create one booking created 31 days ago and one created 29 days ago
    # booking creation time is controlled via clock.now
    # old booking (31 days ago)
    monkeypatch.setattr(clock, "now", lambda: FROZEN_NOW - timedelta(days=31))
    # book Deep tissue massage
    book(client, ["Deep tissue massage"], TUESDAY, "10:00")

    # recent booking (29 days ago)
    monkeypatch.setattr(clock, "now", lambda: FROZEN_NOW - timedelta(days=29))
    book(client, ["Classic facial"], TUESDAY, "11:00")

    # restore clock
    monkeypatch.setattr(clock, "now", lambda: FROZEN_NOW)

    r = client.get("/public/services")
    assert r.status_code == 200
    services = [s for c in r.json() for s in c["services"]]
    popular = [s for s in services if s["popular"]]
    assert len(popular) == 1


def test_cancelled_and_expired_do_not_count(empty_calendar, client, frozen_now):
    menu_ids(client)
    # book A twice then cancel both
    book(client, ["Deep tissue massage"], TUESDAY, "10:00")
    r2 = book(client, ["Deep tissue massage"], TUESDAY, "11:00", confirm=False)
    # cancel both bookings
    if r2.status_code == 200:
        manage_token(client, r2.json()["id"])  # ensure token exists
    # the first book() call confirmed and returned 200; get its id to cancel as well
    # find all bookings for that service and cancel two of them
    from app.models import Booking
    with client.app.state.session_factory() as s:
        b_ids = [b.id for b in s.query(Booking).filter(Booking.status != "expired").all()][:2]
    for bid in b_ids:
        token = manage_token(client, bid)
        client.post(f"/public/bookings/{token}/cancel")

    # book B once (stays booked)
    book(client, ["Classic facial"], TUESDAY, "12:00")

    r = client.get("/public/services")
    assert r.status_code == 200
    services = {s["name"]: s for c in r.json() for s in c["services"]}
    assert services["Classic facial"]["popular"] is True
    assert services["Deep tissue massage"]["popular"] is False


def test_multi_treatment_booking_counts_for_each(empty_calendar, client, frozen_now):
    # one visit with two services should increment both
    book(client, ["Deep tissue massage", "Classic facial"], TUESDAY, "14:00")
    r = client.get("/public/services")
    services = {s["name"]: s for c in r.json() for s in c["services"]}
    assert services["Deep tissue massage"]["popular"] is True
    assert services["Classic facial"]["popular"] is True


def test_no_counts_returns_all_false(empty_calendar, client, frozen_now):
    r = client.get("/public/services")
    assert r.status_code == 200
    services = [s for c in r.json() for s in c["services"]]
    assert not any(s["popular"] for s in services)
