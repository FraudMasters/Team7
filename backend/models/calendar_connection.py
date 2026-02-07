"""
CalendarConnection model for managing external calendar integrations
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CalendarProvider(str, enum.Enum):
    """Supported calendar providers"""

    GOOGLE = "google"
    OUTLOOK = "outlook"


class ConnectionStatus(str, enum.Enum):
    """Status of calendar connection"""

    ACTIVE = "active"
    EXPIRED = "expired"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class CalendarConnection(Base, UUIDMixin, TimestampMixin):
    """
    CalendarConnection model for managing external calendar integrations

    This model stores OAuth connection information for integrating with
    external calendar providers (Google Calendar and Microsoft Outlook/Graph).
    It enables automatic calendar event creation, availability checking,
    and synchronization of interview schedules with users' calendars.

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to Recruiter who owns this connection
        provider: Calendar provider (google or outlook)
        access_token: OAuth access token for API calls
        refresh_token: OAuth refresh token for obtaining new access tokens
        token_expires_at: When the access token expires
        calendar_email: Email address of the connected calendar account
        calendar_id: Provider-specific calendar identifier
        status: Current status of the connection
        webhook_subscription_id: Optional webhook subscription for real-time sync
        last_sync_at: Timestamp of last successful synchronization
        error_message: Optional error details if connection failed
        created_at: Timestamp when connection was created (inherited)
        updated_at: Timestamp when connection was last updated (inherited)
    """

    __tablename__ = "calendar_connections"

    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    provider: Mapped[CalendarProvider] = mapped_column(
        Enum(CalendarProvider), nullable=False, index=True
    )
    access_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(2048), nullable=False)
    token_expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    calendar_email: Mapped[str] = mapped_column(String(255), nullable=False)
    calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus), default=ConnectionStatus.ACTIVE, nullable=False, index=True
    )
    webhook_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_sync_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CalendarConnection(id={self.id}, recruiter_id={self.recruiter_id}, provider={self.provider}, status={self.status})>"

    def is_token_expired(self) -> bool:
        """Check if the access token has expired"""
        from datetime import datetime, timezone

        return self.token_expires_at <= datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if the connection is active and valid"""
        return (
            self.status == ConnectionStatus.ACTIVE
            and not self.is_token_expired()
        )
