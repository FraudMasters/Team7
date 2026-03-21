"""
SearchQuery and PopularSearch models for search analytics
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SearchQuery(Base, UUIDMixin, TimestampMixin):
    """
    SearchQuery model for tracking all search queries performed in the system

    This model captures every search performed, enabling analytics on search patterns,
    popular queries, zero-result searches, and search performance optimization.

    Attributes:
        id: UUID primary key
        recruiter_id: Foreign key to Recruiter who performed the search
        query: Search query string with boolean operators
        filters: Filter settings in JSON format (skills, experience_years, location, language, etc.)
        results_count: Number of results returned by the search
        execution_time_ms: Time taken to execute the search in milliseconds
        search_type: Type of search performed (e.g., 'full_text', 'faceted', 'boolean')
        clicked_result_ids: Array of resume IDs that were clicked from results (stored as JSON)
        created_at: Timestamp when search was performed (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "search_queries"

    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    results_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(nullable=True)
    search_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    clicked_result_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="[]")

    def __repr__(self) -> str:
        return f"<SearchQuery(id={self.id}, query={self.query}, results={self.results_count})>"


class PopularSearch(Base, UUIDMixin, TimestampMixin):
    """
    PopularSearch model for aggregated popular search queries

    This model maintains aggregated statistics for popular search queries,
    enabling quick access to trending searches and search recommendations.

    Attributes:
        id: UUID primary key
        query: Search query string
        filters: Common filter settings for this query in JSON format
        search_count: Number of times this query has been searched
        avg_results_count: Average number of results returned
        avg_click_through_rate: Average click-through rate (clicks / results)
        last_searched_at: Timestamp when this query was last searched
        created_at: Timestamp when this popular search was first recorded (inherited)
        updated_at: Timestamp when statistics were last updated (inherited)
    """

    __tablename__ = "popular_searches"

    query: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, server_default="{}")
    search_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    avg_results_count: Mapped[Optional[float]] = mapped_column(nullable=True)
    avg_click_through_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    last_searched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<PopularSearch(id={self.id}, query={self.query}, count={self.search_count})>"
