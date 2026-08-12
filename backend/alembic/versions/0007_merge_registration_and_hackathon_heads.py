"""merge registration and hackathon migration heads

Revision ID: 0007
Revises: 0006, 3cae343ea484
Create Date: 2026-08-12

"""

from collections.abc import Sequence

revision: str = "0007"
down_revision: tuple[str, str] = ("0006", "3cae343ea484")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
