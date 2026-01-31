"""
UserPreferences model for storing user language, locale, and notification preferences
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class UserPreferences(Base, UUIDMixin, TimestampMixin):
    """
    UserPreferences model for storing user language, locale, and notification settings

    Attributes:
        id: UUID primary key
        language: User's preferred language code (en, ru, etc.)
        timezone: User's preferred timezone (optional)
        email_notifications: Whether user wants to receive email notifications
        in_app_notifications: Whether user wants to receive in-app notifications
        created_at: Timestamp when preference was created (inherited from TimestampMixin)
        updated_at: Timestamp when preference was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "user_preferences"

    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_app_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<UserPreferences(id={self.id}, language={self.language}, email_notifications={self.email_notifications})>"
