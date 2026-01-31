"""
WorkExperience model for storing structured work experience entries extracted from resumes

This table stores individual work experience entries extracted from resumes including:
- Company and job title
- Employment dates
- Job description
- Extraction confidence score
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class WorkExperience(Base, UUIDMixin, TimestampMixin):
    """
    WorkExperience model for storing structured work experience entries

    This table stores individual work experience entries extracted from resumes,
    providing structured access to employment history for analysis and matching.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        company: Name of the company/organization
        title: Job title/position
        start_date: Start date of employment
        end_date: End date of employment (null if currently employed)
        description: Job description and responsibilities
        confidence_score: Confidence score of extraction (0.0 to 1.0)
        created_at: Timestamp when record was created (inherited from TimestampMixin)
        updated_at: Timestamp when record was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "work_experiences"

    # Reference to resume
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Employment details
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quality metric
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<WorkExperience(id={self.id}, company={self.company}, title={self.title})>"
