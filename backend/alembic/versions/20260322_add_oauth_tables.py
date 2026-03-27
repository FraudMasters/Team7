"""Add OAuth provider and token tables

Revision ID: 20260322_add_oauth_tables
Revises: 20260322_add_session_analytics
Create Date: 2026-03-22

This migration creates the oauth_providers and oauth_tokens tables for OAuth 2.0
Single Sign-On integration. This enables:
- Multi-provider OAuth: Support Google, GitHub, Microsoft, Okta, and custom providers
- Organization-scoped configuration: Each org can configure their own OAuth providers
- Secure token storage: Access and refresh tokens are encrypted at rest
- User provisioning: Automatic user creation from OAuth provider attributes
- Token refresh: Refresh tokens enable seamless session management

The oauth_providers table stores:
- provider_name: Human-readable name (e.g., "Company Google OAuth")
- provider_type: Type (google, github, microsoft, okta, generic_oauth)
- client_id/client_secret: OAuth application credentials
- authorization_url/token_url/userinfo_url: OAuth endpoints
- scopes: Requested OAuth scopes
- attribute_mapping_*: Mappings for user profile attributes
- is_enabled/is_default: Configuration flags

The oauth_tokens table stores:
- user_id: User who owns the token
- provider_id: Reference to oauth_providers
- access_token/refresh_token: OAuth tokens (encrypted)
- expires_at: Token expiration
- provider_user_id/provider_email: User info from provider
- provider_metadata: Additional user profile data
- last_used_at: Usage tracking
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260322_add_oauth_tables'
down_revision: Union[str, None] = '20260322_add_session_analytics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create oauth_providers and oauth_tokens tables."""

    # =============================================================================
    # oauth_providers table
    # =============================================================================
    op.create_table(
        'oauth_providers',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Primary key UUID',
        ),
        # Organization scope
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
            comment='Organization ID (null for system-wide config)',
        ),
        # Provider identification
        sa.Column(
            'provider_name',
            sa.String(255),
            nullable=False,
            index=True,
            comment="Human-readable name of the OAuth provider (e.g., 'Google OAuth')",
        ),
        sa.Column(
            'provider_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Provider type: google, github, microsoft, okta, or generic_oauth',
        ),
        # OAuth credentials
        sa.Column(
            'client_id',
            sa.String(500),
            nullable=False,
            comment='OAuth client ID from the identity provider',
        ),
        sa.Column(
            'client_secret',
            sa.Text(),
            nullable=False,
            comment='OAuth client secret (encrypted at rest)',
        ),
        # OAuth endpoints
        sa.Column(
            'authorization_url',
            sa.String(500),
            nullable=False,
            comment='OAuth authorization endpoint URL',
        ),
        sa.Column(
            'token_url',
            sa.String(500),
            nullable=False,
            comment='OAuth token endpoint URL',
        ),
        sa.Column(
            'userinfo_url',
            sa.String(500),
            nullable=False,
            comment='OAuth userinfo endpoint URL to fetch user profile',
        ),
        # OAuth configuration
        sa.Column(
            'scopes',
            sa.String(500),
            nullable=False,
            comment='Space-separated list of OAuth scopes to request',
        ),
        sa.Column(
            'redirect_uri',
            sa.String(500),
            nullable=False,
            comment='OAuth redirect URI configured in the provider',
        ),
        # Attribute mappings for user provisioning
        sa.Column(
            'attribute_mapping_email',
            sa.String(100),
            nullable=False,
            comment='User profile attribute name for email',
        ),
        sa.Column(
            'attribute_mapping_name',
            sa.String(100),
            nullable=False,
            comment='User profile attribute name for display name',
        ),
        sa.Column(
            'attribute_mapping_first_name',
            sa.String(100),
            nullable=True,
            comment='User profile attribute name for first name',
        ),
        sa.Column(
            'attribute_mapping_last_name',
            sa.String(100),
            nullable=True,
            comment='User profile attribute name for last name',
        ),
        sa.Column(
            'attribute_mapping_picture',
            sa.String(100),
            nullable=True,
            comment='User profile attribute name for profile picture URL',
        ),
        # Configuration flags
        sa.Column(
            'is_enabled',
            sa.Boolean(),
            default=True,
            nullable=False,
            index=True,
            comment='Whether this OAuth configuration is active',
        ),
        sa.Column(
            'is_default',
            sa.Boolean(),
            default=False,
            nullable=False,
            index=True,
            comment='Whether this is the default OAuth provider for the organization',
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
        comment='OAuth 2.0 provider configurations for SSO integration',
    )

    # =============================================================================
    # oauth_tokens table
    # =============================================================================
    op.create_table(
        'oauth_tokens',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment='Primary key UUID',
        ),
        # User and provider association
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='User ID who owns this token',
        ),
        sa.Column(
            'provider_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='OAuth provider ID from oauth_providers table',
        ),
        sa.Column(
            'provider_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment='Provider type (google, github, microsoft, etc.) for quick lookup',
        ),
        # OAuth tokens
        sa.Column(
            'access_token',
            sa.Text(),
            nullable=False,
            comment='OAuth access token (encrypted at rest)',
        ),
        sa.Column(
            'refresh_token',
            sa.Text(),
            nullable=True,
            comment='OAuth refresh token for obtaining new access tokens (encrypted at rest)',
        ),
        sa.Column(
            'token_type',
            sa.String(50),
            nullable=False,
            comment='Token type (usually "Bearer")',
        ),
        # Token metadata
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='When the access token expires',
        ),
        sa.Column(
            'scope',
            sa.String(500),
            nullable=True,
            comment='Space-separated list of granted OAuth scopes',
        ),
        sa.Column(
            'id_token',
            sa.Text(),
            nullable=True,
            comment='OpenID Connect ID token if available (encrypted at rest)',
        ),
        # Provider user information
        sa.Column(
            'provider_user_id',
            sa.String(255),
            nullable=False,
            index=True,
            comment='User ID from the OAuth provider',
        ),
        sa.Column(
            'provider_email',
            sa.String(255),
            nullable=True,
            index=True,
            comment='Email from the OAuth provider',
        ),
        sa.Column(
            'provider_metadata',
            postgresql.JSONB(),
            nullable=True,
            comment='Additional metadata from the OAuth provider (user profile data)',
        ),
        # Usage tracking
        sa.Column(
            'last_used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='When this token was last used for authentication',
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
        comment='OAuth 2.0 tokens for authenticated users',
    )

    # =============================================================================
    # Composite indexes for efficient queries
    # =============================================================================

    # Index for finding OAuth provider by organization and type
    op.create_index(
        'ix_oauth_providers_org_type',
        'oauth_providers',
        ['organization_id', 'provider_type'],
        unique=False,
    )

    # Index for finding enabled default provider
    op.create_index(
        'ix_oauth_providers_enabled_default',
        'oauth_providers',
        ['is_enabled', 'is_default'],
        unique=False,
    )

    # Index for finding user's OAuth tokens by provider
    op.create_index(
        'ix_oauth_tokens_user_provider',
        'oauth_tokens',
        ['user_id', 'provider_id'],
        unique=False,
    )

    # Index for finding tokens by provider user ID (for linking accounts)
    op.create_index(
        'ix_oauth_tokens_provider_user',
        'oauth_tokens',
        ['provider_type', 'provider_user_id'],
        unique=False,
    )

    # Index for finding expired tokens (for cleanup)
    op.create_index(
        'ix_oauth_tokens_expires_at',
        'oauth_tokens',
        ['expires_at'],
        unique=False,
    )


def downgrade() -> None:
    """Drop oauth_providers and oauth_tokens tables."""

    # Drop indexes from oauth_tokens
    op.drop_index('ix_oauth_tokens_expires_at', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_provider_user', table_name='oauth_tokens')
    op.drop_index('ix_oauth_tokens_user_provider', table_name='oauth_tokens')

    # Drop indexes from oauth_providers
    op.drop_index('ix_oauth_providers_enabled_default', table_name='oauth_providers')
    op.drop_index('ix_oauth_providers_org_type', table_name='oauth_providers')

    # Drop tables
    op.drop_table('oauth_tokens')
    op.drop_table('oauth_providers')
