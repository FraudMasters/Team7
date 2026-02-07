"""
Data deletion request endpoints for GDPR right to be forgotten.

This module provides endpoints for submitting and managing data deletion requests
in accordance with GDPR Article 17 - Right to Erasure (Right to be Forgotten).
"""
import logging
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from i18n.backend_translations import get_error_message, get_success_message
from database import get_db
from models.data_deletion_request import DataDeletionRequest, DeletionRequestStatus
from models.resume import Resume
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


class DataDeletionRequestSchema(BaseModel):
    """Request model for data deletion requests."""

    resume_id: str = Field(..., description="ID of the resume to delete")
    reason: str = Field(..., description="Reason for deletion request (e.g., 'Right to be forgotten')")
    requester_email: Optional[str] = Field(None, description="Email of the person requesting deletion")


class DataDeletionRequestResponse(BaseModel):
    """Response model for data deletion request creation."""

    id: str = Field(..., description="Unique identifier for the deletion request")
    status: str = Field(..., description="Current status of the deletion request")
    message: str = Field(..., description="Success message")


class DataDeletionRequestListItem(BaseModel):
    """Response model for a single deletion request in a list."""

    id: str = Field(..., description="Unique identifier")
    requester_email: str = Field(..., description="Email of requester")
    requester_type: str = Field(..., description="Type of requester")
    status: str = Field(..., description="Current status")
    created_at: str = Field(..., description="Creation timestamp")
    notes: Optional[str] = Field(None, description="Additional notes")


@router.post(
    "/request",
    response_model=DataDeletionRequestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Data Deletion"],
)
async def create_deletion_request(
    request_data: DataDeletionRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Create a data deletion request (GDPR Right to be Forgotten).

    This endpoint allows individuals to request deletion of their personal data
    in accordance with GDPR Article 17. The request will be verified and processed
    according to the deletion workflow.

    Args:
        request_data: Deletion request details (resume_id, reason, optional email)
        request: FastAPI request object (for Accept-Language header)
        db: Database session

    Returns:
        JSON response with deletion request ID, status, and message

    Raises:
        HTTPException(404): If resume is not found
        HTTPException(422): If resume_id format is invalid
        HTTPException(500): If database operation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/data-deletion/request",
        ...     json={
        ...         "resume_id": "123e4567-e89b-12d3-a456-426614174000",
        ...         "reason": "Right to be forgotten"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "987fcdeb-51a2-43f1-a456-426614174000",
            "status": "pending",
            "message": "Deletion request created successfully"
        }
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate resume_id format
        try:
            resume_uuid = UUID(request_data.resume_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale, id=request_data.resume_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        # Check if resume exists
        resume_query = select(Resume).where(Resume.id == resume_uuid)
        resume_result = await db.execute(resume_query)
        resume = resume_result.scalar_one_or_none()

        if not resume:
            error_msg = get_error_message("resume_not_found", locale, id=request_data.resume_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Use provided email or extract from resume data if available
        requester_email = request_data.requester_email
        requester_type = "candidate"

        # Create notes with resume_id and reason
        notes = f"Resume ID: {request_data.resume_id}. Reason: {request_data.reason}"

        # Create deletion request
        deletion_request = DataDeletionRequest(
            requester_email=requester_email or "unknown@example.com",
            requester_type=requester_type,
            status=DeletionRequestStatus.PENDING,
            notes=notes,
        )

        db.add(deletion_request)
        await db.commit()
        await db.refresh(deletion_request)

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.RESUME_DELETED,  # Reusing existing action type
            entity_type="data_deletion_request",
            entity_id=deletion_request.id,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "resume_id": request_data.resume_id,
                "reason": request_data.reason,
                "requester_email": requester_email or "not provided",
            },
        )

        # Get translated success message
        success_message = get_success_message("deletion_request_created", locale)

        response_data = {
            "id": str(deletion_request.id),
            "status": deletion_request.status.value,
            "message": success_message,
        }

        logger.info(f"Data deletion request created: {deletion_request.id} for resume {request_data.resume_id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error creating deletion request: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("database_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
    except Exception as e:
        logger.error(f"Error creating deletion request: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("internal_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/request/{request_id}",
    response_model=DataDeletionRequestListItem,
    tags=["Data Deletion"],
)
async def get_deletion_request(
    request_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Get a data deletion request by ID.

    Args:
        request_id: UUID of the deletion request
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with deletion request details

    Raises:
        HTTPException(404): If deletion request not found
        HTTPException(422): If request_id format is invalid

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/data-deletion/request/123")
        >>> response.json()
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "requester_email": "user@example.com",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00"
        }
    """
    locale = _extract_locale(request)

    try:
        # Validate request_id format
        try:
            request_uuid = UUID(request_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale, id=request_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        # Query deletion request
        query = select(DataDeletionRequest).where(DataDeletionRequest.id == request_uuid)
        result = await db.execute(query)
        deletion_request = result.scalar_one_or_none()

        if not deletion_request:
            error_msg = get_error_message("deletion_request_not_found", locale, id=request_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(deletion_request.id),
                "requester_email": deletion_request.requester_email,
                "requester_type": deletion_request.requester_type,
                "status": deletion_request.status.value,
                "created_at": deletion_request.created_at.isoformat() if deletion_request.created_at else None,
                "notes": deletion_request.notes,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving deletion request {request_id}: {e}", exc_info=True)
        error_msg = get_error_message("internal_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.get(
    "/requests",
    response_model=list[DataDeletionRequestListItem],
    tags=["Data Deletion"],
)
async def list_deletion_requests(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    List all data deletion requests.

    Returns a paginated list of all deletion requests with their basic information.

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of deletion requests

    Examples:
        >>> response = requests.get("http://localhost:8000/api/data-deletion/requests?limit=10")
        >>> requests = response.json()
    """
    locale = _extract_locale(request)

    try:
        # Query deletion requests
        query = select(DataDeletionRequest).order_by(
            DataDeletionRequest.created_at.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        deletion_requests = result.scalars().all()

        # Convert to response format
        requests_list = []
        for dr in deletion_requests:
            requests_list.append({
                "id": str(dr.id),
                "requester_email": dr.requester_email,
                "requester_type": dr.requester_type,
                "status": dr.status.value,
                "created_at": dr.created_at.isoformat() if dr.created_at else None,
                "notes": dr.notes,
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=requests_list,
        )

    except Exception as e:
        logger.error(f"Error listing deletion requests: {e}", exc_info=True)
        error_msg = get_error_message("internal_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e


@router.delete(
    "/request/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Data Deletion"],
)
async def cancel_deletion_request(
    request_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """
    Cancel a pending data deletion request.

    Args:
        request_id: UUID of the deletion request to cancel
        request: FastAPI request object
        db: Database session

    Returns:
        204 No Content on success

    Raises:
        HTTPException(404): If deletion request not found
        HTTPException(400): If request cannot be cancelled (already processed)

    Examples:
        >>> response = requests.delete("http://localhost:8000/api/data-deletion/request/123")
        >>> response.status_code
        204
    """
    locale = _extract_locale(request)

    try:
        # Validate request_id format
        try:
            request_uuid = UUID(request_id)
        except ValueError:
            error_msg = get_error_message("invalid_uuid", locale, id=request_id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg,
            )

        # Query deletion request
        query = select(DataDeletionRequest).where(DataDeletionRequest.id == request_uuid)
        result = await db.execute(query)
        deletion_request = result.scalar_one_or_none()

        if not deletion_request:
            error_msg = get_error_message("deletion_request_not_found", locale, id=request_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )

        # Can only cancel pending requests
        if deletion_request.status != DeletionRequestStatus.PENDING:
            error_msg = get_error_message("cannot_cancel_request", locale, status=deletion_request.status.value)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

        # Delete the request
        await db.delete(deletion_request)
        await db.commit()

        # Log audit event
        ip_address, user_agent = get_request_context(request)
        await log_audit_event(
            db=db,
            action_type=AuditActionType.RESUME_UPDATED,  # Reusing existing action type
            entity_type="data_deletion_request",
            entity_id=request_uuid,
            ip_address=ip_address,
            user_agent=user_agent,
            action_data={
                "action": "cancelled",
                "previous_status": "pending",
            },
        )

        logger.info(f"Deletion request cancelled: {request_id}")

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deletion request {request_id}: {e}", exc_info=True)
        await db.rollback()
        error_msg = get_error_message("internal_error", locale)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg,
        ) from e
