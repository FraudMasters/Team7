"""
LinkedInImport model for tracking LinkedIn candidate import history
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LinkedInImportStatus(str, enum.Enum):
    """Status of LinkedIn import operations"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class LinkedInImport(Base, UUIDMixin, TimestampMixin):
    """
    LinkedInImport model for tracking LinkedIn candidate import history

    This model maintains a comprehensive audit trail of all LinkedIn candidate import
    operations, enabling recruiters to track the complete history of bulk imports from
    LinkedIn. It records import parameters, execution status, success/failure statistics,
    and any errors encountered during the import process.

    Attributes:
        id: UUID primary key
        status: Current status of the import operation
        recruiter_id: Foreign key to Recruiter who initiated the import
        vacancy_id: Optional foreign key to the job vacancy for which candidates were sourced
        source_type: Type of LinkedIn source (search, recruiter, etc.)
        search_params: JSON object containing the search parameters used
        total_candidates: Total number of candidates found/selected for import
        successful_imports: Number of candidates successfully imported
        failed_imports: Number of candidates that failed to import
        error_message: Optional error message if import failed
        linkedin_search_url: Optional LinkedIn search URL for reference
        import_metadata: JSON object with additional import-specific data
        notes: Optional text notes about the import operation
        created_at: Timestamp when import was initiated (inherited)
        updated_at: Timestamp when import was last updated (inherited)
    """

    __tablename__ = "linkedin_imports"

    status: Mapped[LinkedInImportStatus] = mapped_column(
        String(50), nullable=False, index=True, default=LinkedInImportStatus.PENDING
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    search_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_candidates: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    successful_imports: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    failed_imports: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_search_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<LinkedInImport(id={self.id}, status={self.status}, recruiter={self.recruiter_id})>"
