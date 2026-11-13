"""track late-confirmation slot releases

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-13

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("slot_release_pending", sa.Boolean(),
                                      server_default="0", nullable=False))


def downgrade() -> None:
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_column("slot_release_pending")
