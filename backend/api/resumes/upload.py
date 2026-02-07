"""
Resume upload endpoint and validation functions.

This module provides the endpoint for uploading resume files (PDF, DOCX),
along with helper functions for validating file format and size.
"""
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.resume import Resume, ResumeStatus
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context
from utils.file_validation import validate_magic_number

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


# Directory for storing uploaded resumes
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload endpoint."""

    id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original filename of the uploaded resume")
    status: str = Field(..., description="Processing status of the resume")
    message: str = Field(..., description="Success message")


def validate_file_type(filename: str, content_type: str, locale: str = "en") -> None:
    """
    Validate that the file type is allowed.

    Args:
        filename: Name of the uploaded file
        content_type: MIME type of the file
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file type is not allowed
    """
    # Check file extension
    file_ext = Path(filename).suffix.lower()
    if file_ext not in settings.allowed_file_types:
        allowed = ", ".join(settings.allowed_file_types)
        error_msg = get_error_message("invalid_file_type", locale, file_ext=file_ext, allowed=allowed)
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=error_msg,
        )

    # Check content type for additional validation
    allowed_content_types = {
        ".pdf": ["application/pdf"],
        ".docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ],
    }

    if file_ext in allowed_content_types:
        if content_type not in allowed_content_types[file_ext]:
            logger.warning(
                f"Content type mismatch for {filename}: {content_type} not in {allowed_content_types[file_ext]}"
            )


def validate_file_size(file_size: int, locale: str = "en") -> None:
    """
    Validate that the file size is within allowed limits.

    Args:
        file_size: Size of the file in bytes
        locale: Language code for translated error messages

    Raises:
        HTTPException: If file size exceeds maximum allowed
    """
    max_size = settings.max_upload_size_bytes
    if file_size > max_size:
        max_mb = settings.max_upload_size_mb
        size_mb = file_size / 1024 / 1024
        error_msg = get_error_message("file_too_large", locale, size=size_mb, max_mb=max_mb)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg,
        )


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
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received file upload: {file.filename} ({file_size} bytes)")

        # Validate file type
        validate_file_type(file.filename or "unknown", file.content_type or "application/octet-stream", locale)

        # Validate file size
        validate_file_size(file_size, locale)

        # Validate magic number (file signature) to prevent malicious file uploads
        file_extension = Path(file.filename or "resume").suffix
        is_valid, error_msg = validate_magic_number(file_content, file_extension, locale)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=error_msg,
            )

        # Generate UUID for the resume
        resume_id = uuid4()
        safe_filename = Path(file.filename or "resume").name
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{resume_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file to disk
        logger.info(f"Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create database record
        new_resume = Resume(
            id=resume_id,
            filename=file.filename or "unknown",
            file_path=str(file_path),
            content_type=file.content_type or "application/octet-stream",
            status=ResumeStatus.PENDING,
        )

        db.add(new_resume)
        await db.commit()
        await db.refresh(new_resume)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.RESUME_UPLOADED,
            entity_type="resume",
            entity_id=resume_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "filename": file.filename or "unknown",
                "file_size": file_size,
                "content_type": file.content_type or "application/octet-stream",
            },
        )

        # Get translated success message
        success_message = get_success_message("file_uploaded", locale)

        response_data = {
            "id": str(resume_id),
            "filename": file.filename or "unknown",
            "status": ResumeStatus.PENDING.value,
            "message": success_message,
        }

        logger.info(f"Resume uploaded successfully: {resume_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
