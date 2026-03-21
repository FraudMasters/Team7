"""
SearchRelevanceConfig model for storing search result relevance boost values
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SearchRelevanceConfig(Base, UUIDMixin, TimestampMixin):
    """
    SearchRelevanceConfig model for storing search result relevance boost values

    This model stores boost values for different fields in Elasticsearch queries,
    allowing administrators to fine-tune search result relevance scoring.
    Higher boost values give more weight to that field in the relevance calculation.

    Attributes:
        id: UUID primary key
        name: Name/description of this configuration (e.g., "Default", "Skills-focused")
        skills_boost: Boost value for skills field (default: 1.0)
        experience_boost: Boost value for experience field (default: 1.0)
        education_boost: Boost value for education field (default: 1.0)
        location_boost: Boost value for location field (default: 1.0)
        is_active: Whether this configuration is currently active
        created_at: Timestamp when configuration was created (inherited)
        updated_at: Timestamp when configuration was last updated (inherited)
    """

    __tablename__ = "search_relevance_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skills_boost: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1.0"
    )
    experience_boost: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1.0"
    )
    education_boost: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1.0"
    )
    location_boost: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="1.0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )

    def __repr__(self) -> str:
        return f"<SearchRelevanceConfig(id={self.id}, name={self.name}, active={self.is_active})>"
