"""
Data import endpoints for various candidate sourcing formats.

This module provides REST endpoints for importing candidate data from:
- LinkedIn Recruiter CSV exports
- Indeed XML exports
- HR-XML standard format
- Custom CSV/JSON formats

Features:
- File upload and validation
- Asynchronous import processing
- Progress tracking and status monitoring
- Error reporting and validation
- Duplicate detection
"""
import logging
import os
import tempfile
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.import_job import ImportJob, ImportJobStatus, ImportFormat

# Import schemas
from schemas.import_schemas import (
    ImportJobCreate,
    ImportJobResponse,
    ImportJobUpdate,
    ImportJobListResponse,
    ImportJobStatsResponse,
)

# Import services for parsing different formats
import sys
IN_CONTAINER = os.path.exists('/app/backend/services')
if IN_CONTAINER:
    if '/app/backend' not in sys.path:
        sys.path.insert(0, '/app/backend')
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

try:
    from services.linkedin_csv_importer import LinkedInCSVImporter
    from services.indeed_xml_importer import IndeedXMLImporter
    from services.hrxml_importer import HRXMLImporter
    from services.import_service import ImportService
except (ImportError, ModuleNotFoundError):
    try:
        from backend.services.linkedin_csv_importer import LinkedInCSVImporter
        from backend.services.indeed_xml_importer import IndeedXMLImporter
        from backend.services.hrxml_importer import HRXMLImporter
        from backend.services.import_service import ImportService
    except (ImportError, ModuleNotFoundError):
        # Define stubs if services not available
        def LinkedInCSVImporter(*args, **kwargs):
            raise NotImplementedError("linkedin_csv_importer not available")
        def IndeedXMLImporter(*args, **kwargs):
            raise NotImplementedError("indeed_xml_importer not available")
        def HRXMLImporter(*args, **kwargs):
            raise NotImplementedError("hrxml_importer not available")
        def ImportService(*args, **kwargs):
            raise NotImplementedError("import_service not available")

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


# Constants
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {'.csv', '.xml', '.json'}


def format_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def import_job_to_response(job: ImportJob) -> dict:
    """Convert database ImportJob model to API response"""
    return {
        "id": str(job.id),
        "status": job.status.value,
        "format": job.format.value,
        "recruiter_id": str(job.recruiter_id),
        "vacancy_id": str(job.vacancy_id) if job.vacancy_id else None,
        "file_path": job.file_path,
        "file_size_bytes": job.file_size_bytes,
        "file_size_human": format_size(job.file_size_bytes) if job.file_size_bytes else None,
        "original_filename": job.original_filename,
        "total_records": job.total_records,
        "successful_imports": job.successful_imports,
        "failed_imports": job.failed_imports,
        "skipped_records": job.skipped_records,
        "error_message": job.error_message,
        "import_metadata": job.import_metadata,
        "validation_errors": job.validation_errors,
        "source_system": job.source_system,
        "notes": job.notes,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.post(
    "/upload",
    response_model=ImportJobResponse,
    tags=["Data Import"],
    status_code=status.HTTP_201_CREATED,
)
async def upload_import_file(
    file: UploadFile = File(..., description="Import file (CSV, XML, or JSON)"),
    format: str = Form(..., description="Import format (linkedin_csv, indeed_xml, hrxml, etc.)"),
    recruiter_id: str = Form(..., description="ID of recruiter initiating the import"),
    vacancy_id: Optional[str] = Form(None, description="Optional job vacancy ID for candidate sourcing"),
    notes: Optional[str] = Form(None, description="Optional notes about the import"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Upload and process candidate data import file.

    This endpoint accepts file uploads in various formats (LinkedIn CSV, Indeed XML,
    HR-XML, etc.) and creates an import job for processing candidate data.

    The file is validated for format and size, then saved to the filesystem.
    Processing happens asynchronously - use the returned job ID to check status.

    Supported formats:
    - linkedin_csv: LinkedIn Recruiter CSV exports
    - indeed_xml: Indeed XML exports
    - hrxml: HR-XML standard format
    - custom_csv: Custom CSV format
    - custom_json: Custom JSON format

    Args:
        file: The uploaded file
        format: Import format type
        recruiter_id: ID of recruiter initiating the import
        vacancy_id: Optional job vacancy ID for candidate sourcing
        notes: Optional notes about the import
        db: Database session

    Returns:
        JSON response with created import job details

    Raises:
        HTTPException(400): If file format is invalid or file is too large
        HTTPException(422): If format type is not supported
        HTTPException(500): If file processing fails

    Examples:
        >>> import requests
        >>> files = {'file': open('linkedin_export.csv', 'rb')}
        >>> data = {
        ...     'format': 'linkedin_csv',
        ...     'recruiter_id': '123e4567-e89b-12d3-a456-426614174000'
        ... }
        >>> response = requests.post('/api/data-import/upload', files=files, data=data)
        >>> job = response.json()
        >>> print(job['id'])  # Use this to check import status
    """
    try:
        # Validate format
        valid_formats = [f.value for f in ImportFormat]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}",
            )

        # Validate file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Read file content and check size
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {format_size(MAX_FILE_SIZE)}",
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        # Validate UUIDs
        try:
            recruiter_uuid = UUID(recruiter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid recruiter_id format: {recruiter_id}",
            )

        vacancy_uuid = None
        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy_id format: {vacancy_id}",
                )

        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(settings.UPLOAD_DIR, "imports")
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, safe_filename)

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(
            f"Saved import file: {file_path} ({format_size(file_size)}) "
            f"for recruiter {recruiter_id}"
        )

        # Create import job record
        import_job = ImportJob(
            status=ImportJobStatus.PENDING,
            format=ImportFormat(format),
            recruiter_id=recruiter_uuid,
            vacancy_id=vacancy_uuid,
            file_path=file_path,
            file_size_bytes=file_size,
            original_filename=file.filename,
            notes=notes,
        )

        db.add(import_job)
        await db.commit()
        await db.refresh(import_job)

        logger.info(f"Created import job {import_job.id} for format {format}")

        # TODO: Trigger async processing task
        # from tasks.import_tasks import process_import_job_task
        # process_import_job_task.delay(str(import_job.id))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=import_job_to_response(import_job),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading import file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}",
        )


@router.get(
    "/",
    response_model=List[ImportJobResponse],
    tags=["Data Import"],
)
async def list_import_jobs(
    format: Optional[str] = Query(None, description="Filter by import format"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all import jobs with optional filtering.

    Returns a paginated list of import jobs sorted by creation time (newest first).

    Args:
        format: Optional filter by format (linkedin_csv, indeed_xml, hrxml, etc.)
        status_filter: Optional filter by status (pending, in_progress, completed, failed)
        recruiter_id: Optional filter by recruiter ID
        vacancy_id: Optional filter by vacancy ID
        limit: Maximum number of results
        offset: Pagination offset
        db: Database session

    Returns:
        JSON response with list of import jobs

    Examples:
        >>> import requests
        >>> response = requests.get("/api/data-import/?format=linkedin_csv&limit=10")
        >>> jobs = response.json()
    """
    try:
        query = select(ImportJob).order_by(ImportJob.created_at.desc())

        # Apply filters
        if format:
            try:
                format_enum = ImportFormat(format)
                query = query.filter(ImportJob.format == format_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid import format: {format}",
                )

        if status_filter:
            try:
                status_enum = ImportJobStatus(status_filter)
                query = query.filter(ImportJob.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                query = query.filter(ImportJob.recruiter_id == recruiter_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid recruiter_id format: {recruiter_id}",
                )

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.filter(ImportJob.vacancy_id == vacancy_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid vacancy_id format: {vacancy_id}",
                )

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        jobs = result.scalars().all()

        response_data = [import_job_to_response(job) for job in jobs]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing import jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list import jobs: {str(e)}",
        )


@router.get(
    "/{job_id}",
    response_model=ImportJobResponse,
    tags=["Data Import"],
)
async def get_import_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get details of a specific import job.

    Args:
        job_id: Import job UUID
        db: Database session

    Returns:
        JSON response with import job details

    Raises:
        HTTPException(404): If job not found
        HTTPException(422): If job_id format is invalid

    Examples:
        >>> import requests
        >>> response = requests.get("/api/data-import/123e4567-e89b-12d3-a456-426614174000")
        >>> job = response.json()
        >>> print(job['status'])
    """
    try:
        # Validate UUID format
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_id format: {job_id}",
            )

        # Query job
        query = select(ImportJob).where(ImportJob.id == job_uuid)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import job not found: {job_id}",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=import_job_to_response(job),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get import job: {str(e)}",
        )


@router.delete(
    "/{job_id}",
    tags=["Data Import"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_import_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a pending or in-progress import job.

    Only jobs with status 'pending' or 'in_progress' can be cancelled.

    Args:
        job_id: Import job UUID
        db: Database session

    Raises:
        HTTPException(404): If job not found
        HTTPException(400): If job cannot be cancelled
        HTTPException(422): If job_id format is invalid

    Examples:
        >>> import requests
        >>> response = requests.delete("/api/data-import/123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        # Validate UUID format
        try:
            job_uuid = UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid job_id format: {job_id}",
            )

        # Query job
        query = select(ImportJob).where(ImportJob.id == job_uuid)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Import job not found: {job_id}",
            )

        # Check if job can be cancelled
        if job.status not in [ImportJobStatus.PENDING, ImportJobStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status.value}",
            )

        # Update status
        job.status = ImportJobStatus.CANCELLED
        job.error_message = "Cancelled by user"
        await db.commit()

        logger.info(f"Cancelled import job {job_id}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling import job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel import job: {str(e)}",
        )


@router.get(
    "/stats/summary",
    response_model=ImportJobStatsResponse,
    tags=["Data Import"],
)
async def get_import_stats(
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter ID"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get import statistics and summary.

    Returns aggregate statistics about import jobs including total counts,
    success/failure rates, and format breakdown.

    Args:
        recruiter_id: Optional filter by recruiter ID
        db: Database session

    Returns:
        JSON response with import statistics

    Examples:
        >>> import requests
        >>> response = requests.get("/api/data-import/stats/summary")
        >>> stats = response.json()
        >>> print(f"Total imports: {stats['total_jobs']}")
    """
    try:
        # Build base query
        query = select(ImportJob)

        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                query = query.filter(ImportJob.recruiter_id == recruiter_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid recruiter_id format: {recruiter_id}",
                )

        # Get total counts
        result = await db.execute(query)
        all_jobs = result.scalars().all()

        # Calculate statistics
        total_jobs = len(all_jobs)
        completed_jobs = sum(1 for j in all_jobs if j.status == ImportJobStatus.COMPLETED)
        failed_jobs = sum(1 for j in all_jobs if j.status == ImportJobStatus.FAILED)
        pending_jobs = sum(1 for j in all_jobs if j.status == ImportJobStatus.PENDING)
        in_progress_jobs = sum(1 for j in all_jobs if j.status == ImportJobStatus.IN_PROGRESS)

        total_records_imported = sum(j.successful_imports for j in all_jobs)
        total_records_failed = sum(j.failed_imports for j in all_jobs)
        total_records_skipped = sum(j.skipped_records for j in all_jobs)

        # Format breakdown
        format_breakdown = {}
        for format_type in ImportFormat:
            count = sum(1 for j in all_jobs if j.format == format_type)
            if count > 0:
                format_breakdown[format_type.value] = count

        stats = {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "pending_jobs": pending_jobs,
            "in_progress_jobs": in_progress_jobs,
            "total_records_imported": total_records_imported,
            "total_records_failed": total_records_failed,
            "total_records_skipped": total_records_skipped,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
            "format_breakdown": format_breakdown,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get import stats: {str(e)}",
        )
