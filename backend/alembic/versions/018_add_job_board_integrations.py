"""Add job board integration tables

Revision ID: 018_add_job_board_integrations
Revises: 017_add_candidate_pipeline_features
Create Date: 2026-02-03

This migration creates tables for job board integrations and resume importing:
- job_board_integrations: Configuration for external job board API connections
- imported_resumes: Tracking of resumes imported from job boards
- import_logs: Audit trail of import operations and failures

These features enable automatic resume aggregation from multiple job boards
(Indeed, ZipRecruiter, Glassdoor), webhook-based submissions, and
comprehensive import tracking with retry capability.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_job_board_integrations'
down_revision: Union[str, None] = '017_add_candidate_pipeline_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create job_board_integrations, imported_resumes, and import_logs tables."""

    # Create job_board_integrations table
    op.create_table(
        'job_board_integrations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Job board configuration
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('api_endpoint', sa.String(500), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        # Additional configuration as JSON (filters, sync settings, etc.)
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Sync tracking
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        # Timestamps (inherited from TimestampMixin)
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
        comment='Configuration for external job board API connections',
    )

    # Create indexes for job_board_integrations
    op.create_index(
        'ix_job_board_integrations_name',
        'job_board_integrations',
        ['name'],
    )

    # Create imported_resumes table
    op.create_table(
        'imported_resumes',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Foreign key to resumes (the actual resume record)
        sa.Column(
            'resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resumes.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # Foreign key to job_board_integrations (the source)
        sa.Column(
            'job_board_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_board_integrations.id', ondelete='CASCADE'),
            nullable=False,
            index=True,
        ),
        # External system tracking
        sa.Column('external_id', sa.String(255), nullable=True, index=True),
        sa.Column('source_url', sa.String(1000), nullable=True),
        # Import status tracking
        sa.Column(
            'import_status',
            sa.Enum('PENDING', 'COMPLETED', 'FAILED', 'SKIPPED', 'SYNCED', name='importstatus'),
            nullable=False,
            index=True,
            server_default='PENDING',
        ),
        sa.Column('error_message', sa.Text(), nullable=True),
        # Data from job board (JSONB for efficient querying)
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('candidate_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Candidate information for quick access
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('candidate_name', sa.String(255), nullable=True),
        sa.Column('candidate_email', sa.String(255), nullable=True),
        sa.Column('candidate_phone', sa.String(50), nullable=True),
        # Status and sync tracking
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_synced_at', sa.String(50), nullable=True),
        # Timestamps (inherited from TimestampMixin)
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
        comment='Tracking of resumes imported from job boards',
    )

    # Create indexes for imported_resumes
    op.create_index(
        'ix_imported_resumes_resume_id',
        'imported_resumes',
        ['resume_id'],
    )
    op.create_index(
        'ix_imported_resumes_job_board_id',
        'imported_resumes',
        ['job_board_id'],
    )
    op.create_index(
        'ix_imported_resumes_external_id',
        'imported_resumes',
        ['external_id'],
    )
    op.create_index(
        'ix_imported_resumes_import_status',
        'imported_resumes',
        ['import_status'],
    )

    # Create import_logs table
    op.create_table(
        'import_logs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Optional foreign keys (nullable because logs can exist without entities)
        sa.Column(
            'job_board_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('job_board_integrations.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        sa.Column(
            'imported_resume_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('imported_resumes.id', ondelete='SET NULL'),
            nullable=True,
            index=True,
        ),
        # Import job status
        sa.Column(
            'status',
            sa.String(50),
            nullable=False,
            index=True,
            server_default='in_progress',
        ),
        # Record counts
        sa.Column('records_processed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('records_succeeded', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('records_failed', sa.Integer(), nullable=True, server_default='0'),
        # Error tracking
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Additional metadata
        sa.Column('import_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # Timing information
        sa.Column('started_at', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.String(50), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
        # Timestamps (inherited from TimestampMixin)
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
        comment='Audit trail of import operations and failures',
    )

    # Create indexes for import_logs
    op.create_index(
        'ix_import_logs_job_board_id',
        'import_logs',
        ['job_board_id'],
    )
    op.create_index(
        'ix_import_logs_imported_resume_id',
        'import_logs',
        ['imported_resume_id'],
    )
    op.create_index(
        'ix_import_logs_status',
        'import_logs',
        ['status'],
    )


def downgrade() -> None:
    """Remove job_board_integrations, imported_resumes, and import_logs tables."""

    # Drop import_logs table
    op.drop_index(
        'ix_import_logs_status',
        table_name='import_logs',
    )
    op.drop_index(
        'ix_import_logs_imported_resume_id',
        table_name='import_logs',
    )
    op.drop_index(
        'ix_import_logs_job_board_id',
        table_name='import_logs',
    )
    op.drop_table('import_logs')

    # Drop imported_resumes table
    op.drop_index(
        'ix_imported_resumes_import_status',
        table_name='imported_resumes',
    )
    op.drop_index(
        'ix_imported_resumes_external_id',
        table_name='imported_resumes',
    )
    op.drop_index(
        'ix_imported_resumes_job_board_id',
        table_name='imported_resumes',
    )
    op.drop_index(
        'ix_imported_resumes_resume_id',
        table_name='imported_resumes',
    )
    # Drop Enum type for import_status
    op.execute('DROP TYPE IF EXISTS importstatus')
    op.drop_table('imported_resumes')

    # Drop job_board_integrations table
    op.drop_index(
        'ix_job_board_integrations_name',
        table_name='job_board_integrations',
    )
    op.drop_table('job_board_integrations')
