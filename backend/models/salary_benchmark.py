"""
SalaryBenchmark model for storing market salary data
"""
from typing import Optional

from sqlalchemy import JSON, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SalaryBenchmark(Base, UUIDMixin, TimestampMixin):
    """
    SalaryBenchmark model for storing market salary data for compensation analysis

    Attributes:
        id: UUID primary key
        job_title: Standardized job title (e.g., "Software Engineer", "Product Manager")
        location: Geographic location (city, state, or "Remote")
        country: Country code (ISO 3166-1 alpha-2)
        region: Region or state/province
        industry: Industry sector for specialized roles
        experience_level: Experience level (entry, mid, senior, lead, executive)
        employment_type: Employment type (full_time, contract, part_time)
        salary_min: Minimum salary (p25)
        salary_median: Median salary (p50)
        salary_max: Maximum salary (p75)
        salary_p90: 90th percentile salary
        currency: Currency code (ISO 4217, e.g., "USD", "EUR")
        sample_size: Number of data points in this benchmark
        data_source: Source of the salary data (e.g., "market_api", "internal", "survey")
        source_url: URL to the original data source (if applicable)
        effective_date: Date when this benchmark data is effective
        metadata: Additional metadata (JSON) for extended properties
        created_at: Timestamp when benchmark was created (inherited)
        updated_at: Timestamp when benchmark was last updated (inherited)
    """

    __tablename__ = "salary_benchmarks"

    job_title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="full_time")
    salary_min: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_median: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_p90: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    sample_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    effective_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    def __repr__(self) -> str:
        return f"<SalaryBenchmark(id={self.id}, job_title={self.job_title}, location={self.location})>"
