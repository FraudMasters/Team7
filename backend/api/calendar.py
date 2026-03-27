"""
Calendar connection management endpoints.

This module provides endpoints for:
- Connecting and managing calendar integrations (Google, Outlook)
- Listing calendar connections
- Disconnecting calendar accounts
- Checking calendar connection status
- Checking interviewer availability with conflict detection

Supports OAuth flow for connecting external calendar providers.
"""
import logging
from datetime import datetime, time, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.calendar_connection import CalendarConnection, CalendarProvider, ConnectionStatus
from models.recruiter import Recruiter
from services.calendar_service import get_calendar_service, AvailabilitySlot

logger = logging.getLogger(__name__)

router = APIRouter()


# Business hours configuration
BUSINESS_HOURS_START = time(9, 0)  # 9:00 AM
BUSINESS_HOURS_END = time(17, 0)    # 5:00 PM
BUSINESS_DAYS = [0, 1, 2, 3, 4]     # Monday=0 through Friday=4


# Request/Response Models
class CalendarConnectionCreate(BaseModel):
    """Request model for creating a calendar connection (OAuth callback)."""

    recruiter_id: UUID = Field(..., description="ID of the recruiter")
    provider: str = Field(..., description="Calendar provider (google or outlook)")
    access_token: str = Field(..., min_length=1, description="OAuth access token")
    refresh_token: str = Field(..., min_length=1, description="OAuth refresh token")
    token_expires_at: datetime = Field(..., description="Token expiration timestamp")
    calendar_email: str = Field(..., min_length=1, max_length=255, description="Connected calendar email")
    calendar_id: Optional[str] = Field(None, max_length=255, description="Provider-specific calendar ID")
    webhook_subscription_id: Optional[str] = Field(None, max_length=255, description="Webhook subscription ID")

    @validator("provider")
    def validate_provider(cls, v):
        """Validate provider is supported."""
        try:
            CalendarProvider(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid provider: {v}. Must be 'google' or 'outlook'")

    @validator("token_expires_at")
    def validate_token_expiration(cls, v):
        """Ensure token expiration is in the future."""
        if v <= datetime.now(timezone.utc):
            raise ValueError("Token expiration must be in the future")
        return v


class CalendarConnectionUpdate(BaseModel):
    """Request model for updating a calendar connection."""

    access_token: Optional[str] = Field(None, min_length=1, description="Updated access token")
    refresh_token: Optional[str] = Field(None, min_length=1, description="Updated refresh token")
    token_expires_at: Optional[datetime] = Field(None, description="Updated token expiration")
    status: Optional[str] = Field(None, description="Connection status (active, expired, error, disconnected)")
    error_message: Optional[str] = Field(None, description="Error message if status is error")
    webhook_subscription_id: Optional[str] = Field(None, max_length=255, description="Webhook subscription ID")
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync timestamp")

    @validator("status")
    def validate_status(cls, v):
        """Validate status if provided."""
        if v is not None:
            try:
                ConnectionStatus(v)
                return v
            except ValueError:
                raise ValueError(f"Invalid status: {v}. Must be one of: active, expired, error, disconnected")
        return v


class CalendarConnectionResponse(BaseModel):
    """Response model for a calendar connection."""

    id: str = Field(..., description="Unique identifier for the connection")
    recruiter_id: str = Field(..., description="ID of the recruiter")
    recruiter_name: Optional[str] = Field(None, description="Name of the recruiter")
    recruiter_email: Optional[str] = Field(None, description="Email of the recruiter")
    provider: str = Field(..., description="Calendar provider")
    calendar_email: str = Field(..., description="Connected calendar email")
    calendar_id: Optional[str] = Field(None, description="Provider-specific calendar ID")
    status: str = Field(..., description="Connection status")
    token_expires_at: str = Field(..., description="When the access token expires")
    webhook_subscription_id: Optional[str] = Field(None, description="Webhook subscription ID")
    last_sync_at: Optional[str] = Field(None, description="Last successful sync timestamp")
    error_message: Optional[str] = Field(None, description="Error message if applicable")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    is_active: bool = Field(..., description="Whether the connection is active and valid")

    class Config:
        from_attributes = True


class InterviewerAvailability(BaseModel):
    """Availability status for a single interviewer."""

    interviewer_id: str = Field(..., description="ID of the interviewer/recruiter")
    interviewer_name: Optional[str] = Field(None, description="Name of the interviewer")
    interviewer_email: Optional[str] = Field(None, description="Email of the interviewer")
    is_available: bool = Field(..., description="Whether the interviewer is available")
    has_calendar_connection: bool = Field(..., description="Whether interviewer has connected calendar")
    calendar_provider: Optional[str] = Field(None, description="Calendar provider if connected")
    conflicting_events: List[str] = Field(default_factory=list, description="List of conflicting event titles")


class AvailabilityCheckRequest(BaseModel):
    """Request model for checking interviewer availability."""

    interviewer_ids: List[str] = Field(..., min_items=0, description="List of interviewer/recruiter IDs to check")
    start_time: datetime = Field(..., description="Start time for the slot (ISO 8601)")
    duration_minutes: int = Field(..., gt=0, description="Duration of the interview in minutes")

    @validator("interviewer_ids")
    def validate_interviewer_ids(cls, v):
        """Validate interviewer IDs are valid UUIDs."""
        if v:
            for interviewer_id in v:
                try:
                    UUID(interviewer_id)
                except ValueError:
                    raise ValueError(f"Invalid interviewer_id format: {interviewer_id}")
        return v


class AvailabilityCheckResponse(BaseModel):
    """Response model for availability check results."""

    start_time: str = Field(..., description="Requested start time (ISO 8601)")
    end_time: str = Field(..., description="Calculated end time (ISO 8601)")
    duration_minutes: int = Field(..., description="Duration in minutes")
    all_available: bool = Field(..., description="Whether all interviewers are available")
    interviewer_count: int = Field(..., description="Total number of interviewers checked")
    available_count: int = Field(..., description="Number of interviewers available")
    interviewer_availability: List[InterviewerAvailability] = Field(
        ..., description="Availability status for each interviewer"
    )


class AvailabilitySlotsRequest(BaseModel):
    """Request model for fetching availability slots."""

    recruiter_id: str = Field(..., description="ID of the recruiter")
    start_date: str = Field(..., description="Start date for availability search (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date for availability search (YYYY-MM-DD)")
    duration_minutes: int = Field(..., gt=0, description="Duration of interview slots in minutes")

    @validator("recruiter_id")
    def validate_recruiter_id(cls, v):
        """Validate recruiter_id is a valid UUID."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid recruiter_id format: {v}")

    @validator("start_date", "end_date")
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD")


class AvailabilitySlotResponse(BaseModel):
    """Response model for a single availability slot."""

    start_time: str = Field(..., description="Slot start time (ISO 8601)")
    end_time: str = Field(..., description="Slot end time (ISO 8601)")
    available: bool = Field(..., description="Whether the slot is available")
    confidence: float = Field(..., description="Confidence score for availability (0-1)")


class AvailabilitySlotsResponse(BaseModel):
    """Response model for availability slots."""

    recruiter_id: str = Field(..., description="ID of the recruiter")
    recruiter_name: Optional[str] = Field(None, description="Name of the recruiter")
    recruiter_email: Optional[str] = Field(None, description="Email of the recruiter")
    start_date: str = Field(..., description="Start date for availability search")
    end_date: str = Field(..., description="End date for availability search")
    duration_minutes: int = Field(..., description="Duration of interview slots in minutes")
    has_calendar_connection: bool = Field(..., description="Whether recruiter has connected calendar")
    calendar_provider: Optional[str] = Field(None, description="Calendar provider if connected")
    slots: List[AvailabilitySlotResponse] = Field(..., description="List of availability slots")


def filter_slots_by_business_hours(
    slots: List[AvailabilitySlot],
    duration_minutes: int,
    business_hours_start: time = BUSINESS_HOURS_START,
    business_hours_end: time = BUSINESS_HOURS_END,
    business_days: List[int] = BUSINESS_DAYS,
) -> List[AvailabilitySlot]:
    """
    Filter availability slots by business hours and split long slots into bookable chunks.

    This function:
    1. Filters out slots outside business hours (default: 9am-5pm)
    2. Filters out slots on weekends (default: Saturday and Sunday)
    3. Splits long free slots into bookable chunks based on the requested duration
    4. Ensures each returned slot can accommodate the requested duration

    Args:
        slots: List of availability slots from calendar service
        duration_minutes: Required duration for each bookable slot
        business_hours_start: Start of business hours (default: 9:00 AM)
        business_hours_end: End of business hours (default: 5:00 PM)
        business_days: List of business day numbers (0=Monday, 6=Sunday)

    Returns:
        List of filtered and split AvailabilitySlots
    """
    filtered_slots = []
    duration_delta = timedelta(minutes=duration_minutes)

    for slot in slots:
        # Skip unavailable slots
        if not slot.available:
            continue

        # Skip weekend slots
        if slot.start_time.weekday() not in business_days:
            continue

        # Calculate intersection with business hours for this day
        slot_date = slot.start_time.date()
        business_start_dt = datetime.combine(slot_date, business_hours_start)
        business_end_dt = datetime.combine(slot_date, business_hours_end)

        # Clip slot to business hours
        clipped_start = max(slot.start_time, business_start_dt)
        clipped_end = min(slot.end_time, business_end_dt)

        # Skip if slot is entirely outside business hours
        if clipped_start >= clipped_end:
            continue

        # Skip if clipped slot is too short for the requested duration
        if (clipped_end - clipped_start) < duration_delta:
            continue

        # Split the slot into bookable chunks
        current_time = clipped_start
        while current_time + duration_delta <= clipped_end:
            filtered_slots.append(
                AvailabilitySlot(
                    start_time=current_time,
                    end_time=current_time + duration_delta,
                    available=True,
                    confidence=slot.confidence,
                )
            )
            current_time += duration_delta

    logger.info(
        f"Filtered {len(slots)} slots to {len(filtered_slots)} business hour slots "
        f"({business_hours_start.strftime('%H:%M')}-{business_hours_end.strftime('%H:%M')}, "
        f"weekdays only)"
    )

    return filtered_slots


@router.get(
    "/connections",
    tags=["Calendar"],
)
async def list_calendar_connections(
    request: Request,
    recruiter_id: Optional[str] = None,
    provider: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all calendar connections with optional filters.

    Returns a paginated list of calendar connections. Can be filtered by
    recruiter, provider, and status.
    """
    try:
        logger.info(
            f"Fetching calendar connections - recruiter_id: {recruiter_id}, "
            f"provider: {provider}, status: {status_filter}"
        )

        query = select(CalendarConnection).order_by(CalendarConnection.created_at.desc())

        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                query = query.where(CalendarConnection.recruiter_id == recruiter_uuid)
            except ValueError:
                logger.warning(f"Invalid recruiter_id format: {recruiter_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid recruiter_id format: {recruiter_id}",
                )

        if provider:
            try:
                CalendarProvider(provider)
                query = query.where(CalendarConnection.provider == provider)
            except ValueError:
                logger.warning(f"Invalid provider filter: {provider}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {provider}. Must be 'google' or 'outlook'",
                )

        if status_filter:
            try:
                ConnectionStatus(status_filter)
                query = query.where(CalendarConnection.status == status_filter)
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_filter}",
                )

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        connections = result.scalars().all()

        connection_list = []
        for connection in connections:
            recruiter_query = select(Recruiter).where(Recruiter.id == connection.recruiter_id)
            recruiter_result = await db.execute(recruiter_query)
            recruiter = recruiter_result.scalar_one_or_none()

            connection_list.append({
                "id": str(connection.id),
                "recruiter_id": str(connection.recruiter_id),
                "recruiter_name": recruiter.name if recruiter else None,
                "recruiter_email": recruiter.email if recruiter else None,
                "provider": connection.provider.value,
                "calendar_email": connection.calendar_email,
                "calendar_id": connection.calendar_id,
                "status": connection.status.value,
                "token_expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
                "webhook_subscription_id": connection.webhook_subscription_id,
                "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                "error_message": connection.error_message,
                "created_at": connection.created_at.isoformat() if connection.created_at else None,
                "updated_at": connection.updated_at.isoformat() if connection.updated_at else None,
                "is_active": connection.is_active(),
            })

        logger.info(f"Retrieved {len(connection_list)} calendar connections")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=connection_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing calendar connections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list calendar connections: {str(e)}",
        ) from e


@router.post(
    "/connections",
    tags=["Calendar"],
)
async def create_calendar_connection(
    request: Request,
    connection_data: CalendarConnectionCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new calendar connection (OAuth callback).

    Creates a calendar connection after successful OAuth authentication.
    This is typically called by the OAuth callback handler.
    """
    try:
        logger.info(
            f"Creating calendar connection for recruiter {connection_data.recruiter_id} "
            f"with provider {connection_data.provider}"
        )

        recruiter_query = select(Recruiter).where(Recruiter.id == connection_data.recruiter_id)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recruiter not found: {connection_data.recruiter_id}",
            )

        existing_query = select(CalendarConnection).where(
            and_(
                CalendarConnection.recruiter_id == connection_data.recruiter_id,
                CalendarConnection.provider == CalendarProvider(connection_data.provider)
            )
        )
        existing_result = await db.execute(existing_query)
        existing_connection = existing_result.scalar_one_or_none()

        if existing_connection:
            logger.info(
                f"Found existing connection for recruiter {connection_data.recruiter_id}, "
                f"updating tokens"
            )
            existing_connection.access_token = connection_data.access_token
            existing_connection.refresh_token = connection_data.refresh_token
            existing_connection.token_expires_at = connection_data.token_expires_at
            existing_connection.calendar_email = connection_data.calendar_email
            existing_connection.calendar_id = connection_data.calendar_id
            existing_connection.status = ConnectionStatus.ACTIVE
            existing_connection.webhook_subscription_id = connection_data.webhook_subscription_id
            existing_connection.error_message = None

            await db.commit()
            await db.refresh(existing_connection)

            connection_id_str = str(existing_connection.id)
            return await get_calendar_connection(request, connection_id_str, db)

        try:
            provider_enum = CalendarProvider(connection_data.provider)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: {connection_data.provider}",
            )

        connection = CalendarConnection(
            recruiter_id=connection_data.recruiter_id,
            provider=provider_enum,
            access_token=connection_data.access_token,
            refresh_token=connection_data.refresh_token,
            token_expires_at=connection_data.token_expires_at,
            calendar_email=connection_data.calendar_email,
            calendar_id=connection_data.calendar_id,
            status=ConnectionStatus.ACTIVE,
            webhook_subscription_id=connection_data.webhook_subscription_id,
        )

        db.add(connection)
        await db.commit()
        await db.refresh(connection)

        logger.info(f"Calendar connection created successfully: {connection.id}")

        connection_id_str = str(connection.id)
        return await get_calendar_connection(request, connection_id_str, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating calendar connection: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create calendar connection: {str(e)}",
        ) from e


@router.get(
    "/connections/{connection_id}",
    tags=["Calendar"],
)
async def get_calendar_connection(
    request: Request,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get a specific calendar connection by ID."""
    try:
        logger.info(f"Fetching calendar connection: {connection_id}")

        try:
            connection_uuid = UUID(connection_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid connection ID format: {connection_id}",
            )

        query = select(CalendarConnection).where(CalendarConnection.id == connection_uuid)
        result = await db.execute(query)
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar connection not found: {connection_id}",
            )

        recruiter_query = select(Recruiter).where(Recruiter.id == connection.recruiter_id)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        connection_data = {
            "id": str(connection.id),
            "recruiter_id": str(connection.recruiter_id),
            "recruiter_name": recruiter.name if recruiter else None,
            "recruiter_email": recruiter.email if recruiter else None,
            "provider": connection.provider.value,
            "calendar_email": connection.calendar_email,
            "calendar_id": connection.calendar_id,
            "status": connection.status.value,
            "token_expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
            "webhook_subscription_id": connection.webhook_subscription_id,
            "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "error_message": connection.error_message,
            "created_at": connection.created_at.isoformat() if connection.created_at else None,
            "updated_at": connection.updated_at.isoformat() if connection.updated_at else None,
            "is_active": connection.is_active(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=connection_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar connection {connection_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar connection: {str(e)}",
        ) from e


@router.put(
    "/connections/{connection_id}",
    tags=["Calendar"],
)
async def update_calendar_connection(
    request: Request,
    connection_id: str,
    connection_data: CalendarConnectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Update an existing calendar connection."""
    try:
        logger.info(f"Updating calendar connection {connection_id}")

        try:
            connection_uuid = UUID(connection_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid connection ID format: {connection_id}",
            )

        query = select(CalendarConnection).where(CalendarConnection.id == connection_uuid)
        result = await db.execute(query)
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar connection not found: {connection_id}",
            )

        if connection_data.access_token is not None:
            connection.access_token = connection_data.access_token

        if connection_data.refresh_token is not None:
            connection.refresh_token = connection_data.refresh_token

        if connection_data.token_expires_at is not None:
            connection.token_expires_at = connection_data.token_expires_at

        if connection_data.status is not None:
            try:
                connection.status = ConnectionStatus(connection_data.status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {connection_data.status}",
                )

        if connection_data.error_message is not None:
            connection.error_message = connection_data.error_message

        if connection_data.webhook_subscription_id is not None:
            connection.webhook_subscription_id = connection_data.webhook_subscription_id

        if connection_data.last_sync_at is not None:
            connection.last_sync_at = connection_data.last_sync_at

        await db.commit()
        await db.refresh(connection)

        logger.info(f"Calendar connection updated successfully: {connection.id}")

        return await get_calendar_connection(request, connection_id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating calendar connection {connection_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calendar connection: {str(e)}",
        ) from e


@router.delete(
    "/connections/{connection_id}",
    tags=["Calendar"],
)
async def delete_calendar_connection(
    request: Request,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Delete/disconnect a calendar connection."""
    try:
        logger.info(f"Deleting calendar connection {connection_id}")

        try:
            connection_uuid = UUID(connection_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid connection ID format: {connection_id}",
            )

        query = select(CalendarConnection).where(CalendarConnection.id == connection_uuid)
        result = await db.execute(query)
        connection = result.scalar_one_or_none()

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calendar connection not found: {connection_id}",
            )

        await db.delete(connection)
        await db.commit()

        logger.info(f"Calendar connection deleted successfully: {connection_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Calendar connection deleted successfully",
                "connection_id": connection_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting calendar connection {connection_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete calendar connection: {str(e)}",
        ) from e


@router.get(
    "/connections/recruiter/{recruiter_id}",
    tags=["Calendar"],
)
async def get_recruiter_calendar_connections(
    request: Request,
    recruiter_id: str,
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get all calendar connections for a specific recruiter."""
    try:
        logger.info(f"Fetching calendar connections for recruiter: {recruiter_id}")

        try:
            recruiter_uuid = UUID(recruiter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recruiter_id format: {recruiter_id}",
            )

        recruiter_query = select(Recruiter).where(Recruiter.id == recruiter_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recruiter not found: {recruiter_id}",
            )

        query = select(CalendarConnection).where(
            CalendarConnection.recruiter_id == recruiter_uuid
        )

        if provider:
            try:
                CalendarProvider(provider)
                query = query.where(CalendarConnection.provider == provider)
            except ValueError:
                logger.warning(f"Invalid provider filter: {provider}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider: {provider}",
                )

        query = query.order_by(CalendarConnection.created_at.desc())

        result = await db.execute(query)
        connections = result.scalars().all()

        connection_list = []
        for connection in connections:
            connection_list.append({
                "id": str(connection.id),
                "recruiter_id": str(connection.recruiter_id),
                "recruiter_name": recruiter.name,
                "recruiter_email": recruiter.email,
                "provider": connection.provider.value,
                "calendar_email": connection.calendar_email,
                "calendar_id": connection.calendar_id,
                "status": connection.status.value,
                "token_expires_at": connection.token_expires_at.isoformat() if connection.token_expires_at else None,
                "webhook_subscription_id": connection.webhook_subscription_id,
                "last_sync_at": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
                "error_message": connection.error_message,
                "created_at": connection.created_at.isoformat() if connection.created_at else None,
                "updated_at": connection.updated_at.isoformat() if connection.updated_at else None,
                "is_active": connection.is_active(),
            })

        logger.info(f"Retrieved {len(connection_list)} calendar connections for recruiter {recruiter_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=connection_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calendar connections for recruiter {recruiter_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar connections: {str(e)}",
        ) from e


@router.post(
    "/check-availability",
    tags=["Calendar"],
)
async def check_availability(
    request: Request,
    availability_request: AvailabilityCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Check availability for multiple interviewers.

    Checks if the specified interviewers are available for a given time slot
    based on their connected calendars. Returns availability status for each
    interviewer and indicates if all are available.
    """
    try:
        logger.info(
            f"Checking availability for {len(availability_request.interviewer_ids)} interviewers "
            f"from {availability_request.start_time} for {availability_request.duration_minutes} minutes"
        )

        end_time = availability_request.start_time + timedelta(
            minutes=availability_request.duration_minutes
        )

        interviewer_availability = []
        available_count = 0

        for interviewer_id in availability_request.interviewer_ids:
            try:
                interviewer_uuid = UUID(interviewer_id)
            except ValueError:
                logger.warning(f"Invalid interviewer_id format: {interviewer_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid interviewer_id format: {interviewer_id}",
                )

            recruiter_query = select(Recruiter).where(Recruiter.id == interviewer_uuid)
            recruiter_result = await db.execute(recruiter_query)
            recruiter = recruiter_result.scalar_one_or_none()

            if not recruiter:
                logger.warning(f"Interviewer not found: {interviewer_id}")
                interviewer_availability.append({
                    "interviewer_id": interviewer_id,
                    "interviewer_name": None,
                    "interviewer_email": None,
                    "is_available": False,
                    "has_calendar_connection": False,
                    "calendar_provider": None,
                    "conflicting_events": [],
                })
                continue

            connection_query = select(CalendarConnection).where(
                and_(
                    CalendarConnection.recruiter_id == interviewer_uuid,
                    CalendarConnection.status == ConnectionStatus.ACTIVE
                )
            )
            connection_result = await db.execute(connection_query)
            connection = connection_result.scalar_one_or_none()

            if not connection or not connection.is_active():
                interviewer_availability.append({
                    "interviewer_id": interviewer_id,
                    "interviewer_name": recruiter.name,
                    "interviewer_email": recruiter.email,
                    "is_available": False,
                    "has_calendar_connection": False,
                    "calendar_provider": None,
                    "conflicting_events": [],
                })
                continue

            # Check for actual conflicts using the calendar service
            try:
                calendar_service = get_calendar_service(
                    provider=connection.provider.value,
                    access_token=connection.access_token,
                    refresh_token=connection.refresh_token,
                    token_expires_at=connection.token_expires_at,
                    calendar_email=connection.calendar_email,
                    calendar_id=connection.calendar_id,
                )

                has_conflict, conflicting_events = calendar_service.check_conflict(
                    start_time=availability_request.start_time,
                    end_time=end_time,
                )

                conflicting_event_titles = [event.title for event in conflicting_events]

                interviewer_availability.append({
                    "interviewer_id": interviewer_id,
                    "interviewer_name": recruiter.name,
                    "interviewer_email": recruiter.email,
                    "is_available": not has_conflict,
                    "has_calendar_connection": True,
                    "calendar_provider": connection.provider.value,
                    "conflicting_events": conflicting_event_titles,
                })

                if not has_conflict:
                    available_count += 1

            except Exception as e:
                logger.error(f"Error checking calendar conflicts for interviewer {interviewer_id}: {e}", exc_info=True)
                # If we can't check conflicts, mark as unavailable to be safe
                interviewer_availability.append({
                    "interviewer_id": interviewer_id,
                    "interviewer_name": recruiter.name,
                    "interviewer_email": recruiter.email,
                    "is_available": False,
                    "has_calendar_connection": True,
                    "calendar_provider": connection.provider.value,
                    "conflicting_events": [],
                })

        all_available = available_count == len(availability_request.interviewer_ids)

        response_data = {
            "start_time": availability_request.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": availability_request.duration_minutes,
            "all_available": all_available,
            "interviewer_count": len(availability_request.interviewer_ids),
            "available_count": available_count,
            "interviewer_availability": interviewer_availability,
        }

        logger.info(
            f"Availability check complete: {available_count}/{len(availability_request.interviewer_ids)} available"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check availability: {str(e)}",
        ) from e


@router.post(
    "/availability-slots",
    tags=["Calendar"],
)
async def get_availability_slots(
    request: Request,
    slots_request: AvailabilitySlotsRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get available time slots for a recruiter.

    Returns available time slots for a recruiter within a date range based on
    their connected calendar. Checks for conflicts and returns only free slots
    that match the requested duration.
    """
    try:
        logger.info(
            f"Fetching availability slots for recruiter {slots_request.recruiter_id} "
            f"from {slots_request.start_date} to {slots_request.end_date} "
            f"with duration {slots_request.duration_minutes} minutes"
        )

        try:
            recruiter_uuid = UUID(slots_request.recruiter_id)
        except ValueError:
            logger.warning(f"Invalid recruiter_id format: {slots_request.recruiter_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recruiter_id format: {slots_request.recruiter_id}",
            )

        recruiter_query = select(Recruiter).where(Recruiter.id == recruiter_uuid)
        recruiter_result = await db.execute(recruiter_query)
        recruiter = recruiter_result.scalar_one_or_none()

        if not recruiter:
            logger.warning(f"Recruiter not found: {slots_request.recruiter_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recruiter not found: {slots_request.recruiter_id}",
            )

        connection_query = select(CalendarConnection).where(
            and_(
                CalendarConnection.recruiter_id == recruiter_uuid,
                CalendarConnection.status == ConnectionStatus.ACTIVE
            )
        )
        connection_result = await db.execute(connection_query)
        connection = connection_result.scalar_one_or_none()

        if not connection or not connection.is_active():
            logger.info(f"No active calendar connection for recruiter {slots_request.recruiter_id}")
            response_data = {
                "recruiter_id": slots_request.recruiter_id,
                "recruiter_name": recruiter.name,
                "recruiter_email": recruiter.email,
                "start_date": slots_request.start_date,
                "end_date": slots_request.end_date,
                "duration_minutes": slots_request.duration_minutes,
                "has_calendar_connection": False,
                "calendar_provider": None,
                "slots": [],
            }
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data,
            )

        try:
            start_datetime = datetime.fromisoformat(slots_request.start_date)
            end_datetime = datetime.fromisoformat(slots_request.end_date)
        except ValueError as e:
            logger.warning(f"Invalid date format: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format. Expected YYYY-MM-DD: {str(e)}",
            )

        if start_datetime >= end_datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before end_date",
            )

        try:
            calendar_service = get_calendar_service(
                provider=connection.provider.value,
                access_token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_expires_at=connection.token_expires_at,
                calendar_email=connection.calendar_email,
                calendar_id=connection.calendar_id,
            )

            availability_slots = calendar_service.get_availability(
                start_time=start_datetime,
                end_time=end_datetime,
                duration_minutes=slots_request.duration_minutes,
            )

            # Filter slots by business hours and split into bookable chunks
            filtered_slots = filter_slots_by_business_hours(
                slots=availability_slots,
                duration_minutes=slots_request.duration_minutes,
            )

            slot_responses = [
                {
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "available": slot.available,
                    "confidence": slot.confidence,
                }
                for slot in filtered_slots
            ]

            response_data = {
                "recruiter_id": slots_request.recruiter_id,
                "recruiter_name": recruiter.name,
                "recruiter_email": recruiter.email,
                "start_date": slots_request.start_date,
                "end_date": slots_request.end_date,
                "duration_minutes": slots_request.duration_minutes,
                "has_calendar_connection": True,
                "calendar_provider": connection.provider.value,
                "slots": slot_responses,
            }

            logger.info(
                f"Retrieved {len(slot_responses)} available slots for recruiter {slots_request.recruiter_id}"
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_data,
            )

        except Exception as e:
            logger.error(
                f"Error fetching availability from calendar service for recruiter {slots_request.recruiter_id}: {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch availability from calendar: {str(e)}",
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching availability slots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch availability slots: {str(e)}",
        ) from e
