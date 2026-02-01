"""Add matching weights profiles and history tables

Revision ID: 20250201_add_matching_weights_profiles
Revises: 010_add_unified_metrics
Create Date: 2025-02-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '011_add_matching_weights_profiles'
down_revision = '010_add_unified_metrics'
branch_labels = None
depends_on = None


def upgrade():
    """Create matching weights profiles and history tables."""
    # Create matching_weights_profiles table
    op.create_table(
        'matching_weights_profiles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('keyword_weight', sa.Float(), nullable=False, default=0.5),
        sa.Column('tfidf_weight', sa.Float(), nullable=False, default=0.3),
        sa.Column('vector_weight', sa.Float(), nullable=False, default=0.2),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_preset', sa.Boolean(), nullable=False, default=False),
        sa.Column('preset_type', sa.String(50), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for matching_weights_profiles
    op.create_index(
        'ix_matching_weights_profiles_organization_id',
        'matching_weights_profiles',
        ['organization_id'],
        unique=False
    )
    op.create_index(
        'ix_matching_weights_profiles_is_default',
        'matching_weights_profiles',
        ['is_default'],
        unique=False
    )
    op.create_index(
        'ix_matching_weights_profiles_preset_type',
        'matching_weights_profiles',
        ['preset_type'],
        unique=False
    )

    # Create matching_weights_history table
    op.create_table(
        'matching_weights_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('changed_by', sa.String(), nullable=True),
        # Old values
        sa.Column('old_name', sa.String(255), nullable=True),
        sa.Column('old_description', sa.String(1000), nullable=True),
        sa.Column('old_keyword_weight', sa.Float(), nullable=True),
        sa.Column('old_tfidf_weight', sa.Float(), nullable=True),
        sa.Column('old_vector_weight', sa.Float(), nullable=True),
        sa.Column('old_is_default', sa.Boolean(), nullable=True),
        # New values
        sa.Column('new_name', sa.String(255), nullable=True),
        sa.Column('new_description', sa.String(1000), nullable=True),
        sa.Column('new_keyword_weight', sa.Float(), nullable=True),
        sa.Column('new_tfidf_weight', sa.Float(), nullable=True),
        sa.Column('new_vector_weight', sa.Float(), nullable=True),
        sa.Column('new_is_default', sa.Boolean(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for matching_weights_history
    op.create_index(
        'ix_matching_weights_history_profile_id',
        'matching_weights_history',
        ['profile_id'],
        unique=False
    )
    op.create_index(
        'ix_matching_weights_history_organization_id',
        'matching_weights_history',
        ['organization_id'],
        unique=False
    )
    op.create_index(
        'ix_matching_weights_history_change_type',
        'matching_weights_history',
        ['change_type'],
        unique=False
    )


def downgrade():
    """Remove matching weights profiles and history tables."""
    # Drop matching_weights_history table
    op.drop_index('ix_matching_weights_history_change_type', table_name='matching_weights_history')
    op.drop_index('ix_matching_weights_history_organization_id', table_name='matching_weights_history')
    op.drop_index('ix_matching_weights_history_profile_id', table_name='matching_weights_history')
    op.drop_table('matching_weights_history')

    # Drop matching_weights_profiles table
    op.drop_index('ix_matching_weights_profiles_preset_type', table_name='matching_weights_profiles')
    op.drop_index('ix_matching_weights_profiles_is_default', table_name='matching_weights_profiles')
    op.drop_index('ix_matching_weights_profiles_organization_id', table_name='matching_weights_profiles')
    op.drop_table('matching_weights_profiles')
