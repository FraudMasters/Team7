"""Add salary fields to job_vacancies table

Revision ID: add_salary_to_vacancies
Revises:
Create Date: 2026-01-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_salary_to_vacancies'
down_revision: Union[str, None] = '009_add_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add salary_min, salary_max, english_level, employment_type columns."""
    # Add salary_min column
    op.add_column(
        'job_vacancies',
        sa.Column('salary_min', sa.Integer(), nullable=True)
    )

    # Add salary_max column
    op.add_column(
        'job_vacancies',
        sa.Column('salary_max', sa.Integer(), nullable=True)
    )

    # Add english_level column
    op.add_column(
        'job_vacancies',
        sa.Column('english_level', sa.String(length=50), nullable=True)
    )

    # Add employment_type column
    op.add_column(
        'job_vacancies',
        sa.Column('employment_type', sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    """Remove salary columns."""
    op.drop_column('job_vacancies', 'employment_type')
    op.drop_column('job_vacancies', 'english_level')
    op.drop_column('job_vacancies', 'salary_max')
    op.drop_column('job_vacancies', 'salary_min')
