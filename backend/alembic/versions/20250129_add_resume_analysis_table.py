"""add resume_analysis table

Revision ID: 20250129_add_resume_analysis
Revises: 20250126_add_salary_to_vacancies
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250129_add_resume_analysis'
down_revision: Union[str, None] = 'add_salary_to_vacancies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create resume_analyses table
    op.create_table(
        'resume_analyses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resume_id', sa.UUID(), nullable=False),
        sa.Column('language', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('skills', postgresql.JSON(), nullable=True),
        sa.Column('keywords', postgresql.JSON(), nullable=True),
        sa.Column('entities', postgresql.JSON(), nullable=True),
        sa.Column('total_experience_months', sa.Integer(), nullable=True),
        sa.Column('education', postgresql.JSON(), nullable=True),
        sa.Column('contact_info', postgresql.JSON(), nullable=True),
        sa.Column('grammar_issues', postgresql.JSON(), nullable=True),
        sa.Column('warnings', postgresql.JSON(), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('analyzer_version', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id')
    )
    op.create_index(op.f('ix_resume_analyses_resume_id'), 'resume_analyses', ['resume_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_resume_analyses_resume_id'), table_name='resume_analyses')
    op.drop_table('resume_analyses')
