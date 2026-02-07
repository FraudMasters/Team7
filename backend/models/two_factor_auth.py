"""
TwoFactorAuth model for TOTP secrets and backup codes
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class TwoFactorAuth(Base, UUIDMixin, TimestampMixin):
    """
    TwoFactorAuth model for managing user two-factor authentication settings

    This model enables users to secure their accounts with two-factor authentication (2FA)
    using Time-based One-Time Passwords (TOTP), SMS codes, or email codes. It stores
    encrypted TOTP secrets and backup codes for account recovery. Each user can have
    only one 2FA configuration.

    Attributes:
        id: UUID primary key
        user_id: User ID (unique, one 2FA config per user)
        method: 2FA method: totp, sms, or email
        totp_secret: Encrypted TOTP secret key (only for TOTP method)
        backup_codes: Encrypted JSON array of backup codes for account recovery
        phone: Phone number for SMS-based 2FA (only for SMS method)
        email: Email address for email-based 2FA (only for Email method)
        is_enabled: Whether 2FA is currently active for this user
        is_verified: Whether the 2FA setup has been verified
        last_used_at: Timestamp of last successful 2FA verification
        created_at: Timestamp when 2FA was configured (inherited from TimestampMixin)
        updated_at: Timestamp when 2FA was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "two_factor_auths"

    # User relationship
    user_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID (unique, one 2FA config per user)"
    )

    # 2FA method configuration
    method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="2FA method: totp, sms, or email"
    )

    # TOTP-specific fields
    totp_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Encrypted TOTP secret key (only for TOTP method)"
    )

    # Backup codes for account recovery
    backup_codes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Encrypted JSON array of backup codes for account recovery"
    )

    # SMS-specific fields
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Phone number for SMS-based 2FA (only for SMS method)"
    )

    # Email-specific fields
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email address for email-based 2FA (only for Email method)"
    )

    # Status flags
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether 2FA is currently active for this user"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the 2FA setup has been verified"
    )

    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful 2FA verification"
    )

    def __repr__(self) -> str:
        return f"<TwoFactorAuth(id={self.id}, user_id={self.user_id}, method={self.method}, enabled={self.is_enabled})>"
