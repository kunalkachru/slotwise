"""Alembic: the migrations must produce exactly the schema the models describe."""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.db import Base, make_engine
from app.migrate import BASELINE, alembic_config, migrate


def schema_drift(engine) -> list:
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        return compare_metadata(context, Base.metadata)


def current_revision(engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def head() -> str:
    return ScriptDirectory.from_config(alembic_config()).get_current_head()


def test_there_is_exactly_one_migration_head():
    assert len(ScriptDirectory.from_config(alembic_config()).get_heads()) == 1


def test_fresh_database_matches_the_models(tmp_path):
    """Fails if someone changes app/models.py without adding a migration."""
    engine = make_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    migrate(engine)
    assert current_revision(engine) == head()
    assert schema_drift(engine) == []


def test_database_made_by_create_all_is_stamped_and_keeps_its_data(tmp_path):
    """The live Neon database was created with create_all before Alembic existed."""
    engine = make_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    # Same schema as the slice-1 create_all: the baseline, without migration history.
    with engine.begin() as connection:
        command.upgrade(alembic_config(connection), BASELINE)
        connection.execute(text("DROP TABLE alembic_version"))
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO studio (name, address, phone, email, opening_hours_text, "
            "min_notice_hours, free_cancellation_hours, booking_window_days, "
            "waitlist_offer_minutes, receipt_prefix, created_at) VALUES "
            "('Isar Wellness', 'A', '+49 1', 'a@example.com', '', 2, 24, 60, 30, 'IW', "
            "'2026-10-01 10:00:00')"))
    assert "alembic_version" not in inspect(engine).get_table_names()

    migrate(engine)

    assert current_revision(engine) == head()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT name FROM studio")).scalar() == "Isar Wellness"
    assert schema_drift(engine) == []


def test_migrating_twice_changes_nothing(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'twice.db'}")
    migrate(engine)
    migrate(engine)
    assert current_revision(engine) == head()


def test_the_baseline_is_the_first_revision():
    script = ScriptDirectory.from_config(alembic_config())
    assert script.get_revision(BASELINE).down_revision is None


def test_every_migration_downgrades_and_upgrades_again(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'roundtrip.db'}")
    migrate(engine)
    with engine.begin() as connection:
        command.downgrade(alembic_config(connection), BASELINE)
    assert current_revision(engine) == BASELINE
    migrate(engine)
    assert current_revision(engine) == head()
    assert schema_drift(engine) == []


def test_existing_bookings_become_one_segment_bookings(tmp_path):
    """0006: the live bookings keep exactly the therapist and blocked time they had.
    0007: their items belong to that one segment."""
    engine = make_engine(f"sqlite:///{tmp_path / 'before_segments.db'}")
    with engine.begin() as connection:
        command.upgrade(alembic_config(connection), "0005")
        connection.execute(text(
            "INSERT INTO therapists (id, display_name, active, created_at) "
            "VALUES (7, 'Lena', 1, '2026-10-01 10:00:00')"))
        connection.execute(text(
            "INSERT INTO customers (id, first_name, last_name, email, phone, no_show_count, "
            "created_at) VALUES (3, 'Anna', 'M', 'a@example.com', '+49 1', 0, "
            "'2026-10-01 10:00:00')"))
        connection.execute(text(
            "INSERT INTO bookings (id, customer_id, therapist_id, start_at, end_at, blocked_until,"
            " status, total_price, source, manage_token, late_cancellation, created_at) VALUES "
            "(42, 3, 7, '2026-10-13 15:00:00', '2026-10-13 16:15:00', '2026-10-13 16:25:00', "
            "'booked', 82, 'online', 't', 0, '2026-10-01 10:00:00')"))
        connection.execute(text(
            "INSERT INTO booking_items (id, booking_id, item_type, name_snapshot, "
            "minutes_snapshot, unit_price_snapshot, quantity, created_at) VALUES "
            "(5, 42, 'service', 'Deep tissue massage', 60, 70, 1, '2026-10-01 10:00:00')"))

    migrate(engine)

    with engine.connect() as connection:
        rows = connection.execute(text(
            "SELECT booking_id, position, therapist_id, start_at, end_at, blocked_until "
            "FROM booking_segments")).all()
    assert [tuple(r) for r in rows] == [
        (42, 0, 7, "2026-10-13 15:00:00", "2026-10-13 16:15:00", "2026-10-13 16:25:00")]
    with engine.connect() as connection:
        segment = connection.execute(text("SELECT id FROM booking_segments")).scalar()
        assert connection.execute(text(
            "SELECT segment_id FROM booking_items WHERE id = 5")).scalar() == segment
