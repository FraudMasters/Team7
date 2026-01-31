"""
SkillFeedback model for storing recruiter feedback on skill matches
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SkillFeedback(Base, UUIDMixin, TimestampMixin):
    """
    SkillFeedback model for storing recruiter feedback on skill matching

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        match_result_id: Foreign key to MatchResult (optional)
        skill: The skill name that was matched
        was_correct: Whether the AI's match was correct
        confidence_score: The confidence score the AI assigned (0-1)
        recruiter_correction: What the recruiter corrected it to (if incorrect)
        actual_skill: The actual skill found by the recruiter
        feedback_source: Source of feedback (api, frontend, bulk_import)
        processed: Whether this feedback has been processed by ML pipeline
        extra_metadata: JSON object with additional feedback metadata
        created_at: Timestamp when feedback was submitted (inherited)
        updated_at: Timestamp when feedback was last updated (inherited)
    """

    __tablename__ = "skill_feedback"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_result_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True
    )
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    was_correct: Mapped[bool] = mapped_column(nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    recruiter_correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actual_skill: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    feedback_source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="api"
    )
    processed: Mapped[bool] = mapped_column(nullable=False, default=False)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillFeedback(id={self.id}, skill={self.skill}, correct={self.was_correct})>"
