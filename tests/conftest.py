from dataclasses import replace
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import clock
from app.config import Settings
from app.main import create_app

OWNER_EMAIL = "owner@example.com"
OWNER_PASSWORD = "test-owner-password"

TEST_SETTINGS = Settings(
    database_url="sqlite://",  # fresh in-memory database per app
    secret_key="test-secret-key",
    owner_email=OWNER_EMAIL,
    owner_password=OWNER_PASSWORD,
    seed_demo_data=True,
    jobs_secret="test-jobs-secret",
)

# Requests reach the app from Render's internal proxy, which is what makes
# X-Forwarded-For trustworthy (app/security.py: client_ip).
RENDER_PROXY = "10.0.0.1"

# Saturday 10 Oct 2026, midday in Berlin
FROZEN_NOW = datetime(2026, 10, 10, 12, 0, tzinfo=clock.BERLIN)


@pytest.fixture
def frozen_now(monkeypatch):
    monkeypatch.setattr(clock, "now", lambda: FROZEN_NOW)
    return FROZEN_NOW


@pytest.fixture
def make_client():
    """Factory: make_client(seed_demo_data=False, peer="93.184.216.34", ...) -> started client."""
    clients = []

    def _make(settings: Settings | None = None, peer: str = RENDER_PROXY, **overrides):
        client = TestClient(
            create_app(replace(settings or TEST_SETTINGS, **overrides)), client=(peer, 50000)
        )
        client.__enter__()  # runs startup: create tables + seed
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client, frozen_now):
    return make_client()


@pytest.fixture
def db(client):
    with client.app.state.session_factory() as session:
        yield session


def login(client: TestClient, email: str = OWNER_EMAIL, password: str = OWNER_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


@pytest.fixture
def empty_calendar(client):
    """Demo menu and therapists, but no bookings or customers."""
    from sqlalchemy import delete

    from app.models import Booking, BookingItem, Customer

    with client.app.state.session_factory() as session:
        session.execute(delete(BookingItem))
        session.execute(delete(Booking))
        session.execute(delete(Customer))
        session.commit()
    return client


def menu_ids(client) -> dict:
    """{"Deep tissue massage": 2, ("Deep tissue massage", "Hot stones"): 4, ...}"""
    ids: dict = {}
    for category in client.get("/public/services").json():
        for service in category["services"]:
            ids[service["name"]] = service["id"]
            for add_on in service["add_ons"]:
                ids[(service["name"], add_on["name"])] = add_on["id"]
    return ids


def therapist_id(client, name: str) -> int:
    from sqlalchemy import select

    from app.models import Therapist

    with client.app.state.session_factory() as session:
        return session.scalar(select(Therapist.id).where(Therapist.display_name == name))


CUSTOMER = {
    "first_name": "Anna",
    "last_name": "Müller",
    "email": "anna.mueller@example.com",
    "phone": "+49 151 0000 0001",
}


def book(client, services, day, start, therapist=None, add_ons=(), **customer):
    ids = menu_ids(client)
    body = {
        "service_ids": [ids[s] for s in services],
        "add_on_ids": [ids[a] for a in add_ons],
        "therapist_id": therapist_id(client, therapist) if therapist else None,
        "date": day,
        "start_time": start,
        **CUSTOMER,
        **customer,
    }
    return client.post("/public/bookings", json=body)


def slots(client, services, day, therapist=None, add_ons=()):
    ids = menu_ids(client)
    params = {
        "date": day,
        "service_ids": ",".join(str(ids[s]) for s in services),
        "add_on_ids": ",".join(str(ids[a]) for a in add_ons),
    }
    if therapist:
        params["therapist_id"] = therapist_id(client, therapist)
    return client.get("/public/availability", params=params)
