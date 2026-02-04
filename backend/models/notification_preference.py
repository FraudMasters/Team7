"""
NotificationPreference model for storing user notification preferences per event type and delivery channel
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DigestFrequency(str, enum.Enum):
    """Frequency options for email digests"""

    IMMEDIATE = "immediate"  # Send immediately (no digest)
    HOURLY = "hourly"  # Aggregate and send hourly
    DAILY = "daily"  # Aggregate and send daily
    WEEKLY = "weekly"  # Aggregate and send weekly
    NEVER = "never"  # Do not send


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """
    NotificationPreference model for granular user notification settings

    This model stores user preferences for receiving notifications by type
    and delivery channel. Each record represents a user's preference for
    a specific notification type (e.g., candidate_stage_changed) across
    different delivery channels (email, in-app, push, SMS).

    Attributes:
        id: UUID primary key
        user_id: Foreign key to the Recruiter (user) who owns these preferences
        notification_type: The type of notification this preference applies to
        email_enabled: Whether to send this notification type via email
        in_app_enabled: Whether to show this notification type in-app
        push_enabled: Whether to send this notification type via browser push
        sms_enabled: Whether to send this notification type via SMS
        digest_frequency: How frequently to aggregate email notifications (immediate, hourly, daily, weekly, never)
        created_at: Timestamp when preference was created (inherited from TimestampMixin)
        updated_at: Timestamp when preference was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "notification_preferences"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    digest_frequency: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id}, type={self.notification_type}, email={self.email_enabled})>"
