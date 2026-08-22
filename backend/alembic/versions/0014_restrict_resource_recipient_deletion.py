"""restrict deletion of resource assignment recipients

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-21

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "resource_assignments_registration_id_fkey",
        "resource_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "resource_assignments_registration_id_fkey",
        "resource_assignments",
        "registrations",
        ["registration_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "resource_assignments_registration_id_fkey",
        "resource_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "resource_assignments_registration_id_fkey",
        "resource_assignments",
        "registrations",
        ["registration_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_resource_assignments_team_id_teams",
        "resource_assignments",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="CASCADE",
    )
