"""
Backup model for tracking backup and restore operations
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, BigInteger, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class BackupType(str, enum.Enum):
    """Type of backup"""

    DATABASE = "database"
    FILES = "files"
    MODELS = "models"
    FULL = "full"


class BackupStatus(str, enum.Enum):
    """Status of backup operation"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    RESTORING = "restoring"


class Backup(Base, UUIDMixin, TimestampMixin):
    """
    Backup model for tracking backup and restore operations

    Attributes:
        id: UUID primary key
        name: Human-readable name for the backup
        type: Type of backup (database/files/models/full)
        status: Current status of the backup operation
        size_bytes: Size of the backup in bytes
        backup_path: File system path to the backup archive
        completed_at: Timestamp when backup completed
        retention_days: Number of days to retain this backup
        checksum: SHA256 checksum for integrity verification
        is_incremental: Whether this is an incremental backup
        parent_backup_id: ID of parent backup for incremental backups
        s3_uploaded: Whether backup has been uploaded to S3
        s3_key: S3 object key if uploaded
        error_message: Error message if backup failed
        files_count: Number of files in backup
        tables_count: Number of database tables in backup
    """

    __tablename__ = "backups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[BackupType] = mapped_column(
        Enum(BackupType), default=BackupType.FULL, nullable=False, index=True
    )
    status: Mapped[BackupStatus] = mapped_column(
        Enum(BackupStatus), default=BackupStatus.PENDING, nullable=False, index=True
    )
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    backup_path: Mapped[str] = mapped_column(String(512), nullable=False)
    completed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    is_incremental: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_backup_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    s3_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    s3_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    files_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tables_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Backup(id={self.id}, name={self.name}, type={self.type.value}, status={self.status.value})>"


class BackupConfig(Base, TimestampMixin):
    """
    Backup configuration model for system-wide backup settings

    Attributes:
        id: Primary key (auto-increment)
        retention_days: Default retention period in days
        backup_schedule: Cron expression for scheduled backups
        s3_enabled: Whether S3 off-site backup is enabled
        s3_bucket: S3 bucket name
        s3_endpoint: S3-compatible endpoint URL
        s3_access_key: S3 access key ID
        s3_secret_key: S3 secret access key (encrypted)
        s3_region: S3 region
        notification_email: Email for backup failure notifications
        enabled: Whether automated backups are enabled
        incremental_enabled: Whether incremental backups are enabled
        compression_enabled: Whether to compress backups
        last_backup_at: Timestamp of last successful backup
        last_backup_status: Status of last backup attempt
    """

    __tablename__ = "backup_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    backup_schedule: Mapped[str] = mapped_column(
        String(100), default="0 2 * * *", nullable=False
    )  # Daily at 2 AM
    s3_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    s3_bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_endpoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    s3_access_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_secret_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_region: Mapped[Optional[str]] = mapped_column(String(50), default="us-east-1", nullable=True)
    notification_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    incremental_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    compression_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_backup_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_backup_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:
        return f"<BackupConfig(id={self.id}, enabled={self.enabled}, retention_days={self.retention_days})>"
