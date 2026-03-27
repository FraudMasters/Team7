"""Add session analytics table

Revision ID: 20260322_add_session_analytics
Revises: 20260322_add_token_blacklist
Create Date: 2026-03-22

This migration creates the session_analytics table for tracking session events
and enabling security monitoring. This enables:
- Session activity tracking: Log login, activity, logout, and timeout events
- Security monitoring: Track suspicious activity patterns and anomalies
- User behavior analytics: Analyze user activity across sessions and devices
- Audit trail: Maintain complete history of session-related events

The session_analytics table stores:
- session_id: Reference to the session that generated this event
- user_id: User who triggered the event
- event_type: Type of event ("login", "activity", "logout", "refresh", "timeout")
- ip_address: IP address where the event occurred
- user_agent: User agent string for device identification
- location: Optional location derived from IP
- metadata: Optional JSON metadata for additional context
- created_at: Event timestamp (from TimestampMixin)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260322_add_session_analytics'
down_revision: Union[str, None] = '20260322_add_token_blacklist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create session_analytics table."""

    # =============================================================================
    # session_analytics table
    # =============================================================================
    op.create_table(
        'session_analytics',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Primary key UUID',
        ),
        # Session and user relationships
        sa.Column(
            'session_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='Reference to the session this event belongs to',
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='User ID who triggered this event',
        ),
        # Event information
        sa.Column(
            'event_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Type of event: "login", "activity", "logout", "refresh", "timeout"',
        ),
        # Network and device information
        sa.Column(
            'ip_address',
            sa.String(45),
            nullable=True,
            index=True,
            comment='IP address where the event occurred (supports IPv6)',
        ),
        sa.Column(
            'user_agent',
            sa.Text(),
            nullable=True,
            comment='User agent string for device/browser identification',
        ),
        sa.Column(
            'location',
            sa.String(255),
            nullable=True,
            comment='Optional location derived from IP (e.g., "San Francisco, CA")',
        ),
        # Additional context
        sa.Column(
            'metadata',
            sa.Text(),
            nullable=True,
            comment='Optional JSON metadata for additional event context',
        ),
        # Timestamps (inherited from TimestampMixin)
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Timestamp when event was created',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Timestamp when record was last updated',
        ),
        comment='Tracks session events for security monitoring and analytics',
    )

    # =============================================================================
    # Composite indexes for efficient queries
    # =============================================================================

    # Index for user session history queries (get all events for a user)
    op.create_index(
        'ix_session_analytics_user_created',
        'session_analytics',
        ['user_id', 'created_at'],
        unique=False,
    )

    # Index for session event timeline queries (get all events for a session)
    op.create_index(
        'ix_session_analytics_session_created',
        'session_analytics',
        ['session_id', 'created_at'],
        unique=False,
    )

    # Index for security monitoring queries (track specific event types over time)
    op.create_index(
        'ix_session_analytics_event_created',
        'session_analytics',
        ['event_type', 'created_at'],
        unique=False,
    )

    # Index for IP-based security analysis (track activity from specific IPs)
    op.create_index(
        'ix_session_analytics_ip_created',
        'session_analytics',
        ['ip_address', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    """Drop session_analytics table."""

    # Drop composite indexes first
    op.drop_index('ix_session_analytics_ip_created', table_name='session_analytics')
    op.drop_index('ix_session_analytics_event_created', table_name='session_analytics')
    op.drop_index('ix_session_analytics_session_created', table_name='session_analytics')
    op.drop_index('ix_session_analytics_user_created', table_name='session_analytics')

    # Drop the table
    op.drop_table('session_analytics')
