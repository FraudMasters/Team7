"""
Webhook endpoints for receiving resume submissions from external sources.

This module provides endpoints for external job boards and recruitment platforms
to submit resume data via webhooks.
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.resume import Resume, ResumeStatus
from models.audit_log import AuditActionType
from utils.audit_logger import log_audit_event, get_request_context

logger = logging.getLogger(__name__)

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


class ResumeWebhookRequest(BaseModel):
    """Request model for resume webhook submission."""

    source: str = Field(..., description="Source of the resume submission (e.g., 'linkedin', 'indeed', 'test')")
    resume_url: Optional[HttpUrl] = Field(None, description="URL to the resume file")
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    candidate_email: Optional[str] = Field(None, description="Email address of the candidate")
    candidate_phone: Optional[str] = Field(None, description="Phone number of the candidate")
    job_id: Optional[str] = Field(None, description="ID of the job vacancy this resume is for")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata from the source")


class ResumeWebhookResponse(BaseModel):
    """Response model for resume webhook endpoint."""

    id: str = Field(..., description="Unique identifier for the submitted resume")
    status: str = Field(..., description="Processing status of the resume")
    message: str = Field(..., description="Success message")
    source: str = Field(..., description="Source of the submission")


@router.post(
    "/resume",
    response_model=ResumeWebhookResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Webhooks"],
)
async def receive_resume_webhook(
    request: Request,
    webhook_data: ResumeWebhookRequest,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Receive resume submission via webhook from external sources.

    This endpoint allows external job boards and recruitment platforms to submit
    resume data via webhooks. The resume can be provided as a URL or inline data.

    Args:
        request: FastAPI request object (for Accept-Language header)
        webhook_data: Webhook payload containing resume information
        db: Database session

    Returns:
        JSON response with resume ID, status, and message

    Raises:
        HTTPException(400): If webhook data is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> payload = {
        ...     "source": "test",
        ...     "resume_url": "http://example.com/resume.pdf",
        ...     "candidate_name": "John Doe",
        ...     "candidate_email": "john@example.com"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/webhooks/resume",
        ...     json=payload
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "pending",
            "message": "Resume received successfully",
            "source": "test"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate source
        if not webhook_data.source or len(webhook_data.source.strip()) == 0:
            error_msg = get_error_message("invalid_source", locale)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Generate UUID for the resume
        resume_id = uuid4()

        # Create database record with webhook data
        new_resume = Resume(
            id=resume_id,
            filename=f"webhook_{webhook_data.source}_{resume_id}",
            file_path="",  # Will be updated when file is downloaded
            content_type="application/octet-stream",
            status=ResumeStatus.PENDING,
            raw_text=f"Webhook submission from {webhook_data.source}",
            language="en",  # Default language, will be detected during processing
        )

        # Add additional metadata
        if webhook_data.candidate_name:
            new_resume.raw_text += f"\nCandidate: {webhook_data.candidate_name}"
        if webhook_data.candidate_email:
            new_resume.raw_text += f"\nEmail: {webhook_data.candidate_email}"
        if webhook_data.candidate_phone:
            new_resume.raw_text += f"\nPhone: {webhook_data.candidate_phone}"
        if webhook_data.job_id:
            new_resume.raw_text += f"\nJob ID: {webhook_data.job_id}"
        if webhook_data.resume_url:
            new_resume.raw_text += f"\nResume URL: {str(webhook_data.resume_url)}"

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
                "source": webhook_data.source,
                "resume_url": str(webhook_data.resume_url) if webhook_data.resume_url else None,
                "candidate_name": webhook_data.candidate_name,
                "candidate_email": webhook_data.candidate_email,
                "job_id": webhook_data.job_id,
                "webhook": True,
                "metadata": webhook_data.metadata,
            },
        )

        # Get translated success message
        success_message = get_success_message("file_uploaded", locale)

        response_data = {
            "id": str(resume_id),
            "status": ResumeStatus.PENDING.value,
            "message": success_message,
            "source": webhook_data.source,
        }

        logger.info(
            f"Resume webhook received successfully: {resume_id} from {webhook_data.source}"
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Error processing resume webhook: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("file_upload_failed", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
