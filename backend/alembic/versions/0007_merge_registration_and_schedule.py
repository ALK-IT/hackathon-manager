"""merge registration and scheduled registration branches

Revision ID: 0007
Revises: ba71ee509cd7, 0006
Create Date: 2026-08-12

"""

from collections.abc import Sequence

revision: str = "0007"
down_revision: tuple[str, str] = ("ba71ee509cd7", "0006")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
