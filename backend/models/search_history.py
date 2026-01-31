"""
SearchHistory model for tracking candidate search queries and results
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SearchHistory(Base, UUIDMixin, TimestampMixin):
    """
    SearchHistory model for tracking candidate search queries and results

    This model maintains a comprehensive history of all candidate searches performed,
    enabling recruiters to review and repeat previous searches. It stores the search
    query, filters applied, results count, and performance metrics.

    Attributes:
        id: UUID primary key
        query: Search query string with boolean operators
        filters: Filter settings in JSON format (skills, experience, location, etc.)
        results_count: Number of results returned by the search
        execution_time_seconds: Time taken to execute the search
        recruiter_id: Optional foreign key to Recruiter who performed the search
        search_metadata: Additional metadata about the search (user agent, IP, etc.)
        created_at: Timestamp when search was performed (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "search_history"

    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True, index=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    results_count: Mapped[Optional[int]] = mapped_column(nullable=True)
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    search_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<SearchHistory(id={self.id}, query={self.query}, results={self.results_count})>"
