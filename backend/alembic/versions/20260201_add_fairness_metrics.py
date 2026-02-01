"""Add fairness metrics and demographic inference tables

Revision ID: 017_add_fairness_metrics
Revises: 016_add_workflow_stage_config
Create Date: 2026-02-01

This migration creates tables for AI bias detection and fairness monitoring:
- fairness_metrics: Stores bias analysis results and metrics
- fairness_alerts: Stores bias detection alerts
- demographic_inferences: Stores inferred demographic attributes from resumes

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '017_add_fairness_metrics'
down_revision: Union[str, None] = '016_add_workflow_stage_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create fairness_metrics, fairness_alerts, and demographic_inferences tables."""

    # Create fairness_metrics table
    op.create_table(
        'fairness_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('model_version_id', sa.String(), sa.ForeignKey('ml_model_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('analysis_date', sa.String(50), nullable=False),
        sa.Column('demographic_group', sa.String(50), nullable=False),
        sa.Column('disparate_impact_ratio', sa.Numeric(5, 4), nullable=True),
        sa.Column('statistical_parity_difference', sa.Numeric(5, 4), nullable=True),
        sa.Column('group_selection_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('overall_selection_rate', sa.Numeric(5, 4), nullable=True),
        sa.Column('group_sample_size', sa.Integer(), nullable=True),
        sa.Column('total_sample_size', sa.Integer(), nullable=True),
        sa.Column('alert_threshold', sa.Numeric(5, 4), nullable=False, server_default='0.8'),
        sa.Column('alert_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_severity', sa.String(20), nullable=True),
        sa.Column('group_metrics', sa.JSON(), nullable=True),
        sa.Column('mitigation_suggested', sa.Text(), nullable=True),
        sa.Column('is_fairness_aware', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('analysis_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for fairness_metrics
    op.create_index('ix_fairness_metrics_vacancy_id', 'fairness_metrics', ['vacancy_id'])
    op.create_index('ix_fairness_metrics_model_version_id', 'fairness_metrics', ['model_version_id'])
    op.create_index('ix_fairness_metrics_analysis_date', 'fairness_metrics', ['analysis_date'])
    op.create_index('ix_fairness_metrics_demographic_group', 'fairness_metrics', ['demographic_group'])

    # Create fairness_alerts table
    op.create_table(
        'fairness_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('fairness_metric_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('fairness_metrics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('alert_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('threshold_value', sa.Numeric(5, 4), nullable=True),
        sa.Column('actual_value', sa.Numeric(5, 4), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('acknowledged_at', sa.String(50), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.String(50), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for fairness_alerts
    op.create_index('ix_fairness_alerts_fairness_metric_id', 'fairness_alerts', ['fairness_metric_id'])
    op.create_index('ix_fairness_alerts_vacancy_id', 'fairness_alerts', ['vacancy_id'])
    op.create_index('ix_fairness_alerts_alert_type', 'fairness_alerts', ['alert_type'])
    op.create_index('ix_fairness_alerts_severity', 'fairness_alerts', ['severity'])
    op.create_index('ix_fairness_alerts_status', 'fairness_alerts', ['status'])

    # Create demographic_inferences table
    op.create_table(
        'demographic_inferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resume_analyses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('inferred_gender', sa.Text(), nullable=True),
        sa.Column('gender_confidence', sa.Float(), nullable=True),
        sa.Column('inferred_age_group', sa.Text(), nullable=True),
        sa.Column('age_confidence', sa.Float(), nullable=True),
        sa.Column('inferred_ethnicity', sa.Text(), nullable=True),
        sa.Column('ethnicity_confidence', sa.Float(), nullable=True),
        sa.Column('inferred_geographic_region', sa.Text(), nullable=True),
        sa.Column('geographic_confidence', sa.Float(), nullable=True),
        sa.Column('inferred_education_level', sa.Text(), nullable=True),
        sa.Column('education_confidence', sa.Float(), nullable=True),
        sa.Column('inferred_career_stage', sa.Text(), nullable=True),
        sa.Column('career_stage_confidence', sa.Float(), nullable=True),
        sa.Column('raw_features', sa.JSON(), nullable=True),
        sa.Column('alternative_predictions', sa.JSON(), nullable=True),
        sa.Column('bias_indicators', sa.JSON(), nullable=True),
        sa.Column('inference_method', sa.Text(), nullable=True),
        sa.Column('inference_version', sa.Text(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('is_manual_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('confidence_threshold_met', sa.Boolean(), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=True),
        sa.Column('review_status', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for demographic_inferences
    op.create_index('ix_demographic_inferences_resume_id', 'demographic_inferences', ['resume_id'])
    op.create_index('ix_demographic_inferences_analysis_id', 'demographic_inferences', ['analysis_id'])


def downgrade() -> None:
    """Drop fairness monitoring tables."""

    # Drop demographic_inferences table
    op.drop_index('ix_demographic_inferences_analysis_id', table_name='demographic_inferences')
    op.drop_index('ix_demographic_inferences_resume_id', table_name='demographic_inferences')
    op.drop_table('demographic_inferences')

    # Drop fairness_alerts table
    op.drop_index('ix_fairness_alerts_status', table_name='fairness_alerts')
    op.drop_index('ix_fairness_alerts_severity', table_name='fairness_alerts')
    op.drop_index('ix_fairness_alerts_alert_type', table_name='fairness_alerts')
    op.drop_index('ix_fairness_alerts_vacancy_id', table_name='fairness_alerts')
    op.drop_index('ix_fairness_alerts_fairness_metric_id', table_name='fairness_alerts')
    op.drop_table('fairness_alerts')

    # Drop fairness_metrics table
    op.drop_index('ix_fairness_metrics_demographic_group', table_name='fairness_metrics')
    op.drop_index('ix_fairness_metrics_analysis_date', table_name='fairness_metrics')
    op.drop_index('ix_fairness_metrics_model_version_id', table_name='fairness_metrics')
    op.drop_index('ix_fairness_metrics_vacancy_id', table_name='fairness_metrics')
    op.drop_table('fairness_metrics')
