"""Add AI-powered candidate ranking tables

Revision ID: 011_add_candidate_ranking
Revises: 010_add_unified_metrics
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '011_add_candidate_ranking'
down_revision = '010_add_unified_metrics'
branch_labels = None
depends_on = None


def upgrade():
    """Create candidate_ranks and ranking_feedback tables."""

    # Create candidate_ranks table
    op.create_table(
        'candidate_ranks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resume_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vacancy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('job_vacancies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank_score', sa.Numeric(5, 4), nullable=False, default=0.0),
        sa.Column('rank_position', sa.Numeric(10, 0), nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False, default='v1.0'),
        sa.Column('model_type', sa.String(50), nullable=False, default='random_forest'),
        sa.Column('is_experiment', sa.Boolean(), nullable=False, default=False),
        sa.Column('experiment_group', sa.String(20), nullable=True),
        sa.Column('feature_contributions', sa.JSON(), nullable=True),
        sa.Column('ranking_factors', sa.JSON(), nullable=True),
        sa.Column('prediction_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('recommendation', sa.String(20), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for candidate_ranks
    op.create_index('ix_candidate_ranks_resume_id', 'candidate_ranks', ['resume_id'])
    op.create_index('ix_candidate_ranks_vacancy_id', 'candidate_ranks', ['vacancy_id'])
    op.create_index('ix_candidate_ranks_rank_score', 'candidate_ranks', ['rank_score'])
    op.create_index('ix_candidate_ranks_resume_vacancy', 'candidate_ranks', ['resume_id', 'vacancy_id'])

    # Create ranking_feedback table
    op.create_table(
        'ranking_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rank_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidate_ranks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recruiter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recruiters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=False, default='thumbs'),
        sa.Column('was_helpful', sa.Boolean(), nullable=True),
        sa.Column('actual_outcome', sa.String(50), nullable=True),
        sa.Column('adjusted_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('rating', sa.Numeric(3, 0), nullable=True),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('feedback_source', sa.String(50), nullable=False, default='web_ui'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for ranking_feedback
    op.create_index('ix_ranking_feedback_rank_id', 'ranking_feedback', ['rank_id'])
    op.create_index('ix_ranking_feedback_recruiter_id', 'ranking_feedback', ['recruiter_id'])


def downgrade():
    """Drop ranking tables."""

    # Drop ranking_feedback table
    op.drop_index('ix_ranking_feedback_recruiter_id', table_name='ranking_feedback')
    op.drop_index('ix_ranking_feedback_rank_id', table_name='ranking_feedback')
    op.drop_table('ranking_feedback')

    # Drop candidate_ranks table
    op.drop_index('ix_candidate_ranks_resume_vacancy', table_name='candidate_ranks')
    op.drop_index('ix_candidate_ranks_rank_score', table_name='candidate_ranks')
    op.drop_index('ix_candidate_ranks_vacancy_id', table_name='candidate_ranks')
    op.drop_index('ix_candidate_ranks_resume_id', table_name='candidate_ranks')
    op.drop_table('candidate_ranks')
