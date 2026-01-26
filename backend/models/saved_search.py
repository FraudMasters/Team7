"""
SavedSearch model for storing user search queries and filter configurations
"""
from typing import Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SavedSearch(Base, UUIDMixin, TimestampMixin):
    """
    SavedSearch model for storing user search queries and filter configurations

    Attributes:
        id: UUID primary key
        name: User-provided name for the saved search
        query: Search query string with boolean operators
        filters: Filter settings in JSON format (skills, experience_years, location, language, etc.)
        created_at: Timestamp when search was saved (inherited)
        updated_at: Timestamp when search was last updated (inherited)
    """

    __tablename__ = "saved_searches"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")

    def __repr__(self) -> str:
        return f"<SavedSearch(id={self.id}, name={self.name})>"
