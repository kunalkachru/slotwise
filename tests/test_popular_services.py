from datetime import timedelta

from app import clock
from app.models import Booking


def test_only_recent_booking_counts(make_client, frozen_now):
    client = make_client()
    # recent booking for service B (29 days ago)
    client.app.dependency_overrides = {}
    # create old booking 31 days ago
    client.app.dependency_overrides = {}
    # book service A at 31 days ago
    clock.now = lambda: frozen_now - timedelta(days=31)
    res1 = client.post("/public/bookings", json={
        "service_ids": [2], "add_on_ids": [], "therapist_id": None,
        "date": "2026-11-10", "start_time": "10:00",
        "first_name": "Old", "last_name": "Customer", "email": "old@example.com", "phone": "x"
    })
    assert res1.status_code == 200
    # book service B at 29 days ago
    clock.now = lambda: frozen_now - timedelta(days=29)
    res2 = client.post("/public/bookings", json={
        "service_ids": [3], "add_on_ids": [], "therapist_id": None,
        "date": "2026-11-10", "start_time": "11:00",
        "first_name": "Recent", "last_name": "Customer", "email": "recent@example.com", "phone": "y"
    })
    assert res2.status_code == 200
    # restore time
    clock.now = lambda: frozen_now

    r = client.get("/public/services")
    assert r.status_code == 200
    services = [s for c in r.json() for s in c["services"]]
    # only the recent booking's service should be popular
    popular = [s for s in services if s["popular"]]
    assert len(popular) == 1


def test_cancelled_and_expired_do_not_count(client, frozen_now):
    # service A: two cancelled bookings
    # service B: one booked booking
    ids = {}
    for c in client.get("/public/services").json():
        for s in c["services"]:
            ids[s["name"]] = s["id"]
    # book A twice then cancel
    clock.now = lambda: frozen_now
    r1 = client.post("/public/bookings", json={
        "service_ids": [ids["Deep tissue massage"]], "add_on_ids": [], "therapist_id": None,
        "date": "2026-10-20", "start_time": "10:00",
        "first_name": "A1", "last_name": "X", "email": "a1@example.com", "phone": "p"
    })
    assert r1.status_code == 200
    token = None
    # cancel it
    token = client.app.state.session_factory().run(
        lambda s: s.get(Booking, r1.json()["id"]).manage_token
    )
    assert client.post(f"/public/bookings/{token}/cancel").status_code == 200

    r2 = client.post("/public/bookings", json={
        "service_ids": [ids["Deep tissue massage"]], "add_on_ids": [], "therapist_id": None,
        "date": "2026-10-21", "start_time": "11:00",
        "first_name": "A2", "last_name": "X", "email": "a2@example.com", "phone": "p"
    })
    token2 = client.app.state.session_factory().run(
        lambda s: s.get(Booking, r2.json()["id"]).manage_token
    )
    client.post(f"/public/bookings/{token2}/cancel")

    # book B once (stays booked)
    r3 = client.post("/public/bookings", json={
        "service_ids": [ids["Classic facial"]], "add_on_ids": [], "therapist_id": None,
        "date": "2026-10-22", "start_time": "12:00",
        "first_name": "B1", "last_name": "Y", "email": "b1@example.com", "phone": "q"
    })
    assert r3.status_code == 200

    r = client.get("/public/services")
    assert r.status_code == 200
    services = {s["name"]: s for c in r.json() for s in c["services"]}
    assert services["Classic facial"]["popular"] is True
    assert services["Deep tissue massage"]["popular"] is False


def test_multi_treatment_booking_counts_for_each(client, frozen_now):
    ids = {}
    for c in client.get("/public/services").json():
        for s in c["services"]:
            ids[s["name"]] = s["id"]
    # book one visit with two services
    r = client.post("/public/bookings", json={
        "service_ids": [ids["Deep tissue massage"], ids["Classic facial"]],
        "add_on_ids": [], "therapist_id": None,
        "date": "2026-10-25", "start_time": "10:00",
        "first_name": "C", "last_name": "Z", "email": "c@example.com", "phone": "c"
    })
    assert r.status_code == 200
    r = client.get("/public/services")
    services = {s["name"]: s for c in r.json() for s in c["services"]}
    assert services["Deep tissue massage"]["popular"] is True
    assert services["Classic facial"]["popular"] is True


def test_no_counts_returns_all_false(empty_calendar, client, frozen_now):
    # empty_calendar fixture removed all bookings/customers
    r = client.get("/public/services")
    assert r.status_code == 200
    services = [s for c in r.json() for s in c["services"]]
    assert not any(s["popular"] for s in services)
