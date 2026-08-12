"""add registration opening date

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-11

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "hackathons",
        sa.Column(
            "registration_opens_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.execute(
        sa.text(
            "UPDATE hackathons "
            "SET registration_opens_at = "
            "LEAST(created_at, registration_deadline - INTERVAL '1 second')"
        )
    )
    op.alter_column(
        "hackathons",
        "registration_opens_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_hackathons_registration_window",
        "hackathons",
        "registration_opens_at < registration_deadline",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_hackathons_registration_window",
        "hackathons",
        type_="check",
    )
    op.drop_column("hackathons", "registration_opens_at")
