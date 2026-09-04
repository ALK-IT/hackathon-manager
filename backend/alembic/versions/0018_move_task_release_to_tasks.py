"""move task release time to individual tasks

Revision ID: 0018
Revises: 0017
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathon_tasks",
        sa.Column("visible_from", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("""
        UPDATE hackathon_tasks AS task
        SET visible_from = COALESCE(hackathon.tasks_released_at, hackathon.start_date)
        FROM hackathons AS hackathon
        WHERE task.hackathon_id = hackathon.id
        """)
    op.alter_column("hackathon_tasks", "visible_from", nullable=False)
    op.create_index(
        "ix_hackathon_tasks_hackathon_visible_from",
        "hackathon_tasks",
        ["hackathon_id", "visible_from"],
    )

    op.drop_constraint(
        "ck_hackathons_tasks_release_before_end",
        "hackathons",
        type_="check",
    )
    op.drop_column("hackathons", "tasks_released_at")


def downgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column("tasks_released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute("""
        UPDATE hackathons AS hackathon
        SET tasks_released_at = task.first_visible_from
        FROM (
            SELECT hackathon_id, MIN(visible_from) AS first_visible_from
            FROM hackathon_tasks
            GROUP BY hackathon_id
        ) AS task
        WHERE hackathon.id = task.hackathon_id
        """)
    op.create_check_constraint(
        "ck_hackathons_tasks_release_before_end",
        "hackathons",
        "tasks_released_at IS NULL OR tasks_released_at < end_date",
    )

    op.drop_index(
        "ix_hackathon_tasks_hackathon_visible_from",
        table_name="hackathon_tasks",
    )
    op.drop_column("hackathon_tasks", "visible_from")
