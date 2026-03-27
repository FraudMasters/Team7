"""
RecentSearch model for tracking per-user recent search queries
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RecentSearch(Base, UUIDMixin, TimestampMixin):
    """
    RecentSearch model for tracking recent search queries per user

    This model stores the most recent searches for each recruiter, enabling
    quick access to their search history and search suggestions based on
    their previous queries.

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to Recruiter who performed the search
        query: Search query string with boolean operators
        filters: Filter settings in JSON format (skills, experience_years, location, language, etc.)
        results_count: Number of results returned by the search
        created_at: Timestamp when search was performed (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "recent_searches"

    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    results_count: Mapped[Optional[int]] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint('recruiter_id', 'query', name='uq_recent_search_recruiter_query'),
    )

    def __repr__(self) -> str:
        return f"<RecentSearch(id={self.id}, recruiter_id={self.recruiter_id}, query={self.query})>"
