"""
UserPreferences model for storing user language, locale, notification preferences,
profile settings, dashboard configuration, filter preferences, and API keys
"""
from typing import Optional

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class UserPreferences(Base, UUIDMixin, TimestampMixin):
    """
    UserPreferences model for storing user language, locale, notification settings,
    profile information, dashboard configuration, filter preferences, and API keys

    Attributes:
        id: UUID primary key
        language: User's preferred language code (en, ru, etc.)
        timezone: User's preferred timezone (optional)
        email_notifications: Whether user wants to receive email notifications
        in_app_notifications: Whether user wants to receive in-app notifications
        name: User's display name (optional)
        email: User's email address (optional)
        role: User's role (e.g., recruiter, hiring_manager) (optional)
        avatar_url: URL to user's avatar image (optional)
        dashboard_config: Dashboard layout and widget configuration (JSON)
        filter_preferences: Default filter settings for searches (JSON)
        api_keys: User's personal API keys for integrations (JSON)
        created_at: Timestamp when preference was created (inherited from TimestampMixin)
        updated_at: Timestamp when preference was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "user_preferences"

    # Language and notification preferences
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    in_app_notifications: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Profile fields
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Configuration fields (JSON)
    dashboard_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    filter_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    api_keys: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")

    def __repr__(self) -> str:
        return f"<UserPreferences(id={self.id}, language={self.language}, email_notifications={self.email_notifications})>"
