"""drop unused evaluation publication timestamp

Revision ID: 94f3c802ad61
Revises: 7e904f26bc31
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "94f3c802ad61"
down_revision: str = "7e904f26bc31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("hackathons", "evaluations_published_at")


def downgrade() -> None:
    # Restores the schema only; previously stored timestamps cannot be recovered.
    op.add_column(
        "hackathons",
        sa.Column("evaluations_published_at", sa.DateTime(timezone=True), nullable=True),
    )
