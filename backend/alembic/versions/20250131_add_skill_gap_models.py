"""Add skill gap analysis and learning recommendation models

Revision ID: 013_add_skill_gap_models
Revises: 012_add_skill_taxonomies
Create Date: 2025-01-31

This migration creates tables for:
- skill_gap_reports: Store candidate-to-vacancy skill gap analysis
- learning_resources: Store courses, certifications, and training materials
- skill_development_plans: Track candidate upskilling progress

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '013_add_skill_gap_models'
down_revision: Union[str, None] = '012_add_skill_taxonomies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create skill gap analysis tables."""

    # Create skill_gap_reports table
    op.create_table(
        'skill_gap_reports',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'),
            nullable=False,
        ),
        # Candidate skills data
        sa.Column('candidate_skills', postgresql.JSON(), nullable=True),
        sa.Column('candidate_skill_levels', postgresql.JSON(), nullable=True),
        # Required skills data
        sa.Column('required_skills', postgresql.JSON(), nullable=True),
        sa.Column('required_skill_levels', postgresql.JSON(), nullable=True),
        # Gap analysis
        sa.Column('missing_skills', postgresql.JSON(), nullable=True),
        sa.Column('missing_skill_details', postgresql.JSON(), nullable=True),
        sa.Column('matched_skills', postgresql.JSON(), nullable=True),
        sa.Column('partial_match_skills', postgresql.JSON(), nullable=True),
        # Overall assessment
        sa.Column('gap_severity', sa.String(20), nullable=True),
        sa.Column('gap_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('bridgeability_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('estimated_time_to_bridge', sa.Integer(), nullable=True),
        # Recommendations
        sa.Column('recommended_resources_count', sa.Integer(), nullable=True),
        sa.Column('priority_ordering', postgresql.JSON(), nullable=True),
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
        comment='Store candidate-to-vacancy skill gap analysis results',
    )
    op.create_index(
        op.f('ix_skill_gap_reports_resume_id'), 'skill_gap_reports', ['resume_id']
    )
    op.create_index(
        op.f('ix_skill_gap_reports_vacancy_id'), 'skill_gap_reports', ['vacancy_id']
    )
    op.create_index(
        op.f('ix_skill_gap_reports_resume_vacancy'),
        'skill_gap_reports',
        ['resume_id', 'vacancy_id'],
        unique=False,
    )

    # Create learning_resources table
    op.create_table(
        'learning_resources',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'skill_gap_report_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('skill_gap_reports.id', ondelete='SET NULL'),
            nullable=True,
        ),
        # Basic information
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('source_platform', sa.String(100), nullable=True),
        # Resource content
        sa.Column('skills_taught', postgresql.JSON(), nullable=True),
        sa.Column('skill_level', sa.String(20), nullable=True),
        sa.Column('topics_covered', postgresql.JSON(), nullable=True),
        sa.Column('prerequisites', postgresql.JSON(), nullable=True),
        sa.Column('learning_objectives', postgresql.JSON(), nullable=True),
        # Access information
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('access_type', sa.String(20), nullable=False, default='free'),
        sa.Column('cost_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        # Time investment
        sa.Column('duration_hours', sa.Numeric(8, 2), nullable=True),
        sa.Column('duration_weeks', sa.Numeric(6, 2), nullable=True),
        sa.Column('is_self_paced', sa.Boolean(), nullable=False, default=True),
        # Quality metrics
        sa.Column('rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False, default=0),
        sa.Column('review_count', sa.Integer(), nullable=False, default=0),
        sa.Column('popularity_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('quality_score', sa.Numeric(5, 4), nullable=True),
        # Provider information
        sa.Column('provider_name', sa.String(200), nullable=True),
        sa.Column('instructor_name', sa.String(200), nullable=True),
        sa.Column('certificate_offered', sa.Boolean(), nullable=False, default=False),
        sa.Column('certificate_url', sa.Text(), nullable=True),
        # Additional metadata
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('external_id', sa.String(200), nullable=True),
        sa.Column('resource_metadata', postgresql.JSON(), nullable=True),
        # Usage tracking
        sa.Column('recommendation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('click_count', sa.Integer(), nullable=False, default=0),
        sa.Column('enrollment_count', sa.Integer(), nullable=False, default=0),
        sa.Column('completion_rate', sa.Numeric(4, 3), nullable=True),
        sa.Column('last_recommended_at', sa.String(100), nullable=True),
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
        comment='Store courses, certifications, and training materials',
    )
    op.create_index(
        op.f('ix_learning_resources_skill_gap_report_id'),
        'learning_resources',
        ['skill_gap_report_id'],
    )
    op.create_index(
        op.f('ix_learning_resources_title'), 'learning_resources', ['title']
    )
    op.create_index(
        op.f('ix_learning_resources_resource_type'),
        'learning_resources',
        ['resource_type'],
    )
    op.create_index(
        op.f('ix_learning_resources_source_platform'),
        'learning_resources',
        ['source_platform'],
    )
    op.create_index(
        op.f('ix_learning_resources_skill_level'),
        'learning_resources',
        ['skill_level'],
    )
    op.create_index(
        op.f('ix_learning_resources_external_id'),
        'learning_resources',
        ['external_id'],
    )

    # Create skill_development_plans table
    op.create_table(
        'skill_development_plans',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'skill_gap_report_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('skill_gap_reports.id', ondelete='SET NULL'),
            nullable=True,
        ),
        # Plan details
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='draft'),
        sa.Column('overall_progress', sa.Numeric(5, 2), nullable=False, default=0.0),
        # Timeline
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('target_completion_date', sa.String(50), nullable=True),
        sa.Column('actual_completion_date', sa.String(50), nullable=True),
        # Plan content
        sa.Column('learning_goals', postgresql.JSON(), nullable=True),
        sa.Column('milestones', postgresql.JSON(), nullable=True),
        sa.Column('recommended_resources', postgresql.JSON(), nullable=True),
        sa.Column('completed_resources', postgresql.JSON(), nullable=True),
        # Progress tracking
        sa.Column('total_resources_count', sa.Integer(), nullable=False, default=0),
        sa.Column('completed_resources_count', sa.Integer(), nullable=False, default=0),
        sa.Column('hours_invested', sa.Numeric(8, 2), nullable=False, default=0.0),
        sa.Column('estimated_hours_remaining', sa.Numeric(8, 2), nullable=True),
        # Sharing and access
        sa.Column('shareable_token', sa.String(100), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('shared_with_recruiters', postgresql.JSON(), nullable=True),
        sa.Column('access_expires_at', sa.String(50), nullable=True),
        # Engagement tracking
        sa.Column('last_accessed_at', sa.String(50), nullable=True),
        sa.Column('reminder_scheduled_at', sa.String(50), nullable=True),
        sa.Column('reminder_frequency', sa.String(20), nullable=False, default='none'),
        sa.Column('notes', sa.Text(), nullable=True),
        # Outcome tracking
        sa.Column('reapplication_status', sa.String(50), nullable=False, default='not_applied'),
        sa.Column('reapplication_date', sa.String(50), nullable=True),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        # Additional metadata
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),
        sa.Column('difficulty_level', sa.String(20), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('resource_metadata', postgresql.JSON(), nullable=True),
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
        comment='Track candidate skill development progress',
    )
    op.create_index(
        op.f('ix_skill_development_plans_resume_id'),
        'skill_development_plans',
        ['resume_id'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_vacancy_id'),
        'skill_development_plans',
        ['vacancy_id'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_skill_gap_report_id'),
        'skill_development_plans',
        ['skill_gap_report_id'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_status'),
        'skill_development_plans',
        ['status'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_priority'),
        'skill_development_plans',
        ['priority'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_difficulty_level'),
        'skill_development_plans',
        ['difficulty_level'],
    )
    op.create_index(
        op.f('ix_skill_development_plans_shareable_token'),
        'skill_development_plans',
        ['shareable_token'],
        unique=True,
    )


def downgrade() -> None:
    """Drop skill gap analysis tables."""

    # Drop skill_development_plans table
    op.drop_index(
        op.f('ix_skill_development_plans_shareable_token'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_difficulty_level'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_priority'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_status'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_skill_gap_report_id'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_vacancy_id'),
        table_name='skill_development_plans',
    )
    op.drop_index(
        op.f('ix_skill_development_plans_resume_id'),
        table_name='skill_development_plans',
    )
    op.drop_table('skill_development_plans')

    # Drop learning_resources table
    op.drop_index(
        op.f('ix_learning_resources_external_id'),
        table_name='learning_resources',
    )
    op.drop_index(
        op.f('ix_learning_resources_skill_level'),
        table_name='learning_resources',
    )
    op.drop_index(
        op.f('ix_learning_resources_source_platform'),
        table_name='learning_resources',
    )
    op.drop_index(
        op.f('ix_learning_resources_resource_type'),
        table_name='learning_resources',
    )
    op.drop_index(
        op.f('ix_learning_resources_title'), table_name='learning_resources'
    )
    op.drop_index(
        op.f('ix_learning_resources_skill_gap_report_id'),
        table_name='learning_resources',
    )
    op.drop_table('learning_resources')

    # Drop skill_gap_reports table
    op.drop_index(
        op.f('ix_skill_gap_reports_resume_vacancy'),
        table_name='skill_gap_reports',
    )
    op.drop_index(
        op.f('ix_skill_gap_reports_vacancy_id'), table_name='skill_gap_reports'
    )
    op.drop_index(
        op.f('ix_skill_gap_reports_resume_id'), table_name='skill_gap_reports'
    )
    op.drop_table('skill_gap_reports')
