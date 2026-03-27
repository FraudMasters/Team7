"""
Pydantic schemas for import operations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class ImportJobStatus(str):
    """Status of import job"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_COMPLETED = "partially_completed"


class ImportFormat(str):
    """Supported import formats"""
    LINKEDIN_CSV = "linkedin_csv"
    INDEED_XML = "indeed_xml"
    HRXML = "hrxml"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKABLE = "workable"
    CUSTOM_JSON = "custom_json"
    CUSTOM_CSV = "custom_csv"


class ImportJobCreate(BaseModel):
    """Request model for creating a new import job"""

    format: str = Field(..., description="Import format type")
    original_filename: str = Field(..., description="Original name of uploaded file")
    file_size_bytes: Optional[int] = Field(None, description="Size of uploaded file in bytes")
    vacancy_id: Optional[UUID] = Field(None, description="Optional job vacancy ID for candidate sourcing")
    source_system: Optional[str] = Field(None, description="Source ATS system for migrations")
    notes: Optional[str] = Field(None, description="Optional notes about the import")
    import_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional import-specific metadata")

    @validator("format")
    def validate_format(cls, v):
        valid_formats = [
            "linkedin_csv",
            "indeed_xml",
            "hrxml",
            "greenhouse",
            "lever",
            "workable",
            "custom_json",
            "custom_csv",
        ]
        if v not in valid_formats:
            raise ValueError(f"Invalid import format. Must be one of: {', '.join(valid_formats)}")
        return v


class ImportJobUpdate(BaseModel):
    """Request model for updating an import job"""

    status: Optional[str] = Field(None, description="Update job status")
    total_records: Optional[int] = Field(None, description="Total number of records found")
    successful_imports: Optional[int] = Field(None, description="Number of successful imports")
    failed_imports: Optional[int] = Field(None, description="Number of failed imports")
    skipped_records: Optional[int] = Field(None, description="Number of skipped records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    notes: Optional[str] = Field(None, description="Additional notes")

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


class ImportJobResponse(BaseModel):
    """Response model for a single import job"""

    id: UUID = Field(..., description="Unique identifier for the import job")
    status: str = Field(..., description="Current status")
    format: str = Field(..., description="Import format type")
    recruiter_id: UUID = Field(..., description="ID of recruiter who initiated the import")
    vacancy_id: Optional[UUID] = Field(None, description="Optional job vacancy ID")
    file_path: str = Field(..., description="File system path to import file")
    file_size_bytes: Optional[int] = Field(None, description="Size of file in bytes")
    file_size_human: Optional[str] = Field(None, description="Human-readable file size")
    original_filename: str = Field(..., description="Original filename")
    total_records: Optional[int] = Field(None, description="Total records in file")
    successful_imports: int = Field(..., description="Number of successful imports")
    failed_imports: int = Field(..., description="Number of failed imports")
    skipped_records: int = Field(..., description="Number of skipped records")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    import_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    source_system: Optional[str] = Field(None, description="Source ATS system")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    progress_percentage: Optional[float] = Field(None, description="Import progress percentage")


class ImportJobListResponse(BaseModel):
    """Response model for list of import jobs"""

    jobs: List[ImportJobResponse] = Field(..., description="List of import jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Number of items per page")


class ImportJobStatsResponse(BaseModel):
    """Response model for import job statistics"""

    total_jobs: int = Field(..., description="Total number of import jobs")
    by_status: Dict[str, int] = Field(..., description="Job counts by status")
    by_format: Dict[str, int] = Field(..., description="Job counts by format")
    total_records_imported: int = Field(..., description="Total records successfully imported")
    total_records_failed: int = Field(..., description="Total records that failed")
    total_records_skipped: int = Field(..., description="Total records skipped")
    recent_jobs: List[ImportJobResponse] = Field(..., description="Recent import jobs")
    success_rate: Optional[float] = Field(None, description="Overall success rate percentage")


class ImportValidationError(BaseModel):
    """Model for individual validation error"""

    row_number: int = Field(..., description="Row number in import file")
    field: Optional[str] = Field(None, description="Field that failed validation")
    error: str = Field(..., description="Error description")
    value: Optional[str] = Field(None, description="Invalid value")


class ImportJobStartRequest(BaseModel):
    """Request model for starting an import job"""

    job_id: UUID = Field(..., description="Import job ID to start")
    async_processing: bool = Field(True, description="Process in background using Celery")


class ImportJobCancelRequest(BaseModel):
    """Request model for cancelling an import job"""

    job_id: UUID = Field(..., description="Import job ID to cancel")
    reason: Optional[str] = Field(None, description="Reason for cancellation")


class ImportFieldMapping(BaseModel):
    """Model for field mapping configuration"""

    source_field: str = Field(..., description="Source field name from import file")
    target_field: str = Field(..., description="Target field name in system")
    transform: Optional[str] = Field(None, description="Optional transformation function")
    required: bool = Field(True, description="Whether field is required")
    default_value: Optional[Any] = Field(None, description="Default value if missing")


class ImportMappingConfig(BaseModel):
    """Model for import mapping configuration"""

    format: str = Field(..., description="Import format")
    field_mappings: List[ImportFieldMapping] = Field(..., description="List of field mappings")
    validate_email: bool = Field(True, description="Validate email format")
    deduplicate: bool = Field(True, description="Check for duplicates before import")
    skip_invalid: bool = Field(False, description="Skip invalid records or fail entire import")


class BulkImportRequest(BaseModel):
    """Request model for bulk import operations"""

    format: str = Field(..., description="Import format")
    file_ids: List[UUID] = Field(..., description="List of uploaded file IDs to import")
    vacancy_id: Optional[UUID] = Field(None, description="Optional job vacancy ID")
    mapping_config: Optional[ImportMappingConfig] = Field(None, description="Custom field mapping")
    async_processing: bool = Field(True, description="Process in background")

    @validator("format")
    def validate_format(cls, v):
        valid_formats = [
            "linkedin_csv",
            "indeed_xml",
            "hrxml",
            "greenhouse",
            "lever",
            "workable",
            "custom_json",
            "custom_csv",
        ]
        if v not in valid_formats:
            raise ValueError(f"Invalid import format. Must be one of: {', '.join(valid_formats)}")
        return v

    @validator("file_ids")
    def validate_file_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one file ID is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 files can be imported at once")
        return v
