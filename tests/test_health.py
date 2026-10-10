import pytest

from app.config import Settings


def test_health_reports_dev_without_render_commit(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "dev"}


def test_health_reports_render_git_commit(make_client):
    settings = Settings.from_env(
        {"DATABASE_URL": "sqlite://", "RENDER_GIT_COMMIT": "4f41226abc0123456789"}
    )
    client = make_client(settings)
    assert client.get("/health").json()["version"] == "4f41226abc0123456789"


def test_settings_version_defaults_to_dev():
    assert Settings.from_env({}).version == "dev"
    assert Settings.from_env({"RENDER_GIT_COMMIT": ""}).version == "dev"


@pytest.mark.parametrize("url", ["postgres://u:p@host/db", "postgresql://u:p@host/db"])
def test_postgres_urls_use_psycopg_driver(url):
    settings = Settings.from_env({"DATABASE_URL": url, "SECRET_KEY": "x"})
    assert settings.database_url == "postgresql+psycopg://u:p@host/db"


def test_hosted_database_requires_secret_key():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings.from_env({"DATABASE_URL": "postgresql://u:p@host/db"})


def test_seed_flag_parsing():
    assert Settings.from_env({"SEED_DEMO_DATA": "true"}).seed_demo_data is True
    assert Settings.from_env({"SEED_DEMO_DATA": "TRUE"}).seed_demo_data is True
    assert Settings.from_env({"SEED_DEMO_DATA": "false"}).seed_demo_data is False
    assert Settings.from_env({}).seed_demo_data is False
