"""Add interview preparation table

Revision ID: 018_add_interview_prep
Revises: 016_add_workflow_stage_config
Create Date: 2026-02-01

This migration creates the interview_preps table for storing generated
interview questions based on resume and job vacancy analysis.
- interview_preps: AI-generated interview questions and prep materials

The feature enables automatic generation of technical, behavioral, and
situational interview questions customized to each candidate's background
and the job requirements.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_interview_prep'
down_revision: Union[str, None] = '016_add_workflow_stage_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create interview_preps table."""

    # Create interview_preps table
    op.create_table(
        'interview_preps',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign keys to resumes and job vacancies
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
        # Generated questions by category
        sa.Column(
            'technical_questions',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'behavioral_questions',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'situational_questions',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'skill_verification_topics',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            'areas_to_probe',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # Custom questions added by recruiters
        sa.Column(
            'custom_questions',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # Feedback on question usefulness
        sa.Column(
            'question_feedback',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # Metadata
        sa.Column('provider', sa.Text(), nullable=True),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
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
        comment='AI-generated interview questions and preparation materials',
    )

    # Create indexes for interview_preps
    op.create_index(
        'ix_interview_preps_resume_id',
        'interview_preps',
        ['resume_id'],
    )
    op.create_index(
        'ix_interview_preps_vacancy_id',
        'interview_preps',
        ['vacancy_id'],
    )


def downgrade() -> None:
    """Remove interview_preps table."""

    # Drop indexes
    op.drop_index(
        'ix_interview_preps_vacancy_id',
        table_name='interview_preps',
    )
    op.drop_index(
        'ix_interview_preps_resume_id',
        table_name='interview_preps',
    )

    # Drop table
    op.drop_table('interview_preps')
