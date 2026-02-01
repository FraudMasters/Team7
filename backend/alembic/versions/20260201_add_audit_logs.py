"""Add audit logs table

Revision ID: 018_add_audit_logs
Revises: 017_add_backup_tables
Create Date: 2026-02-01

This migration creates the audit_logs table for tracking system-wide
user actions and changes. It provides a comprehensive audit trail of
all user actions across the system for compliance monitoring, security
auditing, and accountability tracking.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '018_add_audit_logs'
down_revision: Union[str, None] = '017_add_backup_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Action type (indexed for filtering)
        sa.Column('action_type', sa.String(50), nullable=False, index=True),
        # Entity information (indexed for lookups)
        sa.Column('entity_type', sa.String(100), nullable=True, index=True),
        sa.Column(
            'entity_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        # Foreign keys (indexed for filtering)
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        # Request metadata
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        # Action data and before/after values for sensitive operations
        sa.Column('action_data', postgresql.JSON(), nullable=True),
        sa.Column('before_value', postgresql.JSON(), nullable=True),
        sa.Column('after_value', postgresql.JSON(), nullable=True),
        # Optional reason for the action
        sa.Column('reason', sa.Text(), nullable=True),
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
        comment='Comprehensive audit trail of user actions for compliance and security',
    )

    # Create composite indexes for common query patterns
    op.create_index(
        'ix_audit_logs_user_id_action_type',
        'audit_logs',
        ['user_id', 'action_type'],
    )
    op.create_index(
        'ix_audit_logs_organization_id_action_type',
        'audit_logs',
        ['organization_id', 'action_type'],
    )
    op.create_index(
        'ix_audit_logs_entity_type_entity_id',
        'audit_logs',
        ['entity_type', 'entity_id'],
    )
    op.create_index(
        'ix_audit_logs_created_at',
        'audit_logs',
        ['created_at'],
    )


def downgrade() -> None:
    """Drop audit_logs table."""

    # Drop indexes (use try/except to handle missing indexes)
    try:
        op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    except Exception:
        pass
    try:
        op.drop_index('ix_audit_logs_entity_type_entity_id', table_name='audit_logs')
    except Exception:
        pass
    try:
        op.drop_index('ix_audit_logs_organization_id_action_type', table_name='audit_logs')
    except Exception:
        pass
    try:
        op.drop_index('ix_audit_logs_user_id_action_type', table_name='audit_logs')
    except Exception:
        pass

    # Drop table
    try:
        op.drop_table('audit_logs')
    except Exception:
        pass
