"""
SecurityConfig model for per-organization security settings
"""
from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SecurityConfig(Base, UUIDMixin, TimestampMixin):
    """
    SecurityConfig model for per-organization security settings

    This model enables organizations to customize their security posture by configuring
    authentication requirements, session policies, IP restrictions, and password policies.
    Each organization can have its own security configuration, or use the system defaults.

    Attributes:
        id: UUID primary key
        organization_id: Organization ID (null for system default config)
        two_factor_required: Whether 2FA is mandatory for all users in the organization
        two_factor_enabled: Whether 2FA is available for users to enable
        session_timeout_minutes: Session timeout in minutes (0 for no timeout)
        max_concurrent_sessions: Maximum number of concurrent active sessions per user (0 for unlimited)
        ip_whitelist_enabled: Whether IP whitelist restrictions are enforced
        ip_whitelist_strict: Whether to block all access when no whitelist is configured
        password_min_length: Minimum password length in characters
        password_require_uppercase: Whether passwords must contain uppercase letters
        password_require_lowercase: Whether passwords must contain lowercase letters
        password_require_numbers: Whether passwords must contain numbers
        password_require_special: Whether passwords must contain special characters
        password_expiry_days: Password expiry in days (0 for no expiry)
        sso_required: Whether SSO is mandatory for authentication
        sso_only: Whether only SSO authentication is allowed (password login disabled)
        security_alerts_enabled: Whether automatic security alerts are enabled
        failed_login_threshold: Number of failed logins before alert (0 to disable)
        created_at: Timestamp when config was created (inherited from TimestampMixin)
        updated_at: Timestamp when config was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "security_configs"

    # Organization scope
    organization_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        unique=True,
        index=True,
        comment="Organization ID (null for system default config)"
    )

    # Two-factor authentication settings
    two_factor_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether 2FA is mandatory for all users"
    )
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether 2FA is available for users to enable"
    )

    # Session management settings
    session_timeout_minutes: Mapped[int] = mapped_column(
        Integer,
        default=480,
        nullable=False,
        comment="Session timeout in minutes (0 for no timeout, default 8 hours)"
    )
    max_concurrent_sessions: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="Maximum concurrent sessions per user (0 for unlimited)"
    )

    # IP whitelist settings
    ip_whitelist_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether IP whitelist restrictions are enforced"
    )
    ip_whitelist_strict: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Block all access when no whitelist is configured"
    )

    # Password policy settings
    password_min_length: Mapped[int] = mapped_column(
        Integer,
        default=8,
        nullable=False,
        comment="Minimum password length in characters"
    )
    password_require_uppercase: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether passwords must contain uppercase letters"
    )
    password_require_lowercase: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether passwords must contain lowercase letters"
    )
    password_require_numbers: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether passwords must contain numbers"
    )
    password_require_special: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether passwords must contain special characters"
    )
    password_expiry_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Password expiry in days (0 for no expiry)"
    )

    # SSO settings
    sso_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether SSO is mandatory for authentication"
    )
    sso_only: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether only SSO authentication is allowed (password login disabled)"
    )

    # Security alerts settings
    security_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether automatic security alerts are enabled"
    )
    failed_login_threshold: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="Number of failed logins before alert (0 to disable)"
    )

    def __repr__(self) -> str:
        org_id_str = f"org={self.organization_id}" if self.organization_id else "system-default"
        return f"<SecurityConfig(id={self.id}, {org_id_str}, 2fa_required={self.two_factor_required})>"
