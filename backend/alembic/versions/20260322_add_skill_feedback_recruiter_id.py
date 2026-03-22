"""add recruiter_id to skill_feedback table

Revision ID: 20260322_add_skill_feedback_recruiter_id
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260322_add_skill_feedback_recruiter_id'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add recruiter_id column to skill_feedback table
    op.add_column(
        'skill_feedback',
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        )
    )
    op.create_index(
        op.f('ix_skill_feedback_recruiter_id'),
        'skill_feedback',
        ['recruiter_id']
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_skill_feedback_recruiter_id'), table_name='skill_feedback')
    op.drop_column('skill_feedback', 'recruiter_id')
