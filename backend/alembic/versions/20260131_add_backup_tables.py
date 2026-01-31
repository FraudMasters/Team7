"""Add backup tables

Revision ID: 017_add_backup_tables
Revises: 016_add_ats_results
Create Date: 2026-01-31

This migration creates the backups and backup_configs tables for
automated backup and restore functionality.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '017_add_backup_tables'
down_revision: Union[str, None] = '016_add_ats_results'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create backups and backup_configs tables."""

    # Create backups table
    op.create_table(
        'backups',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column(
            'type',
            sa.Enum(
                'DATABASE',
                'FILES',
                'MODELS',
                'FULL',
                name='backuptype',
                inherit_schema=True,
            ),
            nullable=False,
            default='FULL',
        ),
        sa.Column(
            'status',
            sa.Enum(
                'PENDING',
                'IN_PROGRESS',
                'COMPLETED',
                'FAILED',
                'EXPIRED',
                'RESTORING',
                name='backupstatus',
                inherit_schema=True,
            ),
            nullable=False,
            default='PENDING',
        ),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('backup_path', sa.String(512), nullable=False),
        sa.Column('completed_at', sa.String(50), nullable=True),
        sa.Column('retention_days', sa.Integer(), nullable=False, default=30),
        sa.Column('checksum', sa.String(128), nullable=True),
        sa.Column('is_incremental', sa.Boolean(), nullable=False, default=False),
        sa.Column('parent_backup_id', sa.String(50), nullable=True),
        sa.Column('s3_uploaded', sa.Boolean(), nullable=False, default=False),
        sa.Column('s3_key', sa.String(512), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('files_count', sa.Integer(), nullable=True),
        sa.Column('tables_count', sa.Integer(), nullable=True),
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
        comment='Backup tracking table for backup and restore operations',
    )

    # Create indexes for backups
    op.create_index('ix_backups_type', 'backups', ['type'])
    op.create_index('ix_backups_status', 'backups', ['status'])
    op.create_index('ix_backups_checksum', 'backups', ['checksum'])
    op.create_index('ix_backups_parent_backup_id', 'backups', ['parent_backup_id'])

    # Create backup_configs table
    op.create_table(
        'backup_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True, nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False, default=30),
        sa.Column('backup_schedule', sa.String(100), nullable=False, default='0 2 * * *'),
        sa.Column('s3_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('s3_bucket', sa.String(255), nullable=True),
        sa.Column('s3_endpoint', sa.String(512), nullable=True),
        sa.Column('s3_access_key', sa.String(255), nullable=True),
        sa.Column('s3_secret_key', sa.String(255), nullable=True),
        sa.Column('s3_region', sa.String(50), nullable=True, default='us-east-1'),
        sa.Column('notification_email', sa.String(255), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('incremental_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('compression_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_backup_at', sa.String(50), nullable=True),
        sa.Column('last_backup_status', sa.String(50), nullable=True),
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
        comment='Backup configuration for system-wide backup settings',
    )


def downgrade() -> None:
    """Drop backups and backup_configs tables."""

    # Drop indexes (use try/except to handle missing indexes)
    try:
        op.drop_index('ix_backups_parent_backup_id', table_name='backups')
    except Exception:
        pass
    try:
        op.drop_index('ix_backups_checksum', table_name='backups')
    except Exception:
        pass
    try:
        op.drop_index('ix_backups_status', table_name='backups')
    except Exception:
        pass
    try:
        op.drop_index('ix_backups_type', table_name='backups')
    except Exception:
        pass

    # Drop tables
    try:
        op.drop_table('backup_configs')
    except Exception:
        pass
    try:
        op.drop_table('backups')
    except Exception:
        pass

    # Drop enums
    op.execute('DROP TYPE IF EXISTS backuptype CASCADE')
    op.execute('DROP TYPE IF EXISTS backupstatus CASCADE')
