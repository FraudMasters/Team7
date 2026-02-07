"""
Batch resume upload and processing endpoints.

This module provides endpoints for uploading multiple resume files at once,
tracking batch processing status, and retrieving batch results.

The core file upload logic is delegated to UnifiedUploadService for consistency,
while this module maintains batch job tracking and Celery task integration.
This is a compatibility layer that routes upload requests to the new unified service.

**DEPRECATED**: The batch upload endpoint is deprecated and will be removed in a future version.
Please use the unified upload endpoint at `/api/resumes/unified-upload` instead.
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.batch_job import BatchJob, BatchJobStatus
from models.resume import Resume, ResumeStatus
from tasks.analysis_task import batch_analyze_resumes
from celery_app import celery_app
from services.upload_service import get_upload_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# Pydantic models for requests/responses
class BatchUploadRequest(BaseModel):
    """Request model for batch upload with optional notification email."""

    notification_email: Optional[str] = Field(None, description="Email to send notification to when complete")
    analyze: bool = Field(True, description="Whether to analyze resumes after upload")


class BatchUploadResponse(BaseModel):
    """Response model for batch upload initiation."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    total_files: int = Field(..., description="Number of files in the batch")
    status: str = Field(..., description="Initial status of the batch job")
    message: str = Field(..., description="Success message")


class BatchStatusResponse(BaseModel):
    """Response model for batch status query."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Current status of the batch job")
    total_files: int = Field(..., description="Total number of files in the batch")
    processed_files: int = Field(..., description="Number of files processed")
    failed_files: int = Field(..., description="Number of files that failed")
    progress_percentage: int = Field(..., description="Progress percentage")
    created_at: Optional[str] = Field(None, description="Timestamp when batch was created")
    completed_at: Optional[str] = Field(None, description="Timestamp when batch completed")
    error_message: Optional[str] = Field(None, description="Error message if batch failed")


class BatchFileItem(BaseModel):
    """Response model for a single file in batch results."""

    resume_id: str = Field(..., description="Resume identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchResultsResponse(BaseModel):
    """Response model for batch results."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    status: str = Field(..., description="Final status of the batch job")
    total_files: int = Field(..., description="Total number of files")
    successful: int = Field(..., description="Number of successfully processed files")
    failed: int = Field(..., description="Number of failed files")
    files: list[BatchFileItem] = Field(..., description="List of files with their status")


@router.post(
    "/upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_301_MOVED_PERMANENTLY,
    tags=["Batch"],
    deprecated=True,
)
async def upload_batch(
    request: Request,
    files: list[UploadFile] = File(...),
    notification_email: Optional[str] = Form(None),
    analyze: bool = Form(True),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload multiple resume files for batch processing.

    **DEPRECATED**: This endpoint is deprecated as of 2026-02-07.
    Please migrate to the unified upload endpoint at `/api/resumes/unified-upload`.

    This endpoint now permanently redirects to the new unified upload endpoint.
    The new endpoint provides enhanced security features including:
    - Magic number file validation for all files
    - XXE protection for DOCX files
    - Filename sanitization to prevent path traversal
    - Consolidated single and batch upload functionality

    Migration guide:
    - Old: POST /api/batch/upload with files array and optional notification_email, analyze
    - New: POST /api/resumes/unified-upload with files array and optional notification_email, analyze

    Args:
        request: FastAPI request object
        files: List of uploaded resume files (redirected to unified endpoint)
        notification_email: Optional email for completion notification (passed to unified endpoint)
        analyze: Whether to analyze resumes after upload (passed to unified endpoint)
        db: Database session

    Returns:
        Permanent redirect (301) to the new unified upload endpoint

    Raises:
        N/A - This endpoint redirects all requests

    Examples:
        >>> import requests
        >>> # Old endpoint (deprecated - will redirect)
        >>> files = [("files", open("resume1.pdf", "rb")), ("files", open("resume2.docx", "rb"))]
        >>> response = requests.post("http://localhost:8000/api/batch/upload", files=files)
        >>> # New endpoint (use this instead)
        >>> files = [("files", open("resume1.pdf", "rb")), ("files", open("resume2.docx", "rb"))]
        >>> response = requests.post("http://localhost:8000/api/resumes/unified-upload", files=files, data={"analyze": "true"})
    """
    # Log deprecation warning
    logger.warning(
        f"Deprecated endpoint /api/batch/upload called from {request.client.host}. "
        f"Please migrate to /api/resumes/unified-upload"
    )

    # Return permanent redirect to new unified endpoint
    return RedirectResponse(
        url="/api/resumes/unified-upload",
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        headers={
            "X-Deprecated": "true",
            "X-Deprecation-Message": "This endpoint is deprecated. Please use /api/resumes/unified-upload instead.",
            "X-Deprecation-Date": "2026-02-07",
            "Link": '</api/resumes/unified-upload>; rel="alternate"; type="application/json"',
        }
    )


@router.get(
    "/{batch_id}",
    response_model=BatchStatusResponse,
    tags=["Batch"],
)
async def get_batch_status(
    request: Request,
    batch_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get the status of a batch job.

    Args:
        request: FastAPI request object
        batch_id: Unique identifier of the batch job
        db: Database session

    Returns:
        JSON response with current batch status

    Raises:
        HTTPException(404): If batch job not found
    """
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid batch ID format",
        )

    query = select(BatchJob).where(BatchJob.id == batch_uuid)
    result = await db.execute(query)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    # Check Celery task status if processing
    if batch.celery_task_id and batch.status == BatchJobStatus.processing:
        try:
            celery_result = celery_app.AsyncResult(batch.celery_task_id)
            if celery_result.state == "SUCCESS":
                batch.status = BatchJobStatus.completed
                batch.processed_files = batch.total_files
                batch.failed_files = 0
                # Set completion time
                from datetime import datetime, timezone
                batch.completed_at = datetime.now(timezone.utc)
            elif celery_result.state == "FAILURE":
                batch.status = BatchJobStatus.failed
                batch.error_message = "Celery task failed"
                from datetime import datetime, timezone
                batch.completed_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to check Celery task status: {e}")

    progress_percentage = 0
    if batch.total_files > 0:
        progress_percentage = int((batch.processed_files / batch.total_files) * 100)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "total_files": batch.total_files,
            "processed_files": batch.processed_files,
            "failed_files": batch.failed_files,
            "progress_percentage": progress_percentage,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "error_message": batch.error_message,
        }
    )


@router.get(
    "/{batch_id}/results",
    response_model=BatchResultsResponse,
    tags=["Batch"],
)
async def get_batch_results(
    request: Request,
    batch_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get the results of a completed batch job.

    Args:
        request: FastAPI request object
        batch_id: Unique identifier of the batch job
        db: Database session

    Returns:
        JSON response with batch results including individual file status

    Raises:
        HTTPException(404): If batch job not found
    """
    try:
        batch_uuid = UUID(batch_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid batch ID format",
        )

    query = select(BatchJob).where(BatchJob.id == batch_uuid)
    result = await db.execute(query)
    batch = result.scalar_one_or_none()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch job not found",
        )

    # Get all resumes for this batch (by creation time and batch reference)
    # For simplicity, we'll get recent resumes
    from datetime import datetime, timedelta
    from models.resume_analysis import ResumeAnalysis

    # Get resumes created around the batch creation time
    time_threshold = batch.created_at + timedelta(seconds=5)
    resume_query = select(Resume).where(
        Resume.created_at <= time_threshold
    ).order_by(Resume.created_at.desc()).limit(batch.total_files)

    resume_result = await db.execute(resume_query)
    resumes = resume_result.scalars().all()

    files = []
    successful = 0
    failed = 0

    for resume in resumes:
        # Check if analysis exists
        analysis_query = select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume.id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        status = "completed" if analysis else resume.status.value
        if status == "completed":
            successful += 1
        else:
            failed += 1

        files.append({
            "resume_id": str(resume.id),
            "filename": resume.filename,
            "status": status,
            "error": None,
        })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "batch_id": str(batch.id),
            "status": batch.status.value,
            "total_files": batch.total_files,
            "successful": successful,
            "failed": failed,
            "files": files,
        }
    )


@router.get(
    "/",
    tags=["Batch"],
)
async def list_batches(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all batch jobs.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of batch jobs
    """
    try:
        query = select(BatchJob).order_by(BatchJob.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        batches = result.scalars().all()

        batches_list = []
        for batch in batches:
            progress_percentage = 0
            if batch.total_files > 0:
                progress_percentage = int((batch.processed_files / batch.total_files) * 100)

            batches_list.append({
                "batch_id": str(batch.id),
                "status": batch.status.value,
                "total_files": batch.total_files,
                "processed_files": batch.processed_files,
                "failed_files": batch.failed_files,
                "progress_percentage": progress_percentage,
                "created_at": batch.created_at.isoformat() if batch.created_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"batches": batches_list, "total": len(batches_list)},
        )

    except Exception as e:
        logger.error(f"Error listing batches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list batches: {str(e)}",
        ) from e
