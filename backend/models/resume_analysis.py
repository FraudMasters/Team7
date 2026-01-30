"""
ResumeAnalysis model for storing NLP/ML analysis results

This table stores extracted information from resumes including:
- Skills and keywords
- Named entities (organizations, dates, locations)
- Grammar issues
- Experience calculation
- Analysis metadata
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResumeAnalysis(Base, UUIDMixin, TimestampMixin):
    """
    ResumeAnalysis model for storing complete analysis results

    This table stores the results of NLP/ML analysis performed on resumes,
    avoiding the need to re-extract information from raw text on every request.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        language: Detected language (en, ru, etc.)
        raw_text: Extracted text from resume

        # Extracted data
        skills: List of extracted technical skills
        keywords: List of key phrases with relevance scores
        entities: Named entities (persons, orgs, dates, locations)

        # Analysis results
        total_experience_months: Total work experience in months
        education: Extracted education information
        contact_info: Extracted email, phone, links

        # Quality metrics
        grammar_issues: List of grammar/spelling errors found
        warnings: List of detected issues (missing info, etc.)
        quality_score: Overall resume quality score (0-100)

        # Processing metadata
        processing_time_seconds: Time taken for analysis
        analyzer_version: Version of the analyzer used
    """

    __tablename__ = "resume_analyses"

    # Reference to resume
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Language and text
    language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extracted data (JSON fields for flexibility)
    skills: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Analysis results
    total_experience_months: Mapped[Optional[int]] = mapped_column(nullable=True)
    education: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    contact_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Quality metrics
    grammar_issues: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    quality_score: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Processing metadata
    processing_time_seconds: Mapped[Optional[float]] = mapped_column(nullable=True)
    analyzer_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ResumeAnalysis(id={self.id}, resume_id={self.resume_id}, language={self.language})>"
