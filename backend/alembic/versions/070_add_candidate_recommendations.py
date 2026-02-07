"""Add AI-powered candidate recommendation tables

Revision ID: 070_add_candidate_recommendations
Revises: 20260201_add_search_performance_indexes
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: Union[str, None] = "070_add_candidate_recommendations"
down_revision: Union[str, None] = "20260201_add_search_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create candidate_recommendations and recommendation_feedback tables."""

    # Create candidate_recommendations table
    op.create_table(
        'candidate_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('score', sa.Numeric(5, 4), nullable=False, default=0.0),
        sa.Column('similarity_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('risk_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('risk_factors', sa.JSON(), nullable=True),
        sa.Column('explanation', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False, default='v1.0'),
        sa.Column('model_type', sa.String(50), nullable=False, default='collaborative_filtering'),
        sa.Column('is_experiment', sa.Boolean(), nullable=False, default=False),
        sa.Column('experiment_group', sa.String(20), nullable=True),
        sa.Column('feature_contributions', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for candidate_recommendations
    op.create_index('ix_candidate_recommendations_resume_id', 'candidate_recommendations', ['resume_id'])
    op.create_index('ix_candidate_recommendations_vacancy_id', 'candidate_recommendations', ['vacancy_id'])
    op.create_index('ix_candidate_recommendations_recommendation_type', 'candidate_recommendations', ['recommendation_type'])
    op.create_index('ix_candidate_recommendations_score', 'candidate_recommendations', ['score'])
    op.create_index('ix_candidate_recommendations_resume_vacancy_type', 'candidate_recommendations', ['resume_id', 'vacancy_id', 'recommendation_type'])

    # Create recommendation_feedback table
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=False, default='implicit'),
        sa.Column('action', sa.String(50), nullable=True),
        sa.Column('was_helpful', sa.Boolean(), nullable=True),
        sa.Column('rating', sa.Numeric(3, 0), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('feedback_source', sa.String(50), nullable=False, default='web_ui'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for recommendation_feedback
    op.create_index('ix_recommendation_feedback_recommendation_id', 'recommendation_feedback', ['recommendation_id'])
    op.create_index('ix_recommendation_feedback_recruiter_id', 'recommendation_feedback', ['recruiter_id'])
    op.create_index('ix_recommendation_feedback_feedback_type', 'recommendation_feedback', ['feedback_type'])


def downgrade() -> None:
    """Drop recommendation tables."""

    # Drop recommendation_feedback table
    op.drop_index('ix_recommendation_feedback_feedback_type', table_name='recommendation_feedback')
    op.drop_index('ix_recommendation_feedback_recruiter_id', table_name='recommendation_feedback')
    op.drop_index('ix_recommendation_feedback_recommendation_id', table_name='recommendation_feedback')
    op.drop_table('recommendation_feedback')

    # Drop candidate_recommendations table
    op.drop_index('ix_candidate_recommendations_resume_vacancy_type', table_name='candidate_recommendations')
    op.drop_index('ix_candidate_recommendations_score', table_name='candidate_recommendations')
    op.drop_index('ix_candidate_recommendations_recommendation_type', table_name='candidate_recommendations')
    op.drop_index('ix_candidate_recommendations_vacancy_id', table_name='candidate_recommendations')
    op.drop_index('ix_candidate_recommendations_resume_id', table_name='candidate_recommendations')
    op.drop_table('candidate_recommendations')
