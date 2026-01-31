"""Add candidate pipeline features tables

Revision ID: 017_add_candidate_pipeline_features
Revises: 016_add_workflow_stage_config
Create Date: 2026-01-31

This migration creates tables for candidate tagging, notes, and activity tracking:
- candidate_tags: Custom tags for categorizing and prioritizing candidates
- candidate_notes: Collaborative notes and comments on candidates
- candidate_activities: Audit trail of all candidate-related activities

These features enable visual pipeline management, team collaboration, and
comprehensive activity tracking for candidates throughout the hiring process.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '017_add_candidate_pipeline_features'
down_revision: Union[str, None] = '016_add_workflow_stage_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create candidate_tags, candidate_notes, and candidate_activities tables."""

    # Create candidate_tags table
    op.create_table(
        'candidate_tags',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to organizations
        sa.Column(
            'organization_id',
            sa.String(),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Tag configuration
        sa.Column('tag_name', sa.String(100), nullable=False, index=True),
        sa.Column('tag_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        # UI customization
        sa.Column('color', sa.String(7), nullable=True),  # Hex color code
        sa.Column('description', sa.String(500), nullable=True),
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
        comment='Custom tags for categorizing and prioritizing candidates',
    )

    # Create indexes for candidate_tags
    op.create_index(
        'ix_candidate_tags_organization_id',
        'candidate_tags',
        ['organization_id'],
    )
    op.create_index(
        'ix_candidate_tags_tag_name',
        'candidate_tags',
        ['tag_name'],
    )

    # Create candidate_notes table
    op.create_table(
        'candidate_notes',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to resumes
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Optional foreign key to recruiters (author)
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Note content
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='false', index=True),
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
        comment='Collaborative notes and comments on candidates',
    )

    # Create indexes for candidate_notes
    op.create_index(
        'ix_candidate_notes_resume_id',
        'candidate_notes',
        ['resume_id'],
    )
    op.create_index(
        'ix_candidate_notes_recruiter_id',
        'candidate_notes',
        ['recruiter_id'],
    )
    op.create_index(
        'ix_candidate_notes_is_private',
        'candidate_notes',
        ['is_private'],
    )

    # Create candidate_activities table
    op.create_table(
        'candidate_activities',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Activity type and candidate reference
        sa.Column('activity_type', sa.String(50), nullable=False, index=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        # Optional vacancy reference
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Stage change tracking
        sa.Column('from_stage', sa.String(100), nullable=True),
        sa.Column('to_stage', sa.String(100), nullable=True, index=True),
        # Optional foreign keys to related entities
        sa.Column(
            'note_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('candidate_notes.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'tag_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('candidate_tags.id', ondelete='SET NULL'),
            nullable=True,
        ),
        # Recruiter who performed the action
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Additional activity data
        sa.Column('activity_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
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
        comment='Audit trail of all candidate-related activities',
    )

    # Create indexes for candidate_activities
    op.create_index(
        'ix_candidate_activities_activity_type',
        'candidate_activities',
        ['activity_type'],
    )
    op.create_index(
        'ix_candidate_activities_candidate_id',
        'candidate_activities',
        ['candidate_id'],
    )
    op.create_index(
        'ix_candidate_activities_vacancy_id',
        'candidate_activities',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_candidate_activities_to_stage',
        'candidate_activities',
        ['to_stage'],
    )
    op.create_index(
        'ix_candidate_activities_recruiter_id',
        'candidate_activities',
        ['recruiter_id'],
    )


def downgrade() -> None:
    """Remove candidate_tags, candidate_notes, and candidate_activities tables."""

    # Drop candidate_activities table
    op.drop_index(
        'ix_candidate_activities_recruiter_id',
        table_name='candidate_activities',
    )
    op.drop_index(
        'ix_candidate_activities_to_stage',
        table_name='candidate_activities',
    )
    op.drop_index(
        'ix_candidate_activities_vacancy_id',
        table_name='candidate_activities',
    )
    op.drop_index(
        'ix_candidate_activities_candidate_id',
        table_name='candidate_activities',
    )
    op.drop_index(
        'ix_candidate_activities_activity_type',
        table_name='candidate_activities',
    )
    op.drop_table('candidate_activities')

    # Drop candidate_notes table
    op.drop_index(
        'ix_candidate_notes_is_private',
        table_name='candidate_notes',
    )
    op.drop_index(
        'ix_candidate_notes_recruiter_id',
        table_name='candidate_notes',
    )
    op.drop_index(
        'ix_candidate_notes_resume_id',
        table_name='candidate_notes',
    )
    op.drop_table('candidate_notes')

    # Drop candidate_tags table
    op.drop_index(
        'ix_candidate_tags_tag_name',
        table_name='candidate_tags',
    )
    op.drop_index(
        'ix_candidate_tags_organization_id',
        table_name='candidate_tags',
    )
    op.drop_table('candidate_tags')
