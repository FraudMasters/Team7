"""Add database indexes for analytics query performance

Revision ID: 017_add_analytics_indexes
Revises: 016_add_workflow_stage_config
Create Date: 2026-02-01

This migration adds indexes to optimize analytics query performance:

- analytics_events: Add indexes for time-series queries and common filter combinations
- hiring_stages: Add indexes for funnel analytics over time
- reports: Add indexes for report management queries
- scheduled_reports: Add indexes for scheduler queries

These indexes improve dashboard performance and enable efficient date-range queries
for analytics features.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017_add_analytics_indexes'
down_revision: Union[str, None] = '016_add_workflow_stage_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for analytics queries."""

    # Analytics events table - time-series analytics
    op.create_index(
        'ix_analytics_events_created_at',
        'analytics_events',
        ['created_at'],
    )
    op.create_index(
        'ix_analytics_events_event_type_created_at',
        'analytics_events',
        ['event_type', 'created_at'],
    )
    op.create_index(
        'ix_analytics_events_entity_type_id_created_at',
        'analytics_events',
        ['entity_type', 'entity_id', 'created_at'],
    )
    op.create_index(
        'ix_analytics_events_recruiter_id_created_at',
        'analytics_events',
        ['recruiter_id', 'created_at'],
    )

    # Hiring stages table - funnel analytics over time
    op.create_index(
        'ix_hiring_stages_created_at',
        'hiring_stages',
        ['created_at'],
    )
    op.create_index(
        'ix_hiring_stages_vacancy_id_created_at',
        'hiring_stages',
        ['vacancy_id', 'created_at'],
    )
    op.create_index(
        'ix_hiring_stages_resume_id_created_at',
        'hiring_stages',
        ['resume_id', 'created_at'],
    )

    # Reports table - report management
    op.create_index(
        'ix_reports_created_at',
        'reports',
        ['created_at'],
    )
    op.create_index(
        'ix_reports_organization_id_is_active',
        'reports',
        ['organization_id', 'is_active'],
    )

    # Scheduled reports table - scheduler queries
    op.create_index(
        'ix_scheduled_reports_is_active',
        'scheduled_reports',
        ['is_active'],
    )
    op.create_index(
        'ix_scheduled_reports_organization_id_is_active',
        'scheduled_reports',
        ['organization_id', 'is_active'],
    )
    op.create_index(
        'ix_scheduled_reports_next_run_at',
        'scheduled_reports',
        ['next_run_at'],
    )


def downgrade() -> None:
    """Remove analytics performance indexes."""

    # Analytics events table
    op.drop_index(
        'ix_analytics_events_recruiter_id_created_at',
        table_name='analytics_events',
    )
    op.drop_index(
        'ix_analytics_events_entity_type_id_created_at',
        table_name='analytics_events',
    )
    op.drop_index(
        'ix_analytics_events_event_type_created_at',
        table_name='analytics_events',
    )
    op.drop_index(
        'ix_analytics_events_created_at',
        table_name='analytics_events',
    )

    # Hiring stages table
    op.drop_index(
        'ix_hiring_stages_resume_id_created_at',
        table_name='hiring_stages',
    )
    op.drop_index(
        'ix_hiring_stages_vacancy_id_created_at',
        table_name='hiring_stages',
    )
    op.drop_index(
        'ix_hiring_stages_created_at',
        table_name='hiring_stages',
    )

    # Reports table
    op.drop_index(
        'ix_reports_organization_id_is_active',
        table_name='reports',
    )
    op.drop_index(
        'ix_reports_created_at',
        table_name='reports',
    )

    # Scheduled reports table
    op.drop_index(
        'ix_scheduled_reports_next_run_at',
        table_name='scheduled_reports',
    )
    op.drop_index(
        'ix_scheduled_reports_organization_id_is_active',
        table_name='scheduled_reports',
    )
    op.drop_index(
        'ix_scheduled_reports_is_active',
        table_name='scheduled_reports',
    )
