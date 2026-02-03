"""
ImportLog model for tracking import history and failures
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ImportJobStatus(str, enum.Enum):
    """Status of import job from job boards"""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class ImportLog(Base, UUIDMixin, TimestampMixin):
    """
    ImportLog model for tracking resume import history and failures

    This model maintains a comprehensive audit trail of all import operations
    from external job boards, enabling system administrators to monitor
    import performance, track failures, and trigger retries for failed imports.

    Attributes:
        id: UUID primary key
        job_board_id: Foreign key to JobBoardIntegration (source)
        imported_resume_id: Optional foreign key to related ImportedResume
        status: Status of the import job
        records_processed: Total number of records processed in this job
        records_succeeded: Number of successfully imported records
        records_failed: Number of failed records
        error_message: Summary of error if import failed
        error_details: JSON object with detailed error information
        import_metadata: JSON object with additional import job data
        started_at: Timestamp when the import job started
        completed_at: Timestamp when the import job completed
        retry_count: Number of times this import has been retried
        created_at: Timestamp when log entry was created (inherited)
        updated_at: Timestamp when log entry was last updated (inherited)
    """

    __tablename__ = "import_logs"

    job_board_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_board_integrations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    imported_resume_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("imported_resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ImportJobStatus] = mapped_column(
        String(50), nullable=False, index=True, default=ImportJobStatus.IN_PROGRESS
    )
    records_processed: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=0
    )
    records_succeeded: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=0
    )
    records_failed: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=0
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    import_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retry_count: Mapped[Optional[int]] = mapped_column(nullable=True, default=0)

    def __repr__(self) -> str:
        return f"<ImportLog(id={self.id}, status={self.status}, records_processed={self.records_processed})>"
