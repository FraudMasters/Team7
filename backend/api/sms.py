"""
SMS message management endpoints.

This module provides endpoints for managing SMS communications with candidates,
including sending SMS messages, tracking delivery status, and retrieving SMS history.
Supports multiple SMS providers (Twilio, AWS SNS, etc.) with delivery tracking.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.communication import Communication, CommunicationDirection, CommunicationStatus, CommunicationType
from models.sms_message import SMSMessage, SMSDeliveryStatus

logger = logging.getLogger(__name__)

router = APIRouter()


class SMSSendRequest(BaseModel):
    """Request model for sending an SMS message."""

    candidate_id: str = Field(..., description="Candidate ID (resume ID) to send SMS to")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (sender) of the SMS")
    to_number: str = Field(..., min_length=10, max_length=50, description="Recipient phone number (E.164 format)")
    from_number: Optional[str] = Field(None, min_length=10, max_length=50, description="Sender phone number (E.164 format)")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message content")
    provider: str = Field(..., min_length=1, max_length=100, description="SMS provider (e.g., Twilio, AWS SNS)")
    vacancy_id: Optional[str] = Field(None, description="Optional vacancy ID associated with this SMS")


class SMSResponse(BaseModel):
    """Response model for a single SMS message."""

    id: str = Field(..., description="Unique identifier for the SMS")
    communication_id: str = Field(..., description="Communication ID")
    candidate_id: str = Field(..., description="Candidate ID (recipient)")
    recruiter_id: Optional[str] = Field(None, description="Recruiter ID (sender)")
    to_number: str = Field(..., description="Recipient phone number")
    from_number: Optional[str] = Field(None, description="Sender phone number")
    message: str = Field(..., description="SMS message content")
    provider: str = Field(..., description="SMS provider")
    delivery_status: str = Field(..., description="Delivery status")
    delivery_error: Optional[str] = Field(None, description="Error message if delivery failed")
    provider_message_id: Optional[str] = Field(None, description="Provider's message ID")
    segment_count: Optional[int] = Field(None, description="Number of SMS segments used")
    sent_at: Optional[str] = Field(None, description="Timestamp when SMS was sent")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class SMSListResponse(BaseModel):
    """Response model for listing SMS messages."""

    messages: List[SMSResponse] = Field(..., description="List of SMS messages")
    total_count: int = Field(..., description="Total number of SMS messages")


class DeliveryStatusResponse(BaseModel):
    """Response model for delivery status query."""

    id: str = Field(..., description="SMS ID")
    delivery_status: str = Field(..., description="Current delivery status")
    provider_message_id: Optional[str] = Field(None, description="Provider's message ID")
    delivery_error: Optional[str] = Field(None, description="Error message if delivery failed")
    sent_at: Optional[str] = Field(None, description="Timestamp when SMS was sent")
    updated_at: str = Field(..., description="Last update timestamp")


@router.post(
    "/send",
    response_model=SMSResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["SMS"],
)
async def send_sms(
    request: SMSSendRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Send an SMS message to a candidate.

    This endpoint creates and sends an SMS message to a candidate. The SMS is
    logged in the database with delivery tracking. The actual sending is handled
    by a background worker (Celery task) that integrates with the specified SMS provider.

    Args:
        request: Request body containing SMS details
        db: Database session

    Returns:
        JSON response with sent SMS details

    Raises:
        HTTPException(404): If candidate is not found
        HTTPException(422): If validation fails
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/sms/send",
        ...     json={
        ...         "candidate_id": "resume-uuid",
        ...         "to_number": "+1234567890",
        ...         "message": "Hello! We'd like to schedule an interview.",
        ...         "provider": "Twilio",
        ...         "recruiter_id": "recruiter-uuid"
        ...     }
        ... )
        >>> response.status_code
        201
    """
    try:
        logger.info(f"Sending SMS to candidate: {request.candidate_id}")

        # Verify candidate exists
        from models.resume import Resume

        candidate_result = await db.execute(
            select(Resume).where(Resume.id == UUID(request.candidate_id))
        )
        candidate = candidate_result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {request.candidate_id}",
            )

        # Calculate segment count (standard SMS is 160 chars, multipart is 153 chars per segment)
        segment_count = (len(request.message) + 152) // 153 if len(request.message) > 160 else 1

        # Create communication record
        communication = Communication(
            candidate_id=UUID(request.candidate_id),
            recruiter_id=UUID(request.recruiter_id) if request.recruiter_id else None,
            vacancy_id=UUID(request.vacancy_id) if request.vacancy_id else None,
            type=CommunicationType.SMS,
            direction=CommunicationDirection.OUTBOUND,
            status=CommunicationStatus.PENDING,
            subject=None,  # SMS doesn't have subject
            body=request.message,
        )
        db.add(communication)
        await db.flush()

        # Create SMS message record
        new_sms = SMSMessage(
            communication_id=communication.id,
            to_number=request.to_number,
            from_number=request.from_number,
            provider=request.provider,
            delivery_status=SMSDeliveryStatus.PENDING,
            segment_count=segment_count,
        )
        db.add(new_sms)
        await db.flush()

        # Prepare response data
        response_data = {
            "id": str(new_sms.id),
            "communication_id": str(new_sms.communication_id),
            "candidate_id": str(communication.candidate_id),
            "recruiter_id": str(communication.recruiter_id) if communication.recruiter_id else None,
            "to_number": new_sms.to_number,
            "from_number": new_sms.from_number,
            "message": communication.body,
            "provider": new_sms.provider,
            "delivery_status": new_sms.delivery_status.value,
            "delivery_error": new_sms.delivery_error,
            "provider_message_id": new_sms.provider_message_id,
            "segment_count": new_sms.segment_count,
            "sent_at": communication.sent_at.isoformat() if communication.sent_at else None,
            "created_at": new_sms.created_at.isoformat(),
            "updated_at": new_sms.updated_at.isoformat(),
        }

        await db.commit()

        logger.info(f"SMS created with ID: {new_sms.id}, queued for sending")

        # TODO: Trigger Celery task to send SMS via provider
        # from tasks.sms_task import send_sms_task
        # send_sms_task.delay(str(new_sms.id))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error sending SMS: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS: {str(e)}",
        ) from e


@router.get("/", tags=["SMS"])
async def list_sms_messages(
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    recruiter_id: Optional[str] = Query(None, description="Filter by recruiter ID"),
    provider: Optional[str] = Query(None, description="Filter by SMS provider"),
    delivery_status: Optional[str] = Query(None, description="Filter by delivery status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List SMS messages with optional filters.

    This endpoint retrieves SMS messages with support for filtering
    by candidate, recruiter, provider, and delivery status.

    Args:
        candidate_id: Optional candidate ID filter
        recruiter_id: Optional recruiter ID filter
        provider: Optional provider filter
        delivery_status: Optional delivery status filter
        limit: Maximum number of results to return (default: 100)
        offset: Number of results to skip (default: 0)
        db: Database session

    Returns:
        JSON response with list of SMS messages

    Raises:
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/sms/?candidate_id=resume-uuid")
        >>> response.json()
        {
            "messages": [...],
            "total_count": 5
        }
    """
    try:
        logger.info(f"Listing SMS messages with filters: candidate_id={candidate_id}, provider={provider}")

        # Build base query
        query = (
            select(SMSMessage, Communication)
            .join(Communication, SMSMessage.communication_id == Communication.id)
            .where(Communication.type == CommunicationType.SMS)
        )

        # Apply filters
        if candidate_id:
            query = query.where(Communication.candidate_id == UUID(candidate_id))
        if recruiter_id:
            query = query.where(Communication.recruiter_id == UUID(recruiter_id))
        if provider:
            query = query.where(SMSMessage.provider == provider)
        if delivery_status:
            try:
                status_enum = SMSDeliveryStatus(delivery_status)
                query = query.where(SMSMessage.delivery_status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid delivery status: {delivery_status}",
                )

        # Get total count
        count_query = select(SMSMessage).join(
            Communication, SMSMessage.communication_id == Communication.id
        )
        if candidate_id:
            count_query = count_query.where(Communication.candidate_id == UUID(candidate_id))
        if recruiter_id:
            count_query = count_query.where(Communication.recruiter_id == UUID(recruiter_id))
        if provider:
            count_query = count_query.where(SMSMessage.provider == provider)
        if delivery_status:
            count_query = count_query.where(SMSMessage.delivery_status == status_enum)

        count_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
        total_count = count_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(SMSMessage.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        rows = result.all()

        messages = []
        for sms, communication in rows:
            messages.append({
                "id": str(sms.id),
                "communication_id": str(sms.communication_id),
                "candidate_id": str(communication.candidate_id),
                "recruiter_id": str(communication.recruiter_id) if communication.recruiter_id else None,
                "to_number": sms.to_number,
                "from_number": sms.from_number,
                "message": communication.body or "",
                "provider": sms.provider,
                "delivery_status": sms.delivery_status.value,
                "delivery_error": sms.delivery_error,
                "provider_message_id": sms.provider_message_id,
                "segment_count": sms.segment_count,
                "sent_at": communication.sent_at.isoformat() if communication.sent_at else None,
                "created_at": sms.created_at.isoformat(),
                "updated_at": sms.updated_at.isoformat(),
            })

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "messages": messages,
                "total_count": total_count,
            },
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error listing SMS messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list SMS messages: {str(e)}",
        ) from e


@router.get("/{sms_id}", tags=["SMS"])
async def get_sms(
    sms_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get a single SMS message by ID.

    This endpoint retrieves details of a specific SMS message including
    delivery status and provider information.

    Args:
        sms_id: SMS ID (UUID)
        db: Database session

    Returns:
        JSON response with SMS details

    Raises:
        HTTPException(404): If SMS is not found
        HTTPException(422): If UUID format is invalid
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/sms/sms-uuid")
        >>> response.json()
        {
            "id": "sms-uuid",
            "communication_id": "...",
            "to_number": "+1234567890",
            "message": "Hello!",
            "delivery_status": "delivered"
        }
    """
    try:
        logger.info(f"Fetching SMS message: {sms_id}")

        result = await db.execute(
            select(SMSMessage, Communication)
            .join(Communication, SMSMessage.communication_id == Communication.id)
            .where(SMSMessage.id == UUID(sms_id))
        )
        row = result.first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SMS message not found: {sms_id}",
            )

        sms, communication = row

        response_data = {
            "id": str(sms.id),
            "communication_id": str(sms.communication_id),
            "candidate_id": str(communication.candidate_id),
            "recruiter_id": str(communication.recruiter_id) if communication.recruiter_id else None,
            "to_number": sms.to_number,
            "from_number": sms.from_number,
            "message": communication.body or "",
            "provider": sms.provider,
            "delivery_status": sms.delivery_status.value,
            "delivery_error": sms.delivery_error,
            "provider_message_id": sms.provider_message_id,
            "segment_count": sms.segment_count,
            "sent_at": communication.sent_at.isoformat() if communication.sent_at else None,
            "created_at": sms.created_at.isoformat(),
            "updated_at": sms.updated_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error fetching SMS message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch SMS message: {str(e)}",
        ) from e


@router.get("/delivery-status", tags=["SMS"])
async def get_delivery_status(
    provider_message_id: Optional[str] = Query(None, description="Provider message ID to query"),
    sms_id: Optional[str] = Query(None, description="SMS ID to query"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get delivery status for SMS messages.

    This endpoint retrieves the current delivery status of SMS messages.
    You can query by either the provider's message ID or the SMS ID.

    Args:
        provider_message_id: Optional provider message ID filter
        sms_id: Optional SMS ID filter
        db: Database session

    Returns:
        JSON response with delivery status information

    Raises:
        HTTPException(422): If neither filter is provided or both are provided
        HTTPException(404): If SMS is not found
        HTTPException(500): If an internal error occurs

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/sms/delivery-status?sms_id=sms-uuid")
        >>> response.json()
        {
            "id": "sms-uuid",
            "delivery_status": "delivered",
            "provider_message_id": "provider-msg-id"
        }
    """
    try:
        # Validate that exactly one filter is provided
        if provider_message_id and sms_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide either provider_message_id or sms_id, not both",
            )
        if not provider_message_id and not sms_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide either provider_message_id or sms_id",
            )

        logger.info(f"Fetching delivery status: sms_id={sms_id}, provider_message_id={provider_message_id}")

        # Build query
        query = select(SMSMessage)
        if sms_id:
            query = query.where(SMSMessage.id == UUID(sms_id))
        else:
            query = query.where(SMSMessage.provider_message_id == provider_message_id)

        result = await db.execute(query)
        sms = result.scalar_one_or_none()

        if not sms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SMS message not found",
            )

        # Get communication for sent_at timestamp
        comm_result = await db.execute(
            select(Communication).where(Communication.id == sms.communication_id)
        )
        communication = comm_result.scalar_one_or_none()

        response_data = {
            "id": str(sms.id),
            "delivery_status": sms.delivery_status.value,
            "provider_message_id": sms.provider_message_id,
            "delivery_error": sms.delivery_error,
            "sent_at": communication.sent_at.isoformat() if communication and communication.sent_at else None,
            "updated_at": sms.updated_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format",
        )
    except Exception as e:
        logger.error(f"Error fetching delivery status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch delivery status: {str(e)}",
        ) from e
