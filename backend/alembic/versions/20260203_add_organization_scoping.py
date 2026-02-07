"""add organization scoping to existing tables

Revision ID: 20260203_add_organization_scoping
Revises: 20260203_add_organizations
Create Date: 2026-02-03

This migration adds organization_id foreign key columns to existing tables
to enable multi-tenant data isolation. Tables affected:
- resumes: Link resumes to organizations
- job_vacancies: Link job vacancies to organizations
- skill_taxonomies: Link skill taxonomies to organizations

Note: workflow_stage_configs already has organization_id from its initial migration.

For existing data: A data migration script should be run to associate
existing records with appropriate organizations before making these columns
non-nullable in a future migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260203_add_organization_scoping'
down_revision: Union[str, None] = '20260203_add_organizations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add organization_id to resumes table
    op.add_column(
        'resumes',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=True,
            comment='Organization that owns this resume'
        )
    )
    op.create_index(
        op.f('ix_resumes_organization_id'),
        'resumes',
        ['organization_id']
    )

    # Add organization_id to job_vacancies table
    op.add_column(
        'job_vacancies',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=True,
            comment='Organization that owns this job vacancy'
        )
    )
    op.create_index(
        op.f('ix_job_vacancies_organization_id'),
        'job_vacancies',
        ['organization_id']
    )

    # Add organization_id to skill_taxonomies table
    op.add_column(
        'skill_taxonomies',
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id', ondelete='CASCADE'),
            nullable=True,
            comment='Organization that owns this taxonomy entry'
        )
    )
    op.create_index(
        op.f('ix_skill_taxonomies_organization_id'),
        'skill_taxonomies',
        ['organization_id']
    )


def downgrade() -> None:
    # Remove organization_id from skill_taxonomies
    op.drop_index(
        op.f('ix_skill_taxonomies_organization_id'),
        table_name='skill_taxonomies'
    )
    op.drop_column('skill_taxonomies', 'organization_id')

    # Remove organization_id from job_vacancies
    op.drop_index(
        op.f('ix_job_vacancies_organization_id'),
        table_name='job_vacancies'
    )
    op.drop_column('job_vacancies', 'organization_id')

    # Remove organization_id from resumes
    op.drop_index(
        op.f('ix_resumes_organization_id'),
        table_name='resumes'
    )
    op.drop_column('resumes', 'organization_id')
