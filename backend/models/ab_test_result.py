"""
ABTestResult model for storing A/B testing outcomes
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ABTestResult(Base, UUIDMixin, TimestampMixin):
    """
    ABTestResult model for storing individual A/B test outcomes

    Tracks the outcome of each matching operation performed during an A/B test,
    linking the test variant used to the actual match result and hiring outcome.

    Attributes:
        id: UUID primary key
        ab_test_id: Foreign key to ABTest
        vacancy_id: Foreign key to JobVacancy being tested
        resume_id: Foreign key to Resume being matched
        match_result_id: Foreign key to MatchResult that was generated
        variant_assigned: Which variant was used ('a' or 'b')
        outcome: Hiring outcome (hired/rejected/pending/shortlisted)
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ab_test_results"

    ab_test_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ab_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_vacancies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_result_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("match_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_assigned: Mapped[str] = mapped_column(
        String(1), nullable=False, index=True
    )
    outcome: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return (
            f"<ABTestResult(id={self.id}, test_id={self.ab_test_id}, "
            f"variant={self.variant_assigned}, outcome={self.outcome})>"
        )
