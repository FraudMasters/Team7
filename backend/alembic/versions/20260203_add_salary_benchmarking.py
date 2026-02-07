"""Add salary benchmarking and compensation analysis tables

Revision ID: 20260203_add_salary_benchmarking
Revises: 20260201_add_search_performance_indexes
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260203_add_salary_benchmarking'
down_revision: Union[str, None] = '20260201_add_search_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create salary benchmarking and compensation analysis tables."""

    # Create salary_benchmarks table
    op.create_table(
        'salary_benchmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('experience_level', sa.String(length=50), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=True, server_default='full_time'),
        sa.Column('salary_min', sa.Integer(), nullable=False),
        sa.Column('salary_median', sa.Integer(), nullable=False),
        sa.Column('salary_max', sa.Integer(), nullable=False),
        sa.Column('salary_p90', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('data_source', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('effective_date', sa.String(length=10), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for salary_benchmarks
    op.create_index('ix_salary_benchmarks_job_title', 'salary_benchmarks', ['job_title'])
    op.create_index('ix_salary_benchmarks_location', 'salary_benchmarks', ['location'])
    op.create_index('ix_salary_benchmarks_country', 'salary_benchmarks', ['country'])
    op.create_index('ix_salary_benchmarks_industry', 'salary_benchmarks', ['industry'])
    op.create_index('ix_salary_benchmarks_experience_level', 'salary_benchmarks', ['experience_level'])

    # Create salary_history table
    op.create_table(
        'salary_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('salary_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('salary_frequency', sa.String(length=20), nullable=False, server_default='annual'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('effective_date', sa.String(length=10), nullable=False),
        sa.Column('salary_type', sa.String(length=20), nullable=False, server_default='current'),
        sa.Column('employment_type', sa.String(length=50), nullable=False, server_default='full_time'),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('bonus_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('bonus_type', sa.String(length=50), nullable=True),
        sa.Column('equity_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('equity_type', sa.String(length=50), nullable=True),
        sa.Column('other_compensation', sa.JSON(), nullable=True),
        sa.Column('total_compensation', sa.Numeric(12, 2), nullable=True),
        sa.Column('is_confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('data_source', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('verification_status', sa.String(length=20), nullable=False, server_default='self_reported'),
        sa.Column('metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for salary_history
    op.create_index('ix_salary_history_resume_id', 'salary_history', ['resume_id'])
    op.create_index('ix_salary_history_effective_date', 'salary_history', ['effective_date'])
    op.create_index('ix_salary_history_salary_type', 'salary_history', ['salary_type'])
    op.create_index('ix_salary_history_verification_status', 'salary_history', ['verification_status'])

    # Create salary_offers table
    op.create_table(
        'salary_offers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('offer_status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('salary_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('salary_frequency', sa.String(length=20), nullable=False, server_default='annual'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('start_date', sa.String(length=10), nullable=True),
        sa.Column('employment_type', sa.String(length=50), nullable=False, server_default='full_time'),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('bonus_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('bonus_type', sa.String(length=50), nullable=True),
        sa.Column('equity_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('equity_type', sa.String(length=50), nullable=True),
        sa.Column('other_compensation', sa.JSON(), nullable=True),
        sa.Column('total_compensation', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('current_total_comp', sa.Numeric(12, 2), nullable=True),
        sa.Column('increase_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('offer_expires_at', sa.String(length=10), nullable=True),
        sa.Column('responded_at', sa.String(length=10), nullable=True),
        sa.Column('negotiation_round', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for salary_offers
    op.create_index('ix_salary_offers_resume_id', 'salary_offers', ['resume_id'])
    op.create_index('ix_salary_offers_job_vacancy_id', 'salary_offers', ['job_vacancy_id'])
    op.create_index('ix_salary_offers_offer_status', 'salary_offers', ['offer_status'])

    # Create cost_of_living_indices table
    op.create_table(
        'cost_of_living_indices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('cost_of_living_index', sa.Float(), nullable=False),
        sa.Column('housing_index', sa.Float(), nullable=True),
        sa.Column('transportation_index', sa.Float(), nullable=True),
        sa.Column('groceries_index', sa.Float(), nullable=True),
        sa.Column('utilities_index', sa.Float(), nullable=True),
        sa.Column('healthcare_index', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('data_source', sa.String(length=100), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('effective_date', sa.String(length=10), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for cost_of_living_indices
    op.create_index('ix_cost_of_living_indices_location', 'cost_of_living_indices', ['location'])
    op.create_index('ix_cost_of_living_indices_country', 'cost_of_living_indices', ['country'])


def downgrade() -> None:
    """Drop salary benchmarking and compensation analysis tables."""

    # Drop cost_of_living_indices table
    op.drop_index('ix_cost_of_living_indices_country', table_name='cost_of_living_indices')
    op.drop_index('ix_cost_of_living_indices_location', table_name='cost_of_living_indices')
    op.drop_table('cost_of_living_indices')

    # Drop salary_offers table
    op.drop_index('ix_salary_offers_offer_status', table_name='salary_offers')
    op.drop_index('ix_salary_offers_job_vacancy_id', table_name='salary_offers')
    op.drop_index('ix_salary_offers_resume_id', table_name='salary_offers')
    op.drop_table('salary_offers')

    # Drop salary_history table
    op.drop_index('ix_salary_history_verification_status', table_name='salary_history')
    op.drop_index('ix_salary_history_salary_type', table_name='salary_history')
    op.drop_index('ix_salary_history_effective_date', table_name='salary_history')
    op.drop_index('ix_salary_history_resume_id', table_name='salary_history')
    op.drop_table('salary_history')

    # Drop salary_benchmarks table
    op.drop_index('ix_salary_benchmarks_experience_level', table_name='salary_benchmarks')
    op.drop_index('ix_salary_benchmarks_industry', table_name='salary_benchmarks')
    op.drop_index('ix_salary_benchmarks_country', table_name='salary_benchmarks')
    op.drop_index('ix_salary_benchmarks_location', table_name='salary_benchmarks')
    op.drop_index('ix_salary_benchmarks_job_title', table_name='salary_benchmarks')
    op.drop_table('salary_benchmarks')
