"""add email verification and auth version

Revision ID: 0019
Revises: 0016
Create Date: 2026-09-02

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column("auth_version", sa.Integer(), server_default="0", nullable=False),
    )
    op.execute("UPDATE users SET email_verified_at = CURRENT_TIMESTAMP")


def downgrade() -> None:
    op.drop_column("users", "auth_version")
    op.drop_column("users", "email_verified_at")
