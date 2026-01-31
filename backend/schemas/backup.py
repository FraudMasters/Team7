"""
Pydantic schemas for backup and restore operations
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class BackupType(str):
    """Type of backup"""
    DATABASE = "database"
    FILES = "files"
    MODELS = "models"
    FULL = "full"


class BackupStatus(str):
    """Status of backup operation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    RESTORING = "restoring"


class S3Config(BaseModel):
    """S3 configuration for off-site backups"""

    enabled: bool = Field(False, description="Enable S3 off-site backup")
    bucket: Optional[str] = Field(None, description="S3 bucket name")
    endpoint: Optional[str] = Field(None, description="S3-compatible endpoint URL")
    access_key: Optional[str] = Field(None, description="S3 access key ID")
    secret_key: Optional[str] = Field(None, description="S3 secret access key")
    region: str = Field("us-east-1", description="S3 region")


class BackupCreate(BaseModel):
    """Request model for creating a new backup"""

    name: str = Field(..., description="Human-readable name for the backup")
    type: str = Field("full", description="Type of backup: database, files, models, or full")
    retention_days: int = Field(30, ge=1, le=365, description="Retention period in days")
    is_incremental: bool = Field(False, description="Create incremental backup if possible")
    upload_to_s3: bool = Field(False, description="Upload to S3 after creation")

    @validator("type")
    def validate_type(cls, v):
        valid_types = ["database", "files", "models", "full"]
        if v not in valid_types:
            raise ValueError(f"Invalid backup type. Must be one of: {', '.join(valid_types)}")
        return v


class BackupRestoreRequest(BaseModel):
    """Request model for restoring from a backup"""

    restore_type: Optional[str] = Field(
        None, description="Type of restore: full, database, files, or models. Default: full"
    )
    confirm: bool = Field(
        False, description="Confirmation flag - must be True to proceed with restore"
    )
    create_backup_before: bool = Field(
        True, description="Create a backup before restoring"
    )

    @validator("confirm")
    def confirm_required(cls, v):
        if not v:
            raise ValueError("confirm must be True to proceed with restore")
        return v

    @validator("restore_type")
    def validate_restore_type(cls, v):
        if v is not None and v not in ["full", "database", "files", "models"]:
            raise ValueError("Invalid restore type. Must be one of: full, database, files, models")
        return v


class BackupResponse(BaseModel):
    """Response model for a single backup entry"""

    id: str = Field(..., description="Unique identifier for the backup")
    name: str = Field(..., description="Human-readable name")
    type: str = Field(..., description="Type of backup")
    status: str = Field(..., description="Current status")
    size_bytes: Optional[int] = Field(None, description="Size of backup in bytes")
    size_human: Optional[str] = Field(None, description="Human-readable size")
    backup_path: str = Field(..., description="File system path to backup")
    created_at: str = Field(..., description="Creation timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    retention_days: int = Field(..., description="Retention period in days")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")
    checksum: Optional[str] = Field(None, description="SHA256 checksum")
    is_incremental: bool = Field(..., description="Whether this is an incremental backup")
    parent_backup_id: Optional[str] = Field(None, description="Parent backup ID for incremental")
    s3_uploaded: bool = Field(..., description="Whether uploaded to S3")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    files_count: Optional[int] = Field(None, description="Number of files in backup")
    tables_count: Optional[int] = Field(None, description="Number of database tables")


class BackupConfigResponse(BaseModel):
    """Response model for backup configuration"""

    retention_days: int = Field(..., description="Default retention period in days")
    backup_schedule: str = Field(..., description="Cron expression for scheduled backups")
    s3_enabled: bool = Field(..., description="Whether S3 backup is enabled")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    s3_endpoint: Optional[str] = Field(None, description="S3 endpoint URL")
    s3_region: Optional[str] = Field(None, description="S3 region")
    notification_email: Optional[str] = Field(None, description="Email for failure notifications")
    enabled: bool = Field(..., description="Whether automated backups are enabled")
    incremental_enabled: bool = Field(..., description="Whether incremental backups are enabled")
    compression_enabled: bool = Field(..., description="Whether compression is enabled")
    last_backup_at: Optional[str] = Field(None, description="Last successful backup time")
    last_backup_status: Optional[str] = Field(None, description="Last backup status")


class BackupConfigUpdate(BaseModel):
    """Request model for updating backup configuration"""

    retention_days: Optional[int] = Field(None, ge=1, le=365, description="Retention period in days")
    backup_schedule: Optional[str] = Field(None, description="Cron expression")
    s3_enabled: Optional[bool] = Field(None, description="Enable/disable S3 backup")
    s3_bucket: Optional[str] = Field(None, description="S3 bucket name")
    s3_endpoint: Optional[str] = Field(None, description="S3 endpoint URL")
    s3_access_key: Optional[str] = Field(None, description="S3 access key")
    s3_secret_key: Optional[str] = Field(None, description="S3 secret key")
    s3_region: Optional[str] = Field(None, description="S3 region")
    notification_email: Optional[str] = Field(None, description="Notification email")
    enabled: Optional[bool] = Field(None, description="Enable/disable automated backups")
    incremental_enabled: Optional[bool] = Field(None, description="Enable/disable incremental backups")
    compression_enabled: Optional[bool] = Field(None, description="Enable/disable compression")


class BackupStatusResponse(BaseModel):
    """Response model for overall backup system status"""

    enabled: bool = Field(..., description="Whether automated backups are enabled")
    last_backup_at: Optional[str] = Field(None, description="Last successful backup time")
    last_backup_status: Optional[str] = Field(None, description="Last backup status")
    total_backups: int = Field(..., description="Total number of backups")
    total_size_bytes: int = Field(..., description="Total size of all backups")
    total_size_human: str = Field(..., description="Human-readable total size")
    next_scheduled_backup: Optional[str] = Field(None, description="Next scheduled backup time")
    recent_backups: List[BackupResponse] = Field(..., description="Recent backups")
    disk_usage_bytes: Optional[int] = Field(None, description="Disk usage for backup directory")
    disk_usage_human: Optional[str] = Field(None, description="Human-readable disk usage")


class BackupVerifyResponse(BaseModel):
    """Response model for backup verification"""

    backup_id: str = Field(..., description="Backup ID")
    valid: bool = Field(..., description="Whether backup is valid")
    checksum_match: bool = Field(..., description="Whether checksum matches")
    files_intact: bool = Field(..., description="Whether all files are intact")
    details: Optional[str] = Field(None, description="Additional details")
