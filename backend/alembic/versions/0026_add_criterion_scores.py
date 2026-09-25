"""add criterion scores to task submissions

Revision ID: 0026
Revises: 0025
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "task_submissions",
        sa.Column(
            "criterion_scores",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.drop_constraint("ck_task_submissions_score_range", "task_submissions", type_="check")
    op.alter_column(
        "task_submissions",
        "score",
        existing_type=sa.Numeric(precision=4, scale=2),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_task_submissions_score_range",
        "task_submissions",
        "score >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_task_submissions_score_range", "task_submissions", type_="check")
    op.execute("UPDATE task_submissions SET score = 10 WHERE score > 10")
    op.alter_column(
        "task_submissions",
        "score",
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=sa.Numeric(precision=4, scale=2),
        existing_nullable=True,
    )
    op.create_check_constraint(
        "ck_task_submissions_score_range",
        "task_submissions",
        "score >= 0 AND score <= 10",
    )
    op.drop_column("task_submissions", "criterion_scores")
