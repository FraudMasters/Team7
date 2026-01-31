"""add work_experiences table

Revision ID: 013_work_experience
Revises: 010_add_unified_metrics
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013_work_experience'
down_revision: Union[str, None] = '010_add_unified_metrics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create work_experiences table
    op.create_table(
        'work_experiences',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resume_id', sa.UUID(), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_experiences_resume_id'), 'work_experiences', ['resume_id'], unique=False)
    op.create_index(op.f('ix_work_experiences_start_date'), 'work_experiences', ['start_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_work_experiences_start_date'), table_name='work_experiences')
    op.drop_index(op.f('ix_work_experiences_resume_id'), table_name='work_experiences')
    op.drop_table('work_experiences')
