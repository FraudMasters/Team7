"""Add A/B testing tables for matching weight experiments

Revision ID: 20260321_add_ab_testing_tables
Revises: 20260321_add_ranking_features_weights
Create Date: 2026-03-21

This migration creates the ab_tests and ab_test_results tables
for A/B testing different matching weight configurations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '20260321_add_ab_testing_tables'
down_revision: Union[str, None] = '20260321_add_ranking_features_weights'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create A/B testing tables."""

    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'variant_a_profile_id',
            UUID(as_uuid=True),
            sa.ForeignKey('matching_weights_profiles.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'variant_b_profile_id',
            UUID(as_uuid=True),
            sa.ForeignKey('matching_weights_profiles.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for ab_tests
    op.create_index(
        'ix_ab_tests_organization_id',
        'ab_tests',
        ['organization_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_tests_variant_a_profile_id',
        'ab_tests',
        ['variant_a_profile_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_tests_variant_b_profile_id',
        'ab_tests',
        ['variant_b_profile_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_tests_status',
        'ab_tests',
        ['status'],
        unique=False
    )

    # Create ab_test_results table
    op.create_table(
        'ab_test_results',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            'ab_test_id',
            UUID(as_uuid=True),
            sa.ForeignKey('ab_tests.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'vacancy_id',
            UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'resume_id',
            UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'match_result_id',
            UUID(as_uuid=True),
            sa.ForeignKey('match_results.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('variant_assigned', sa.String(1), nullable=False),
        sa.Column('outcome', sa.String(20), nullable=True, server_default=None),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for ab_test_results
    op.create_index(
        'ix_ab_test_results_ab_test_id',
        'ab_test_results',
        ['ab_test_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_results_vacancy_id',
        'ab_test_results',
        ['vacancy_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_results_resume_id',
        'ab_test_results',
        ['resume_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_results_match_result_id',
        'ab_test_results',
        ['match_result_id'],
        unique=False
    )
    op.create_index(
        'ix_ab_test_results_variant_assigned',
        'ab_test_results',
        ['variant_assigned'],
        unique=False
    )


def downgrade() -> None:
    """Remove A/B testing tables."""

    # Drop ab_test_results table
    op.drop_index('ix_ab_test_results_variant_assigned', table_name='ab_test_results')
    op.drop_index('ix_ab_test_results_match_result_id', table_name='ab_test_results')
    op.drop_index('ix_ab_test_results_resume_id', table_name='ab_test_results')
    op.drop_index('ix_ab_test_results_vacancy_id', table_name='ab_test_results')
    op.drop_index('ix_ab_test_results_ab_test_id', table_name='ab_test_results')
    op.drop_table('ab_test_results')

    # Drop ab_tests table
    op.drop_index('ix_ab_tests_status', table_name='ab_tests')
    op.drop_index('ix_ab_tests_variant_b_profile_id', table_name='ab_tests')
    op.drop_index('ix_ab_tests_variant_a_profile_id', table_name='ab_tests')
    op.drop_index('ix_ab_tests_organization_id', table_name='ab_tests')
    op.drop_table('ab_tests')
