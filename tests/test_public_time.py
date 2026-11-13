from datetime import UTC, datetime


def test_public_time_returns_utc_time(client):
    response = client.get("/public/time")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "utc" in response.json()


def test_public_time_is_utc(client):
    value = client.get("/public/time").json()["utc"]

    assert value.endswith("Z")
    assert (
        datetime.fromisoformat(value[:-1] + "+00:00").utcoffset()
        == UTC.utcoffset(None)
    )


def test_public_time_uses_application_clock(client, frozen_now):
    response = client.get("/public/time")

    assert response.json() == {"utc": "2026-10-10T10:00:00Z"}
