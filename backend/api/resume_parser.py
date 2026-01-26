"""
Resume parsing endpoints.

This module provides endpoints for parsing resume files (PDF, DOCX),
validating file format and size, extracting text content, and preparing
the resume for analysis.
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


class ResumeParseResponse(BaseModel):
    """Response model for resume parse endpoint."""

    id: str = Field(..., description="Unique identifier for the parsed resume")
    filename: str = Field(..., description="Original filename of the parsed resume")
    status: str = Field(..., description="Processing status of the resume")
    raw_text: Optional[str] = Field(None, description="Extracted text content from resume")
    language: Optional[str] = Field(None, description="Detected language code (e.g., 'en', 'ru')")
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
    "/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Resume Parser"],
)
async def parse_resume(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """
    Parse a resume file to extract text content.

    This endpoint accepts resume files in PDF or DOCX format, validates the file
    type and size, stores the file, extracts text content, detects language,
    and prepares the resume for further analysis.

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)

    Returns:
        JSON response with resume ID, filename, status, extracted text, and language

    Raises:
        HTTPException(415): If file type is not supported
        HTTPException(413): If file size exceeds maximum allowed
        HTTPException(500): If file storage or parsing fails

    Examples:
        >>> import requests
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8000/api/resume-parser/parse", files={"file": f})
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "filename": "resume.pdf",
            "status": "processing",
            "raw_text": "John Doe\\nSoftware Engineer...",
            "language": "en",
            "message": "Resume parsing initiated"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        logger.info(f"Received file for parsing: {file.filename} ({file_size} bytes)")

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
        success_message = get_success_message("resume_parsing_initiated", locale)

        # For now, return a response indicating parsing has been initiated
        # Actual parsing implementation will be added in a later subtask
        # when we have the text extraction service integrated
        response_data = {
            "id": file_id,
            "filename": file.filename or "unknown",
            "status": ResumeStatus.PROCESSING.value,
            "raw_text": None,
            "language": None,
            "message": success_message,
        }

        logger.info(f"Resume parsing initiated: {file_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error parsing resume: {e}", exc_info=True)
        error_msg = get_error_message("resume_parsing_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
