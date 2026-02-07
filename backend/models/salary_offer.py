"""
SalaryOffer model for tracking job offers and compensation packages
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SalaryOffer(Base, UUIDMixin, TimestampMixin):
    """
    SalaryOffer model for tracking job offers and compensation packages

    This model stores salary offer data for candidates to enable:
    - Offer comparison with current compensation
    - Offer negotiation tracking
    - Compensation package analysis
    - Internal equity comparison

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume (candidate)
        job_vacancy_id: Foreign key to JobVacancy (role being offered)
        offer_status: Current status of the offer (draft, sent, accepted, rejected, expired, withdrawn)
        salary_amount: Base salary amount being offered
        salary_frequency: Payment frequency (annual, monthly, hourly, weekly)
        currency: Currency code (ISO 4217, e.g., "USD", "EUR")
        start_date: Proposed start date for the role
        employment_type: Employment type (full_time, contract, part_time, internship)
        job_title: Job title for the offer
        bonus_amount: Annual bonus amount (if applicable)
        bonus_type: Type of bonus (signing, performance, annual, none)
        equity_value: Estimated annual value of equity/stock grants
        equity_type: Type of equity (rsu, options, stock, none)
        other_compensation: Other compensation details (JSON) - benefits, perks, etc.
        total_compensation: Total annual compensation (salary + bonus + equity)
        current_salary: Candidate's current salary for comparison
        current_total_comp: Candidate's current total compensation
        increase_percentage: Percentage increase from current compensation
        offer_expires_at: Deadline for candidate to respond
        responded_at: Timestamp when candidate responded
        negotiation_round: Number of negotiation rounds (0 for initial offer)
        notes: Additional notes about the offer
        metadata: Additional metadata (JSON) for extended properties
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "salary_offers"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Offer status
    offer_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )  # draft, sent, accepted, rejected, expired, withdrawn

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
    start_date: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, default=None
    )  # YYYY-MM-DD format

    # Employment details
    employment_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full_time"
    )  # full_time, contract, part_time, internship
    job_title: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )

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

    # Comparison fields
    current_salary: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )  # Candidate's current salary
    current_total_comp: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True, default=None
    )  # Candidate's current total comp
    increase_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True, default=None
    )  # Percentage increase from current

    # Offer timeline
    offer_expires_at: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, default=None
    )  # YYYY-MM-DD format
    responded_at: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, default=None
    )  # YYYY-MM-DD format

    # Negotiation tracking
    negotiation_round: Mapped[int] = mapped_column(
        nullable=False, default=0
    )  # 0 for initial offer, increments with counter-offers

    # Additional information
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=dict
    )

    def __repr__(self) -> str:
        return (
            f"<SalaryOffer(id={self.id}, resume_id={self.resume_id}, "
            f"job_vacancy_id={self.job_vacancy_id}, "
            f"salary_amount={self.salary_amount} {self.currency}, "
            f"offer_status={self.offer_status})>"
        )

    def calculate_total_compensation(self) -> Optional[float]:
        """
        Calculate total annual compensation for the offer

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

    def calculate_increase_percentage(self) -> Optional[float]:
        """
        Calculate percentage increase from current compensation

        Returns:
            Percentage increase from current total compensation,
            or None if current compensation is not available
        """
        if not self.current_total_comp or not self.total_compensation:
            return None

        if self.current_total_comp == 0:
            return None

        increase = (
            (float(self.total_compensation) - float(self.current_total_comp))
            / float(self.current_total_comp)
        ) * 100

        return round(increase, 2)

    def is_expired(self) -> bool:
        """
        Check if the offer has expired

        Returns:
            True if the offer has an expiration date and it has passed,
            False otherwise
        """
        from datetime import datetime

        if not self.offer_expires_at:
            return False

        try:
            expiration_date = datetime.strptime(self.offer_expires_at, "%Y-%m-%d")
            return expiration_date < datetime.now()
        except (ValueError, TypeError):
            return False
