"""add optimization enhancement fields to resume_feedbacks

Revision ID: 20260322_add_optimization_enhancements
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

Adds enhancement fields to resume_feedbacks table:
- completeness_score: Resume completeness score (0-100)
- ats_score: ATS compatibility score (0-100)
- ranking_prediction: Before/after ranking prediction (JSON)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260322_add_optimization_enhancements'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add optimization enhancement fields to resume_feedbacks table
    op.add_column('resume_feedbacks', sa.Column('completeness_score', sa.Integer(), nullable=True))
    op.add_column('resume_feedbacks', sa.Column('ats_score', sa.Integer(), nullable=True))
    op.add_column('resume_feedbacks', sa.Column('ranking_prediction', postgresql.JSON(), nullable=True))


def downgrade() -> None:
    # Remove optimization enhancement fields from resume_feedbacks table
    op.drop_column('resume_feedbacks', 'ranking_prediction')
    op.drop_column('resume_feedbacks', 'ats_score')
    op.drop_column('resume_feedbacks', 'completeness_score')
