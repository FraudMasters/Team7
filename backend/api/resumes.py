"""
Resume upload and management endpoints.

This module provides endpoints for uploading resume files (PDF, DOCX),
validating file format and size, storing files, and creating database records.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from ..config import get_settings
from ..i18n.backend_translations import get_error_message, get_success_message
from ..models.resume import Resume, ResumeStatus

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
async def upload_resume(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload a resume file for analysis.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, stores the file, and creates a database record for tracking.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)

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

        # Generate unique filename to avoid conflicts
        safe_filename = Path(file.filename or "resume").name
        file_id = f"{os.urandom(8).hex()}"
        file_extension = Path(safe_filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file to disk
        logger.info(f"Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Get translated success message
        success_message = get_success_message("file_uploaded", locale)

        # For now, create a simple response without database operations
        # Database integration will be added in a later subtask when we have async session setup
        response_data = {
            "id": file_id,
            "filename": file.filename or "unknown",
            "status": ResumeStatus.PENDING.value,
            "message": success_message,
        }

        logger.info(f"Resume uploaded successfully: {file_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}", exc_info=True)
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get("/{resume_id}", tags=["Resumes"])
async def get_resume(request: Request, resume_id: str) -> JSONResponse:
    """
    Get resume information by ID.

    Args:
        request: FastAPI request object (for Accept-Language header)
        resume_id: Unique identifier of the resume

    Returns:
        JSON response with resume details

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(500): If database query fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/resumes/123e4567-e89b-12d3-a456-426614174000")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "pending",
            "uploaded_at": "2024-01-24T12:00:00Z"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    # TODO: Implement database lookup in a later subtask
    # For now, return a placeholder response
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "id": resume_id,
            "filename": "unknown",
            "status": "pending",
            "message": "Database integration pending",
        },
    )
