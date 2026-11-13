def test_version_returns_configured_app_version(make_client):
    client = make_client(version="2026.11.13-test")

    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "2026.11.13-test"}


def test_version_returns_default_dev(client):
    response = client.get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "dev"}
