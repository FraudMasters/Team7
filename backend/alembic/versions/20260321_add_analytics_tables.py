"""Add analytics and reporting tables

Revision ID: 20260321_add_analytics_tables
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-21

This migration creates tables for advanced analytics and reporting dashboard:
- application_sources: Track where job applications originate for source effectiveness analysis
- pipeline_stage_transitions: Track candidate movement through hiring stages for time-to-hire metrics
- diversity_metrics: Store aggregated diversity and inclusion metrics
- diversity_goals: Store diversity targets and goal tracking
- scheduled_reports: Configuration for automated report generation and delivery

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260321_add_analytics_tables'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create analytics and reporting tables."""

    # Create application_sources table
    op.create_table(
        'application_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_name', sa.String(255), nullable=False),
        sa.Column('source_url', sa.String(1000), nullable=True),
        sa.Column('campaign_id', sa.String(255), nullable=True),
        sa.Column('referrer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cost_per_application', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment='Track where job applications originate for source effectiveness analysis',
    )

    # Create indexes for application_sources
    op.create_index('ix_application_sources_application_id', 'application_sources', ['application_id'])
    op.create_index('ix_application_sources_source_type', 'application_sources', ['source_type'])
    op.create_index('ix_application_sources_source_name', 'application_sources', ['source_name'])
    op.create_index('ix_application_sources_campaign_id', 'application_sources', ['campaign_id'])
    op.create_index('ix_application_sources_referrer_id', 'application_sources', ['referrer_id'])

    # Create pipeline_stage_transitions table
    op.create_table(
        'pipeline_stage_transitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_stage', sa.String(50), nullable=True),
        sa.Column('to_stage', sa.String(50), nullable=False),
        sa.Column('transition_reason', sa.String(50), nullable=False, server_default='MANUAL'),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('transition_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('automated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment='Track candidate movement through hiring stages for time-to-hire and funnel conversion metrics',
    )

    # Create indexes for pipeline_stage_transitions
    op.create_index('ix_pipeline_stage_transitions_resume_id', 'pipeline_stage_transitions', ['resume_id'])
    op.create_index('ix_pipeline_stage_transitions_vacancy_id', 'pipeline_stage_transitions', ['vacancy_id'])
    op.create_index('ix_pipeline_stage_transitions_from_stage', 'pipeline_stage_transitions', ['from_stage'])
    op.create_index('ix_pipeline_stage_transitions_to_stage', 'pipeline_stage_transitions', ['to_stage'])
    op.create_index('ix_pipeline_stage_transitions_transition_reason', 'pipeline_stage_transitions', ['transition_reason'])
    op.create_index('ix_pipeline_stage_transitions_recruiter_id', 'pipeline_stage_transitions', ['recruiter_id'])
    op.create_index('ix_pipeline_stage_transitions_transition_date', 'pipeline_stage_transitions', ['transition_date'])

    # Create diversity_metrics table
    op.create_table(
        'diversity_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('pipeline_stage_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_stage_transitions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('period_start', sa.String(50), nullable=False),
        sa.Column('period_end', sa.String(50), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('demographic_category', sa.String(50), nullable=False),
        sa.Column('demographic_value', sa.String(100), nullable=False),
        sa.Column('total_candidates', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_applicants', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_screened', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_interviewed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_offered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_hired', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('candidates_rejected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('representation_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('screening_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('interview_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('offer_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('hire_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('conversion_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('target_representation', sa.Numeric(5, 4), nullable=True),
        sa.Column('goal_met', sa.Boolean(), nullable=True),
        sa.Column('variance_from_target', sa.Numeric(6, 4), nullable=True),
        sa.Column('overall_pool_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('industry_benchmark', sa.Numeric(5, 4), nullable=True),
        sa.Column('prior_period_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('year_over_year_change', sa.Numeric(6, 4), nullable=True),
        sa.Column('stage_breakdown', sa.JSON(), nullable=True),
        sa.Column('source_breakdown', sa.JSON(), nullable=True),
        sa.Column('department_breakdown', sa.JSON(), nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('trend_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.Numeric(3, 2), nullable=True, server_default='0.95'),
        sa.Column('margin_of_error', sa.Numeric(5, 4), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('analysis_notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment='Store aggregated diversity and inclusion metrics across hiring pipelines',
    )

    # Create indexes for diversity_metrics
    op.create_index('ix_diversity_metrics_organization_id', 'diversity_metrics', ['organization_id'])
    op.create_index('ix_diversity_metrics_vacancy_id', 'diversity_metrics', ['vacancy_id'])
    op.create_index('ix_diversity_metrics_pipeline_stage_id', 'diversity_metrics', ['pipeline_stage_id'])
    op.create_index('ix_diversity_metrics_period_start', 'diversity_metrics', ['period_start'])
    op.create_index('ix_diversity_metrics_period_end', 'diversity_metrics', ['period_end'])
    op.create_index('ix_diversity_metrics_demographic_category', 'diversity_metrics', ['demographic_category'])
    op.create_index('ix_diversity_metrics_demographic_value', 'diversity_metrics', ['demographic_value'])

    # Create diversity_goals table
    op.create_table(
        'diversity_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('goal_name', sa.String(200), nullable=False),
        sa.Column('goal_description', sa.Text(), nullable=True),
        sa.Column('demographic_category', sa.String(50), nullable=False),
        sa.Column('demographic_value', sa.String(100), nullable=False),
        sa.Column('target_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('target_count', sa.Integer(), nullable=True),
        sa.Column('baseline_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('baseline_count', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.String(50), nullable=False),
        sa.Column('target_date', sa.String(50), nullable=False),
        sa.Column('review_frequency', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('current_percentage', sa.Numeric(5, 4), nullable=True),
        sa.Column('current_count', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Numeric(3, 2), nullable=True),
        sa.Column('on_track', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_notes', sa.JSON(), nullable=True),
        sa.Column('goal_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment='Store diversity targets and goal tracking for organizational D&I initiatives',
    )

    # Create indexes for diversity_goals
    op.create_index('ix_diversity_goals_organization_id', 'diversity_goals', ['organization_id'])
    op.create_index('ix_diversity_goals_vacancy_id', 'diversity_goals', ['vacancy_id'])
    op.create_index('ix_diversity_goals_demographic_category', 'diversity_goals', ['demographic_category'])
    op.create_index('ix_diversity_goals_demographic_value', 'diversity_goals', ['demographic_value'])
    op.create_index('ix_diversity_goals_start_date', 'diversity_goals', ['start_date'])
    op.create_index('ix_diversity_goals_target_date', 'diversity_goals', ['target_date'])
    op.create_index('ix_diversity_goals_status', 'diversity_goals', ['status'])

    # Create scheduled_reports table
    op.create_table(
        'scheduled_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', sa.String(), nullable=False),
        sa.Column('report_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('schedule_config', sa.JSON(), nullable=False),
        sa.Column('delivery_config', sa.JSON(), nullable=False),
        sa.Column('recipients', sa.JSON(), nullable=False),
        sa.Column('format', sa.String(), nullable=False, server_default='pdf'),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        comment='Configuration for automated report generation and email delivery',
    )

    # Create indexes for scheduled_reports
    op.create_index('ix_scheduled_reports_organization_id', 'scheduled_reports', ['organization_id'])
    op.create_index('ix_scheduled_reports_report_id', 'scheduled_reports', ['report_id'])
    op.create_index('ix_scheduled_reports_next_run_at', 'scheduled_reports', ['next_run_at'])


def downgrade() -> None:
    """Drop analytics and reporting tables."""

    # Drop scheduled_reports table
    op.drop_index('ix_scheduled_reports_next_run_at', table_name='scheduled_reports')
    op.drop_index('ix_scheduled_reports_report_id', table_name='scheduled_reports')
    op.drop_index('ix_scheduled_reports_organization_id', table_name='scheduled_reports')
    op.drop_table('scheduled_reports')

    # Drop diversity_goals table
    op.drop_index('ix_diversity_goals_status', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_target_date', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_start_date', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_demographic_value', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_demographic_category', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_vacancy_id', table_name='diversity_goals')
    op.drop_index('ix_diversity_goals_organization_id', table_name='diversity_goals')
    op.drop_table('diversity_goals')

    # Drop diversity_metrics table
    op.drop_index('ix_diversity_metrics_demographic_value', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_demographic_category', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_period_end', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_period_start', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_pipeline_stage_id', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_vacancy_id', table_name='diversity_metrics')
    op.drop_index('ix_diversity_metrics_organization_id', table_name='diversity_metrics')
    op.drop_table('diversity_metrics')

    # Drop pipeline_stage_transitions table
    op.drop_index('ix_pipeline_stage_transitions_transition_date', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_recruiter_id', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_transition_reason', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_to_stage', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_from_stage', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_vacancy_id', table_name='pipeline_stage_transitions')
    op.drop_index('ix_pipeline_stage_transitions_resume_id', table_name='pipeline_stage_transitions')
    op.drop_table('pipeline_stage_transitions')

    # Drop application_sources table
    op.drop_index('ix_application_sources_referrer_id', table_name='application_sources')
    op.drop_index('ix_application_sources_campaign_id', table_name='application_sources')
    op.drop_index('ix_application_sources_source_name', table_name='application_sources')
    op.drop_index('ix_application_sources_source_type', table_name='application_sources')
    op.drop_index('ix_application_sources_application_id', table_name='application_sources')
    op.drop_table('application_sources')
