"""Settings read from environment variables. Nothing else in the app reads os.environ."""

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass

log = logging.getLogger(__name__)

DEV_SECRET_KEY = "dev-only-secret-key-change-me"


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./slotwise.db"
    secret_key: str = DEV_SECRET_KEY
    jobs_secret: str | None = None
    email_api_key: str | None = None
    owner_email: str | None = None
    owner_password: str | None = None
    seed_demo_data: bool = False
    version: str = "dev"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @classmethod
    def from_env(cls, env: Mapping[str, str] = os.environ) -> "Settings":
        settings = cls(
            database_url=_normalize_db_url(env.get("DATABASE_URL") or cls.database_url),
            secret_key=env.get("SECRET_KEY") or DEV_SECRET_KEY,
            jobs_secret=env.get("JOBS_SECRET") or None,
            email_api_key=env.get("EMAIL_API_KEY") or None,
            owner_email=env.get("OWNER_EMAIL") or None,
            owner_password=env.get("OWNER_PASSWORD") or None,
            seed_demo_data=_flag(env.get("SEED_DEMO_DATA")),
            version=env.get("RENDER_GIT_COMMIT") or "dev",
        )
        if settings.secret_key == DEV_SECRET_KEY:
            if not settings.is_sqlite:
                raise RuntimeError("SECRET_KEY must be set when using a hosted database.")
            log.warning("SECRET_KEY is not set; using an insecure development key.")
        return settings


def _normalize_db_url(url: str) -> str:
    """Neon and Render hand out postgres:// URLs; SQLAlchemy needs the psycopg 3 driver name."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url
