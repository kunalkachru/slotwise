from app.config import Settings


def test_public_version_defaults_to_dev(client):
    response = client.get("/public/version")

    assert response.status_code == 200
    assert response.json() == {"version": "dev"}


def test_public_version_returns_render_commit(make_client):
    settings = Settings.from_env(
        {"DATABASE_URL": "sqlite://", "RENDER_GIT_COMMIT": "4f41226abc0123456789"}
    )
    client = make_client(settings)

    response = client.get("/public/version")

    assert response.status_code == 200
    assert response.json() == {"version": "4f41226abc0123456789"}


def test_public_version_is_public_and_has_stable_shape(client):
    response = client.get("/public/version")

    assert response.status_code == 200
    assert set(response.json()) == {"version"}
