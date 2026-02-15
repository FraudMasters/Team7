"""
SavedSearch model for storing user search queries and filter configurations
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SavedSearch(Base, UUIDMixin, TimestampMixin):
    """
    SavedSearch model for storing user search queries and filter configurations

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to Recruiter
        name: User-provided name for the saved search
        query: Search query string with boolean operators
        filters: Filter settings in JSON format (skills, experience_years, location, language, etc.)
        alert_enabled: Whether automatic alerts are enabled for this saved search
        alert_frequency: Frequency of alerts (e.g., 'daily', 'weekly', 'realtime')
        last_alert_at: Timestamp when the last alert was sent for this search
        created_at: Timestamp when search was saved (inherited)
        updated_at: Timestamp when search was last updated (inherited)
    """

    __tablename__ = "saved_searches"

    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", index=True
    )
    alert_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_alert_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<SavedSearch(id={self.id}, name={self.name})>"
