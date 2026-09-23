"""merge language and evaluation heads

Revision ID: b31f0b7ad812
Revises: 0023, 94f3c802ad61
Create Date: 2026-09-23
"""

from collections.abc import Sequence

revision: str = "b31f0b7ad812"
down_revision: tuple[str, str] = ("0023", "94f3c802ad61")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
