"""
SalaryHistory model for tracking candidate salary progression over time
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SalaryHistory(Base, UUIDMixin, TimestampMixin):
    """
    SalaryHistory model for tracking candidate salary progression and compensation history

    This model stores historical salary data for candidates to enable:
    - Salary progression analysis
    - Offer comparison tools
    - Compensation trend tracking
    - Internal equity analysis

    Salary data is stored securely and compliantly with proper access controls.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        salary_amount: Base salary amount
        salary_frequency: Payment frequency (annual, monthly, hourly, weekly)
        currency: Currency code (ISO 4217, e.g., "USD", "EUR")
        effective_date: Date when this salary was/will be effective
        salary_type: Type of salary record (current, previous, offer, projected)
        employment_type: Employment type (full_time, contract, part_time, internship)
        job_title: Job title for this salary period
        company_name: Company name for this salary period
        location: Geographic location of the job
        country: Country code (ISO 3166-1 alpha-2)
        bonus_amount: Annual bonus amount (if applicable)
        bonus_type: Type of bonus (signing, performance, annual, none)
        equity_value: Estimated annual value of equity/stock grants
        equity_type: Type of equity (rsu, options, none)
        other_compensation: Other compensation details (JSON)
        total_compensation: Total annual compensation (salary + bonus + equity)
        is_confirmed: Whether salary data is confirmed or estimated
        data_source: Source of salary data (extracted, manual, api)
        verification_status: Verification status (unverified, self_reported, verified)
        metadata: Additional metadata (JSON) for extended properties
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "salary_history"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Main salary information
    salary_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    salary_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="annual"
    )  # annual, monthly, hourly, weekly
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD"
    )
    effective_date: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )  # YYYY-MM-DD format

    # Salary classification
    salary_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="current", index=True
    )  # current, previous, offer, projected
    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full_time"
    )  # full_time, contract, part_time, internship

    # Job details
    job_title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    company_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    country: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True, default=None
    )  # ISO 3166-1 alpha-2

    # Additional compensation
    bonus_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )
    bonus_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )  # signing, performance, annual, none
    equity_value: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )
    equity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )  # rsu, options, stock, none
    other_compensation: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=None
    )  # benefits, perks, etc.

    # Calculated fields
    total_compensation: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )  # Sum of salary + bonus + equity (annualized)

    # Data quality
    is_confirmed: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    data_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual"
    )  # extracted, manual, api, offer
    verification_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="self_reported", index=True
    )  # unverified, self_reported, verified

    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict
    )

    def __repr__(self) -> str:
        return (
            f"<SalaryHistory(id={self.id}, resume_id={self.resume_id}, "
            f"salary_amount={self.salary_amount} {self.currency}, "
            f"salary_type={self.salary_type}, effective_date={self.effective_date})>"
        )

    def calculate_total_compensation(self) -> Optional[float]:
        """
        Calculate total annual compensation

        Returns:
            Total annual compensation including salary, bonus, and equity,
            or None if components are missing
        """
        if not self.salary_amount:
            return None

        total = float(self.salary_amount)

        # Adjust salary to annual if needed
        if self.salary_frequency == "monthly":
            total *= 12
        elif self.salary_frequency == "weekly":
            total *= 52
        elif self.salary_frequency == "hourly":
            # Assume 2080 hours per year (40 hours/week * 52 weeks)
            total *= 2080

        # Add bonus (assumed annual)
        if self.bonus_amount:
            total += float(self.bonus_amount)

        # Add equity value (assumed annual)
        if self.equity_value:
            total += float(self.equity_value)

        return round(total, 2)
