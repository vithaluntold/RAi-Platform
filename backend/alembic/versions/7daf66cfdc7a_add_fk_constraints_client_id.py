"""add_fk_constraints_client_id

Revision ID: 7daf66cfdc7a
Revises: a8b522e8b117
Create Date: 2026-02-12 17:29:57.419740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7daf66cfdc7a'
down_revision: Union[str, Sequence[str], None] = 'a8b522e8b117'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key('fk_workflow_assignments_client_id', 'workflow_assignments', 'clients', ['client_id'], ['id'])
    op.create_foreign_key('fk_projects_client_id', 'projects', 'clients', ['client_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_projects_client_id', 'projects', type_='foreignkey')
    op.drop_constraint('fk_workflow_assignments_client_id', 'workflow_assignments', type_='foreignkey')
