"""merge attendance and hackathon task heads

Revision ID: 4750a7d27b3b
Revises: 0018, 9d8bb15da04b
Create Date: 2026-09-08 13:42:16.795362

"""

from collections.abc import Sequence

revision: str = "4750a7d27b3b"
down_revision: tuple[str, str] = ("0018", "9d8bb15da04b")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
