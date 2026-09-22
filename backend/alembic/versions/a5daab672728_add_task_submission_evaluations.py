"""add task submission evaluations

Revision ID: a5daab672728
Revises: 4750a7d27b3b
Create Date: 2026-09-14 15:03:52.936117

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5daab672728"
down_revision: str | None = "4750a7d27b3b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column("evaluations_published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "task_submissions",
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=True),
    )
    op.add_column(
        "task_submissions",
        sa.Column("feedback", sa.Text(), nullable=True),
    )
    op.add_column(
        "task_submissions",
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "task_submissions",
        sa.Column("evaluated_by_id", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_task_submissions_score_range",
        "task_submissions",
        "score >= 0 AND score <= 10",
    )
    op.create_index(
        op.f("ix_task_submissions_evaluated_by_id"),
        "task_submissions",
        ["evaluated_by_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_task_submissions_evaluated_by_id_users",
        "task_submissions",
        "users",
        ["evaluated_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_task_submissions_evaluated_by_id_users",
        "task_submissions",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_task_submissions_evaluated_by_id"),
        table_name="task_submissions",
    )
    op.drop_constraint(
        "ck_task_submissions_score_range",
        "task_submissions",
        type_="check",
    )
    op.drop_column("task_submissions", "evaluated_by_id")
    op.drop_column("task_submissions", "evaluated_at")
    op.drop_column("task_submissions", "feedback")
    op.drop_column("task_submissions", "score")
    op.drop_column("hackathons", "evaluations_published_at")
