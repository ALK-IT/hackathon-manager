"""expand hackathons

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The old schema contained only the three demo rows inserted in migration 0001.
    # They do not have an owner, so they cannot be carried into the new domain model.
    op.execute(sa.text("DELETE FROM hackathons"))

    op.add_column(
        "hackathons",
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.add_column(
        "hackathons",
        sa.Column("organizer_id", sa.Integer(), nullable=False),
    )
    op.add_column("hackathons", sa.Column("description", sa.Text(), nullable=False))
    op.add_column(
        "hackathons",
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "hackathons",
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "hackathons",
        sa.Column(
            "registration_open",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column("hackathons", sa.Column("capacity", sa.Integer(), nullable=True))
    op.add_column(
        "hackathons",
        sa.Column("max_team_size", sa.Integer(), nullable=False),
    )
    op.add_column(
        "hackathons",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "hackathons",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "hackathons",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "hackathons",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_hackathons_public_id",
        "hackathons",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_hackathons_organizer_id",
        "hackathons",
        ["organizer_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_hackathons_organizer_id_users",
        "hackathons",
        "users",
        ["organizer_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_hackathons_date_range",
        "hackathons",
        "end_date > start_date",
    )
    op.create_check_constraint(
        "ck_hackathons_capacity_positive",
        "hackathons",
        "capacity IS NULL OR capacity >= 1",
    )
    op.create_check_constraint(
        "ck_hackathons_max_team_size_positive",
        "hackathons",
        "max_team_size >= 1",
    )
    op.create_check_constraint(
        "ck_hackathons_team_size_within_capacity",
        "hackathons",
        "capacity IS NULL OR max_team_size <= capacity",
    )

    op.create_table(
        "hackathon_co_organizers",
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hackathon_id"],
            ["hackathons.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("hackathon_id", "user_id"),
    )


def downgrade() -> None:
    op.drop_table("hackathon_co_organizers")
    op.drop_constraint(
        "ck_hackathons_team_size_within_capacity",
        "hackathons",
        type_="check",
    )
    op.drop_constraint(
        "ck_hackathons_max_team_size_positive",
        "hackathons",
        type_="check",
    )
    op.drop_constraint(
        "ck_hackathons_capacity_positive",
        "hackathons",
        type_="check",
    )
    op.drop_constraint("ck_hackathons_date_range", "hackathons", type_="check")
    op.drop_constraint(
        "fk_hackathons_organizer_id_users",
        "hackathons",
        type_="foreignkey",
    )
    op.drop_index("ix_hackathons_organizer_id", table_name="hackathons")
    op.drop_index("ix_hackathons_public_id", table_name="hackathons")

    op.drop_column("hackathons", "updated_at")
    op.drop_column("hackathons", "created_at")
    op.drop_column("hackathons", "deleted_at")
    op.drop_column("hackathons", "is_deleted")
    op.drop_column("hackathons", "max_team_size")
    op.drop_column("hackathons", "capacity")
    op.drop_column("hackathons", "registration_open")
    op.drop_column("hackathons", "end_date")
    op.drop_column("hackathons", "start_date")
    op.drop_column("hackathons", "description")
    op.drop_column("hackathons", "organizer_id")
    op.drop_column("hackathons", "public_id")
