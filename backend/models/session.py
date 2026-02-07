"""
Session model for active session tracking and management
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class Session(Base, UUIDMixin, TimestampMixin):
    """
    Session model for tracking active user sessions and enabling remote logout

    This model enables users and administrators to view and manage active sessions
    across multiple devices. It stores device information, IP addresses, and activity
    timestamps to support session management features including viewing active devices,
    remote logout, and session timeout enforcement.

    Attributes:
        id: UUID primary key
        user_id: User ID who owns this session
        token: Session token or JWT token hash
        device_name: User-friendly device name (e.g., "Chrome on Windows", "Safari on iPhone")
        device_type: Device type: desktop, mobile, tablet, or unknown
        user_agent: Full user agent string for detailed device info
        ip_address: IP address where session was created
        location: Optional location derived from IP (e.g., "San Francisco, CA")
        is_active: Whether the session is currently active
        expires_at: Session expiration timestamp
        last_activity_at: Timestamp of last user activity
        revoked_at: Timestamp when session was revoked (null if active)
        revoke_reason: Reason for revocation (e.g., "user_logout", "security_reset", "admin_action")
        created_at: Timestamp when session was created (inherited from TimestampMixin)
        updated_at: Timestamp when session was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "sessions"

    # User relationship
    user_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User ID who owns this session"
    )

    # Session identifier
    token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="Session token or JWT token hash"
    )

    # Device information
    device_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User-friendly device name (e.g., 'Chrome on Windows')"
    )
    device_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Device type: desktop, mobile, tablet, or unknown"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full user agent string for detailed device info"
    )

    # Network information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address where session was created (supports IPv6)"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional location derived from IP (e.g., 'San Francisco, CA')"
    )

    # Session status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the session is currently active"
    )

    # Expiration and activity tracking
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Session expiration timestamp (null for no expiration)"
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
        index=True,
        comment="Timestamp of last user activity"
    )

    # Revocation tracking
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Timestamp when session was revoked (null if active)"
    )
    revoke_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Reason for revocation: user_logout, security_reset, admin_action, timeout"
    )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "revoked"
        return f"<Session(id={self.id}, user_id={self.user_id}, device={self.device_name}, status={status})>"

    def is_expired(self) -> bool:
        """Check if session is expired based on expires_at timestamp"""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    def is_valid(self) -> bool:
        """Check if session is both active and not expired"""
        return self.is_active and not self.is_expired()
