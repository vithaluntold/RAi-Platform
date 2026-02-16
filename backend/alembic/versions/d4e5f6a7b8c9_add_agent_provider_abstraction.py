"""add_agent_provider_abstraction

Revision ID: d4e5f6a7b8c9
Revises: 165cafc59c14
Create Date: 2026-02-16 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '165cafc59c14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add provider abstraction columns to agents table."""

    # 1. Create the ProviderType enum in PostgreSQL
    provider_type_enum = sa.Enum(
        'EXTERNAL', 'ON_PREM', 'HYBRID',
        name='providertype',
    )
    provider_type_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add new columns
    op.add_column(
        'agents',
        sa.Column(
            'provider_type',
            sa.Enum('EXTERNAL', 'ON_PREM', 'HYBRID', name='providertype'),
            nullable=False,
            server_default='EXTERNAL',
        ),
    )
    op.add_column(
        'agents',
        sa.Column('external_url', sa.String(500), nullable=True),
    )
    op.add_column(
        'agents',
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
    )

    # 3. Widen description from 1000 → 2000 chars
    op.alter_column(
        'agents',
        'description',
        existing_type=sa.String(1000),
        type_=sa.String(2000),
        existing_nullable=True,
    )

    # 4. Add COMPLIANCE_ANALYSIS to AgentType enum
    op.execute("ALTER TYPE agenttype ADD VALUE IF NOT EXISTS 'COMPLIANCE_ANALYSIS'")

    # 5. Add index on provider_type
    op.create_index('idx_agents_provider', 'agents', ['provider_type'])


def downgrade() -> None:
    """Remove provider abstraction columns."""
    op.drop_index('idx_agents_provider', table_name='agents')

    op.alter_column(
        'agents',
        'description',
        existing_type=sa.String(2000),
        type_=sa.String(1000),
        existing_nullable=True,
    )

    op.drop_column('agents', 'version')
    op.drop_column('agents', 'external_url')
    op.drop_column('agents', 'provider_type')

    # Drop the enum type
    sa.Enum(name='providertype').drop(op.get_bind(), checkfirst=True)
