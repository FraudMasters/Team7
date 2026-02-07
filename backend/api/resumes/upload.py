"""
Resume upload endpoint and validation functions.

This module provides the endpoint for uploading resume files (PDF, DOCX).
The core upload logic is delegated to the UnifiedUploadService for consistency,
while this module maintains the compatibility layer and adds audit logging.

This is a compatibility layer that routes requests to the new unified service.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.resume import ResumeStatus
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context
from services.upload_service import get_upload_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload endpoint."""

    id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Processing status of the resume")
    message: str = Field(..., description="Success message")


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resumes"],
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload a resume file for analysis.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, stores the file, and creates a database record for tracking.

    The core upload logic is delegated to UnifiedUploadService for consistency
    across the application, while this endpoint maintains the compatibility layer
    and adds audit logging.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)
        db: Database session

    Returns:
        JSON response with resume ID, filename, and status

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum allowed
        HTTPException(500): If file storage or database operation fails

    Examples:
        >>> import requests
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8000/api/resumes/upload", files={"file": f})
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "pending",
            "message": "Resume uploaded successfully"
        }
    """
    # Get the unified upload service
    upload_service = get_upload_service()

    # Extract locale from Accept-Language header
    locale = upload_service.extract_locale(request)

    try:
        # Use unified upload service for core upload logic
        result = await upload_service.upload_file(file, db, locale, request)

        # Log audit event (compatibility layer adds this)
        resume_id = UUID(result["id"])
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.RESUME_UPLOADED,
            entity_type="resume",
            entity_id=resume_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "filename": result["filename"],
                "content_type": file.content_type or "application/octet-stream" if file else "application/octet-stream",
            },
        )

        logger.info(f"Resume uploaded successfully: {result['id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=result,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume upload failed: {str(e)}",
        ) from e
