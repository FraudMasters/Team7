"""Add ranking features weights table for 13-feature matching

Revision ID: 20260321_add_ranking_features_weights
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-21

This migration creates the ranking_features_weights table which expands
the matching algorithm from 3 weights (keyword, tfidf, vector) to 13
ranking features for more granular control over candidate matching.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '20260321_add_ranking_features_weights'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ranking_features_weights table with 13 weight fields."""

    # Create ranking_features_weights table
    op.create_table(
        'ranking_features_weights',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        # 13 ranking feature weights
        sa.Column('skill_match_weight', sa.Float(), nullable=False, server_default='0.15'),
        sa.Column('experience_weight', sa.Float(), nullable=False, server_default='0.12'),
        sa.Column('education_weight', sa.Float(), nullable=False, server_default='0.08'),
        sa.Column('location_weight', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('keyword_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('tfidf_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('vector_weight', sa.Float(), nullable=False, server_default='0.10'),
        sa.Column('recency_weight', sa.Float(), nullable=False, server_default='0.08'),
        sa.Column('culture_fit_weight', sa.Float(), nullable=False, server_default='0.07'),
        sa.Column('salary_match_weight', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('availability_weight', sa.Float(), nullable=False, server_default='0.05'),
        sa.Column('certifications_weight', sa.Float(), nullable=False, server_default='0.03'),
        sa.Column('industry_experience_weight', sa.Float(), nullable=False, server_default='0.02'),
        # Profile flags
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_preset', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('preset_type', sa.String(50), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        # Timestamps
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
    )

    # Create indexes for ranking_features_weights
    op.create_index(
        'ix_ranking_features_weights_organization_id',
        'ranking_features_weights',
        ['organization_id'],
        unique=False
    )
    op.create_index(
        'ix_ranking_features_weights_is_default',
        'ranking_features_weights',
        ['is_default'],
        unique=False
    )
    op.create_index(
        'ix_ranking_features_weights_is_preset',
        'ranking_features_weights',
        ['is_preset'],
        unique=False
    )
    op.create_index(
        'ix_ranking_features_weights_preset_type',
        'ranking_features_weights',
        ['preset_type'],
        unique=False
    )

    # Insert preset profiles for common role types
    op.execute("""
        INSERT INTO ranking_features_weights (
            id,
            organization_id,
            name,
            description,
            skill_match_weight,
            experience_weight,
            education_weight,
            location_weight,
            keyword_weight,
            tfidf_weight,
            vector_weight,
            recency_weight,
            culture_fit_weight,
            salary_match_weight,
            availability_weight,
            certifications_weight,
            industry_experience_weight,
            is_default,
            is_preset,
            preset_type
        )
        VALUES
            (
                gen_random_uuid(),
                'system',
                'Technical Role Focus',
                'Optimized for software engineering and technical positions - emphasizes skills and certifications',
                0.25, 0.15, 0.08, 0.03, 0.12, 0.08, 0.08, 0.05, 0.05, 0.04, 0.03, 0.04, 0.00,
                false, true, 'technical'
            ),
            (
                gen_random_uuid(),
                'system',
                'Sales Role Focus',
                'Optimized for sales positions - emphasizes experience and culture fit',
                0.10, 0.20, 0.05, 0.08, 0.08, 0.08, 0.08, 0.05, 0.15, 0.05, 0.05, 0.01, 0.02,
                false, true, 'sales'
            ),
            (
                gen_random_uuid(),
                'system',
                'Executive Role Focus',
                'Optimized for executive positions - emphasizes experience, education and industry knowledge',
                0.08, 0.22, 0.15, 0.02, 0.08, 0.08, 0.08, 0.03, 0.12, 0.03, 0.02, 0.02, 0.07,
                false, true, 'executive'
            ),
            (
                gen_random_uuid(),
                'system',
                'Balanced',
                'Balanced weights across all 13 ranking features',
                0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077, 0.077,
                false, true, 'balanced'
            )
    """)


def downgrade() -> None:
    """Remove ranking_features_weights table."""

    # Drop indexes
    op.drop_index('ix_ranking_features_weights_preset_type', table_name='ranking_features_weights')
    op.drop_index('ix_ranking_features_weights_is_preset', table_name='ranking_features_weights')
    op.drop_index('ix_ranking_features_weights_is_default', table_name='ranking_features_weights')
    op.drop_index('ix_ranking_features_weights_organization_id', table_name='ranking_features_weights')

    # Drop table
    op.drop_table('ranking_features_weights')
