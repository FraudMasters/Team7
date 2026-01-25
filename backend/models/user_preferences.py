"""
UserPreferences model for storing user language and locale preferences
"""
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class UserPreferences(Base, UUIDMixin, TimestampMixin):
    """
    UserPreferences model for storing user language and locale settings

    Attributes:
        id: UUID primary key
        language: User's preferred language code (en, ru, etc.)
        timezone: User's preferred timezone (optional)
        created_at: Timestamp when preference was created (inherited from TimestampMixin)
        updated_at: Timestamp when preference was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "user_preferences"

    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<UserPreferences(id={self.id}, language={self.language})>"
