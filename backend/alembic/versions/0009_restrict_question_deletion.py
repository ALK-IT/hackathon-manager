"""restrict deletion of answered registration questions

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("answers_question_id_fkey", "answers", type_="foreignkey")
    op.create_foreign_key(
        "answers_question_id_fkey",
        "answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("answers_question_id_fkey", "answers", type_="foreignkey")
    op.create_foreign_key(
        "answers_question_id_fkey",
        "answers",
        "questions",
        ["question_id"],
        ["id"],
        ondelete="CASCADE",
    )
