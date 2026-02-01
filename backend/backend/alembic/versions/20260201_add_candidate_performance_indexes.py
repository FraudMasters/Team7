"""Add candidate performance indexes

Revision ID: 017_add_candidate_performance_indexes
Revises: 016_add_workflow_stage_config
Create Date: 2026-02-01

This migration adds composite indexes for optimizing candidate queries:
- hiring_stages(resume_id, vacancy_id) - finding candidate's stage for specific vacancy
- hiring_stages(vacancy_id, stage_name) - filtering candidates by stage for vacancy
- hiring_stages(resume_id, stage_name) - tracking candidate's progression history
- match_results(resume_id, vacancy_id) - finding specific match results
- match_results(vacancy_id, overall_score) - top candidates per vacancy
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '017_add_candidate_performance_indexes'
down_revision: Union[str, None] = '016_add_workflow_stage_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for candidate query optimization."""

    # Indexes for hiring_stages table
    # Composite index for finding a candidate's stage for a specific vacancy
    op.create_index(
        'ix_hiring_stages_resume_id_vacancy_id',
        'hiring_stages',
        ['resume_id', 'vacancy_id'],
    )

    # Composite index for filtering candidates by stage for a vacancy
    # Common query: "Show all candidates in 'interview' stage for vacancy X"
    op.create_index(
        'ix_hiring_stages_vacancy_id_stage_name',
        'hiring_stages',
        ['vacancy_id', 'stage_name'],
    )

    # Composite index for tracking candidate's progression history
    # Common query: "Show all stages candidate X has been through"
    op.create_index(
        'ix_hiring_stages_resume_id_stage_name',
        'hiring_stages',
        ['resume_id', 'stage_name'],
    )

    # Indexes for match_results table
    # Composite index for finding specific match result between resume and vacancy
    # This complements the existing individual indexes
    op.create_index(
        'ix_match_results_resume_id_vacancy_id',
        'match_results',
        ['resume_id', 'vacancy_id'],
    )

    # Composite index for finding top candidates for a vacancy by overall_score
    # Common query: "Show best matching candidates for vacancy X ordered by score"
    op.create_index(
        'ix_match_results_vacancy_id_overall_score',
        'match_results',
        ['vacancy_id', 'overall_score'],
    )


def downgrade() -> None:
    """Remove candidate performance indexes."""

    # Drop match_results indexes
    op.drop_index(
        'ix_match_results_vacancy_id_overall_score',
        table_name='match_results',
    )
    op.drop_index(
        'ix_match_results_resume_id_vacancy_id',
        table_name='match_results',
    )

    # Drop hiring_stages indexes
    op.drop_index(
        'ix_hiring_stages_resume_id_stage_name',
        table_name='hiring_stages',
    )
    op.drop_index(
        'ix_hiring_stages_vacancy_id_stage_name',
        table_name='hiring_stages',
    )
    op.drop_index(
        'ix_hiring_stages_resume_id_vacancy_id',
        table_name='hiring_stages',
    )
