"""Add bulk action fields to job_vacancies table

Revision ID: 20260203_add_vacancy_bulk_fields
Revises: 018_add_audit_logs
Create Date: 2026-02-03

This migration adds fields to support bulk operations on job vacancies:
- is_active: Boolean flag for vacancy status (active/inactive)
- organization_id: Foreign key to organizations table for assignment

These fields enable bulk status updates and bulk organization assignment
functionality in the vacancies bulk actions feature.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260203_add_vacancy_bulk_fields'
down_revision: Union[str, None] = '018_add_audit_logs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active and organization_id columns to job_vacancies table."""

    # Add is_active column
    # Default to True for existing vacancies (assume active)
    op.add_column(
        'job_vacancies',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )

    # Add index for is_active to optimize filtering queries
    op.create_index(
        op.f('ix_job_vacancies_is_active'),
        'job_vacancies',
        ['is_active'],
    )

    # Add organization_id column as a foreign key
    # Nullable to allow vacancies without organization
    op.add_column(
        'job_vacancies',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='SET NULL'),
            nullable=True
        )
    )

    # Add index for organization_id to optimize filtering queries
    op.create_index(
        op.f('ix_job_vacancies_organization_id'),
        'job_vacancies',
        ['organization_id'],
    )


def downgrade() -> None:
    """Remove is_active and organization_id columns from job_vacancies table."""

    # Drop organization_id index and column
    op.drop_index(
        op.f('ix_job_vacancies_organization_id'),
        table_name='job_vacancies',
    )
    op.drop_column('job_vacancies', 'organization_id')

    # Drop is_active index and column
    op.drop_index(
        op.f('ix_job_vacancies_is_active'),
        table_name='job_vacancies',
    )
    op.drop_column('job_vacancies', 'is_active')
