"""add user role

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-03

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');
            END IF;
        END
        $$
        """)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role user_role")
    op.execute("UPDATE users SET role = 'USER' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False)
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS user_role")
