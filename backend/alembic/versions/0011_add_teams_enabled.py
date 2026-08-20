"""add teams enabled flag

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column(
            "teams_enabled",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("hackathons", "teams_enabled")
