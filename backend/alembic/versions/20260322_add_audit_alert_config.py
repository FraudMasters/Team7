"""Add audit alert config table

Revision ID: 019_add_audit_alert_config
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

This migration creates the audit_alert_configs table for configuring
alert rules that detect suspicious patterns in audit logs. Alert rules
can monitor for failed logins, bulk data exports, permission changes,
and other security-relevant events. Rules can be scoped to specific
organizations or applied globally.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_add_audit_alert_config'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_alert_configs table."""

    # Create audit_alert_configs table
    op.create_table(
        'audit_alert_configs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Core alert configuration (indexed for filtering)
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('alert_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column(
            'severity',
            sa.String(20),
            nullable=False,
            server_default='warning',
            index=True,
        ),
        # Organization scope (indexed for filtering)
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
        ),
        # Threshold and time window configuration
        sa.Column(
            'threshold',
            sa.Integer(),
            nullable=False,
            server_default='5',
            comment='Numeric threshold that triggers the alert',
        ),
        sa.Column(
            'time_window_minutes',
            sa.Integer(),
            nullable=False,
            server_default='10',
            comment='Time window in minutes for threshold evaluation',
        ),
        # Action filtering
        sa.Column(
            'action_types',
            postgresql.JSON(),
            nullable=True,
            comment='List of AuditActionType values to monitor (null for all)',
        ),
        # Notification configuration
        sa.Column(
            'recipients',
            postgresql.JSON(),
            nullable=True,
            comment='Notification recipients: {emails: [], webhooks: [], slack_channels: []}',
        ),
        sa.Column(
            'alert_config',
            postgresql.JSON(),
            nullable=True,
            comment='Additional alert-specific configuration and metadata',
        ),
        # Alert throttling and tracking
        sa.Column(
            'cooldown_minutes',
            sa.Integer(),
            nullable=False,
            server_default='60',
            comment='Minutes to wait before sending another alert of the same type',
        ),
        sa.Column('last_triggered_at', sa.String(50), nullable=True),
        sa.Column(
            'trigger_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='Number of times this alert has been triggered',
        ),
        # Audit trail for the configuration itself
        sa.Column(
            'created_by',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            'updated_by',
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
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
        comment='Alert rules for detecting suspicious patterns in audit logs',
    )

    # Create composite indexes for common query patterns
    op.create_index(
        'ix_audit_alert_configs_organization_id_enabled',
        'audit_alert_configs',
        ['organization_id', 'enabled'],
    )
    op.create_index(
        'ix_audit_alert_configs_alert_type_enabled',
        'audit_alert_configs',
        ['alert_type', 'enabled'],
    )
    op.create_index(
        'ix_audit_alert_configs_severity_enabled',
        'audit_alert_configs',
        ['severity', 'enabled'],
    )


def downgrade() -> None:
    """Drop audit_alert_configs table."""

    # Drop indexes (use try/except to handle missing indexes)
    try:
        op.drop_index('ix_audit_alert_configs_severity_enabled', table_name='audit_alert_configs')
    except Exception:
        pass
    try:
        op.drop_index('ix_audit_alert_configs_alert_type_enabled', table_name='audit_alert_configs')
    except Exception:
        pass
    try:
        op.drop_index('ix_audit_alert_configs_organization_id_enabled', table_name='audit_alert_configs')
    except Exception:
        pass

    # Drop table
    try:
        op.drop_table('audit_alert_configs')
    except Exception:
        pass
