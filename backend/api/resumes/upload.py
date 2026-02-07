"""
Resume upload endpoint and validation functions.

This module provides the endpoint for uploading resume files (PDF, DOCX).
The core upload logic is delegated to the UnifiedUploadService for consistency,
while this module maintains the compatibility layer and adds audit logging.

This is a compatibility layer that routes requests to the new unified service.

**DEPRECATED**: This endpoint is deprecated and will be removed in a future version.
Please use the unified upload endpoint at `/api/resumes/unified-upload` instead.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
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
    status_code=status.HTTP_301_MOVED_PERMANENTLY,
    tags=["Resumes"],
    deprecated=True,
)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Upload a resume file for analysis.

    **DEPRECATED**: This endpoint is deprecated as of 2026-02-07.
    Please migrate to the unified upload endpoint at `/api/resumes/unified-upload`.

    This endpoint now permanently redirects to the new unified upload endpoint.
    The new endpoint provides enhanced security features including:
    - Magic number file validation
    - XXE protection for DOCX files
    - Filename sanitization to prevent path traversal
    - Consolidated single and batch upload functionality

    Migration guide:
    - Old: POST /api/resumes/upload with file in form data
    - New: POST /api/resumes/unified-upload with files in form data

    Args:
        request: FastAPI request object (for Accept-Language header)
        file: Uploaded resume file (PDF or DOCX)
        db: Database session

    Returns:
        Permanent redirect (301) to the new unified upload endpoint

    Examples:
        >>> import requests
        >>> # Old endpoint (deprecated - will redirect)
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8000/api/resumes/upload", files={"file": f})
        >>> # New endpoint (use this instead)
        >>> with open("resume.pdf", "rb") as f:
        ...     response = requests.post("http://localhost:8000/api/resumes/unified-upload", files={"files": f})
    """
    # Log deprecation warning
    logger.warning(
        f"Deprecated endpoint /api/resumes/upload called from {request.client.host}. "
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
