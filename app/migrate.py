"""Run database migrations at startup (replaces Base.metadata.create_all).

Databases created before Alembic was adopted (the live Neon database was made by
create_all in slice 1) have every table but no `alembic_version`. Their schema equals
the baseline revision, so they are *stamped* as being at the baseline instead of
re-running it; after that, only newer migrations are applied.
"""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

MIGRATIONS = Path(__file__).parent / "migrations"
BASELINE = "0001"


def alembic_config(connection=None) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def migrate(engine: Engine) -> None:
    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        config = alembic_config(connection)
        if "studio" in tables and "alembic_version" not in tables:
            log.info("Existing database without migration history: stamping baseline %s.",
                     BASELINE)
            command.stamp(config, BASELINE)
        command.upgrade(config, "head")
