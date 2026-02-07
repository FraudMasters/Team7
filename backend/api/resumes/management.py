"""
Resume management endpoints.

This module provides endpoints for updating resume status and deleting resumes.
These endpoints support the Kanban board workflow and resume lifecycle management.
"""
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message
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


class ResumeStatusUpdate(BaseModel):
    """Request model for updating resume status."""

    status: str = Field(..., description="New status value (new, reviewed, interview, offered, hired)")


@router.patch("/{resume_id}", tags=["Resumes"])
async def update_resume_status(
    request: Request,
    resume_id: str,
    status_update: ResumeStatusUpdate,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Update resume status (for Kanban board drag-and-drop).

    This endpoint allows updating a resume's status to support the Kanban board workflow.
    Valid statuses: new, reviewed, interview, offered, hired

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume to update
        status_update: Request body containing new status
        db: Database session

    Returns:
        JSON response with updated resume details

    Raises:
        HTTPException(404): If resume not found
        HTTPException(422): If invalid status value

    Examples:
        >>> import requests
        >>> response = requests.patch(
        ...     "http://localhost:8000/api/resumes/123e4567-e89b-12d3-a456-426614174000",
        ...     json={"status": "interview"}
        ... )
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "status": "interview"
        }
    """
    locale = _extract_locale(request)

    # Validate status value (accept both lowercase and uppercase, normalize to uppercase)
    valid_statuses = {"new", "reviewed", "interview", "offered", "hired", "pending", "completed", "processing", "failed"}
    status_lower = status_update.status.lower()
    if status_lower not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_update.status}'. Valid values: {', '.join(sorted(valid_statuses))}"
        )

    # Map lowercase to uppercase for database
    status_map = {
        "new": "NEW",
        "reviewed": "REVIEWED",
        "interview": "INTERVIEW",
        "offered": "OFFERED",
        "hired": "HIRED",
        "pending": "PENDING",
        "completed": "COMPLETED",
        "processing": "PROCESSING",
        "failed": "FAILED",
    }
    normalized_status = status_map.get(status_lower, status_update.status.upper())

    try:
        from models.resume import Resume as ResumeModel

        # Find resume
        try:
            resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
            resume_result = await db.execute(resume_query)
            resume_record = resume_result.scalar_one_or_none()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid resume ID format: {resume_id}"
            )

        if not resume_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume not found: {resume_id}"
            )

        # Store old status for audit log
        old_status = resume_record.status.value if resume_record.status else None

        # Update status (use normalized uppercase value for enum)
        new_status = ResumeStatus(normalized_status)
        resume_record.status = new_status

        await db.commit()
        await db.refresh(resume_record)

        # Log audit event (if audit_logs table exists)
        try:
            ip_address, user_agent = get_request_context(request)
            await log_audit_event(
                db=db,
                action_type=AuditActionType.RESUME_UPDATED,
                entity_type="resume",
                entity_id=resume_record.id,
                ip_address=ip_address,
                user_agent=user_agent,
                before_value={"status": old_status},
                after_value={"status": new_status.value},
            )
        except Exception as audit_err:
            logger.warning(f"Failed to log audit event: {audit_err}")

        logger.info(f"Updated resume {resume_id} status from {old_status} to {new_status.value}")

        # Return lowercase status for frontend compatibility
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(resume_record.id),
                "status": status_lower,  # Return lowercase for frontend
                "filename": resume_record.filename,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume status {resume_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update resume status: {str(e)}",
        ) from e


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Resumes"])
async def delete_resume(
    request: Request,
    resume_id: str,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Delete a resume by ID.

    Args:
        request: FastAPI request object
        resume_id: UUID of the resume to delete
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If resume not found

    Example:
        >>> response = requests.delete("http://localhost:8000/api/resumes/123")
        >>> response.status_code
        204
    """
    try:
        # First, try to find resume in database
        from models.resume import Resume as ResumeModel
        from pathlib import Path

        resume_record = None
        file_path = None

        # Try to parse as UUID for database lookup
        try:
            resume_query = select(ResumeModel).where(ResumeModel.id == UUID(resume_id))
            resume_result = await db.execute(resume_query)
            resume_record = resume_result.scalar_one_or_none()
        except ValueError:
            pass

        # Determine file path
        if resume_record and resume_record.file_path:
            file_path = Path(resume_record.file_path)

        # Delete from database if found
        if resume_record:
            # Log audit event before deletion
            ip_address, user_agent = get_request_context(request)
            await log_audit_event(
                db=db,
                action_type=AuditActionType.RESUME_DELETED,
                entity_type="resume",
                entity_id=resume_record.id,
                ip_address=ip_address,
                user_agent=user_agent,
                before_value={
                    "filename": resume_record.filename,
                    "status": resume_record.status.value if resume_record.status else None,
                    "created_at": resume_record.created_at.isoformat() if resume_record.created_at else None,
                },
            )

            await db.delete(resume_record)
            await db.commit()

        # Delete file from disk if exists
        if file_path and file_path.exists():
            file_path.unlink()

        logger.info(f"Deleted resume: {resume_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except Exception as e:
        logger.error(f"Error deleting resume {resume_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}",
        ) from e
