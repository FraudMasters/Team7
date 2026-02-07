"""Add security features tables

Revision ID: 019_add_security_features
Revises: 017_add_candidate_performance_indexes
Create Date: 2026-02-03

This migration creates all tables required for advanced security features including:
- security_configs: Per-organization security settings (2FA, sessions, IP whitelist, passwords)
- sso_configs: SAML SSO provider configurations for Okta, Azure AD, Google Workspace
- two_factor_auths: User 2FA settings with TOTP secrets and backup codes
- sessions: Active session tracking with device info and remote logout support
- ip_whitelists: Organization IP access restrictions for enhanced security

These tables enable enterprise security features required for SSO integration,
two-factor authentication, comprehensive session management, and IP-based
access control.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '019_add_security_features'
down_revision: Union[str, None] = '017_add_candidate_performance_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all security feature tables."""

    # =============================================================================
    # security_configs table
    # =============================================================================
    op.create_table(
        'security_configs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Organization scope (indexed for lookups)
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            unique=True,
            index=True,
            comment='Organization ID (null for system default config)',
        ),
        # Two-factor authentication settings
        sa.Column(
            'two_factor_required',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether 2FA is mandatory for all users',
        ),
        sa.Column(
            'two_factor_enabled',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether 2FA is available for users to enable',
        ),
        # Session management settings
        sa.Column(
            'session_timeout_minutes',
            sa.Integer(),
            nullable=False,
            default=480,
            comment='Session timeout in minutes (0 for no timeout, default 8 hours)',
        ),
        sa.Column(
            'max_concurrent_sessions',
            sa.Integer(),
            nullable=False,
            default=5,
            comment='Maximum concurrent sessions per user (0 for unlimited)',
        ),
        # IP whitelist settings
        sa.Column(
            'ip_whitelist_enabled',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether IP whitelist restrictions are enforced',
        ),
        sa.Column(
            'ip_whitelist_strict',
            sa.Boolean(),
            nullable=False,
            default=False,
            comment='Block all access when no whitelist is configured',
        ),
        # Password policy settings
        sa.Column(
            'password_min_length',
            sa.Integer(),
            nullable=False,
            default=8,
            comment='Minimum password length in characters',
        ),
        sa.Column(
            'password_require_uppercase',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether passwords must contain uppercase letters',
        ),
        sa.Column(
            'password_require_lowercase',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether passwords must contain lowercase letters',
        ),
        sa.Column(
            'password_require_numbers',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether passwords must contain numbers',
        ),
        sa.Column(
            'password_require_special',
            sa.Boolean(),
            nullable=False,
            default=False,
            comment='Whether passwords must contain special characters',
        ),
        sa.Column(
            'password_expiry_days',
            sa.Integer(),
            nullable=False,
            default=0,
            comment='Password expiry in days (0 for no expiry)',
        ),
        # SSO settings
        sa.Column(
            'sso_required',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether SSO is mandatory for authentication',
        ),
        sa.Column(
            'sso_only',
            sa.Boolean(),
            nullable=False,
            default=False,
            comment='Whether only SSO authentication is allowed (password login disabled)',
        ),
        # Security alerts settings
        sa.Column(
            'security_alerts_enabled',
            sa.Boolean(),
            nullable=False,
            default=True,
            comment='Whether automatic security alerts are enabled',
        ),
        sa.Column(
            'failed_login_threshold',
            sa.Integer(),
            nullable=False,
            default=5,
            comment='Number of failed logins before alert (0 to disable)',
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
        comment='Per-organization security settings for 2FA, sessions, IP whitelist, and passwords',
    )

    # =============================================================================
    # sso_configs table
    # =============================================================================
    op.create_table(
        'sso_configs',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Organization scope (indexed for lookups)
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
            comment="Human-readable name of the SSO provider (e.g., 'Company Okta')",
        ),
        sa.Column(
            'provider_type',
            sa.String(50),
            nullable=False,
            index=True,
            comment="Provider type: okta, azure_ad, google_workspace, or generic_saml",
        ),
        # SAML configuration
        sa.Column(
            'entity_id',
            sa.String(500),
            nullable=False,
            comment='SAML Entity ID (IdP identifier) from the identity provider',
        ),
        sa.Column(
            'sso_url',
            sa.String(500),
            nullable=False,
            comment='SAML SSO URL where authentication requests are sent',
        ),
        sa.Column(
            'sls_url',
            sa.String(500),
            nullable=True,
            comment='SAML Single Logout Service URL for logout requests',
        ),
        sa.Column(
            'x509_certificate',
            sa.Text(),
            nullable=False,
            comment='X.509 certificate from IdP for verifying SAML responses',
        ),
        sa.Column(
            'metadata_url',
            sa.String(500),
            nullable=True,
            comment='Optional URL to fetch SAML metadata automatically',
        ),
        # Attribute mappings for user provisioning
        sa.Column(
            'attribute_mapping_email',
            sa.String(100),
            nullable=False,
            default='email',
            comment='SAML attribute name for user email',
        ),
        sa.Column(
            'attribute_mapping_name',
            sa.String(100),
            nullable=False,
            default='displayName',
            comment='SAML attribute name for user display name',
        ),
        sa.Column(
            'attribute_mapping_first_name',
            sa.String(100),
            nullable=True,
            default='firstName',
            comment='SAML attribute name for user first name',
        ),
        sa.Column(
            'attribute_mapping_last_name',
            sa.String(100),
            nullable=True,
            default='lastName',
            comment='SAML attribute name for user last name',
        ),
        sa.Column(
            'attribute_mapping_department',
            sa.String(100),
            nullable=True,
            default='department',
            comment='SAML attribute name for user department',
        ),
        # Configuration flags
        sa.Column(
            'is_enabled',
            sa.Boolean(),
            nullable=False,
            default=True,
            index=True,
            comment='Whether this SSO configuration is active',
        ),
        sa.Column(
            'is_default',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether this is the default SSO provider for the organization',
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
        comment='SAML SSO provider configurations for Okta, Azure AD, and Google Workspace',
    )

    # Create composite index for SSO configs
    op.create_index(
        'ix_sso_configs_organization_id_is_enabled',
        'sso_configs',
        ['organization_id', 'is_enabled'],
    )

    # =============================================================================
    # two_factor_auths table
    # =============================================================================
    op.create_table(
        'two_factor_auths',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # User relationship (unique, one 2FA config per user)
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            index=True,
            comment='User ID (unique, one 2FA config per user)',
        ),
        # 2FA method configuration
        sa.Column(
            'method',
            sa.String(20),
            nullable=False,
            index=True,
            comment="2FA method: totp, sms, or email",
        ),
        # TOTP-specific fields
        sa.Column(
            'totp_secret',
            sa.String(255),
            nullable=True,
            comment='Encrypted TOTP secret key (only for TOTP method)',
        ),
        # Backup codes for account recovery
        sa.Column(
            'backup_codes',
            sa.Text(),
            nullable=True,
            comment='Encrypted JSON array of backup codes for account recovery',
        ),
        # SMS-specific fields
        sa.Column(
            'phone',
            sa.String(50),
            nullable=True,
            comment='Phone number for SMS-based 2FA (only for SMS method)',
        ),
        # Email-specific fields
        sa.Column(
            'email',
            sa.String(255),
            nullable=True,
            comment='Email address for email-based 2FA (only for Email method)',
        ),
        # Status flags
        sa.Column(
            'is_enabled',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether 2FA is currently active for this user',
        ),
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            default=False,
            index=True,
            comment='Whether the 2FA setup has been verified',
        ),
        # Usage tracking
        sa.Column(
            'last_used_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp of last successful 2FA verification',
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
        comment='User 2FA settings with TOTP secrets and backup codes',
    )

    # Create composite index for 2FA
    op.create_index(
        'ix_two_factor_auths_user_id_is_enabled',
        'two_factor_auths',
        ['user_id', 'is_enabled'],
    )

    # =============================================================================
    # sessions table
    # =============================================================================
    op.create_table(
        'sessions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # User relationship
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
            comment='User ID who owns this session',
        ),
        # Session identifier
        sa.Column(
            'token',
            sa.String(500),
            nullable=False,
            unique=True,
            index=True,
            comment='Session token or JWT token hash',
        ),
        # Device information
        sa.Column(
            'device_name',
            sa.String(255),
            nullable=True,
            comment="User-friendly device name (e.g., 'Chrome on Windows')",
        ),
        sa.Column(
            'device_type',
            sa.String(50),
            nullable=True,
            index=True,
            comment="Device type: desktop, mobile, tablet, or unknown",
        ),
        sa.Column(
            'user_agent',
            sa.Text(),
            nullable=True,
            comment='Full user agent string for detailed device info',
        ),
        # Network information
        sa.Column(
            'ip_address',
            sa.String(45),
            nullable=True,
            index=True,
            comment='IP address where session was created (supports IPv6)',
        ),
        sa.Column(
            'location',
            sa.String(255),
            nullable=True,
            comment="Optional location derived from IP (e.g., 'San Francisco, CA')",
        ),
        # Session status
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            default=True,
            index=True,
            comment='Whether the session is currently active',
        ),
        # Expiration and activity tracking
        sa.Column(
            'expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='Session expiration timestamp (null for no expiration)',
        ),
        sa.Column(
            'last_activity_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
            comment='Timestamp of last user activity',
        ),
        # Revocation tracking
        sa.Column(
            'revoked_at',
            sa.DateTime(timezone=True),
            nullable=True,
            index=True,
            comment='Timestamp when session was revoked (null if active)',
        ),
        sa.Column(
            'revoke_reason',
            sa.String(100),
            nullable=True,
            comment='Reason for revocation: user_logout, security_reset, admin_action, timeout',
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
        comment='Active session tracking with device info and remote logout support',
    )

    # Create composite indexes for sessions
    op.create_index(
        'ix_sessions_user_id_is_active',
        'sessions',
        ['user_id', 'is_active'],
    )
    op.create_index(
        'ix_sessions_user_id_last_activity_at',
        'sessions',
        ['user_id', 'last_activity_at'],
    )

    # =============================================================================
    # ip_whitelists table
    # =============================================================================
    op.create_table(
        'ip_whitelists',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # Organization scope
        sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
            comment='Organization ID (null for system-wide whitelist)',
        ),
        # Identification
        sa.Column(
            'name',
            sa.String(255),
            nullable=False,
            index=True,
            comment="Friendly name for this IP range (e.g., 'Office Network')",
        ),
        sa.Column(
            'description',
            sa.Text(),
            nullable=True,
            comment='Optional description with additional context',
        ),
        # IP range specification
        sa.Column(
            'cidr_notation',
            sa.String(50),
            nullable=True,
            index=True,
            comment="IP range in CIDR notation (e.g., '192.168.1.0/24')",
        ),
        sa.Column(
            'start_ip',
            sa.String(45),
            nullable=True,
            comment='Starting IP address (for range-based whitelisting, supports IPv6)',
        ),
        sa.Column(
            'end_ip',
            sa.String(45),
            nullable=True,
            comment='Ending IP address (for range-based whitelisting, supports IPv6)',
        ),
        # Status
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            default=True,
            index=True,
            comment='Whether this IP range is currently enforced',
        ),
        # Audit tracking
        sa.Column(
            'created_by',
            postgresql.UUID(as_uuid=True),
            nullable=True,
            index=True,
            comment='User ID who created this whitelist entry',
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
        comment='Organization IP access restrictions for enhanced security',
    )

    # Create composite index for IP whitelists
    op.create_index(
        'ix_ip_whitelists_organization_id_is_active',
        'ip_whitelists',
        ['organization_id', 'is_active'],
    )


def downgrade() -> None:
    """Drop all security feature tables."""

    # Drop ip_whitelists table
    try:
        op.drop_index('ix_ip_whitelists_organization_id_is_active', table_name='ip_whitelists')
    except Exception:
        pass
    try:
        op.drop_table('ip_whitelists')
    except Exception:
        pass

    # Drop sessions table
    try:
        op.drop_index('ix_sessions_user_id_last_activity_at', table_name='sessions')
    except Exception:
        pass
    try:
        op.drop_index('ix_sessions_user_id_is_active', table_name='sessions')
    except Exception:
        pass
    try:
        op.drop_table('sessions')
    except Exception:
        pass

    # Drop two_factor_auths table
    try:
        op.drop_index('ix_two_factor_auths_user_id_is_enabled', table_name='two_factor_auths')
    except Exception:
        pass
    try:
        op.drop_table('two_factor_auths')
    except Exception:
        pass

    # Drop sso_configs table
    try:
        op.drop_index('ix_sso_configs_organization_id_is_enabled', table_name='sso_configs')
    except Exception:
        pass
    try:
        op.drop_table('sso_configs')
    except Exception:
        pass

    # Drop security_configs table
    try:
        op.drop_table('security_configs')
    except Exception:
        pass
