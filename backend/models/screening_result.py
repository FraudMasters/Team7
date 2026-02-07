"""
ScreeningResult model for storing screening outcomes
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ScreeningResult(Base, UUIDMixin, TimestampMixin):
    """
    ScreeningResult model for storing automated screening outcomes

    This model stores the results of the automated screening process that
    applies rule-based filters, ML scoring thresholds, and recruiter feedback
    patterns to categorize candidates into tiers (High Priority, Review, Reject).

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        screening_rule_id: Foreign key to ScreeningRule used
        tier: Screening tier category (HIGH_PRIORITY, REVIEW, REJECT)
        score_applied: The ranking score that was applied (0-100)
        rejection_reasons: JSON array of reasons for rejection (if applicable)
        screening_timestamp: Timestamp when screening was performed
        auto_response_sent: Whether auto-response email was sent to candidate
        review_reminder_sent: Whether review reminder was sent to recruiter
        notification_sent_at: Timestamp when last notification was sent
        created_at: Timestamp when result was created (inherited)
        updated_at: Timestamp when result was last updated (inherited)
    """

    __tablename__ = "screening_results"

    # References to resume, vacancy, and screening rule
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    screening_rule_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("screening_rules.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )

    # Tier categorization
    tier: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # HIGH_PRIORITY, REVIEW, REJECT

    # Score applied during screening
    score_applied: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )

    # Rejection details
    rejection_reasons: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Screening timestamp
    screening_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Notification tracking
    auto_response_sent: Mapped[bool] = mapped_column(nullable=False, default=False)
    review_reminder_sent: Mapped[bool] = mapped_column(nullable=False, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningResult(id={self.id}, resume_id={self.resume_id}, "
            f"vacancy_id={self.vacancy_id}, tier={self.tier}, "
            f"score_applied={self.score_applied})>"
        )
