"""
CandidateFeedback model for storing constructive feedback for candidates
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateFeedback(Base, UUIDMixin, TimestampMixin):
    """
    CandidateFeedback model for storing constructive feedback for candidates

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        match_result_id: Foreign key to MatchResult
        template_id: Foreign key to FeedbackTemplate
        language: Language code for the feedback (e.g., 'en', 'ru')
        grammar_feedback: JSON object with grammar feedback
        skills_feedback: JSON object with skills feedback
        experience_feedback: JSON object with experience feedback
        recommendations: JSON array with recommendations
        match_score: Overall match score
        tone: Tone of feedback
        feedback_source: Source of feedback (automated, manual)
        viewed_by_candidate: Whether candidate has viewed the feedback
        downloaded: Whether feedback was downloaded
        extra_metadata: Additional metadata in JSON format
        created_at: Timestamp when feedback was created (inherited)
        updated_at: Timestamp when feedback was last updated (inherited)
    """

    __tablename__ = "candidate_feedback"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    match_result_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("match_results.id", ondelete="SET NULL"), nullable=True
    )
    template_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("feedback_templates.id", ondelete="SET NULL"), nullable=True
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    grammar_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    experience_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    recommendations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    match_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    tone: Mapped[str] = mapped_column(String(50), nullable=False, server_default="constructive")
    feedback_source: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="automated"
    )
    viewed_by_candidate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    downloaded: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateFeedback(id={self.id}, resume_id={self.resume_id}, language={self.language})>"
