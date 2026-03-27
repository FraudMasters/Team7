"""Add token blacklist table

Revision ID: 20260322_add_token_blacklist
Revises: 20260221_add_skill_hierarchy_and_relationships
Create Date: 2026-03-22

This migration creates the token_blacklist table for tracking revoked/invalidated
JWT tokens. This enables:
- Token rotation: Old refresh tokens are blacklisted when new ones are issued
- Immediate revocation: Tokens can be invalidated before natural expiration
- Logout functionality: All user tokens can be revoked on logout
- Security response: Compromised tokens can be immediately blocked

The token_blacklist table stores:
- token: The full JWT token string (hashed for security)
- token_type: Type of token ("access" or "refresh")
- user_id: Associated user for bulk revocation
- expires_at: Original expiration time for cleanup
- revoked_at: When the token was blacklisted
- reason: Optional reason (e.g., "rotation", "logout", "security")
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260322_add_token_blacklist'
down_revision: Union[str, None] = '20260221_add_skill_hierarchy_and_relationships'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create token_blacklist table."""

    # =============================================================================
    # token_blacklist table
    # =============================================================================
    op.create_table(
        'token_blacklist',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Primary key UUID',
        ),
        # Token information
        sa.Column(
            'token',
            sa.Text(),
            nullable=False,
            unique=True,
            index=True,
            comment='JWT token string (hashed with SHA-256 for security)',
        ),
        sa.Column(
            'token_type',
            sa.String(20),
            nullable=False,
            index=True,
            comment='Type of token: "access" or "refresh"',
        ),
        # User association for bulk operations
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
            comment='User ID for bulk revocation (null for system tokens)',
        ),
        # Expiration and revocation tracking
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
            comment='Original expiration time of the token (for cleanup)',
        ),
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
            comment='When the token was blacklisted',
        ),
        sa.Column(
            'reason',
            sa.String(100),
            nullable=True,
            comment='Reason for blacklisting: "rotation", "logout", "security", etc.',
        ),
        # Timestamps (inherited from TimestampMixin)
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            comment='Timestamp when record was created',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
            comment='Timestamp when record was last updated',
        ),
        comment='Tracks revoked/invalidated JWT tokens to prevent reuse',
    )

    # =============================================================================
    # Composite indexes for efficient queries
    # =============================================================================

    # Index for token validation queries (check if specific token is blacklisted)
    op.create_index(
        'ix_token_blacklist_token_expires',
        'token_blacklist',
        ['token', 'expires_at'],
        unique=False,
    )

    # Index for user-based bulk revocation and cleanup queries
    op.create_index(
        'ix_token_blacklist_user_revoked',
        'token_blacklist',
        ['user_id', 'revoked_at'],
        unique=False,
    )


def downgrade() -> None:
    """Drop token_blacklist table."""

    # Drop composite indexes first
    op.drop_index('ix_token_blacklist_user_revoked', table_name='token_blacklist')
    op.drop_index('ix_token_blacklist_token_expires', table_name='token_blacklist')

    # Drop the table
    op.drop_table('token_blacklist')
