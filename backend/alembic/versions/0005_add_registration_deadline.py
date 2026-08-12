"""add registration deadline

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column(
            "registration_deadline",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        sa.text("UPDATE hackathons " "SET registration_deadline = start_date - INTERVAL '48 hours'")
    )
    op.alter_column(
        "hackathons",
        "registration_deadline",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_hackathons_registration_deadline_before_start",
        "hackathons",
        "registration_deadline < start_date",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_hackathons_registration_deadline_before_start",
        "hackathons",
        type_="check",
    )
    op.drop_column("hackathons", "registration_deadline")
