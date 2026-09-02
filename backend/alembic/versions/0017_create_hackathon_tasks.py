"""create hackathon tasks and team submissions

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column("tasks_released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_hackathons_tasks_release_before_end",
        "hackathons",
        "tasks_released_at IS NULL OR tasks_released_at < end_date",
    )

    op.create_table(
        "hackathon_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_hackathon_tasks_public_id",
        "hackathon_tasks",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_hackathon_tasks_hackathon_id",
        "hackathon_tasks",
        ["hackathon_id"],
    )

    op.create_table(
        "task_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("github_url", sa.String(length=500), nullable=False),
        sa.Column("submitted_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["hackathon_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("task_id", "team_id", name="uq_task_submission_task_team"),
    )
    op.create_index(
        "ix_task_submissions_public_id",
        "task_submissions",
        ["public_id"],
        unique=True,
    )
    op.create_index("ix_task_submissions_task_id", "task_submissions", ["task_id"])
    op.create_index("ix_task_submissions_team_id", "task_submissions", ["team_id"])
    op.create_index(
        "ix_task_submissions_submitted_by_id",
        "task_submissions",
        ["submitted_by_id"],
    )


def downgrade() -> None:
    op.drop_table("task_submissions")
    op.drop_table("hackathon_tasks")
    op.drop_constraint(
        "ck_hackathons_tasks_release_before_end",
        "hackathons",
        type_="check",
    )
    op.drop_column("hackathons", "tasks_released_at")
