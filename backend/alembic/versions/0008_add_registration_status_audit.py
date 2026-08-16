"""add registration status audit fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "registrations",
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "registrations",
        sa.Column("status_changed_by_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_registrations_status_changed_by_id",
        "registrations",
        ["status_changed_by_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_registrations_status_changed_by_id_users",
        "registrations",
        "users",
        ["status_changed_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_registrations_status_changed_by_id_users",
        "registrations",
        type_="foreignkey",
    )
    op.drop_index("ix_registrations_status_changed_by_id", table_name="registrations")
    op.drop_column("registrations", "status_changed_by_id")
    op.drop_column("registrations", "status_changed_at")
