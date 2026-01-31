"""Add workflow stage config table

Revision ID: 016_add_workflow_stage_config
Revises: 015_add_ats_results
Create Date: 2026-01-31

This migration creates the workflow_stage_configs table for storing
per-organization customizable hiring workflow stages, and adds a foreign
key column to hiring_stages to support custom stages.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '016_add_workflow_stage_config'
down_revision: Union[str, None] = '015_add_ats_results'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workflow_stage_configs table and update hiring_stages table."""

    # Create workflow_stage_configs table
    op.create_table(
        'workflow_stage_configs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to organizations
        sa.Column(
            'organization_id',
            sa.String(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Stage configuration
        sa.Column('stage_name', sa.String(100), nullable=False, index=True),
        sa.Column('stage_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # UI customization
        sa.Column('color', sa.String(7), nullable=True),  # Hex color code
        sa.Column('description', sa.String(500), nullable=True),
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
        comment='Per-organization customizable hiring workflow stages',
    )

    # Create indexes for workflow_stage_configs
    op.create_index(
        'ix_workflow_stage_configs_organization_id',
        'workflow_stage_configs',
        ['organization_id'],
    )
    op.create_index(
        'ix_workflow_stage_configs_stage_name',
        'workflow_stage_configs',
        ['stage_name'],
    )

    # Add workflow_stage_config_id column to hiring_stages table
    op.add_column(
        'hiring_stages',
        sa.Column(
            'workflow_stage_config_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('workflow_stage_configs.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )

    # Create index for the new foreign key
    op.create_index(
        'ix_hiring_stages_workflow_stage_config_id',
        'hiring_stages',
        ['workflow_stage_config_id'],
    )

    # Update stage_name column to be String(100) to support custom stage names
    op.alter_column(
        'hiring_stages',
        'stage_name',
        existing_type=sa.String(50),
        type_=sa.String(100),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Remove workflow_stage_configs table and revert hiring_stages changes."""

    # Drop indexes
    op.drop_index(
        'ix_hiring_stages_workflow_stage_config_id',
        table_name='hiring_stages',
    )
    op.drop_index(
        'ix_workflow_stage_configs_stage_name',
        table_name='workflow_stage_configs',
    )
    op.drop_index(
        'ix_workflow_stage_configs_organization_id',
        table_name='workflow_stage_configs',
    )

    # Remove workflow_stage_config_id column from hiring_stages
    op.drop_column('hiring_stages', 'workflow_stage_config_id')

    # Revert stage_name column to String(50)
    op.alter_column(
        'hiring_stages',
        'stage_name',
        existing_type=sa.String(100),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # Drop workflow_stage_configs table
    op.drop_table('workflow_stage_configs')
