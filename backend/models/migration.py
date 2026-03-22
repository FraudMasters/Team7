"""
Migration model for tracking data migration operations between systems
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MigrationStatus(str, enum.Enum):
    """Status of migration operations"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class MigrationType(str, enum.Enum):
    """Types of migration operations"""

    FULL_MIGRATION = "full_migration"
    PARTIAL_MIGRATION = "partial_migration"
    DATA_SYNC = "data_sync"
    SYSTEM_UPGRADE = "system_upgrade"


class Migration(Base, UUIDMixin, TimestampMixin):
    """
    Migration model for tracking data migration operations between systems

    This model maintains a comprehensive audit trail of all data migration operations,
    enabling HR teams to track migrations between different ATS platforms (e.g.,
    Greenhouse to AgentHR, Lever to AgentHR). It records migration parameters,
    execution status, success/failure statistics, and any errors encountered during
    the migration process.

    Attributes:
        id: UUID primary key
        status: Current status of the migration operation
        migration_type: Type of migration being performed
        recruiter_id: Foreign key to Recruiter who initiated the migration
        source_system: Name of source system being migrated from
        target_system: Name of target system being migrated to (usually AgentHR)
        source_system_version: Optional version of source system
        total_records: Total number of records to migrate
        successful_migrations: Number of records successfully migrated
        failed_migrations: Number of records that failed to migrate
        skipped_records: Number of records skipped (duplicates, invalid data, etc.)
        error_message: Optional error message if migration failed
        migration_metadata: JSON object with additional migration-specific data
        validation_errors: JSON array of validation errors encountered
        entity_types: JSON array of entity types being migrated (candidates, jobs, etc.)
        notes: Optional text notes about the migration operation
        started_at: Optional timestamp when migration processing started
        completed_at: Optional timestamp when migration was completed
        created_at: Timestamp when migration was initiated (inherited)
        updated_at: Timestamp when migration was last updated (inherited)
    """

    __tablename__ = "migrations"

    status: Mapped[MigrationStatus] = mapped_column(
        Enum(MigrationStatus), default=MigrationStatus.PENDING, nullable=False, index=True
    )
    migration_type: Mapped[MigrationType] = mapped_column(
        Enum(MigrationType), nullable=False, index=True
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_system: Mapped[str] = mapped_column(
        String(100), nullable=False, default="AgentHR"
    )
    source_system_version: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    total_records: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    successful_migrations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_migrations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    migration_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    validation_errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    entity_types: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<Migration(id={self.id}, source={self.source_system}, status={self.status.value})>"
