"""add resume_feedbacks table

Revision ID: 020_add_resume_feedback
Revises: 019_create_interview_tables
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '020_add_resume_feedback'
down_revision: Union[str, None] = '019_create_interview_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resume_feedbacks table
    op.create_table(
        'resume_feedbacks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resume_id', sa.UUID(), nullable=False),
        sa.Column('target_job_description', sa.Text(), nullable=True),
        sa.Column('suggestions', postgresql.JSON(), nullable=True),
        sa.Column('total_suggestions', sa.Integer(), nullable=True),
        sa.Column('high_priority_count', sa.Integer(), nullable=True),
        sa.Column('medium_priority_count', sa.Integer(), nullable=True),
        sa.Column('low_priority_count', sa.Integer(), nullable=True),
        sa.Column('keywords_found', postgresql.JSON(), nullable=True),
        sa.Column('missing_keywords', postgresql.JSON(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('analyzer_version', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id')
    )
    op.create_index(op.f('ix_resume_feedbacks_resume_id'), 'resume_feedbacks', ['resume_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_feedbacks_resume_id'), table_name='resume_feedbacks')
    op.drop_table('resume_feedbacks')
