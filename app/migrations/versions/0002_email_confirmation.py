"""Email confirmation: pending/expired booking statuses, waitlist double opt-in.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-11

Written by hand: autogenerate doesn't detect changes to CHECK constraints.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD_BOOKING = "status IN ('booked', 'confirmed', 'done', 'no_show', 'cancelled')"
NEW_BOOKING = ("status IN ('pending', 'booked', 'confirmed', 'done', 'no_show', 'cancelled', "
               "'expired')")
OLD_WAITLIST = "status IN ('waiting', 'offered', 'booked', 'expired', 'removed')"
NEW_WAITLIST = "status IN ('pending', 'waiting', 'offered', 'booked', 'expired', 'removed')"


def upgrade() -> None:
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_constraint("ck_bookings_status", type_="check")
        batch_op.create_check_constraint("ck_bookings_status", NEW_BOOKING)
    with op.batch_alter_table("waitlist_entries") as batch_op:
        batch_op.drop_constraint("ck_waitlist_entries_status", type_="check")
        batch_op.create_check_constraint("ck_waitlist_entries_status", NEW_WAITLIST)
        batch_op.add_column(sa.Column("confirm_token", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_waitlist_entries_confirm_token", ["confirm_token"])


def downgrade() -> None:
    # Rows in the new states must go first, or the old constraints would reject them.
    op.execute("UPDATE bookings SET status = 'cancelled' WHERE status IN ('pending', 'expired')")
    op.execute("UPDATE waitlist_entries SET status = 'removed' WHERE status = 'pending'")
    with op.batch_alter_table("waitlist_entries") as batch_op:
        batch_op.drop_constraint("uq_waitlist_entries_confirm_token", type_="unique")
        batch_op.drop_column("confirm_token")
        batch_op.drop_constraint("ck_waitlist_entries_status", type_="check")
        batch_op.create_check_constraint("ck_waitlist_entries_status", OLD_WAITLIST)
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_constraint("ck_bookings_status", type_="check")
        batch_op.create_check_constraint("ck_bookings_status", OLD_BOOKING)
