"""Alembic environment.

The database URL comes from DATABASE_URL (same normalisation as the app). When the app
runs migrations at startup it passes its own connection in `config.attributes`.
"""

import os
from logging.config import fileConfig

from alembic import context

import app.models  # noqa: F401  (registers every table on Base.metadata)
from app.config import Settings, _normalize_db_url
from app.db import Base, UTCDateTime, make_engine

config = context.config
if config.config_file_name and not config.attributes.get("connection"):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    """Migrations must not import app code: render our UTC column type as plain SQL."""
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def _configure(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=connection.dialect.name == "sqlite",  # SQLite can't ALTER much
        compare_type=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        _configure(connection)
        return
    url = _normalize_db_url(os.environ.get("DATABASE_URL") or Settings.database_url)
    engine = make_engine(url)
    try:
        with engine.begin() as connection:
            _configure(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline (SQL script) mode isn't used here; run against a database.")
run_migrations_online()
