from app.config import Settings


def test_version_returns_configured_app_version(make_client):
    settings = Settings(database_url="sqlite://", version="4f41226abc012345")

    response = make_client(settings).get("/version")

    assert response.status_code == 200
    assert response.json() == {"version": "4f41226abc012345"}
