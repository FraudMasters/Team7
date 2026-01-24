"""
Resume model for storing uploaded resume data
"""
import enum
from typing import Optional

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResumeStatus(str, enum.Enum):
    """Status of resume processing"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Resume(Base, UUIDMixin, TimestampMixin):
    """
    Resume model for storing uploaded resume files and metadata

    Attributes:
        id: UUID primary key
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

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ResumeStatus] = mapped_column(
        Enum(ResumeStatus), default=ResumeStatus.PENDING, nullable=False, index=True
    )
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, filename={self.filename}, status={self.status.value})>"
