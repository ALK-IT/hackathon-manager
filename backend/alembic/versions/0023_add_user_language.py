"""add user language

Revision ID: 0023
Revises: 0022
Create Date: 2026-09-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(length=2), server_default="en", nullable=False),
    )
    op.create_check_constraint(
        "ck_users_language_supported",
        "users",
        "language IN ('pl', 'en')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_language_supported", "users", type_="check")
    op.drop_column("users", "language")
