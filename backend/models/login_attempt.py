"""
Login attempt model for security monitoring and brute force protection
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LoginAttempt(Base, UUIDMixin, TimestampMixin):
    """
    Login attempt model for tracking authentication attempts and preventing brute force attacks

    This model records all login attempts (successful and failed) to enable security monitoring,
    rate limiting, and account lockout protection. It stores IP addresses, user agents, and
    failure reasons to help detect suspicious activity and investigate security incidents.

    Attributes:
        id: UUID primary key
        user_id: Optional user ID if the account exists (null for non-existent accounts)
        email: Email address used in the login attempt
        ip_address: IP address from which the login attempt originated
        user_agent: User agent string from the browser/client
        success: Whether the login attempt was successful
        failure_reason: Reason for failure (e.g., "invalid_password", "account_locked", "user_not_found")
        location: Optional location derived from IP (e.g., "San Francisco, CA")
        created_at: Timestamp when login attempt was made (inherited from TimestampMixin)
        updated_at: Timestamp when record was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "login_attempts"

    # User identification
    user_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User ID if the account exists (null for non-existent accounts)"
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Email address used in the login attempt"
    )

    # Network information
    ip_address: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        index=True,
        comment="IP address from which the login attempt originated (supports IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string from the browser/client"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional location derived from IP (e.g., 'San Francisco, CA')"
    )

    # Attempt result
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
        comment="Whether the login attempt was successful"
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reason for failure: invalid_password, account_locked, user_not_found, invalid_mfa, etc."
    )

    def __repr__(self) -> str:
        status = "success" if self.success else f"failed ({self.failure_reason})"
        return f"<LoginAttempt(id={self.id}, email={self.email}, ip={self.ip_address}, status={status})>"

    def is_successful(self) -> bool:
        """Check if login attempt was successful"""
        return self.success

    def is_failed(self) -> bool:
        """Check if login attempt failed"""
        return not self.success
