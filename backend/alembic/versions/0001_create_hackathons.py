"""create hackathons table

Revision ID: 0001
Revises:
Create Date: 2026-07-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hackathons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    hackathons = sa.table(
        "hackathons",
        sa.column("name", sa.String),
    )
    op.bulk_insert(
        hackathons,
        [
            {"name": "HackYeah 2026"},
            {"name": "Poznan Hackathon"},
            {"name": "ALK Student Hack"},
        ],
    )


def downgrade() -> None:
    op.drop_table("hackathons")