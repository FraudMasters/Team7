"""
BatchJob model for tracking batch resume processing operations
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class BatchJobStatus(str, enum.Enum):
    """Status of batch job processing"""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class BatchJob(Base, UUIDMixin, TimestampMixin):
    """
    BatchJob model for tracking batch resume processing operations

    Attributes:
        id: UUID primary key
        total_files: Total number of files in the batch
        processed_files: Number of files successfully processed
        failed_files: Number of files that failed to process
        status: Current status of the batch job
        notification_email: Email to send notification to when complete
        celery_task_id: ID of the background Celery task processing this batch
        error_message: Error message if the batch failed
        completed_at: Timestamp when the batch completed
        created_at: Timestamp when batch was created (inherited)
        updated_at: Timestamp when batch was last updated (inherited)
    """

    __tablename__ = "batch_jobs"

    total_files: Mapped[int] = mapped_column(nullable=False)
    processed_files: Mapped[int] = mapped_column(server_default="0", nullable=False)
    failed_files: Mapped[int] = mapped_column(server_default="0", nullable=False)
    status: Mapped[BatchJobStatus] = mapped_column(
        Enum(BatchJobStatus), default=BatchJobStatus.pending, nullable=False, index=True
    )
    notification_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<BatchJob(id={self.id}, status={self.status.value}, processed={self.processed_files}/{self.total_files})>"
