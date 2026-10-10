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
)

# Saturday 10 Oct 2026, midday in Berlin
FROZEN_NOW = datetime(2026, 10, 10, 12, 0, tzinfo=clock.BERLIN)


@pytest.fixture
def frozen_now(monkeypatch):
    monkeypatch.setattr(clock, "now", lambda: FROZEN_NOW)
    return FROZEN_NOW


@pytest.fixture
def make_client():
    """Factory: make_client(seed_demo_data=False, ...) -> started TestClient."""
    clients = []

    def _make(settings: Settings | None = None, **overrides) -> TestClient:
        client = TestClient(create_app(replace(settings or TEST_SETTINGS, **overrides)))
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
