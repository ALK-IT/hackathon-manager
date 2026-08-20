"""create resources and resource items

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _public_id():
    return sa.Column("public_id", postgresql.UUID(as_uuid=True), nullable=False)


def upgrade() -> None:
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        _public_id(),
        sa.Column("hackathon_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("distribution_mode", sa.String(length=50), nullable=False),
        sa.Column("target", sa.String(length=50), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["hackathon_id"], ["hackathons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_resources_public_id", "resources", ["public_id"], unique=True)
    op.create_index("ix_resources_hackathon_id", "resources", ["hackathon_id"])

    op.create_table(
        "resource_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        _public_id(),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        sa.Column("is_assigned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_resource_items_public_id", "resource_items", ["public_id"], unique=True)
    op.create_index("ix_resource_items_resource_id", "resource_items", ["resource_id"])

    op.create_table(
        "resource_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        _public_id(),
        sa.Column("resource_item_id", sa.Integer(), nullable=False),
        sa.Column("registration_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resource_item_id"], ["resource_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["registration_id"], ["registrations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_resource_assignments_public_id", "resource_assignments", ["public_id"], unique=True)
    op.create_index("ix_resource_assignments_resource_item_id", "resource_assignments", ["resource_item_id"])
    op.create_index("ix_resource_assignments_registration_id", "resource_assignments", ["registration_id"])

    op.create_table(
        "resource_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        _public_id(),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index("ix_resource_audit_logs_public_id", "resource_audit_logs", ["public_id"], unique=True)
    op.create_index("ix_resource_audit_logs_resource_id", "resource_audit_logs", ["resource_id"])


def downgrade() -> None:
    op.drop_table("resource_audit_logs")
    op.drop_table("resource_assignments")
    op.drop_table("resource_items")
    op.drop_table("resources")
