"""
Unified upload endpoint for single and batch resume uploads.

This module provides a consolidated endpoint for uploading resume files,
handling both single file and batch upload scenarios through a single interface.
It uses the UnifiedUploadService for all upload operations, ensuring consistent
validation, security, and error handling.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.audit_log import AuditActionType
from models.batch_job import BatchJob, BatchJobStatus
from utils.audit_logger import log_audit_event, get_request_context
from services.upload_service import UnifiedUploadService, get_upload_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# Pydantic models for requests/responses
class UnifiedUploadResponse(BaseModel):
    """Response model for single file upload via unified endpoint."""

    id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Processing status of the resume")
    message: str = Field(..., description="Success message")


class UnifiedBatchUploadResponse(BaseModel):
    """Response model for batch upload via unified endpoint."""

    batch_id: str = Field(..., description="Unique identifier for the batch job")
    total_files: int = Field(..., description="Total number of files in the batch")
    success_count: int = Field(..., description="Number of successfully uploaded files")
    failure_count: int = Field(..., description="Number of failed file uploads")
    status: str = Field(..., description="Status of the batch operation")
    successful: list[dict] = Field(..., description="List of successfully uploaded files")
    failed: list[dict] = Field(..., description="List of failed uploads with errors")
    message: str = Field(..., description="Success or error message")


@router.post(
    "/unified-upload",
    status_code=status.HTTP_201_CREATED,
    tags=["Resumes"],
)
async def unified_upload(
    request: Request,
    files: list[UploadFile] = File(...),
    notification_email: Optional[str] = Form(None),
    analyze: bool = Form(True),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Unified upload endpoint for single and batch resume uploads.

    This endpoint consolidates single and batch upload functionality into a single
    interface. It automatically detects whether a single file or multiple files are
    being uploaded and processes them accordingly.

    ## Features:
    - Automatic detection of single vs. batch upload
    - File type validation (PDF, DOCX)
    - File size validation
    - Magic number verification for security
    - Filename sanitization to prevent path traversal
    - Locale-aware error messages
    - Optional batch job creation for tracking
    - Audit logging for all uploads

    ## Args:
        request: FastAPI request object (for Accept-Language header and IP address)
        files: List of uploaded resume files (single file = single upload, multiple = batch)
        notification_email: Optional email for batch completion notification
        analyze: Whether to trigger analysis after upload (default: True)
        db: Database session

    ## Returns:
        For single file upload:
            JSON response with resume ID, filename, and status
        For batch upload:
            JSON response with batch ID, file counts, and per-file results

    ## Raises:
        HTTPException(400): No files provided or invalid request format
        HTTPException(413): File size exceeds maximum
        HTTPException(415): File type not supported
        HTTPException(500): File storage or database operation fails

    ## Examples:
        Single file upload:
        ```python
        import requests
        with open("resume.pdf", "rb") as f:
            response = requests.post(
                "http://localhost:8000/api/resumes/unified-upload",
                files={"files": f}
            )
        # Response: {"id": "...", "filename": "resume.pdf", "status": "pending", ...}
        ```

        Batch upload:
        ```python
        files = [("files", open("resume1.pdf", "rb")),
                 ("files", open("resume2.docx", "rb"))]
        response = requests.post(
            "http://localhost:8000/api/resumes/unified-upload",
            files=files,
            data={"analyze": "true"}
        )
        # Response: {"batch_id": "...", "total_files": 2, "success_count": 2, ...}
        ```
    """
    # Get upload service instance
    upload_service = get_upload_service()

    # Extract locale for translated messages
    locale = upload_service.extract_locale(request)

    # Validate that files were provided
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided",
        )

    logger.info(f"Unified upload request received: {len(files)} file(s), analyze={analyze}")

    try:
        # Single file upload - return simplified response
        if len(files) == 1:
            file = files[0]
            result = await upload_service.upload_file(file, db, locale, request)

            # Log audit event for single file upload
            ip_address, user_agent = get_request_context(request)
            await log_audit_event(
                db=db,
                action_type=AuditActionType.RESUME_UPLOADED,
                entity_type="resume",
                entity_id=result["id"],
                ip_address=ip_address,
                user_agent=user_agent,
                action_data={
                    "filename": result["filename"],
                    "upload_type": "unified_single",
                },
            )

            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=result,
            )

        # Batch upload - create batch job and return detailed results
        from uuid import uuid4

        batch_id = uuid4()
        batch_job = BatchJob(
            id=batch_id,
            total_files=len(files),
            processed_files=0,
            failed_files=0,
            status=BatchJobStatus.pending,
            notification_email=notification_email,
        )
        db.add(batch_job)
        await db.flush()

        # Process batch upload
        batch_result = await upload_service.upload_batch(files, db, locale, request)

        # Update batch job with results
        batch_job.total_files = batch_result["total_files"]
        batch_job.failed_files = batch_result["failure_count"]

        if batch_result["failure_count"] > 0:
            batch_job.status = BatchJobStatus.failed if batch_result["success_count"] == 0 else BatchJobStatus.partial
            batch_job.error_message = f"{batch_result['failure_count']} file(s) failed to upload"
        else:
            batch_job.status = BatchJobStatus.completed
            batch_job.processed_files = batch_result["success_count"]

        await db.commit()

        # Log audit event for batch upload
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.RESUME_UPLOADED,
            entity_type="batch",
            entity_id=str(batch_id),
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "total_files": batch_result["total_files"],
                "success_count": batch_result["success_count"],
                "failure_count": batch_result["failure_count"],
                "upload_type": "unified_batch",
            },
        )

        # Return batch upload response
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "batch_id": str(batch_id),
                "total_files": batch_result["total_files"],
                "success_count": batch_result["success_count"],
                "failure_count": batch_result["failure_count"],
                "status": batch_job.status.value,
                "successful": batch_result["successful"],
                "failed": batch_result["failed"],
                "message": f"Batch upload completed: {batch_result['success_count']} successful, "
                          f"{batch_result['failure_count']} failed",
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error in unified upload: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed due to server error",
        ) from e
