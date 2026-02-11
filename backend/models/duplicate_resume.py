"""
DuplicateResume model for tracking detected duplicate resumes
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class DuplicateResume(Base, UUIDMixin, TimestampMixin):
    """
    DuplicateResume model for tracking detected duplicate resumes

    Stores records of duplicate resume detections to help recruiters identify
    and review duplicate submissions during bulk upload operations.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns these resumes
        original_resume_id: ID of the first/original resume that was uploaded
        duplicate_resume_id: ID of the newly detected duplicate resume
        content_hash: SHA-256 hash of the file content used for detection
        batch_job_id: ID of the batch job that detected this duplicate
        detection_timestamp: When the duplicate was detected
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "duplicate_resumes"

    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    duplicate_resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    batch_job_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("batch_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    detection_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Relationships
    original_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[original_resume_id], backref="duplicates_found"
    )
    duplicate_resume: Mapped["Resume"] = relationship(
        "Resume", foreign_keys=[duplicate_resume_id], backref="duplicate_of"
    )
    batch_job: Mapped[Optional["BatchJob"]] = relationship(
        "BatchJob", backref="duplicates"
    )

    def __repr__(self) -> str:
        return f"<DuplicateResume(id={self.id}, original={self.original_resume_id}, duplicate={self.duplicate_resume_id})>"
