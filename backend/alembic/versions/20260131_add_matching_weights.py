"""Add matching weight profile models

Revision ID: 014_add_matching_weights
Revises: 013_add_skill_gap_models
Create Date: 2025-01-31

This migration creates tables for:
- matching_weight_profiles: Store custom weight configurations for unified matching
- matching_weight_versions: Track version history of weight profiles for audit

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '014_add_matching_weights'
down_revision: Union[str, None] = '013_add_skill_gap_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create matching weight profile tables."""

    # Create matching_weight_profiles table
    op.create_table(
        'matching_weight_profiles',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Profile metadata
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        # Organization/Scope
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'),
            nullable=True,
        ),
        # Profile flags
        sa.Column('is_preset', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        # Matching weights (should sum to 1.0)
        sa.Column('keyword_weight', sa.Float(), nullable=False, default=0.5),
        sa.Column('tfidf_weight', sa.Float(), nullable=False, default=0.3),
        sa.Column('vector_weight', sa.Float(), nullable=False, default=0.2),
        # Tracking
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        # Audit metadata
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        # Timestamps
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
        comment='Store custom weight configurations for unified matching algorithm',
    )

    # Create indexes for matching_weight_profiles
    op.create_index(
        'ix_matching_weight_profiles_name',
        'matching_weight_profiles',
        ['name'],
    )
    op.create_index(
        'ix_matching_weight_profiles_organization_id',
        'matching_weight_profiles',
        ['organization_id'],
    )
    op.create_index(
        'ix_matching_weight_profiles_vacancy_id',
        'matching_weight_profiles',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_matching_weight_profiles_is_preset',
        'matching_weight_profiles',
        ['is_preset'],
    )
    op.create_index(
        'ix_matching_weight_profiles_is_active',
        'matching_weight_profiles',
        ['is_active'],
    )

    # Create unique constraints
    op.create_unique_constraint(
        'uq_matching_weight_profile_org_name',
        'matching_weight_profiles',
        ['organization_id', 'name'],
    )
    op.create_unique_constraint(
        'uq_matching_weight_profile_vacancy',
        'matching_weight_profiles',
        ['vacancy_id'],
    )

    # Create matching_weight_versions table
    op.create_table(
        'matching_weight_versions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'profile_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('matching_weight_profiles.id', ondelete='CASCADE'),
            nullable=False,
        ),
        # Snapshot of weights at this version
        sa.Column('keyword_weight', sa.Float(), nullable=False),
        sa.Column('tfidf_weight', sa.Float(), nullable=False),
        sa.Column('vector_weight', sa.Float(), nullable=False),
        # Change tracking
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        # Timestamps
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
        comment='Version history for matching weight profiles',
    )

    # Create indexes for matching_weight_versions
    op.create_index(
        'ix_matching_weight_versions_profile_id',
        'matching_weight_versions',
        ['profile_id'],
    )

    # Insert preset profiles
    op.execute("""
        INSERT INTO matching_weight_profiles (name, description, keyword_weight, tfidf_weight, vector_weight, is_preset, is_active, version)
        VALUES
            ('Technical', 'Keyword-heavy matching for technical roles requiring exact skill matching', 0.60, 0.25, 0.15, true, true, 'v1.0'),
            ('Creative', 'Vector-heavy matching for creative roles requiring conceptual understanding', 0.20, 0.25, 0.55, true, true, 'v1.0'),
            ('Executive', 'Balanced matching for executive roles requiring comprehensive evaluation', 0.33, 0.34, 0.33, true, true, 'v1.0'),
            ('Balanced', 'Even distribution across all matching methods', 0.34, 0.33, 0.33, true, true, 'v1.0')
    """)


def downgrade() -> None:
    """Drop matching weight profile tables."""

    # Drop matching_weight_versions table
    op.drop_index(
        'ix_matching_weight_versions_profile_id',
        table_name='matching_weight_versions',
    )
    op.drop_table('matching_weight_versions')

    # Drop matching_weight_profiles table
    op.drop_constraint(
        'uq_matching_weight_profile_vacancy',
        'matching_weight_profiles',
        type_='unique',
    )
    op.drop_constraint(
        'uq_matching_weight_profile_org_name',
        'matching_weight_profiles',
        type_='unique',
    )
    op.drop_index(
        'ix_matching_weight_profiles_is_active',
        table_name='matching_weight_profiles',
    )
    op.drop_index(
        'ix_matching_weight_profiles_is_preset',
        table_name='matching_weight_profiles',
    )
    op.drop_index(
        'ix_matching_weight_profiles_vacancy_id',
        table_name='matching_weight_profiles',
    )
    op.drop_index(
        'ix_matching_weight_profiles_organization_id',
        table_name='matching_weight_profiles',
    )
    op.drop_index(
        'ix_matching_weight_profiles_name',
        table_name='matching_weight_profiles',
    )
    op.drop_table('matching_weight_profiles')
