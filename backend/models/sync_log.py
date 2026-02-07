"""
SyncLog model for tracking sync operations, errors, and status
"""
import enum
from uuid import UUID
from typing import Optional

from sqlalchemy import ForeignKey, JSON, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SyncType(str, enum.Enum):
    """Types of sync operations that can be performed"""

    FULL_SYNC = "full_sync"
    INCREMENTAL_SYNC = "incremental_sync"
    WEBHOOK = "webhook"
    MANUAL_SYNC = "manual_sync"
    SCHEDULED_SYNC = "scheduled_sync"


class SyncStatus(str, enum.Enum):
    """Status of sync operations"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class SyncLog(Base, UUIDMixin, TimestampMixin):
    """
    SyncLog model for tracking sync operations, errors, and status

    This model enables comprehensive tracking of all sync operations performed
    with external HRIS/ATS platforms, allowing for monitoring, error recovery,
    and audit trail generation.

    Attributes:
        id: UUID primary key
        integration_id: Foreign key to Integration being synced
        sync_type: Type of sync operation performed
        status: Current status of the sync operation
        records_processed: Number of records processed in the sync
        records_successful: Number of records successfully synced
        records_failed: Number of records that failed to sync
        started_at: Timestamp when the sync operation started
        completed_at: Timestamp when the sync operation completed
        error_message: Optional error message if sync failed
        error_details: JSON object with detailed error information
        sync_metadata: JSON object with sync-specific metadata and configuration
        created_at: Timestamp when log entry was created (inherited)
        updated_at: Timestamp when log entry was last updated (inherited)
    """

    __tablename__ = "sync_logs"

    integration_id: Mapped[UUID] = mapped_column(
        ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sync_type: Mapped[SyncType] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[SyncStatus] = mapped_column(
        String(50), nullable=False, index=True
    )
    records_processed: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    records_successful: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    records_failed: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=0
    )
    started_at: Mapped[Optional[object]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[object]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sync_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, integration_id={self.integration_id}, type={self.sync_type}, status={self.status})>"
