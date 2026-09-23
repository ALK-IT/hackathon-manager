"""merge notifications and evaluation heads

Revision ID: 7e904f26bc31
Revises: 0022, a5daab672728
Create Date: 2026-09-18
"""

from collections.abc import Sequence

revision: str = "7e904f26bc31"
down_revision: tuple[str, str] = ("0022", "a5daab672728")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
