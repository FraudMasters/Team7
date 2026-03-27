"""
ImportJob model for tracking import operations from various formats
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ImportJobStatus(str, enum.Enum):
    """Status of import operations"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class ImportFormat(str, enum.Enum):
    """Supported import formats"""

    LINKEDIN_CSV = "linkedin_csv"
    INDEED_XML = "indeed_xml"
    HRXML = "hrxml"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKABLE = "workable"
    CUSTOM_JSON = "custom_json"
    CUSTOM_CSV = "custom_csv"


class ImportJob(Base, UUIDMixin, TimestampMixin):
    """
    ImportJob model for tracking import operations from various formats

    This model maintains a comprehensive audit trail of all data import operations,
    enabling HR teams to track imports from LinkedIn CSV, Indeed XML, HR-XML, and
    other ATS platforms. It records import parameters, execution status, success/failure
    statistics, and any errors encountered during the import process.

    Attributes:
        id: UUID primary key
        status: Current status of the import operation
        format: Format of the import source (LinkedIn CSV, Indeed XML, etc.)
        recruiter_id: Foreign key to Recruiter who initiated the import
        vacancy_id: Optional foreign key to the job vacancy for which candidates were sourced
        file_path: File system path to the uploaded import file
        file_size_bytes: Size of the import file in bytes
        original_filename: Original name of the uploaded file
        total_records: Total number of records found in import file
        successful_imports: Number of records successfully imported
        failed_imports: Number of records that failed to import
        skipped_records: Number of records skipped (duplicates, invalid data, etc.)
        error_message: Optional error message if import failed
        import_metadata: JSON object with additional import-specific data
        validation_errors: JSON array of validation errors encountered
        source_system: Optional name of source ATS system for migrations
        notes: Optional text notes about the import operation
        created_at: Timestamp when import was initiated (inherited)
        updated_at: Timestamp when import was last updated (inherited)
    """

    __tablename__ = "import_jobs"

    status: Mapped[ImportJobStatus] = mapped_column(
        Enum(ImportJobStatus), default=ImportJobStatus.PENDING, nullable=False, index=True
    )
    format: Mapped[ImportFormat] = mapped_column(
        Enum(ImportFormat), nullable=False, index=True
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_records: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    successful_imports: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_imports: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, format={self.format.value}, status={self.status.value})>"
