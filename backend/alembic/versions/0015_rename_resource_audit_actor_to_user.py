"""rename resource audit actor to user

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-21

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "resource_audit_logs_actor_id_fkey",
        "resource_audit_logs",
        type_="foreignkey",
    )
    op.alter_column(
        "resource_audit_logs",
        "actor_id",
        new_column_name="user_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "resource_audit_logs_user_id_fkey",
        "resource_audit_logs",
        "users",
        ["user_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "resource_audit_logs_user_id_fkey",
        "resource_audit_logs",
        type_="foreignkey",
    )
    op.alter_column(
        "resource_audit_logs",
        "user_id",
        new_column_name="actor_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.create_foreign_key(
        "resource_audit_logs_actor_id_fkey",
        "resource_audit_logs",
        "users",
        ["actor_id"],
        ["id"],
        ondelete="RESTRICT",
    )
