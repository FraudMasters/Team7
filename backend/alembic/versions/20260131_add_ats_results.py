"""Add ATS results table

Revision ID: 016_add_ats_results
Revises: 013_work_experience
Create Date: 2025-01-31

This migration creates the ats_results table for storing
LLM-based ATS simulation results of resume evaluations against job postings.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '016_add_ats_results'
down_revision: Union[str, None] = '013_work_experience'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ats_results table."""

    op.create_table(
        'ats_results',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign keys
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
        # Pass/Fail status
        sa.Column('passed', sa.Boolean(), nullable=False, default=False, index=True),
        # Overall score
        sa.Column('overall_score', sa.Float(), nullable=False, index=True),
        # Individual scores
        sa.Column('keyword_score', sa.Float(), nullable=True),
        sa.Column('experience_score', sa.Float(), nullable=True),
        sa.Column('education_score', sa.Float(), nullable=True),
        sa.Column('fit_score', sa.Float(), nullable=True),
        # Professional appearance and disqualification
        sa.Column('looks_professional', sa.Boolean(), default=True),
        sa.Column('disqualified', sa.Boolean(), default=False),
        # Issues and feedback (JSON)
        sa.Column('visual_issues', sa.JSON(), nullable=True),
        sa.Column('ats_issues', sa.JSON(), nullable=True),
        sa.Column('missing_keywords', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
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
        comment='LLM-based ATS simulation results for resume evaluation',
    )

    # Create indexes
    op.create_index(
        'ix_ats_results_resume_id',
        'ats_results',
        ['resume_id'],
    )
    op.create_index(
        'ix_ats_results_vacancy_id',
        'ats_results',
        ['vacancy_id'],
    )
    op.create_index(
        'ix_ats_results_passed',
        'ats_results',
        ['passed'],
    )
    op.create_index(
        'ix_ats_results_overall_score',
        'ats_results',
        ['overall_score'],
    )

    # Create composite index for resume-vacancy lookup
    op.create_index(
        'ix_ats_results_resume_vacancy',
        'ats_results',
        ['resume_id', 'vacancy_id'],
        unique=True,
    )


def downgrade() -> None:
    """Drop ats_results table."""

    # Drop indexes
    op.drop_index(
        'ix_ats_results_resume_vacancy',
        'ats_results',
        unique=True,
    )
    op.drop_index(
        'ix_ats_results_overall_score',
        table_name='ats_results',
    )
    op.drop_index(
        'ix_ats_results_passed',
        table_name='ats_results',
    )
    op.drop_index(
        'ix_ats_results_vacancy_id',
        table_name='ats_results',
    )
    op.drop_index(
        'ix_ats_results_resume_id',
        table_name='ats_results',
    )

    # Drop table
    op.drop_table('ats_results')
