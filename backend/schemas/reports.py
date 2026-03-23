"""
Pydantic schemas for report management and generation.

This module provides schema definitions for creating, updating, and generating
reports including candidate summaries, hiring pipeline reports, EEOC compliance
reports, and custom analytics reports.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Types of reports available in the system."""

    CANDIDATE_SUMMARY = "candidate_summary"
    HIRING_PIPELINE = "hiring_pipeline"
    EEOC_COMPLIANCE = "eeoc_compliance"
    CUSTOM_ANALYTICS = "custom_analytics"
    RECRUITER_PERFORMANCE = "recruiter_performance"
    SOURCE_EFFECTIVENESS = "source_effectiveness"


class ReportFormat(str, Enum):
    """Supported export formats for reports."""

    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class ReportScheduleFrequency(str, Enum):
    """Frequency options for scheduled reports."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportCreate(BaseModel):
    """Request model for creating a custom report."""

    organization_id: str = Field(
        ...,
        description="Organization identifier",
    )
    name: str = Field(
        ...,
        description="Human-readable name for the report",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the report's purpose",
    )
    report_type: ReportType = Field(
        ...,
        description="Type of report (candidate_summary, hiring_pipeline, eeoc_compliance, custom_analytics)",
    )
    configuration: Dict[str, Any] = Field(
        ...,
        description="JSON object containing filters, dimensions, metrics, and visualization settings",
    )
    created_by: Optional[str] = Field(
        None,
        description="User ID who created this report configuration",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this report configuration is currently active",
    )


class ReportUpdate(BaseModel):
    """Request model for updating a custom report."""

    name: Optional[str] = Field(
        None,
        description="Human-readable name for the report",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the report's purpose",
    )
    report_type: Optional[ReportType] = Field(
        None,
        description="Type of report",
    )
    configuration: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON object containing filters, dimensions, metrics, and visualization settings",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether this report configuration is currently active",
    )


class ReportResponse(BaseModel):
    """Response model for a single report entry."""

    id: str = Field(
        ...,
        description="Unique identifier for the report (UUID)",
    )
    organization_id: str = Field(
        ...,
        description="Organization identifier",
    )
    name: str = Field(
        ...,
        description="Human-readable name for the report",
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the report's purpose",
    )
    report_type: str = Field(
        ...,
        description="Type of report",
    )
    configuration: Dict[str, Any] = Field(
        ...,
        description="JSON object containing filters, dimensions, metrics, and visualization settings",
    )
    created_by: Optional[str] = Field(
        None,
        description="User ID who created this report configuration",
    )
    is_active: bool = Field(
        ...,
        description="Whether this report configuration is currently active",
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp when report was created",
    )
    updated_at: str = Field(
        ...,
        description="ISO 8601 timestamp when report was last updated",
    )


class ReportListResponse(BaseModel):
    """Response model for listing reports."""

    reports: List[ReportResponse] = Field(
        ...,
        description="List of report configurations",
    )
    total_count: int = Field(
        ...,
        description="Total number of reports",
    )
    organization_id: Optional[str] = Field(
        None,
        description="Organization identifier (if filtered)",
    )


class ScheduledReportCreate(BaseModel):
    """Request model for creating a scheduled report."""

    organization_id: str = Field(
        ...,
        description="Organization identifier",
    )
    report_id: str = Field(
        ...,
        description="Reference to the Report configuration to use (UUID)",
    )
    name: str = Field(
        ...,
        description="Human-readable name for the scheduled report",
        min_length=1,
        max_length=255,
    )
    schedule_config: Dict[str, Any] = Field(
        ...,
        description="JSON object containing frequency, timezone, and schedule settings",
    )
    delivery_config: Dict[str, Any] = Field(
        ...,
        description="JSON object containing delivery method (email, Slack, etc.) and settings",
    )
    recipients: List[str] = Field(
        ...,
        description="List of user IDs or email addresses to receive the report",
        min_items=1,
    )
    created_by: Optional[str] = Field(
        None,
        description="User ID who created this scheduled report",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this scheduled report is currently active",
    )


class ScheduledReportUpdate(BaseModel):
    """Request model for updating a scheduled report."""

    name: Optional[str] = Field(
        None,
        description="Human-readable name for the scheduled report",
        min_length=1,
        max_length=255,
    )
    schedule_config: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON object containing frequency, timezone, and schedule settings",
    )
    delivery_config: Optional[Dict[str, Any]] = Field(
        None,
        description="JSON object containing delivery method and settings",
    )
    recipients: Optional[List[str]] = Field(
        None,
        description="List of user IDs or email addresses to receive the report",
        min_items=1,
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether this scheduled report is currently active",
    )


class ScheduledReportResponse(BaseModel):
    """Response model for a scheduled report entry."""

    id: str = Field(
        ...,
        description="Unique identifier for the scheduled report (UUID)",
    )
    organization_id: str = Field(
        ...,
        description="Organization identifier",
    )
    report_id: str = Field(
        ...,
        description="Reference to the Report configuration (UUID)",
    )
    name: str = Field(
        ...,
        description="Human-readable name for the scheduled report",
    )
    schedule_config: Dict[str, Any] = Field(
        ...,
        description="JSON object containing frequency, timezone, and schedule settings",
    )
    delivery_config: Dict[str, Any] = Field(
        ...,
        description="JSON object containing delivery method and settings",
    )
    recipients: List[str] = Field(
        ...,
        description="List of user IDs or email addresses to receive the report",
    )
    created_by: Optional[str] = Field(
        None,
        description="User ID who created this scheduled report",
    )
    is_active: bool = Field(
        ...,
        description="Whether this scheduled report is currently active",
    )
    next_run_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp for when the next report generation should occur",
    )
    last_run_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp for when the report was last generated",
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp when scheduled report was created",
    )
    updated_at: str = Field(
        ...,
        description="ISO 8601 timestamp when scheduled report was last updated",
    )


class ScheduledReportListResponse(BaseModel):
    """Response model for listing scheduled reports."""

    scheduled_reports: List[ScheduledReportResponse] = Field(
        ...,
        description="List of scheduled report configurations",
    )
    total_count: int = Field(
        ...,
        description="Total number of scheduled reports",
    )
    organization_id: Optional[str] = Field(
        None,
        description="Organization identifier (if filtered)",
    )


class ReportGenerationRequest(BaseModel):
    """Request model for generating a report on-demand."""

    report_id: str = Field(
        ...,
        description="Report configuration ID to generate (UUID)",
    )
    format: ReportFormat = Field(
        default=ReportFormat.PDF,
        description="Export format (pdf, excel, csv)",
    )
    override_filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional filters to override the report's default configuration",
    )


class ReportGenerationResponse(BaseModel):
    """Response model for report generation result."""

    report_id: str = Field(
        ...,
        description="Report configuration ID that was generated",
    )
    format: str = Field(
        ...,
        description="Export format used",
    )
    download_url: str = Field(
        ...,
        description="URL to download the generated report",
    )
    expires_at: str = Field(
        ...,
        description="ISO 8601 timestamp when download link expires",
    )
    generated_at: str = Field(
        ...,
        description="ISO 8601 timestamp when report was generated",
    )
    file_size_bytes: Optional[int] = Field(
        None,
        description="Size of the generated file in bytes",
    )


class ReportAuditLogEntry(BaseModel):
    """Audit log entry for report access."""

    report_id: str = Field(
        ...,
        description="Report ID that was accessed",
    )
    user_id: str = Field(
        ...,
        description="User ID who accessed the report",
    )
    action: str = Field(
        ...,
        description="Action performed (view, download, generate, schedule)",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of the action",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the action",
    )


class ScheduleConfig(BaseModel):
    """Configuration for scheduled report execution."""

    frequency: ReportScheduleFrequency = Field(
        ...,
        description="Frequency of report generation (daily, weekly, monthly)",
    )
    hour: int = Field(
        ...,
        description="Hour of day to run (0-23)",
        ge=0,
        le=23,
    )
    minute: int = Field(
        default=0,
        description="Minute of hour to run (0-59)",
        ge=0,
        le=59,
    )
    day_of_week: Optional[int] = Field(
        None,
        description="Day of week for weekly reports (0=Sunday, 6=Saturday)",
        ge=0,
        le=6,
    )
    day_of_month: Optional[int] = Field(
        None,
        description="Day of month for monthly reports (1-28)",
        ge=1,
        le=28,
    )
    timezone: str = Field(
        default="UTC",
        description="Timezone for schedule execution",
    )


class DeliveryConfig(BaseModel):
    """Configuration for report delivery."""

    format: ReportFormat = Field(
        ...,
        description="Export format for the report",
    )
    include_charts: bool = Field(
        default=True,
        description="Whether to include charts in the report",
    )
    include_summary: bool = Field(
        default=True,
        description="Whether to include executive summary",
    )
    email_subject: Optional[str] = Field(
        None,
        description="Custom email subject line",
    )
    email_body: Optional[str] = Field(
        None,
        description="Custom email body text",
    )
