"""Add migrations table

Revision ID: 019_add_migrations
Revises: 018_add_import_jobs
Create Date: 2026-03-21

This migration creates the migrations table for tracking data migration
operations between ATS systems including migrations from Greenhouse, Lever,
Workable, and other platforms to AgentHR.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_add_migrations'
down_revision: Union[str, None] = '018_add_import_jobs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create migrations table."""

    # Create migrations table
    op.create_table(
        'migrations',
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
                name='migrationstatus',
                inherit_schema=True,
            ),
            nullable=False,
            default='PENDING',
        ),
        sa.Column(
            'migration_type',
            sa.Enum(
                'FULL_MIGRATION',
                'PARTIAL_MIGRATION',
                'DATA_SYNC',
                'SYSTEM_UPGRADE',
                name='migrationtype',
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
        sa.Column('source_system', sa.String(100), nullable=False),
        sa.Column('target_system', sa.String(100), nullable=False, default='AgentHR'),
        sa.Column('source_system_version', sa.String(50), nullable=True),
        sa.Column('total_records', sa.Integer(), nullable=True),
        sa.Column('successful_migrations', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_migrations', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_records', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('migration_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_errors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('entity_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.String(50), nullable=True),
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
        comment='Migration tracking table for data migration operations between ATS systems',
    )

    # Create indexes for migrations
    op.create_index('ix_migrations_status', 'migrations', ['status'])
    op.create_index('ix_migrations_migration_type', 'migrations', ['migration_type'])
    op.create_index('ix_migrations_recruiter_id', 'migrations', ['recruiter_id'])
    op.create_index('ix_migrations_source_system', 'migrations', ['source_system'])


def downgrade() -> None:
    """Drop migrations table."""

    # Drop indexes (use try/except to handle missing indexes)
    try:
        op.drop_index('ix_migrations_source_system', table_name='migrations')
    except Exception:
        pass
    try:
        op.drop_index('ix_migrations_recruiter_id', table_name='migrations')
    except Exception:
        pass
    try:
        op.drop_index('ix_migrations_migration_type', table_name='migrations')
    except Exception:
        pass
    try:
        op.drop_index('ix_migrations_status', table_name='migrations')
    except Exception:
        pass

    # Drop table
    try:
        op.drop_table('migrations')
    except Exception:
        pass

    # Drop enums
    op.execute('DROP TYPE IF EXISTS migrationstatus CASCADE')
    op.execute('DROP TYPE IF EXISTS migrationtype CASCADE')
