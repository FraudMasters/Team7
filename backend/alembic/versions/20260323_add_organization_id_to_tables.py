"""
Add organization_id to tables and fix type mismatches

Revision ID: 20260323_add_organization_id_to_tables
Revises: 20260322_add_agency_multi_tenant
Create Date: 2026-03-23

This migration fixes organization_id column types and adds missing columns:
1. Alters organization_id from UUID to String(100) in resumes table
2. Alters organization_id from UUID to String(100) in job_vacancies table
3. Adds organization_id as String(100) to candidate_ranks table

The type change is necessary because Organization.id is String(100), not UUID.
For existing data: UUID values will need to be converted to strings during migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260323_add_organization_id_to_tables"
down_revision: Union[str, None] = "20260322_add_agency_multi_tenant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix organization_id columns and add missing ones."""

    # Step 1: Drop foreign key constraints and indexes for resumes.organization_id
    op.drop_constraint(
        "resumes_organization_id_fkey",
        "resumes",
        type_="foreignkey"
    )
    op.drop_index(op.f("ix_resumes_organization_id"), table_name="resumes")

    # Step 2: Alter column type from UUID to String(100) for resumes
    op.alter_column(
        "resumes",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(100),
        existing_nullable=True,
        postgresql_using="organization_id::text"
    )

    # Step 3: Recreate foreign key and index for resumes
    op.create_foreign_key(
        "resumes_organization_id_fkey",
        "resumes",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE"
    )
    op.create_index(
        op.f("ix_resumes_organization_id"),
        "resumes",
        ["organization_id"]
    )

    # Step 4: Drop foreign key constraints and indexes for job_vacancies.organization_id
    op.drop_constraint(
        "job_vacancies_organization_id_fkey",
        "job_vacancies",
        type_="foreignkey"
    )
    op.drop_index(op.f("ix_job_vacancies_organization_id"), table_name="job_vacancies")

    # Step 5: Alter column type from UUID to String(100) for job_vacancies
    op.alter_column(
        "job_vacancies",
        "organization_id",
        existing_type=postgresql.UUID(as_uuid=True),
        type_=sa.String(100),
        existing_nullable=True,
        postgresql_using="organization_id::text"
    )

    # Step 6: Recreate foreign key and index for job_vacancies
    op.create_foreign_key(
        "job_vacancies_organization_id_fkey",
        "job_vacancies",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL"
    )
    op.create_index(
        op.f("ix_job_vacancies_organization_id"),
        "job_vacancies",
        ["organization_id"]
    )

    # Step 7: Add organization_id to candidate_ranks table
    op.add_column(
        "candidate_ranks",
        sa.Column(
            "organization_id",
            sa.String(100),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
            comment="Organization that owns this ranking"
        )
    )
    op.create_index(
        op.f("ix_candidate_ranks_organization_id"),
        "candidate_ranks",
        ["organization_id"]
    )


def downgrade() -> None:
    """Revert organization_id changes."""

    # Step 1: Remove organization_id from candidate_ranks
    op.drop_index(
        op.f("ix_candidate_ranks_organization_id"),
        table_name="candidate_ranks"
    )
    op.drop_column("candidate_ranks", "organization_id")

    # Step 2: Drop foreign key and index for job_vacancies.organization_id
    op.drop_constraint(
        "job_vacancies_organization_id_fkey",
        "job_vacancies",
        type_="foreignkey"
    )
    op.drop_index(op.f("ix_job_vacancies_organization_id"), table_name="job_vacancies")

    # Step 3: Alter column type back to UUID for job_vacancies
    op.alter_column(
        "job_vacancies",
        "organization_id",
        existing_type=sa.String(100),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=True,
        postgresql_using="organization_id::uuid"
    )

    # Step 4: Recreate foreign key and index for job_vacancies
    op.create_foreign_key(
        "job_vacancies_organization_id_fkey",
        "job_vacancies",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE"
    )
    op.create_index(
        op.f("ix_job_vacancies_organization_id"),
        "job_vacancies",
        ["organization_id"]
    )

    # Step 5: Drop foreign key and index for resumes.organization_id
    op.drop_constraint(
        "resumes_organization_id_fkey",
        "resumes",
        type_="foreignkey"
    )
    op.drop_index(op.f("ix_resumes_organization_id"), table_name="resumes")

    # Step 6: Alter column type back to UUID for resumes
    op.alter_column(
        "resumes",
        "organization_id",
        existing_type=sa.String(100),
        type_=postgresql.UUID(as_uuid=True),
        existing_nullable=True,
        postgresql_using="organization_id::uuid"
    )

    # Step 7: Recreate foreign key and index for resumes
    op.create_foreign_key(
        "resumes_organization_id_fkey",
        "resumes",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE"
    )
    op.create_index(
        op.f("ix_resumes_organization_id"),
        "resumes",
        ["organization_id"]
    )
