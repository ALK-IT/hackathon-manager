"""allow resource assignments to registrations or teams

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "resource_assignments",
        "registration_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "resource_assignments",
        sa.Column("team_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_resource_assignments_team_id",
        "resource_assignments",
        ["team_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_resource_assignments_exactly_one_recipient",
        "resource_assignments",
        "(registration_id IS NOT NULL AND team_id IS NULL) OR "
        "(registration_id IS NULL AND team_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_resource_assignments_exactly_one_recipient",
        "resource_assignments",
        type_="check",
    )
    op.drop_constraint(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        type_="foreignkey",
    )
    op.drop_index("ix_resource_assignments_team_id", table_name="resource_assignments")
    op.drop_column("resource_assignments", "team_id")
    op.alter_column(
        "resource_assignments",
        "registration_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
