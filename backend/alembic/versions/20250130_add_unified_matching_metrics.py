"""Add unified matching metrics to match_results

Revision ID: 20250130_add_unified_matching_metrics
Revises: 20250129_add_resume_analysis_table
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '010_add_unified_metrics'
down_revision = '20250129_add_resume_analysis'
branch_labels = None
depends_on = None


def upgrade():
    """Add unified matching metrics columns to match_results table."""
    # Add new columns for unified matching metrics
    op.add_column('match_results', sa.Column('overall_score', sa.Numeric(5, 4), nullable=True))
    op.add_column('match_results', sa.Column('keyword_score', sa.Numeric(5, 4), nullable=True))
    op.add_column('match_results', sa.Column('tfidf_score', sa.Numeric(5, 4), nullable=True))
    op.add_column('match_results', sa.Column('vector_score', sa.Numeric(5, 4), nullable=True))
    op.add_column('match_results', sa.Column('vector_similarity', sa.Numeric(5, 4), nullable=True))
    op.add_column('match_results', sa.Column('recommendation', sa.String(20), nullable=True))
    op.add_column('match_results', sa.Column('keyword_passed', sa.Boolean(), nullable=True))
    op.add_column('match_results', sa.Column('tfidf_passed', sa.Boolean(), nullable=True))
    op.add_column('match_results', sa.Column('vector_passed', sa.Boolean(), nullable=True))
    op.add_column('match_results', sa.Column('tfidf_matched', sa.JSON(), nullable=True))
    op.add_column('match_results', sa.Column('tfidf_missing', sa.JSON(), nullable=True))
    op.add_column('match_results', sa.Column('matcher_version', sa.String(50), nullable=True, server_default='unified-v1'))

    # Create index on resume_id and vacancy_id composite for faster lookups
    op.create_index(
        'ix_match_results_resume_vacancy',
        'match_results',
        ['resume_id', 'vacancy_id'],
        unique=False
    )

    # Create index on overall_score for ranking
    op.create_index(
        'ix_match_results_overall_score',
        'match_results',
        ['overall_score'],
        unique=False
    )


def downgrade():
    """Remove unified matching metrics columns."""
    # Drop indexes
    op.drop_index('ix_match_results_overall_score', table_name='match_results')
    op.drop_index('ix_match_results_resume_vacancy', table_name='match_results')

    # Drop columns
    op.drop_column('match_results', 'matcher_version')
    op.drop_column('match_results', 'tfidf_missing')
    op.drop_column('match_results', 'tfidf_matched')
    op.drop_column('match_results', 'vector_passed')
    op.drop_column('match_results', 'tfidf_passed')
    op.drop_column('match_results', 'keyword_passed')
    op.drop_column('match_results', 'recommendation')
    op.drop_column('match_results', 'vector_similarity')
    op.drop_column('match_results', 'vector_score')
    op.drop_column('match_results', 'tfidf_score')
    op.drop_column('match_results', 'keyword_score')
    op.drop_column('match_results', 'overall_score')
