"""
ScreeningRule model for per-vacancy screening configuration
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ScreeningRule(Base, UUIDMixin, TimestampMixin):
    """
    ScreeningRule model for per-vacancy screening configuration

    This model stores the screening rules for each job vacancy, including
    score thresholds, must-have skills, and automated rejection settings.
    These rules are used by the screening service to automatically categorize
    candidates into tiers (High Priority, Review, Reject).

    Attributes:
        id: UUID primary key
        vacancy_id: Foreign key to JobVacancy
        min_score_threshold: Minimum score (0-100) required to pass screening
        must_have_skills: JSON array of skills that are required (hard filter)
        auto_reject_threshold: Score below which candidates are auto-rejected (0-100)
        auto_reject_with_notification: Whether to send notification to rejected candidates
        high_priority_threshold: Score above which candidates are marked high priority (0-100)
        rule_priority: Priority order when multiple rules exist for a vacancy (lower = higher priority)
        is_active: Whether this rule is currently active
        created_at: Timestamp when rule was created (inherited)
        updated_at: Timestamp when rule was last updated (inherited)
    """

    __tablename__ = "screening_rules"

    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Score thresholds
    min_score_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=50.0
    )
    auto_reject_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=30.0
    )
    high_priority_threshold: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=80.0
    )

    # Must-have skills (hard filter)
    must_have_skills: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )

    # Auto-rejection settings
    auto_reject_with_notification: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )

    # Rule management
    rule_priority: Mapped[int] = mapped_column(
        Numeric(10, 0), nullable=False, default=100
    )
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningRule(id={self.id}, vacancy_id={self.vacancy_id}, "
            f"min_score_threshold={self.min_score_threshold}, is_active={self.is_active})>"
        )
