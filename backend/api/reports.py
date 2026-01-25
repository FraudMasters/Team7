"""
Custom report management endpoints.

This module provides endpoints for managing custom analytics reports,
including CRUD operations for creating, reading, updating, and deleting
saved reports with metrics and filters.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportCreate(BaseModel):
    """Request model for creating a custom report."""

    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    created_by: Optional[str] = Field(None, description="User ID who is creating this report")
    metrics: List[str] = Field(..., description="List of metrics to include (e.g., time_to_hire, resumes_processed, match_rates)")
    filters: Dict = Field(default_factory=dict, description="Report filters (e.g., date range, sources)")
    is_public: bool = Field(False, description="Whether this report is visible to all organization members")


class ReportUpdate(BaseModel):
    """Request model for updating a custom report."""

    name: Optional[str] = Field(None, description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    metrics: Optional[List[str]] = Field(None, description="List of metrics to include")
    filters: Optional[Dict] = Field(None, description="Report filters")
    is_public: Optional[bool] = Field(None, description="Whether this report is visible to all organization members")


class ReportResponse(BaseModel):
    """Response model for a single report entry."""

    id: str = Field(..., description="Unique identifier for the report")
    organization_id: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    created_by: Optional[str] = Field(None, description="User ID who created this report")
    metrics: List[str] = Field(..., description="List of metrics included in the report")
    filters: Dict = Field(..., description="Report filters")
    is_public: bool = Field(..., description="Whether this report is visible to all organization members")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class ReportListResponse(BaseModel):
    """Response model for listing reports."""

    organization_id: Optional[str] = Field(None, description="Organization identifier (if filtered)")
    reports: List[ReportResponse] = Field(..., description="List of report entries")
    total_count: int = Field(..., description="Total number of entries")


class PDFExportRequest(BaseModel):
    """Request model for exporting a report to PDF."""

    report_id: str = Field(..., description="Report identifier to export")
    data: Dict = Field(..., description="Report data to include in the PDF")
    format: Optional[str] = Field("A4", description="Page format (e.g., A4, Letter)")


class PDFExportResponse(BaseModel):
    """Response model for PDF export."""

    report_id: str = Field(..., description="Report identifier")
    download_url: str = Field(..., description="URL to download the generated PDF")
    expires_at: str = Field(..., description="Expiration timestamp for download link")


class CSVExportRequest(BaseModel):
    """Request model for exporting analytics data to CSV."""

    metrics: List[str] = Field(..., description="List of metrics to export (e.g., time_to_hire, resumes_processed, match_rates)")
    filters: Dict = Field(default_factory=dict, description="Filters to apply to the data (e.g., date range, sources)")
    format: Optional[str] = Field("standard", description="CSV format variant (e.g., standard, detailed)")


class ScheduleReportRequest(BaseModel):
    """Request model for scheduling automated reports."""

    name: str = Field(..., description="Schedule name")
    organization_id: Optional[str] = Field(None, description="Organization identifier")
    report_id: Optional[str] = Field(None, description="Existing report ID to schedule (optional)")
    configuration: Dict = Field(..., description="Report configuration with metrics and filters")
    schedule_config: Dict = Field(..., description="Schedule settings (frequency, day_of_week, day_of_month, hour, minute)")
    delivery_config: Dict = Field(..., description="Delivery settings (format, include_charts, include_summary)")
    recipients: List[str] = Field(..., description="List of email recipient addresses")
    is_active: bool = Field(True, description="Whether the schedule is active")


class ScheduleReportResponse(BaseModel):
    """Response model for scheduled report creation."""

    id: str = Field(..., description="Schedule ID")
    name: str = Field(..., description="Schedule name")
    report_id: Optional[str] = Field(None, description="Associated report ID")
    next_run_at: str = Field(..., description="Next scheduled run timestamp")
    created_at: str = Field(..., description="Creation timestamp")


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reports"],
)
async def create_report(request: ReportCreate) -> JSONResponse:
    """
    Create a custom report.

    This endpoint accepts a custom report definition with metrics and filters,
    validating the data and creating a database record for the saved report.

    Args:
        request: Create request with report details

    Returns:
        JSON response with created report entry

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Monthly Hiring Report",
        ...     "description": "Overview of hiring metrics for this month",
        ...     "organization_id": "org123",
        ...     "created_by": "user456",
        ...     "metrics": ["time_to_hire", "resumes_processed", "match_rates"],
        ...     "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
        ...     "is_public": True
        ... }
        >>> response = requests.post("http://localhost:8000/api/reports/", json=data)
        >>> response.json()
        {
            "id": "report-123",
            "organization_id": "org123",
            "name": "Monthly Hiring Report",
            ...
        }
    """
    try:
        logger.info(f"Creating report '{request.name}'")

        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Report name cannot be empty",
            )

        # Validate metrics list
        if not request.metrics or len(request.metrics) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one metric must be provided",
            )

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        response_data = {
            "id": "placeholder-report-id",
            "organization_id": request.organization_id or "default",
            "name": request.name,
            "description": request.description,
            "created_by": request.created_by,
            "metrics": request.metrics,
            "filters": request.filters,
            "is_public": request.is_public,
            "created_at": now,
            "updated_at": now,
        }

        logger.info(f"Created report '{request.name}' with ID: {response_data['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}",
        ) from e


@router.get("/", tags=["Reports"])
async def list_reports(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator user ID"),
    is_public: Optional[bool] = Query(None, description="Filter by public status"),
) -> JSONResponse:
    """
    List custom reports with optional filters.

    Args:
        organization_id: Optional organization ID filter
        created_by: Optional creator user ID filter
        is_public: Optional public status filter

    Returns:
        JSON response with list of report entries

    Raises:
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/reports/?organization_id=org123")
        >>> response.json()
    """
    try:
        logger.info(f"Listing reports with filters - organization_id: {organization_id}, created_by: {created_by}, is_public: {is_public}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "organization_id": organization_id,
            "reports": [],
            "total_count": 0,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}",
        ) from e


@router.get("/{report_id}", tags=["Reports"])
async def get_report(report_id: str) -> JSONResponse:
    """
    Get a specific report by ID.

    Args:
        report_id: Unique identifier of the report

    Returns:
        JSON response with report details

    Raises:
        HTTPException(404): If report is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/reports/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
    """
    try:
        logger.info(f"Getting report: {report_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": report_id,
                "organization_id": "org123",
                "name": "Sample Report",
                "description": "A sample report",
                "created_by": "user456",
                "metrics": ["time_to_hire", "resumes_processed"],
                "filters": {},
                "is_public": True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": "2024-01-25T00:00:00Z",
            },
        )

    except Exception as e:
        logger.error(f"Error getting report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}",
        ) from e


@router.put("/{report_id}", tags=["Reports"])
async def update_report(
    report_id: str, request: ReportUpdate
) -> JSONResponse:
    """
    Update a custom report.

    Args:
        report_id: Unique identifier of the report
        request: Update request with fields to modify

    Returns:
        JSON response with updated report entry

    Raises:
        HTTPException(404): If report is not found
        HTTPException(422): If validation fails
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> data = {"name": "Updated Report Name", "metrics": ["time_to_hire", "match_rates"]}
        >>> response = requests.put(
        ...     "http://localhost:8000/api/reports/123",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Updating report: {report_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": report_id,
                "organization_id": "org123",
                "name": request.name or "Sample Report",
                "description": request.description,
                "created_by": "user456",
                "metrics": request.metrics or ["time_to_hire"],
                "filters": request.filters or {},
                "is_public": request.is_public if request.is_public is not None else True,
                "created_at": "2024-01-25T00:00:00Z",
                "updated_at": now,
            },
        )

    except Exception as e:
        logger.error(f"Error updating report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report: {str(e)}",
        ) from e


@router.delete("/{report_id}", tags=["Reports"])
async def delete_report(report_id: str) -> JSONResponse:
    """
    Delete a custom report.

    Args:
        report_id: Unique identifier of the report

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If report is not found
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/reports/123")
        >>> response.json()
        {"message": "Report deleted successfully"}
    """
    try:
        logger.info(f"Deleting report: {report_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Report {report_id} deleted successfully"},
        )

    except Exception as e:
        logger.error(f"Error deleting report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}",
        ) from e


@router.delete("/organization/{organization_id}", tags=["Reports"])
async def delete_reports_by_organization(organization_id: str) -> JSONResponse:
    """
    Delete all custom reports for a specific organization.

    Args:
        organization_id: Organization identifier to delete reports for

    Returns:
        JSON response confirming deletion with count

    Raises:
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/reports/organization/org123")
        >>> response.json()
        {"message": "Deleted 5 reports for organization: org123"}
    """
    try:
        logger.info(f"Deleting all reports for organization: {organization_id}")

        # For now, return placeholder response
        # Database integration will be added in a later subtask when we have async session setup
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Deleted reports for organization: {organization_id}", "deleted_count": 0},
        )

    except Exception as e:
        logger.error(f"Error deleting reports for organization {organization_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete reports: {str(e)}",
        ) from e


@router.post("/export/pdf", tags=["Reports"])
async def export_report_pdf(request: PDFExportRequest) -> JSONResponse:
    """
    Export a report to PDF format.

    This endpoint generates a PDF document from report data and returns
    a download URL for the generated file.

    Args:
        request: PDF export request with report ID and data

    Returns:
        JSON response with download URL and expiration

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If PDF generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "report_id": "test-id",
        ...     "data": {
        ...         "title": "Monthly Hiring Report",
        ...         "metrics": {"time_to_hire": "15 days", "resumes_processed": 150},
        ...         "charts": []
        ...     }
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/reports/export/pdf",
        ...     json=data
        ... )
        >>> response.json()
        {
            "report_id": "test-id",
            "download_url": "https://example.com/downloads/report-test-id.pdf",
            "expires_at": "2024-01-26T00:00:00Z"
        }
    """
    try:
        logger.info(f"Generating PDF for report: {request.report_id}")

        # Validate report_id
        if not request.report_id or len(request.report_id.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Report ID cannot be empty",
            )

        # Validate data
        if not request.data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Report data cannot be empty",
            )

        # For now, generate a placeholder response
        # Actual PDF generation will be added in a later subtask with reportlab or weasyprint
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        expires_at = (now + timedelta(hours=24)).isoformat() + "Z"

        response_data = {
            "report_id": request.report_id,
            "download_url": f"/api/reports/downloads/{request.report_id}.pdf",
            "expires_at": expires_at,
        }

        logger.info(f"PDF generated successfully for report: {request.report_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF for report {request.report_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}",
        ) from e


@router.post("/export/csv", tags=["Reports"])
async def export_report_csv(request: CSVExportRequest) -> StreamingResponse:
    """
    Export analytics data to CSV format.

    This endpoint generates a CSV file from analytics metrics and filters,
    returning the file directly for download.

    Args:
        request: CSV export request with metrics and filters

    Returns:
        StreamingResponse with CSV file content

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If CSV generation fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "metrics": ["time_to_hire", "resumes_processed"],
        ...     "filters": {"start_date": "2024-01-01", "end_date": "2024-01-31"}
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/reports/export/csv",
        ...     json=data
        ... )
        >>> with open("report.csv", "wb") as f:
        ...     f.write(response.content)
    """
    try:
        logger.info(f"Generating CSV for metrics: {request.metrics}")

        # Validate metrics list
        if not request.metrics or len(request.metrics) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one metric must be provided",
            )

        # Generate CSV content
        # For now, generate a placeholder CSV with sample data
        # Actual data fetching will be added in a later subtask when database is integrated
        import io
        csv_buffer = io.StringIO()

        # Write CSV header
        header = ["metric", "value", "date"]
        csv_buffer.write(",".join(header) + "\n")

        # Write sample data rows based on requested metrics
        from datetime import datetime, timedelta
        sample_data = {
            "time_to_hire": {"value": "15 days", "unit": "days"},
            "resumes_processed": {"value": "150", "unit": "count"},
            "match_rates": {"value": "85%", "unit": "percentage"},
            "interviews_scheduled": {"value": "25", "unit": "count"},
            "offers_extended": {"value": "10", "unit": "count"},
            "offers_accepted": {"value": "8", "unit": "count"},
        }

        # Generate a row for each metric with today's date
        today = datetime.utcnow().strftime("%Y-%m-%d")
        for metric in request.metrics:
            if metric in sample_data:
                row = [metric, sample_data[metric]["value"], today]
                csv_buffer.write(",".join(row) + "\n")
            else:
                row = [metric, "N/A", today]
                csv_buffer.write(",".join(row) + "\n")

        csv_content = csv_buffer.getvalue()
        csv_buffer.close()

        logger.info(f"CSV generated successfully for metrics: {request.metrics}")

        # Return as downloadable CSV file
        return StreamingResponse(
            io.BytesIO(csv_content.encode("utf-8")),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics_export.csv",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CSV: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CSV: {str(e)}",
        ) from e


@router.post("/schedule", tags=["Reports"], response_model=ScheduleReportResponse)
async def schedule_report(request: ScheduleReportRequest) -> JSONResponse:
    """
    Schedule an automated report with email delivery.

    This endpoint creates a scheduled report configuration that will automatically
    generate and email reports based on the specified schedule and delivery settings.

    Args:
        request: Schedule report request with configuration, schedule, and delivery settings

    Returns:
        JSON response with schedule ID and next run time

    Raises:
        HTTPException(422): If validation fails
        HTTPException(500): If scheduling fails

    Examples:
        >>> import requests
        >>> data = {
        ...     "name": "Weekly Analytics Report",
        ...     "organization_id": "org123",
        ...     "report_id": None,
        ...     "configuration": {
        ...         "metrics": ["time_to_hire", "resumes_processed"],
        ...         "filters": {}
        ...     },
        ...     "schedule_config": {
        ...         "frequency": "weekly",
        ...         "day_of_week": 1,
        ...         "hour": 9,
        ...         "minute": 0
        ...     },
        ...     "delivery_config": {
        ...         "format": "pdf",
        ...         "include_charts": True,
        ...         "include_summary": True
        ...     },
        ...     "recipients": ["manager@example.com"],
        ...     "is_active": True
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/reports/schedule",
        ...     json=data
        ... )
        >>> response.json()
    """
    try:
        logger.info(f"Creating scheduled report: {request.name}")

        # Validate name
        if not request.name or len(request.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Schedule name cannot be empty",
            )

        # Validate configuration has metrics
        if not request.configuration.get("metrics") or len(request.configuration["metrics"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one metric must be provided in configuration",
            )

        # Validate recipients
        if not request.recipients or len(request.recipients) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one recipient email must be provided",
            )

        # Validate email format for recipients
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        for email in request.recipients:
            if not re.match(email_pattern, email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid email address: {email}",
                )

        # Validate schedule_config
        freq = request.schedule_config.get("frequency")
        if freq not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Frequency must be one of: daily, weekly, monthly",
            )

        hour = request.schedule_config.get("hour", 0)
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Hour must be an integer between 0 and 23",
            )

        minute = request.schedule_config.get("minute", 0)
        if not isinstance(minute, int) or minute < 0 or minute > 59:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Minute must be an integer between 0 and 59",
            )

        # Validate weekly schedule has day_of_week
        if freq == "weekly":
            day_of_week = request.schedule_config.get("day_of_week")
            if day_of_week is None or not isinstance(day_of_week, int) or day_of_week < 0 or day_of_week > 6:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="day_of_week must be an integer between 0 (Sunday) and 6 (Saturday) for weekly frequency",
                )

        # Validate monthly schedule has day_of_month
        if freq == "monthly":
            day_of_month = request.schedule_config.get("day_of_month")
            if day_of_month is None or not isinstance(day_of_month, int) or day_of_month < 1 or day_of_month > 28:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="day_of_month must be an integer between 1 and 28 for monthly frequency",
                )

        # Validate delivery_config format
        format_type = request.delivery_config.get("format")
        if format_type not in ["pdf", "csv", "both"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Format must be one of: pdf, csv, both",
            )

        # For now, generate a placeholder response
        # Database integration and Celery task scheduling will be added in later subtasks
        from datetime import datetime, timedelta
        import uuid

        schedule_id = str(uuid.uuid4())
        now = datetime.utcnow()
        created_at = now.isoformat() + "Z"

        # Calculate next_run_at based on schedule configuration
        if freq == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif freq == "weekly":
            day_of_week = request.schedule_config.get("day_of_week", 0)
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            next_run += timedelta(days=days_ahead)
        else:  # monthly
            day_of_month = request.schedule_config.get("day_of_month", 1)
            next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                # Move to next month
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)

        next_run_at = next_run.isoformat() + "Z"

        response_data = {
            "id": schedule_id,
            "name": request.name,
            "report_id": request.report_id,
            "next_run_at": next_run_at,
            "created_at": created_at,
        }

        logger.info(f"Scheduled report '{request.name}' created with ID: {schedule_id}, next run: {next_run_at}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating scheduled report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled report: {str(e)}",
        ) from e
