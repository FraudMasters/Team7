"""
ImportedResume model for tracking imported resume metadata from job boards
"""
import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ImportStatus(str, enum.Enum):
    """Status of resume import from job boards"""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    SYNCED = "SYNCED"


class ImportedResume(Base, UUIDMixin, TimestampMixin):
    """
    ImportedResume model for tracking resumes imported from job boards

    This model stores metadata about resumes that have been imported from
    external job boards, linking them to the actual Resume records and
    tracking the import status and synchronization state.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to the actual Resume record
        job_board_id: Foreign key to JobBoardIntegration (source)
        external_id: ID of the resume in the external job board system
        source_url: URL to the original resume on the job board
        import_status: Current status of the import process
        error_message: Error message if import failed
        metadata: Additional metadata from the job board (JSON)
        candidate_data: Candidate information from job board (JSON)
        job_title: Job title associated with the resume
        candidate_name: Name of the candidate
        candidate_email: Email of the candidate
        candidate_phone: Phone number of the candidate
        is_active: Whether this import record is active
        last_synced_at: Last time this record was synced with the source
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "imported_resumes"

    resume_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_board_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_board_integrations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    import_status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus), default=ImportStatus.PENDING, nullable=False, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    candidate_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict
    )
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    candidate_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<ImportedResume(id={self.id}, external_id={self.external_id}, status={self.import_status.value})>"
