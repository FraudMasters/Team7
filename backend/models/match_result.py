"""
MatchResult model for storing resume-vacancy matching results
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MatchResult(Base, UUIDMixin, TimestampMixin):
    """
    MatchResult model for storing resume-to-vacancy matching results

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        match_percentage: Overall match score (0-100) - legacy field
        matched_skills: JSON array of skills found in resume with metadata
        missing_skills: JSON array of required skills not found in resume
        additional_skills_matched: JSON array of additional skills matched
        experience_verified: Whether experience requirements were met
        experience_details: JSON object with experience breakdown by skill

        # Unified matching metrics
        overall_score: Combined score from all methods (0-1)
        keyword_score: Enhanced keyword matching score (0-1)
        tfidf_score: TF-IDF weighted score (0-1)
        vector_score: Semantic similarity score (0-1)
        vector_similarity: Raw cosine similarity (-1 to 1)
        recommendation: Hiring recommendation (excellent/good/maybe/poor)
        keyword_passed: Whether keyword matching threshold was met
        tfidf_passed: Whether TF-IDF threshold was met
        vector_passed: Whether vector threshold was met
        tfidf_matched: JSON array of matched keywords from TF-IDF
        tfidf_missing: JSON array of missing keywords from TF-IDF
        matcher_version: Version of the matcher used

        created_at: Timestamp when match was computed (inherited)
        updated_at: Timestamp when match was last updated (inherited)
    """

    __tablename__ = "match_results"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Legacy fields
    match_percentage: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )
    matched_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    missing_skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    additional_skills_matched: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    experience_verified: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    experience_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Unified matching metrics
    overall_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    keyword_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    tfidf_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    vector_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    vector_similarity: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )
    recommendation: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default=None
    )
    keyword_passed: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    tfidf_passed: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    vector_passed: Mapped[Optional[bool]] = mapped_column(nullable=True, default=None)
    tfidf_matched: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    tfidf_missing: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    matcher_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="unified-v1"
    )

    def __repr__(self) -> str:
        return (
            f"<MatchResult(id={self.id}, resume_id={self.resume_id}, "
            f"vacancy_id={self.vacancy_id}, overall_score={self.overall_score})>"
        )
