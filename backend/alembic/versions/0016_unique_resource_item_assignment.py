"""ensure each resource item has at most one assignment

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-31

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_resource_assignment_item",
        "resource_assignments",
        ["resource_item_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_resource_assignment_item",
        "resource_assignments",
        type_="unique",
    )
