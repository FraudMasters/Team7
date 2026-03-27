"""add resume source field

Revision ID: 20260322_add_resume_source
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

This migration adds a source field to the resumes table to track
the origin of each resume (linkedin, direct_application, referral, etc.)
for sourcing analytics and attribution tracking.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260322_add_resume_source'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source column to resumes table
    op.add_column(
        'resumes',
        sa.Column(
            'source',
            sa.String(50),
            nullable=True,
            comment='Source of the resume (linkedin, direct_application, referral, etc.)'
        )
    )
    op.create_index(
        op.f('ix_resumes_source'),
        'resumes',
        ['source']
    )


def downgrade() -> None:
    # Remove source column and index
    op.drop_index(
        op.f('ix_resumes_source'),
        table_name='resumes'
    )
    op.drop_column('resumes', 'source')
