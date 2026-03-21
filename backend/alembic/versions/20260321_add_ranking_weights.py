"""Add ranking weight profile models

Revision ID: 20260321_add_ranking_weights
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-21

This migration creates tables for:
- ranking_weight_profiles: Store custom weight configurations for ranking algorithm
- ranking_weight_versions: Track version history of weight profiles for audit

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260321_add_ranking_weights'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ranking weight profile tables."""

    # Create ranking_weight_profiles table
    op.create_table(
        'ranking_weight_profiles',
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
        sa.Column('preset_type', sa.String(50), nullable=True),
        # Ranking feature weights (13 features, should sum to 1.0)
        sa.Column('overall_match_score_weight', sa.Float(), nullable=False, default=0.15),
        sa.Column('keyword_score_weight', sa.Float(), nullable=False, default=0.10),
        sa.Column('tfidf_score_weight', sa.Float(), nullable=False, default=0.08),
        sa.Column('vector_score_weight', sa.Float(), nullable=False, default=0.07),
        sa.Column('skills_match_ratio_weight', sa.Float(), nullable=False, default=0.20),
        sa.Column('experience_months_weight', sa.Float(), nullable=False, default=0.08),
        sa.Column('experience_relevance_weight', sa.Float(), nullable=False, default=0.10),
        sa.Column('education_level_weight', sa.Float(), nullable=False, default=0.06),
        sa.Column('recent_experience_weight', sa.Float(), nullable=False, default=0.05),
        sa.Column('skill_rarity_weight', sa.Float(), nullable=False, default=0.04),
        sa.Column('title_similarity_weight', sa.Float(), nullable=False, default=0.04),
        sa.Column('freshness_score_weight', sa.Float(), nullable=False, default=0.02),
        sa.Column('completeness_score_weight', sa.Float(), nullable=False, default=0.01),
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
        comment='Store custom weight configurations for candidate ranking algorithm',
    )

    # Create indexes for ranking_weight_profiles
    op.create_index(
        'ix_ranking_weight_profiles_name',
        'ranking_weight_profiles',
        ['name'],
    )
    op.create_index(
        'ix_ranking_weight_profiles_organization_id',
        'ranking_weight_profiles',
        ['organization_id'],
    )
    op.create_index(
        'ix_ranking_weight_profiles_vacancy_id',
        'ranking_weight_profiles',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_ranking_weight_profiles_is_preset',
        'ranking_weight_profiles',
        ['is_preset'],
    )
    op.create_index(
        'ix_ranking_weight_profiles_is_active',
        'ranking_weight_profiles',
        ['is_active'],
    )
    op.create_index(
        'ix_ranking_weight_profiles_preset_type',
        'ranking_weight_profiles',
        ['preset_type'],
    )

    # Create unique constraints
    op.create_unique_constraint(
        'uq_ranking_weight_profile_org_name',
        'ranking_weight_profiles',
        ['organization_id', 'name'],
    )
    op.create_unique_constraint(
        'uq_ranking_weight_profile_vacancy',
        'ranking_weight_profiles',
        ['vacancy_id'],
    )

    # Create ranking_weight_versions table
    op.create_table(
        'ranking_weight_versions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'profile_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('ranking_weight_profiles.id', ondelete='CASCADE'),
            nullable=False,
        ),
        # Snapshot of weights at this version (13 ranking features)
        sa.Column('overall_match_score_weight', sa.Float(), nullable=False),
        sa.Column('keyword_score_weight', sa.Float(), nullable=False),
        sa.Column('tfidf_score_weight', sa.Float(), nullable=False),
        sa.Column('vector_score_weight', sa.Float(), nullable=False),
        sa.Column('skills_match_ratio_weight', sa.Float(), nullable=False),
        sa.Column('experience_months_weight', sa.Float(), nullable=False),
        sa.Column('experience_relevance_weight', sa.Float(), nullable=False),
        sa.Column('education_level_weight', sa.Float(), nullable=False),
        sa.Column('recent_experience_weight', sa.Float(), nullable=False),
        sa.Column('skill_rarity_weight', sa.Float(), nullable=False),
        sa.Column('title_similarity_weight', sa.Float(), nullable=False),
        sa.Column('freshness_score_weight', sa.Float(), nullable=False),
        sa.Column('completeness_score_weight', sa.Float(), nullable=False),
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
        comment='Version history for ranking weight profiles',
    )

    # Create indexes for ranking_weight_versions
    op.create_index(
        'ix_ranking_weight_versions_profile_id',
        'ranking_weight_versions',
        ['profile_id'],
    )

    # Insert preset profiles
    op.execute("""
        INSERT INTO ranking_weight_profiles (
            id,
            name,
            description,
            is_preset,
            is_active,
            preset_type,
            overall_match_score_weight,
            keyword_score_weight,
            tfidf_score_weight,
            vector_score_weight,
            skills_match_ratio_weight,
            experience_months_weight,
            experience_relevance_weight,
            education_level_weight,
            recent_experience_weight,
            skill_rarity_weight,
            title_similarity_weight,
            freshness_score_weight,
            completeness_score_weight,
            version
        )
        VALUES
            (
                gen_random_uuid(),
                'Balanced',
                'Equal consideration of all ranking factors for general-purpose hiring',
                true,
                true,
                'balanced',
                0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.076,
                'v1.0'
            ),
            (
                gen_random_uuid(),
                'Technical',
                'Optimized for technical roles - prioritizes skills match, keyword matching, and education',
                true,
                true,
                'technical',
                0.15, 0.15, 0.10, 0.08, 0.25, 0.05, 0.10, 0.08, 0.02, 0.01, 0.01, 0.00, 0.00,
                'v1.0'
            ),
            (
                gen_random_uuid(),
                'Sales',
                'Optimized for sales roles - prioritizes title similarity, experience relevance, and recent activity',
                true,
                true,
                'sales',
                0.12, 0.08, 0.06, 0.05, 0.10, 0.12, 0.20, 0.05, 0.10, 0.02, 0.08, 0.01, 0.01,
                'v1.0'
            ),
            (
                gen_random_uuid(),
                'Executive',
                'Optimized for executive/leadership roles - prioritizes experience, education, and title similarity',
                true,
                true,
                'executive',
                0.10, 0.05, 0.05, 0.05, 0.08, 0.20, 0.22, 0.12, 0.05, 0.01, 0.06, 0.00, 0.01,
                'v1.0'
            )
    """)


def downgrade() -> None:
    """Drop ranking weight profile tables."""

    # Drop ranking_weight_versions table
    op.drop_index(
        'ix_ranking_weight_versions_profile_id',
        table_name='ranking_weight_versions',
    )
    op.drop_table('ranking_weight_versions')

    # Drop ranking_weight_profiles table
    op.drop_constraint(
        'uq_ranking_weight_profile_vacancy',
        'ranking_weight_profiles',
        type_='unique',
    )
    op.drop_constraint(
        'uq_ranking_weight_profile_org_name',
        'ranking_weight_profiles',
        type_='unique',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_preset_type',
        table_name='ranking_weight_profiles',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_is_active',
        table_name='ranking_weight_profiles',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_is_preset',
        table_name='ranking_weight_profiles',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_vacancy_id',
        table_name='ranking_weight_profiles',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_organization_id',
        table_name='ranking_weight_profiles',
    )
    op.drop_index(
        'ix_ranking_weight_profiles_name',
        table_name='ranking_weight_profiles',
    )
    op.drop_table('ranking_weight_profiles')
