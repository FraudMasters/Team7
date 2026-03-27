"""Add import_jobs table

Revision ID: 018_add_import_jobs
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-21

This migration creates the import_jobs table for tracking data import
operations from various formats including LinkedIn CSV, Indeed XML, HR-XML,
and ATS platform migrations (Greenhouse, Lever, Workable).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_import_jobs'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create import_jobs table."""

    # Create import_jobs table
    op.create_table(
        'import_jobs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.Enum(
                'PENDING',
                'IN_PROGRESS',
                'COMPLETED',
                'FAILED',
                'CANCELLED',
                'PARTIALLY_COMPLETED',
                name='importjobstatus',
                inherit_schema=True,
            ),
            nullable=False,
            default='PENDING',
        ),
        sa.Column(
            'format',
            sa.Enum(
                'LINKEDIN_CSV',
                'INDEED_XML',
                'HRXML',
                'GREENHOUSE',
                'LEVER',
                'WORKABLE',
                'CUSTOM_JSON',
                'CUSTOM_CSV',
                name='importformat',
                inherit_schema=True,
            ),
            nullable=False,
        ),
        sa.Column(
            'recruiter_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('recruiters.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'vacancy_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_vacancies.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('successful_imports', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_imports', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_records', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('import_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_system', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        comment='Import job tracking table for data import operations from various formats',
    )

    # Create indexes for import_jobs
    op.create_index('ix_import_jobs_status', 'import_jobs', ['status'])
    op.create_index('ix_import_jobs_format', 'import_jobs', ['format'])
    op.create_index('ix_import_jobs_recruiter_id', 'import_jobs', ['recruiter_id'])
    op.create_index('ix_import_jobs_vacancy_id', 'import_jobs', ['vacancy_id'])


def downgrade() -> None:
    """Drop import_jobs table."""

    # Drop indexes (use try/except to handle missing indexes)
    try:
        op.drop_index('ix_import_jobs_vacancy_id', table_name='import_jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_import_jobs_recruiter_id', table_name='import_jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_import_jobs_format', table_name='import_jobs')
    except Exception:
        pass
    try:
        op.drop_index('ix_import_jobs_status', table_name='import_jobs')
    except Exception:
        pass

    # Drop table
    try:
        op.drop_table('import_jobs')
    except Exception:
        pass

    # Drop enums
    op.execute('DROP TYPE IF EXISTS importjobstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS importformat CASCADE')
