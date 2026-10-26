from datetime import date

from app.main import create_app
from app.db import make_engine, make_session_factory
from app.seed import seed
from app.config import Settings
from fastapi.testclient import TestClient


def setup_db():
    settings = Settings.from_env()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed(db, settings)
    return engine, session_factory


def test_free_count_matches_slots(tmp_path):
    engine, session_factory = setup_db()
    app = create_app(Settings.from_env())
    app.state.engine = engine
    app.state.session_factory = session_factory
    client = TestClient(app)
    # pick a seeded day that has slots; seed creates demo data on today
    day = date.today().isoformat()
    r = client.get(f"/public/availability?date={day}")
    assert r.status_code == 200
    data = r.json()
    assert 'free_count' in data and isinstance(data['free_count'], int)
    assert data['free_count'] == len(data.get('slots', []))


def test_booking_reduces_free_count(tmp_path):
    engine, session_factory = setup_db()
    app = create_app(Settings.from_env())
    app.state.engine = engine
    app.state.session_factory = session_factory
    client = TestClient(app)
    day = date.today().isoformat()
    # get slots
    r = client.get(f"/public/availability?date={day}")
    assert r.status_code == 200
    data = r.json()
    slots = data.get('slots', [])
    if not slots:
        return
    slot = slots[0]
    # build a simple booking payload for the slot
    payload = {
        "service_ids": [1],
        "add_on_ids": [],
        "therapist_id": slot['therapist_id'],
        "date": day,
        "start_time": slot['time'],
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "123",
    }
    r2 = client.post("/public/bookings", json=payload)
    assert r2.status_code == 200
    r3 = client.get(f"/public/availability?date={day}")
    assert r3.status_code == 200
    data2 = r3.json()
    assert data2['free_count'] == max(0, data['free_count'] - 1)
