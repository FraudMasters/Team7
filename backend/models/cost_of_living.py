"""
CostOfLivingIndex model for storing geographic cost of living adjustments
"""
from typing import Optional

from sqlalchemy import JSON, String, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CostOfLivingIndex(Base, UUIDMixin, TimestampMixin):
    """
    CostOfLivingIndex model for storing geographic cost of living data for compensation adjustments

    Attributes:
        id: UUID primary key
        location: Geographic location (city, state, or country)
        country: Country code (ISO 3166-1 alpha-2)
        region: Region or state/province
        cost_of_living_index: Overall cost of living index (baseline = 100)
        housing_index: Housing cost index component
        transportation_index: Transportation cost index component
        groceries_index: Groceries cost index component
        utilities_index: Utilities cost index component
        healthcare_index: Healthcare cost index component
        currency: Currency code (ISO 4217, e.g., "USD", "EUR")
        data_source: Source of the cost of living data (e.g., "api", "internal", "survey")
        source_url: URL to the original data source (if applicable)
        effective_date: Date when this index data is effective
        metadata: Additional metadata (JSON) for extended properties
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "cost_of_living_indices"

    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cost_of_living_index: Mapped[float] = mapped_column(Float, nullable=False)
    housing_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transportation_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    groceries_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    utilities_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    healthcare_index: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    data_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    effective_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    def __repr__(self) -> str:
        return f"<CostOfLivingIndex(id={self.id}, location={self.location}, index={self.cost_of_living_index})>"
