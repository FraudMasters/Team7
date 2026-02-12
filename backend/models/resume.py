"""
Resume model for storing uploaded resume data
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ResumeStatus(str, enum.Enum):
    """Status of resume processing and hiring pipeline"""

    # Processing statuses
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    # Hiring pipeline / Kanban stages
    NEW = "NEW"
    REVIEWED = "REVIEWED"      # Screening stage
    INTERVIEW = "INTERVIEW"    # Interview stage
    OFFERED = "OFFERED"        # Offer stage
    HIRED = "HIRED"            # Hired stage


class Resume(Base, UUIDMixin, TimestampMixin):
    """
    Resume model for storing uploaded resume files and metadata

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this resume
        vacancy_id: Optional vacancy ID if resume was submitted via vacancy-specific email
        filename: Original filename of uploaded resume
        file_path: Path to stored resume file
        content_type: MIME type of the file (e.g., application/pdf)
        status: Current processing status
        raw_text: Extracted text content from resume
        language: Detected language (en, ru, etc.)
        error_message: Error message if processing failed
        uploaded_at: Timestamp when resume was uploaded (inherited from TimestampMixin)
    """

    __tablename__ = "resumes"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus), default=ResumeStatus.PENDING, nullable=False, index=True
    )
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    job_applications: Mapped[list["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="resume"
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, org={self.organization_id}, filename={self.filename}, status={self.status.value})>"
