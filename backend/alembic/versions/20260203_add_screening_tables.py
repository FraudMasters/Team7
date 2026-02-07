"""Add screening tables

Revision ID: 018_add_screening_tables
Revises: 017_add_candidate_pipeline_features
Create Date: 2026-02-03

This migration creates tables for automated resume screening and triage:
- screening_rules: Per-vacancy screening configuration with thresholds and filters
- screening_results: Historical screening outcomes with tier categorization

These tables enable automated screening that applies rule-based filters, ML scoring
thresholds, and recruiter feedback patterns to categorize candidates into tiers
(High Priority, Review, Reject).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_screening_tables'
down_revision: Union[str, None] = '017_add_candidate_pipeline_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create screening_rules and screening_results tables."""

    # Create screening_rules table
    op.create_table(
        'screening_rules',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to job_vacancies
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Score thresholds
        sa.Column(
            'min_score_threshold',
            sa.Numeric(5, 2),
            nullable=False,
            server_default='50.0',
        ),
        sa.Column(
            'auto_reject_threshold',
            sa.Numeric(5, 2),
            nullable=False,
            server_default='30.0',
        ),
        sa.Column(
            'high_priority_threshold',
            sa.Numeric(5, 2),
            nullable=False,
            server_default='80.0',
        ),
        # Must-have skills (hard filter)
        sa.Column(
            'must_have_skills',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # Auto-rejection settings
        sa.Column(
            'auto_reject_with_notification',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        # Rule management
        sa.Column(
            'rule_priority',
            sa.Numeric(10, 0),
            nullable=False,
            server_default='100',
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            index=True,
        ),
        # Timestamps (inherited from TimestampMixin)
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
        comment='Per-vacancy screening configuration with thresholds and filters',
    )

    # Create indexes for screening_rules
    op.create_index(
        'ix_screening_rules_vacancy_id',
        'screening_rules',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_screening_rules_is_active',
        'screening_rules',
        ['is_active'],
    )
    # Composite index for querying active rules by vacancy
    op.create_index(
        'ix_screening_rules_vacancy_id_is_active',
        'screening_rules',
        ['vacancy_id', 'is_active'],
    )

    # Create screening_results table
    op.create_table(
        'screening_results',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # References to resume, vacancy, and screening rule
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        sa.Column(
            'screening_rule_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('screening_rules.id', ondelete='SET NULL'),
            nullable=True,
        ),
        # Tier categorization
        sa.Column(
            'tier',
            sa.String(20),
            nullable=False,
            index=True,
        ),  # HIGH_PRIORITY, REVIEW, REJECT
        # Score applied during screening
        sa.Column(
            'score_applied',
            sa.Numeric(5, 2),
            nullable=False,
            server_default='0.0',
        ),
        # Rejection details
        sa.Column(
            'rejection_reasons',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # Screening timestamp
        sa.Column(
            'screening_timestamp',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Notification tracking
        sa.Column(
            'auto_response_sent',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        sa.Column(
            'review_reminder_sent',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
        sa.Column(
            'notification_sent_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        # Timestamps (inherited from TimestampMixin)
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
        comment='Historical screening outcomes with tier categorization',
    )

    # Create indexes for screening_results
    op.create_index(
        'ix_screening_results_resume_id',
        'screening_results',
        ['resume_id'],
    )
    op.create_index(
        'ix_screening_results_vacancy_id',
        'screening_results',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_screening_results_tier',
        'screening_results',
        ['tier'],
    )
    # Composite indexes for common query patterns
    op.create_index(
        'ix_screening_results_resume_id_vacancy_id',
        'screening_results',
        ['resume_id', 'vacancy_id'],
    )
    op.create_index(
        'ix_screening_results_vacancy_id_tier',
        'screening_results',
        ['vacancy_id', 'tier'],
    )


def downgrade() -> None:
    """Remove screening_rules and screening_results tables."""

    # Drop screening_results table
    op.drop_index(
        'ix_screening_results_vacancy_id_tier',
        table_name='screening_results',
    )
    op.drop_index(
        'ix_screening_results_resume_id_vacancy_id',
        table_name='screening_results',
    )
    op.drop_index(
        'ix_screening_results_tier',
        table_name='screening_results',
    )
    op.drop_index(
        'ix_screening_results_vacancy_id',
        table_name='screening_results',
    )
    op.drop_index(
        'ix_screening_results_resume_id',
        table_name='screening_results',
    )
    op.drop_table('screening_results')

    # Drop screening_rules table
    op.drop_index(
        'ix_screening_rules_vacancy_id_is_active',
        table_name='screening_rules',
    )
    op.drop_index(
        'ix_screening_rules_is_active',
        table_name='screening_rules',
    )
    op.drop_index(
        'ix_screening_rules_vacancy_id',
        table_name='screening_rules',
    )
    op.drop_table('screening_rules')
