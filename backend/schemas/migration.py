"""
Pydantic schemas for migration operations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class MigrationStatus(str):
    """Status of migration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class MigrationType(str):
    """Types of migration operations"""
    FULL_MIGRATION = "full_migration"
    PARTIAL_MIGRATION = "partial_migration"
    DATA_SYNC = "data_sync"
    SYSTEM_UPGRADE = "system_upgrade"


class MigrationCreate(BaseModel):
    """Request model for creating a new migration"""

    migration_type: str = Field(..., description="Type of migration operation")
    source_system: str = Field(..., description="Source system name")
    target_system: str = Field("AgentHR", description="Target system name")
    source_system_version: Optional[str] = Field(None, description="Version of source system")
    entity_types: Optional[List[str]] = Field(None, description="Entity types to migrate (candidates, jobs, etc.)")
    notes: Optional[str] = Field(None, description="Optional notes about the migration")
    migration_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional migration-specific metadata")

    @validator("migration_type")
    def validate_migration_type(cls, v):
        valid_types = [
            "full_migration",
            "partial_migration",
            "data_sync",
            "system_upgrade",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid migration type. Must be one of: {', '.join(valid_types)}")
        return v


class MigrationUpdate(BaseModel):
    """Request model for updating a migration"""

    status: Optional[str] = Field(None, description="Update migration status")
    total_records: Optional[int] = Field(None, description="Total number of records to migrate")
    successful_migrations: Optional[int] = Field(None, description="Number of successful migrations")
    failed_migrations: Optional[int] = Field(None, description="Number of failed migrations")
    skipped_records: Optional[int] = Field(None, description="Number of skipped records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    notes: Optional[str] = Field(None, description="Additional notes")
    started_at: Optional[str] = Field(None, description="Migration start timestamp")
    completed_at: Optional[str] = Field(None, description="Migration completion timestamp")

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [
                "pending",
                "in_progress",
                "completed",
                "failed",
                "cancelled",
                "partially_completed",
            ]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v


class MigrationResponse(BaseModel):
    """Response model for a single migration"""

    id: UUID = Field(..., description="Unique identifier for the migration")
    status: str = Field(..., description="Current status")
    migration_type: str = Field(..., description="Type of migration operation")
    recruiter_id: UUID = Field(..., description="ID of recruiter who initiated the migration")
    source_system: str = Field(..., description="Source system name")
    target_system: str = Field(..., description="Target system name")
    source_system_version: Optional[str] = Field(None, description="Source system version")
    total_records: Optional[int] = Field(None, description="Total records to migrate")
    successful_migrations: int = Field(..., description="Number of successful migrations")
    failed_migrations: int = Field(..., description="Number of failed migrations")
    skipped_records: int = Field(..., description="Number of skipped records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    migration_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    entity_types: Optional[List[str]] = Field(None, description="Entity types being migrated")
    notes: Optional[str] = Field(None, description="Additional notes")
    started_at: Optional[str] = Field(None, description="Migration start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    progress_percentage: Optional[float] = Field(None, description="Migration progress percentage")


class MigrationListResponse(BaseModel):
    """Response model for list of migrations"""

    migrations: List[MigrationResponse] = Field(..., description="List of migrations")
    total: int = Field(..., description="Total number of migrations")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")


class MigrationStatsResponse(BaseModel):
    """Response model for migration statistics"""

    total_migrations: int = Field(..., description="Total number of migrations")
    by_status: Dict[str, int] = Field(..., description="Migration counts by status")
    by_type: Dict[str, int] = Field(..., description="Migration counts by type")
    by_source_system: Dict[str, int] = Field(..., description="Migration counts by source system")
    total_records_migrated: int = Field(..., description="Total records successfully migrated")
    total_records_failed: int = Field(..., description="Total records that failed")
    total_records_skipped: int = Field(..., description="Total records skipped")
    recent_migrations: List[MigrationResponse] = Field(..., description="Recent migrations")
    success_rate: Optional[float] = Field(None, description="Overall success rate percentage")


class MigrationValidationError(BaseModel):
    """Model for individual validation error"""

    record_id: Optional[str] = Field(None, description="Record identifier")
    entity_type: Optional[str] = Field(None, description="Entity type (candidate, job, etc.)")
    field: Optional[str] = Field(None, description="Field that failed validation")
    error: str = Field(..., description="Error description")
    value: Optional[str] = Field(None, description="Invalid value")


class MigrationStartRequest(BaseModel):
    """Request model for starting a migration"""

    migration_id: UUID = Field(..., description="Migration ID to start")
    async_processing: bool = Field(True, description="Process in background using Celery")


class MigrationCancelRequest(BaseModel):
    """Request model for cancelling a migration"""

    migration_id: UUID = Field(..., description="Migration ID to cancel")
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class MigrationFieldMapping(BaseModel):
    """Model for field mapping configuration"""

    source_field: str = Field(..., description="Source field name from source system")
    target_field: str = Field(..., description="Target field name in AgentHR")
    transform: Optional[str] = Field(None, description="Optional transformation function")
    required: bool = Field(True, description="Whether field is required")
    default_value: Optional[Any] = Field(None, description="Default value if missing")


class MigrationMappingConfig(BaseModel):
    """Model for migration mapping configuration"""

    source_system: str = Field(..., description="Source system name")
    entity_type: str = Field(..., description="Entity type (candidate, job, etc.)")
    field_mappings: List[MigrationFieldMapping] = Field(..., description="List of field mappings")
    validate_email: bool = Field(True, description="Validate email format")
    deduplicate: bool = Field(True, description="Check for duplicates before migration")
    skip_invalid: bool = Field(False, description="Skip invalid records or fail entire migration")


class BulkMigrationRequest(BaseModel):
    """Request model for bulk migration operations"""

    migration_type: str = Field(..., description="Type of migration")
    source_system: str = Field(..., description="Source system name")
    entity_types: List[str] = Field(..., description="Entity types to migrate")
    mapping_config: Optional[MigrationMappingConfig] = Field(None, description="Custom field mapping")
    async_processing: bool = Field(True, description="Process in background")

    @validator("migration_type")
    def validate_migration_type(cls, v):
        valid_types = [
            "full_migration",
            "partial_migration",
            "data_sync",
            "system_upgrade",
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid migration type. Must be one of: {', '.join(valid_types)}")
        return v


class MigrationPreviewRequest(BaseModel):
    """Request model for previewing a migration"""

    source_system: str = Field(..., description="Source system name")
    entity_types: List[str] = Field(..., description="Entity types to preview")
    sample_size: int = Field(10, description="Number of sample records to preview")


class MigrationPreviewResponse(BaseModel):
    """Response model for migration preview"""

    source_system: str = Field(..., description="Source system name")
    entity_type: str = Field(..., description="Entity type")
    total_records: int = Field(..., description="Total records available")
    sample_records: List[Dict[str, Any]] = Field(..., description="Sample records")
    field_mapping_suggestions: Optional[List[MigrationFieldMapping]] = Field(
        None, description="Suggested field mappings"
    )
    validation_warnings: Optional[List[str]] = Field(None, description="Potential validation issues")
