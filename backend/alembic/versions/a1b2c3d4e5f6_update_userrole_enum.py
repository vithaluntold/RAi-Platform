"""update userrole enum: replace worker with manager and enduser

Revision ID: a1b2c3d4e5f6
Revises: 86c3eb25451f
Create Date: 2026-02-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7050dcdeddb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace 'WORKER' with 'MANAGER' and add 'ENDUSER' in the userrole enum."""

    # Step 1: Convert column to VARCHAR so we can freely manipulate values
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text")

    # Step 2: Migrate existing 'WORKER' rows to 'MANAGER'
    op.execute("UPDATE users SET role = 'MANAGER' WHERE role = 'WORKER'")

    # Step 3: Drop old enum and create the new one
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'MANAGER', 'ENDUSER', 'CLIENT')")

    # Step 4: Convert column back to enum
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'ENDUSER'")


def downgrade() -> None:
    """Revert to original enum with 'WORKER' instead of 'MANAGER'/'ENDUSER'."""

    # Convert MANAGER/ENDUSER back to WORKER
    op.execute("UPDATE users SET role = 'WORKER' WHERE role IN ('MANAGER', 'ENDUSER')")

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20)")
    op.execute("DROP TYPE userrole")
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'WORKER', 'CLIENT')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'WORKER'"
    )
