"""Add organizations table

Revision ID: 20260203_add_organizations
Revises: 20260201_add_search_performance_indexes
Create Date: 2026-02-03

This migration creates the organizations table for multi-tenant support,
enabling organizations to have customized hiring workflows, branding,
email templates, and skill taxonomies.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260203_add_organizations'
down_revision: Union[str, None] = '20260201_add_search_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create organizations table."""

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column(
            'id',
            sa.String(100),
            primary_key=True,
            nullable=False,
        ),
        # Organization details
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('domain', sa.String(255), nullable=True, unique=True),
        # Branding
        sa.Column('logo_url', sa.String(500), nullable=True),
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        # Timestamps (inherited from TimestampMixin)
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        comment='Organizations for multi-tenant customization support',
    )

    # Create indexes for organizations
    op.create_index(
        'ix_organizations_name',
        'organizations',
        ['name'],
    )
    op.create_index(
        'ix_organizations_slug',
        'organizations',
        ['slug'],
    )
    op.create_index(
        'ix_organizations_is_active',
        'organizations',
        ['is_active'],
    )


def downgrade() -> None:
    """Remove organizations table."""

    # Drop indexes
    op.drop_index(
        'ix_organizations_is_active',
        table_name='organizations',
    )
    op.drop_index(
        'ix_organizations_slug',
        table_name='organizations',
    )
    op.drop_index(
        'ix_organizations_name',
        table_name='organizations',
    )

    # Drop organizations table
    op.drop_table('organizations')
