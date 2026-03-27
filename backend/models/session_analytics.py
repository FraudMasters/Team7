"""
Session analytics model for tracking session events and security monitoring
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SessionAnalytics(Base, UUIDMixin, TimestampMixin):
    """
    Session analytics model for tracking login, activity, and logout events

    This model enables security monitoring and user behavior analytics by logging
    all session-related events. It supports anomaly detection, security auditing,
    and user activity analysis across multiple sessions and devices.

    Attributes:
        id: UUID primary key
        session_id: Reference to the session this event belongs to
        user_id: User ID who triggered this event
        event_type: Type of event: "login", "activity", "logout", "refresh", "timeout"
        ip_address: IP address where the event occurred
        user_agent: User agent string for device/browser identification
        location: Optional location derived from IP (e.g., "San Francisco, CA")
        metadata: Optional JSON metadata for additional event context
        created_at: Timestamp when event was created (inherited from TimestampMixin)
        updated_at: Timestamp when event was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "session_analytics"

    # Session and user relationships
    session_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Reference to the session this event belongs to"
    )
    user_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="User ID who triggered this event"
    )

    # Event information
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment='Type of event: "login", "activity", "logout", "refresh", "timeout"'
    )

    # Network and device information
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address where the event occurred (supports IPv6)"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string for device/browser identification"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional location derived from IP (e.g., 'San Francisco, CA')"
    )

    # Additional context
    metadata: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional JSON metadata for additional event context"
    )

    def __repr__(self) -> str:
        return f"<SessionAnalytics(id={self.id}, user_id={self.user_id}, event_type={self.event_type}, created_at={self.created_at})>"
