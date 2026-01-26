"""
SearchAlert model for notifications when new resumes match saved searches
"""
from typing import Optional

from sqlalchemy import ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SearchAlert(Base, UUIDMixin, TimestampMixin):
    """
    SearchAlert model for notifications when new resumes match saved searches

    Attributes:
        id: UUID primary key
        saved_search_id: Foreign key to SavedSearch
        resume_id: Foreign key to Resume
        is_sent: Whether the notification has been sent
        sent_at: Timestamp when the notification was sent
        error_message: Error message if notification sending failed
        created_at: Timestamp when alert was created (inherited)
        updated_at: Timestamp when alert was last updated (inherited)
    """

    __tablename__ = "search_alerts"

    saved_search_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("saved_searches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    sent_at: Mapped[Optional[object]] = mapped_column(
        nullable=True
    )  # DateTime timezone=True type
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SearchAlert(id={self.id}, saved_search_id={self.saved_search_id}, is_sent={self.is_sent})>"
