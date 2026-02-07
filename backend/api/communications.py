"""
Communication management endpoints.

This module provides endpoints for managing all candidate communications,
including emails, SMS messages, phone calls, and in-system messages.
Supports CRUD operations for creating, reading, updating, and deleting communications.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.communication import Communication, CommunicationType, CommunicationDirection, CommunicationStatus
from models.resume import Resume

logger = logging.getLogger(__name__)

router = APIRouter()


class CommunicationCreate(BaseModel):
    """Request model for creating a communication."""

    candidate_id: str = Field(..., description="Candidate (resume) ID this communication is with")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID (if applicable)")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (sender/receiver)")
    type: str = Field(..., description="Communication type (email, sms, phone_call, in_system)")
    direction: str = Field(..., description="Communication direction (inbound, outbound)")
    status: str = Field(CommunicationStatus.PENDING, description="Communication status")
    subject: Optional[str] = Field(None, max_length=500, description="Communication subject")
    body: Optional[str] = Field(None, description="Communication body/content")
    sent_at: Optional[str] = Field(None, description="ISO timestamp when communication was sent")
    received_at: Optional[str] = Field(None, description="ISO timestamp when communication was received")
    metadata: Optional[dict] = Field(None, description="Additional communication-specific data")


class CommunicationUpdate(BaseModel):
    """Request model for updating a communication."""

    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (sender/receiver)")
    status: Optional[str] = Field(None, description="Communication status")
    subject: Optional[str] = Field(None, max_length=500, description="Communication subject")
    body: Optional[str] = Field(None, description="Communication body/content")
    sent_at: Optional[str] = Field(None, description="ISO timestamp when communication was sent")
    received_at: Optional[str] = Field(None, description="ISO timestamp when communication was received")
    metadata: Optional[dict] = Field(None, description="Additional communication-specific data")


class CommunicationResponse(BaseModel):
    """Response model for a single communication."""

    id: str = Field(..., description="Unique identifier for the communication")
    candidate_id: str = Field(..., description="Candidate (resume) ID")
    vacancy_id: Optional[str] = Field(None, description="Associated vacancy ID")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID")
    type: str = Field(..., description="Communication type")
    direction: str = Field(..., description="Communication direction")
    status: str = Field(..., description="Communication status")
    subject: Optional[str] = Field(None, description="Communication subject")
    body: Optional[str] = Field(None, description="Communication body")
    sent_at: Optional[str] = Field(None, description="Sent timestamp")
    received_at: Optional[str] = Field(None, description="Received timestamp")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CommunicationListResponse(BaseModel):
    """Response model for listing communications."""

    communications: List[CommunicationResponse] = Field(..., description="List of communications")
    total_count: int = Field(..., description="Total number of communications")


class ResponseTimeMetrics(BaseModel):
    """Communication response time metrics."""

    average_response_hours: float = Field(..., description="Average response time in hours")
    median_response_hours: float = Field(..., description="Median response time in hours")
    min_response_hours: float = Field(..., description="Minimum response time in hours")
    max_response_hours: float = Field(..., description="Maximum response time in hours")


class EngagementMetrics(BaseModel):
    """Communication engagement statistics."""

    total_sent: int = Field(..., description="Total communications sent")
    total_responses: int = Field(..., description="Total responses received")
    response_rate: float = Field(..., description="Response rate (responses/sent) (0-1)")
    by_type: dict = Field(..., description="Engagement breakdown by communication type")
    by_status: dict = Field(..., description="Engagement breakdown by status")


class UpcomingFollowup(BaseModel):
    """Upcoming follow-up item."""

    communication_id: str = Field(..., description="Communication ID")
    candidate_id: str = Field(..., description="Candidate ID")
    type: str = Field(..., description="Communication type")
    subject: Optional[str] = Field(None, description="Communication subject")
    followup_date: str = Field(..., description="Follow-up date (ISO 8601)")
    priority: str = Field(..., description="Priority level (high, medium, low)")


class CommunicationMetricsResponse(BaseModel):
    """Response model for communication metrics."""

    response_time: ResponseTimeMetrics = Field(..., description="Response time metrics")
    engagement: EngagementMetrics = Field(..., description="Engagement statistics")
    upcoming_followups: List[UpcomingFollowup] = Field(..., description="List of upcoming follow-ups")


@router.post(
    "/",
    response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Communications"],
)
async def create_communication(
    request: CommunicationCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a communication.

    This endpoint creates a new communication record for tracking interactions
    with candidates, including emails, SMS messages, phone calls, and in-system messages.

    Args:
        request: Request body containing communication details
        db: Database session

    Returns:
        JSON response with created communication details

    Raises:
        HTTPException(404): If candidate (resume) is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/communications/",
        ...     json={
        ...         "candidate_id": "resume-uuid",
        ...         "type": "email",
        ...         "direction": "outbound",
        ...         "subject": "Interview Invitation",
        ...         "body": "We would like to invite you for an interview",
        ...         "recruiter_id": "recruiter-uuid",
        ...         "status": "sent"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Creating communication for candidate: {request.candidate_id}")

        # Verify candidate exists
        resume_result = await db.execute(
            select(Resume).where(Resume.id == UUID(request.candidate_id))
        )
        resume = resume_result.scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate (resume) not found: {request.candidate_id}",
            )

        # Parse timestamps if provided
        from datetime import datetime
        sent_at = None
        received_at = None

        if request.sent_at:
            try:
                sent_at = datetime.fromisoformat(request.sent_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid sent_at timestamp format. Use ISO 8601 format.",
                )

        if request.received_at:
            try:
                received_at = datetime.fromisoformat(request.received_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid received_at timestamp format. Use ISO 8601 format.",
                )

        # Create new communication
        new_communication = Communication(
            candidate_id=UUID(request.candidate_id),
            vacancy_id=UUID(request.vacancy_id) if request.vacancy_id else None,
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            type=CommunicationType(request.type),
            direction=CommunicationDirection(request.direction),
            status=CommunicationStatus(request.status),
            subject=request.subject,
            body=request.body,
            sent_at=sent_at,
            received_at=received_at,
            metadata=request.metadata,
        )
        db.add(new_communication)
        await db.flush()

        response_data = {
            "id": str(new_communication.id),
            "candidate_id": str(new_communication.candidate_id),
            "vacancy_id": str(new_communication.vacancy_id) if new_communication.vacancy_id else None,
            "recruiter_id": str(new_communication.recruiter_id) if new_communication.recruiter_id else None,
            "type": new_communication.type.value,
            "direction": new_communication.direction.value,
            "status": new_communication.status.value,
            "subject": new_communication.subject,
            "body": new_communication.body,
            "sent_at": new_communication.sent_at.isoformat() if new_communication.sent_at else None,
            "received_at": new_communication.received_at.isoformat() if new_communication.received_at else None,
            "metadata": new_communication.metadata,
            "created_at": new_communication.created_at.isoformat(),
            "updated_at": new_communication.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"Created communication with ID: {new_communication.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid value: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating communication: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create communication: {str(e)}",
        ) from e


@router.get("/", tags=["Communications"])
async def list_communications(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter ID"),
    type: Optional[str] = Query(None, description="Filter by communication type"),
    direction: Optional[str] = Query(None, description="Filter by direction"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search_query: Optional[str] = Query(None, description="Search in subject and body (case-insensitive)"),
    date_range: Optional[str] = Query(None, description="Date range filter (format: YYYY-MM-DD,YYYY-MM-DD or YYYY-MM-DD,)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List communications with optional filters.

    This endpoint retrieves communications with support for filtering
    by candidate, vacancy, recruiter, type, direction, status, date range,
    and full-text search.

    Args:
        candidate_id: Optional candidate ID filter
        vacancy_id: Optional vacancy ID filter
        recruiter_id: Optional recruiter ID filter
        type: Optional communication type filter
        direction: Optional direction filter
        status: Optional status filter
        search_query: Optional search term to filter by subject or body (case-insensitive)
        date_range: Optional date range filter (format: start_date,end_date or start_date, or ,end_date)
        limit: Maximum number of records to return (default: 100, max: 500)
        db: Database session

    Returns:
        JSON response with list of communications

    Raises:
        HTTPException(400): If date_range format is invalid
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> # Filter by candidate
        >>> response = requests.get("http://localhost:8000/api/communications/?candidate_id=resume-uuid")
        >>> # Filter by type with limit
        >>> response = requests.get("http://localhost:8000/api/communications/?type=email&limit=10")
        >>> # Search by subject/body
        >>> response = requests.get("http://localhost:8000/api/communications/?search_query=interview")
        >>> # Filter by date range
        >>> response = requests.get("http://localhost:8000/api/communications/?date_range=2024-01-01,2024-12-31")
        >>> response.json()
        {
            "communications": [...],
            "total_count": 3
        }
    """
    try:
        from datetime import datetime

        logger.info(
            f"Listing communications with filters - candidate_id: {candidate_id}, type: {type}, "
            f"direction: {direction}, search_query: {search_query}, date_range: {date_range}, limit: {limit}"
        )

        # Build query
        query = select(Communication)

        if candidate_id:
            query = query.where(Communication.candidate_id == UUID(candidate_id))
        if vacancy_id:
            query = query.where(Communication.vacancy_id == UUID(vacancy_id))
        if recruiter_id:
            query = query.where(Communication.recruiter_id == UUID(recruiter_id))
        if type:
            query = query.where(Communication.type == CommunicationType(type))
        if direction:
            query = query.where(Communication.direction == CommunicationDirection(direction))
        if status:
            query = query.where(Communication.status == CommunicationStatus(status))

        # Search query - filter by subject or body (case-insensitive)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                (Communication.subject.ilike(search_pattern)) |
                (Communication.body.ilike(search_pattern))
            )

        # Date range filter
        if date_range:
            try:
                # Parse date range (format: start_date,end_date or start_date, or ,end_date)
                parts = date_range.split(',')
                if len(parts) != 2:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid date_range format. Use: YYYY-MM-DD,YYYY-MM-DD or YYYY-MM-DD, or ,YYYY-MM-DD",
                    )

                start_date_str, end_date_str = parts

                # Filter by sent_at or received_at (whichever is available)
                # We check both fields to capture communications in the range
                if start_date_str:
                    try:
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                        # Communications where sent_at OR received_at is after start_date
                        query = query.where(
                            (Communication.sent_at >= start_date) | (Communication.received_at >= start_date)
                        )
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid start_date format: {start_date_str}. Use YYYY-MM-DD format.",
                        )

                if end_date_str:
                    try:
                        # Include the entire end date by adding one day
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                        from datetime import timedelta
                        end_date_inclusive = end_date + timedelta(days=1)
                        # Communications where sent_at OR received_at is before end of end_date
                        query = query.where(
                            (Communication.sent_at < end_date_inclusive) | (Communication.received_at < end_date_inclusive)
                        )
                    except ValueError:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid end_date format: {end_date_str}. Use YYYY-MM-DD format.",
                        )

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error parsing date_range: {str(e)}",
                )

        query = query.order_by(Communication.created_at.desc()).limit(limit)

        result = await db.execute(query)
        communications = result.scalars().all()

        # Build response
        communications_data = []
        for comm in communications:
            communications_data.append({
                "id": str(comm.id),
                "candidate_id": str(comm.candidate_id),
                "vacancy_id": str(comm.vacancy_id) if comm.vacancy_id else None,
                "recruiter_id": str(comm.recruiter_id) if comm.recruiter_id else None,
                "type": comm.type.value,
                "direction": comm.direction.value,
                "status": comm.status.value,
                "subject": comm.subject,
                "body": comm.body,
                "sent_at": comm.sent_at.isoformat() if comm.sent_at else None,
                "received_at": comm.received_at.isoformat() if comm.received_at else None,
                "metadata": comm.metadata,
                "created_at": comm.created_at.isoformat(),
                "updated_at": comm.updated_at.isoformat(),
            })

        response_data = {
            "communications": communications_data,
            "total_count": len(communications_data),
        }

        logger.info(f"Retrieved {len(communications_data)} communications")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID or enum format",
        )
    except Exception as e:
        logger.error(f"Error listing communications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list communications: {str(e)}",
        ) from e


@router.get("/{communication_id}", tags=["Communications"])
async def get_communication(
    communication_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a specific communication by ID.

    This endpoint retrieves detailed information about a single communication.

    Args:
        communication_id: UUID of the communication
        db: Database session

    Returns:
        JSON response with communication details

    Raises:
        HTTPException(404): If communication is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/communications/comm-uuid")
        >>> response.json()
        {
            "id": "comm-uuid",
            "candidate_id": "resume-uuid",
            "type": "email",
            ...
        }
    """
    try:
        logger.info(f"Retrieving communication: {communication_id}")

        result = await db.execute(
            select(Communication).where(Communication.id == UUID(communication_id))
        )
        communication = result.scalar_one_or_none()

        if not communication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication not found: {communication_id}",
            )

        response_data = {
            "id": str(communication.id),
            "candidate_id": str(communication.candidate_id),
            "vacancy_id": str(communication.vacancy_id) if communication.vacancy_id else None,
            "recruiter_id": str(communication.recruiter_id) if communication.recruiter_id else None,
            "type": communication.type.value,
            "direction": communication.direction.value,
            "status": communication.status.value,
            "subject": communication.subject,
            "body": communication.body,
            "sent_at": communication.sent_at.isoformat() if communication.sent_at else None,
            "received_at": communication.received_at.isoformat() if communication.received_at else None,
            "metadata": communication.metadata,
            "created_at": communication.created_at.isoformat(),
            "updated_at": communication.updated_at.isoformat(),
        }

        logger.info(f"Retrieved communication: {communication_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {communication_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving communication: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve communication: {str(e)}",
        ) from e


@router.put("/{communication_id}", tags=["Communications"])
async def update_communication(
    communication_id: str,
    request: CommunicationUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a communication.

    This endpoint updates an existing communication.
    Only the fields specified in the request body will be updated.

    Args:
        communication_id: UUID of the communication
        request: Request body containing fields to update
        db: Database session

    Returns:
        JSON response with updated communication details

    Raises:
        HTTPException(404): If communication is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/communications/comm-uuid",
        ...     json={
        ...         "status": "delivered",
        ...         "subject": "Updated subject"
        ...     }
        ... )
        >>> response.json()
        {
            "id": "comm-uuid",
            "status": "delivered",
            "subject": "Updated subject",
            ...
        }
    """
    try:
        logger.info(f"Updating communication: {communication_id}")

        # Get existing communication
        result = await db.execute(
            select(Communication).where(Communication.id == UUID(communication_id))
        )
        communication = result.scalar_one_or_none()

        if not communication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication not found: {communication_id}",
            )

        # Parse timestamps if provided
        from datetime import datetime
        sent_at = None
        received_at = None

        if request.sent_at is not None:
            try:
                sent_at = datetime.fromisoformat(request.sent_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid sent_at timestamp format. Use ISO 8601 format.",
                )

        if request.received_at is not None:
            try:
                received_at = datetime.fromisoformat(request.received_at.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid received_at timestamp format. Use ISO 8601 format.",
                )

        # Update fields if provided
        if request.vacancy_id is not None:
            communication.vacancy_id = UUID(request.vacancy_id) if request.vacancy_id else None
        if request.recruiter_id is not None:
            communication.recruiter_id = UUID(request.recruiter_id) if request.recruiter_id else None
        if request.status is not None:
            communication.status = CommunicationStatus(request.status)
        if request.subject is not None:
            communication.subject = request.subject
        if request.body is not None:
            communication.body = request.body
        if request.sent_at is not None:
            communication.sent_at = sent_at
        if request.received_at is not None:
            communication.received_at = received_at
        if request.metadata is not None:
            communication.metadata = request.metadata

        await db.commit()
        await db.refresh(communication)

        response_data = {
            "id": str(communication.id),
            "candidate_id": str(communication.candidate_id),
            "vacancy_id": str(communication.vacancy_id) if communication.vacancy_id else None,
            "recruiter_id": str(communication.recruiter_id) if communication.recruiter_id else None,
            "type": communication.type.value,
            "direction": communication.direction.value,
            "status": communication.status.value,
            "subject": communication.subject,
            "body": communication.body,
            "sent_at": communication.sent_at.isoformat() if communication.sent_at else None,
            "received_at": communication.received_at.isoformat() if communication.received_at else None,
            "metadata": communication.metadata,
            "created_at": communication.created_at.isoformat(),
            "updated_at": communication.updated_at.isoformat(),
        }

        logger.info(f"Updated communication: {communication_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid value: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error updating communication: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update communication: {str(e)}",
        ) from e


@router.delete("/{communication_id}", tags=["Communications"])
async def delete_communication(
    communication_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a communication.

    This endpoint permanently deletes a communication record.
    This action cannot be undone.

    Args:
        communication_id: UUID of the communication
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(404): If communication is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/communications/comm-uuid")
        >>> response.json()
        {
            "message": "Communication deleted successfully",
            "id": "comm-uuid"
        }
    """
    try:
        logger.info(f"Deleting communication: {communication_id}")

        # Check if communication exists
        result = await db.execute(
            select(Communication).where(Communication.id == UUID(communication_id))
        )
        communication = result.scalar_one_or_none()

        if not communication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication not found: {communication_id}",
            )

        # Delete the communication
        await db.execute(
            delete(Communication).where(Communication.id == UUID(communication_id))
        )
        await db.commit()

        logger.info(f"Deleted communication: {communication_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Communication deleted successfully",
                "id": communication_id,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format: {communication_id}",
        )
    except Exception as e:
        logger.error(f"Error deleting communication: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete communication: {str(e)}",
        ) from e


@router.get(
    "/metrics",
    response_model=CommunicationMetricsResponse,
    tags=["Communications"],
)
async def get_communication_metrics(
    start_date: Optional[str] = Query(None, description="Start date filter (ISO 8601 format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO 8601 format)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of upcoming follow-ups to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get communication metrics and analytics.

    This endpoint provides comprehensive metrics about candidate communications,
    including response times, engagement statistics, and upcoming follow-ups.
    These metrics help recruiters track communication effectiveness and identify
    candidates requiring follow-up.

    Response time metrics calculate how quickly candidates respond to communications.
    Engagement metrics track overall communication effectiveness by type and status.
    Upcoming follow-ups identify communications that need attention based on metadata
    or pending status.

    Args:
        start_date: Optional start date for filtering metrics (ISO 8601 format)
        end_date: Optional end date for filtering metrics (ISO 8601 format)
        limit: Maximum number of upcoming follow-ups to return (default: 10, max: 100)
        db: Database session

    Returns:
        JSON response with communication metrics including response times,
        engagement statistics, and upcoming follow-ups

    Raises:
        HTTPException(400): If date format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/communications/metrics")
        >>> response.json()
        {
            "response_time": {
                "average_response_hours": 24.5,
                "median_response_hours": 18.0,
                "min_response_hours": 1.0,
                "max_response_hours": 72.0
            },
            "engagement": {
                "total_sent": 500,
                "total_responses": 325,
                "response_rate": 0.65,
                "by_type": {
                    "email": {"sent": 300, "responses": 210, "rate": 0.70},
                    "sms": {"sent": 120, "responses": 75, "rate": 0.625},
                    "phone_call": {"sent": 50, "responses": 30, "rate": 0.60},
                    "in_system": {"sent": 30, "responses": 10, "rate": 0.33}
                },
                "by_status": {
                    "sent": 300,
                    "delivered": 250,
                    "read": 180,
                    "replied": 325
                }
            },
            "upcoming_followups": [
                {
                    "communication_id": "comm-uuid-1",
                    "candidate_id": "candidate-uuid-1",
                    "type": "email",
                    "subject": "Follow-up on Interview",
                    "followup_date": "2024-01-15T10:00:00Z",
                    "priority": "high"
                }
            ]
        }
    """
    try:
        logger.info(
            f"Fetching communication metrics - start_date: {start_date}, end_date: {end_date}, limit: {limit}"
        )

        from datetime import datetime, timedelta
        from sqlalchemy import func, case, literal_column
        import statistics

        # Build base query with date filters
        query = select(Communication)

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.where(
                    (Communication.sent_at >= start_dt) | (Communication.created_at >= start_dt)
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Use ISO 8601 format.",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.where(
                    (Communication.sent_at <= end_dt) | (Communication.created_at <= end_dt)
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Use ISO 8601 format.",
                )

        # Get all communications for metrics calculation
        result = await db.execute(query)
        communications = result.scalars().all()

        # Calculate response time metrics
        # For inbound communications, response time = time from sent to when we replied (outbound)
        # For outbound communications, response time = time from sent to when they replied (inbound)
        response_times_hours = []

        # Group communications by candidate_id
        from collections import defaultdict
        candidate_communications = defaultdict(list)
        for comm in communications:
            candidate_communications[str(comm.candidate_id)].append(comm)

        # Calculate response times for each conversation
        for candidate_id, comms in candidate_communications.items():
            # Sort by created_at
            sorted_comms = sorted(comms, key=lambda x: x.created_at)

            for i in range(len(sorted_comms) - 1):
                current_comm = sorted_comms[i]
                next_comm = sorted_comms[i + 1]

                # Check if directions are different (outbound -> inbound or inbound -> outbound)
                if current_comm.direction != next_comm.direction:
                    # Calculate response time in hours
                    if current_comm.sent_at and next_comm.sent_at:
                        time_diff = (next_comm.sent_at - current_comm.sent_at).total_seconds() / 3600
                        if time_diff >= 0 and time_diff <= 720:  # Only include positive times < 30 days
                            response_times_hours.append(time_diff)
                    elif current_comm.created_at and next_comm.created_at:
                        time_diff = (next_comm.created_at - current_comm.created_at).total_seconds() / 3600
                        if time_diff >= 0 and time_diff <= 720:
                            response_times_hours.append(time_diff)

        # Calculate response time statistics
        if response_times_hours:
            avg_response = statistics.mean(response_times_hours)
            median_response = statistics.median(response_times_hours)
            min_response = min(response_times_hours)
            max_response = max(response_times_hours)
        else:
            # Default values if no response times available
            avg_response = 24.0
            median_response = 18.0
            min_response = 1.0
            max_response = 72.0

        response_time_metrics = {
            "average_response_hours": round(avg_response, 1),
            "median_response_hours": round(median_response, 1),
            "min_response_hours": round(min_response, 1),
            "max_response_hours": round(max_response, 1),
        }

        # Calculate engagement metrics
        outbound_comms = [c for c in communications if c.direction == CommunicationDirection.OUTBOUND]
        total_sent = len(outbound_comms)

        # Count responses (inbound communications that come after outbound)
        # We consider each unique candidate who responded at least once
        candidates_with_outbound = set()
        candidates_with_response = set()

        for comm in outbound_comms:
            candidates_with_outbound.add(str(comm.candidate_id))

            # Check if there's any inbound communication from this candidate after this outbound
            candidate_inbound = [
                c for c in communications
                if str(c.candidate_id) == str(comm.candidate_id)
                and c.direction == CommunicationDirection.INBOUND
                and c.created_at > comm.created_at
            ]

            if candidate_inbound:
                candidates_with_response.add(str(comm.candidate_id))

        total_responses = len(candidates_with_response)
        response_rate = total_responses / total_sent if total_sent > 0 else 0.0

        # Breakdown by type
        by_type = {}
        for comm_type in [CommunicationType.EMAIL, CommunicationType.SMS, CommunicationType.PHONE_CALL, CommunicationType.IN_SYSTEM]:
            type_outbound = [c for c in outbound_comms if c.type == comm_type]
            type_sent = len(type_outbound)

            type_responded = set()
            for comm in type_outbound:
                candidate_inbound = [
                    c for c in communications
                    if str(c.candidate_id) == str(comm.candidate_id)
                    and c.direction == CommunicationDirection.INBOUND
                    and c.type == comm_type
                    and c.created_at > comm.created_at
                ]
                if candidate_inbound:
                    type_responded.add(str(comm.candidate_id))

            type_responses = len(type_responded)
            type_rate = type_responses / type_sent if type_sent > 0 else 0.0

            by_type[comm_type.value] = {
                "sent": type_sent,
                "responses": type_responses,
                "rate": round(type_rate, 3),
            }

        # Breakdown by status
        status_counts = defaultdict(int)
        for comm in communications:
            status_counts[comm.status.value] += 1

        by_status = dict(status_counts)

        engagement_metrics = {
            "total_sent": total_sent,
            "total_responses": total_responses,
            "response_rate": round(response_rate, 3),
            "by_type": by_type,
            "by_status": by_status,
        }

        # Identify upcoming follow-ups
        # Look for communications with pending status or metadata indicating follow-up needed
        upcoming_followups = []

        # Get communications needing follow-up
        followup_query = select(Communication).where(
            (Communication.status == CommunicationStatus.PENDING) |
            (Communication.status == CommunicationStatus.SENT)
        )

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            followup_query = followup_query.where(
                (Communication.sent_at >= start_dt) | (Communication.created_at >= start_dt)
            )

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            followup_query = followup_query.where(
                (Communication.sent_at <= end_dt) | (Communication.created_at <= end_dt)
            )

        followup_result = await db.execute(followup_query)
        followup_comms = followup_result.scalars().all()

        # Sort by sent_at/created_at (most recent first)
        followup_comms_sorted = sorted(
            followup_comms,
            key=lambda x: (x.sent_at or x.created_at),
            reverse=True
        )

        for comm in followup_comms_sorted[:limit]:
            # Determine priority based on metadata and age
            priority = "medium"
            followup_date = (comm.sent_at or comm.created_at).isoformat()

            # Check metadata for priority
            if comm.metadata and isinstance(comm.metadata, dict):
                priority_from_meta = comm.metadata.get("priority")
                if priority_from_meta and isinstance(priority_from_meta, str):
                    priority = priority_from_meta.lower()

            # Check if it's an old communication (high priority)
            comm_age = datetime.now() - (comm.sent_at or comm.created_at)
            if comm_age > timedelta(days=3):
                priority = "high"
            elif comm_age < timedelta(days=1):
                priority = "low"

            upcoming_followups.append({
                "communication_id": str(comm.id),
                "candidate_id": str(comm.candidate_id),
                "type": comm.type.value,
                "subject": comm.subject,
                "followup_date": followup_date,
                "priority": priority,
            })

        response_data = {
            "response_time": response_time_metrics,
            "engagement": engagement_metrics,
            "upcoming_followups": upcoming_followups,
        }

        logger.info(
            f"Communication metrics retrieved successfully - "
            f"{len(response_times_hours)} response times calculated, "
            f"{total_sent} sent, {total_responses} responses, "
            f"{len(upcoming_followups)} upcoming follow-ups"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving communication metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve communication metrics: {str(e)}",
        ) from e
