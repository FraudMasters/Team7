"""Add login attempts table

Revision ID: 20260322_add_login_attempts
Revises: 20260322_add_session_analytics
Create Date: 2026-03-22

This migration creates the login_attempts table for tracking authentication
attempts and enabling brute force protection. This enables:
- Security monitoring: Track all login attempts (successful and failed)
- Rate limiting: Detect and prevent brute force attacks
- Account lockout: Automatically lock accounts after repeated failures
- Audit trail: Investigate security incidents and suspicious activity

The login_attempts table stores:
- user_id: Optional user ID if the account exists (null for non-existent accounts)
- email: Email address used in the login attempt
- ip_address: IP address from which the attempt originated
- user_agent: User agent string from the browser/client
- success: Whether the login attempt was successful
- failure_reason: Reason for failure (invalid_password, account_locked, etc.)
- location: Optional location derived from IP
- created_at: Timestamp when attempt was made (from TimestampMixin)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260322_add_login_attempts'
down_revision: Union[str, None] = '20260322_add_session_analytics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create login_attempts table."""

    # =============================================================================
    # login_attempts table
    # =============================================================================
    op.create_table(
        'login_attempts',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Primary key UUID',
        ),
        # User identification
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
            comment='User ID if the account exists (null for non-existent accounts)',
        ),
        sa.Column(
            'email',
            sa.String(255),
            nullable=False,
            index=True,
            comment='Email address used in the login attempt',
        ),
        # Network and device information
        sa.Column(
            'ip_address',
            sa.String(45),
            nullable=False,
            index=True,
            comment='IP address from which the login attempt originated (supports IPv6)',
        ),
        sa.Column(
            'user_agent',
            sa.Text(),
            nullable=True,
            comment='User agent string from the browser/client',
        ),
        sa.Column(
            'location',
            sa.String(255),
            nullable=True,
            comment='Optional location derived from IP (e.g., "San Francisco, CA")',
        ),
        # Attempt result
        sa.Column(
            'success',
            sa.Boolean(),
            nullable=False,
            index=True,
            comment='Whether the login attempt was successful',
        ),
        sa.Column(
            'failure_reason',
            sa.String(100),
            nullable=True,
            comment='Reason for failure: invalid_password, account_locked, user_not_found, invalid_mfa, etc.',
        ),
        # Timestamps (inherited from TimestampMixin)
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Timestamp when login attempt was made',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Timestamp when record was last updated',
        ),
        comment='Tracks login attempts for security monitoring and brute force protection',
    )

    # =============================================================================
    # Composite indexes for efficient queries
    # =============================================================================

    # Index for rate limiting queries (count failed attempts by email in time window)
    op.create_index(
        'ix_login_attempts_email_created',
        'login_attempts',
        ['email', 'created_at'],
        unique=False,
    )

    # Index for IP-based rate limiting (detect attacks from specific IPs)
    op.create_index(
        'ix_login_attempts_ip_created',
        'login_attempts',
        ['ip_address', 'created_at'],
        unique=False,
    )

    # Index for user security audit queries (get all attempts for a user)
    op.create_index(
        'ix_login_attempts_user_created',
        'login_attempts',
        ['user_id', 'created_at'],
        unique=False,
    )

    # Index for failed login analysis (track patterns of failures)
    op.create_index(
        'ix_login_attempts_success_created',
        'login_attempts',
        ['success', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    """Drop login_attempts table."""

    # Drop composite indexes first
    op.drop_index('ix_login_attempts_success_created', table_name='login_attempts')
    op.drop_index('ix_login_attempts_user_created', table_name='login_attempts')
    op.drop_index('ix_login_attempts_ip_created', table_name='login_attempts')
    op.drop_index('ix_login_attempts_email_created', table_name='login_attempts')

    # Drop the table
    op.drop_table('login_attempts')
