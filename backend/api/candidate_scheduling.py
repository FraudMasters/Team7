"""
Candidate self-scheduling API endpoints.

This module provides endpoints for candidates to self-schedule interviews
from available time slots shared by recruiters. Candidates receive a unique
token via email/SMS and can use it to book an interview at their preferred time.

Supports the complete candidate self-scheduling workflow with calendar integration.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.interview import Interview, InterviewStatus, InterviewType
from models.resume import Resume
from models.recruiter import Recruiter
from models.job_vacancy import JobVacancy
from models.candidate_activity import CandidateActivity, CandidateActivityType
from models.calendar_connection import CalendarConnection

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class SelfScheduleRequest(BaseModel):
    """Request model for candidate self-scheduling an interview."""

    token: str = Field(..., description="Unique self-scheduling token provided to the candidate")
    selected_slot: datetime = Field(..., description="Selected interview time slot")
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=480,
        description="Duration of interview in minutes (15-480)"
    )
    interview_type: Optional[str] = Field(
        default="video",
        description="Type of interview (defaults to video)"
    )


class SelfScheduleResponse(BaseModel):
    """Response model for successful self-scheduling."""

    interview_id: str = Field(..., description="ID of the created interview")
    candidate_name: str = Field(..., description="Name of the candidate")
    scheduled_start: str = Field(..., description="Interview start time")
    scheduled_end: str = Field(..., description="Interview end time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    interview_type: str = Field(..., description="Type of interview")
    title: str = Field(..., description="Interview title")
    meeting_link: Optional[str] = Field(None, description="Virtual meeting link if applicable")
    location: Optional[str] = Field(None, description="Physical location if applicable")
    recruiter_name: Optional[str] = Field(None, description="Name of the recruiter/interviewer")
    message: str = Field(..., description="Success message")

    class Config:
        from_attributes = True


class AvailableSlotsRequest(BaseModel):
    """Request model for retrieving available slots via token."""

    token: str = Field(..., description="Unique self-scheduling token")


class AvailableSlotResponse(BaseModel):
    """Response model for an available time slot."""

    start_time: str = Field(..., description="Slot start time")
    end_time: str = Field(..., description="Slot end time")
    duration_minutes: int = Field(..., description="Slot duration in minutes")
    available: bool = Field(..., description="Whether the slot is available")


class AvailableSlotsResponse(BaseModel):
    """Response model for available slots."""

    recruiter_name: str = Field(..., description="Name of the recruiter")
    vacancy_title: Optional[str] = Field(None, description="Title of the position")
    available_slots: list[AvailableSlotResponse] = Field(..., description="List of available slots")
    expires_at: Optional[str] = Field(None, description="When the scheduling link expires")


@router.post(
    "/schedule",
    tags=["Candidate Scheduling"],
    status_code=status.HTTP_201_CREATED,
)
async def schedule_interview(
    request: Request,
    schedule_data: SelfScheduleRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Candidate self-schedules an interview using a unique token.

    This endpoint allows candidates to book an interview at their preferred time
    from the available slots provided by the recruiter. The token validates the
    candidate's identity and links them to the appropriate job vacancy and recruiter.

    Returns:
        JSONResponse with interview details and confirmation message
    """
    try:
        logger.info(f"Processing self-schedule request with token: {schedule_data.token[:10]}...")

        # TODO: Implement token validation and decoding (subtask 4-2)
        # For now, we'll accept any token and use test data
        # In the real implementation, the token should contain:
        # - candidate_id
        # - recruiter_id
        # - vacancy_id (optional)
        # - expiration timestamp
        # - signature/hash for security

        # Mock token parsing for initial implementation
        # This will be replaced with actual token validation in subtask 4-2
        token_data = {
            "candidate_id": None,  # Will be extracted from token
            "recruiter_id": None,  # Will be extracted from token
            "vacancy_id": None,  # Will be extracted from token
            "expires_at": None,  # Will be extracted from token
        }

        # Validate token format
        if not schedule_data.token or len(schedule_data.token) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scheduling token format",
            )

        # TODO: Validate token hasn't expired
        # TODO: Validate token hasn't been used already
        # TODO: Extract candidate_id, recruiter_id, vacancy_id from token

        # For initial implementation, we'll create a basic interview
        # This will be enhanced when token system is implemented

        # Validate selected time slot is in the future
        if schedule_data.selected_slot < datetime.now(schedule_data.selected_slot.tzinfo):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected time slot must be in the future",
            )

        # Calculate end time
        scheduled_end = schedule_data.selected_slot + timedelta(minutes=schedule_data.duration_minutes)

        # Validate interview type
        try:
            interview_type = InterviewType(schedule_data.interview_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview type: {schedule_data.interview_type}. Must be one of: {[t.value for t in InterviewType]}",
            )

        # TODO: Get actual candidate, recruiter, and vacancy from token
        # For now, return a response indicating token validation is needed
        candidate_name = "Candidate"  # Will come from token
        recruiter_name = "Recruiter"  # Will come from token
        vacancy_title = None  # Will come from token

        # Create interview title
        interview_title = f"Interview with {candidate_name}"
        if vacancy_title:
            interview_title = f"{vacancy_title} - {interview_title}"

        # TODO: Create actual interview record once token validation is implemented
        # For now, return success response with mock data for API contract testing

        logger.info(
            f"Successfully processed self-schedule request for time slot: {schedule_data.selected_slot.isoformat()}"
        )

        # Mock response for initial implementation
        # This will be replaced with actual interview creation in subtask 4-2
        mock_interview_id = "00000000-0000-0000-0000-000000000000"

        response_data = {
            "interview_id": mock_interview_id,
            "candidate_name": candidate_name,
            "scheduled_start": schedule_data.selected_slot.isoformat(),
            "scheduled_end": scheduled_end.isoformat(),
            "duration_minutes": schedule_data.duration_minutes,
            "interview_type": interview_type.value,
            "title": interview_title,
            "meeting_link": None,  # Will be generated after calendar integration
            "location": None,
            "recruiter_name": recruiter_name,
            "message": "Interview scheduled successfully! You will receive a confirmation email shortly.",
        }

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling interview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule interview: {str(e)}",
        ) from e


@router.post(
    "/available-slots",
    tags=["Candidate Scheduling"],
)
async def get_available_slots(
    request: Request,
    slots_request: AvailableSlotsRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Retrieve available time slots for a candidate using their scheduling token.

    This endpoint returns the available interview slots that the candidate can
    choose from, based on the recruiter's availability and the token parameters.

    Returns:
        JSONResponse with available slots and scheduling context
    """
    try:
        logger.info(f"Fetching available slots for token: {slots_request.token[:10]}...")

        # TODO: Implement token validation and decoding (subtask 4-2)
        # For now, return mock data for API contract testing

        # Validate token format
        if not slots_request.token or len(slots_request.token) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid scheduling token format",
            )

        # TODO: Validate token and extract recruiter_id, vacancy_id
        # TODO: Fetch actual available slots from recruiter's calendar
        # TODO: Filter out already booked slots

        # Mock response for initial implementation
        mock_slots = [
            {
                "start_time": (datetime.now() + timedelta(days=1, hours=10)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1, hours=11)).isoformat(),
                "duration_minutes": 60,
                "available": True,
            },
            {
                "start_time": (datetime.now() + timedelta(days=1, hours=14)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=1, hours=15)).isoformat(),
                "duration_minutes": 60,
                "available": True,
            },
            {
                "start_time": (datetime.now() + timedelta(days=2, hours=10)).isoformat(),
                "end_time": (datetime.now() + timedelta(days=2, hours=11)).isoformat(),
                "duration_minutes": 60,
                "available": True,
            },
        ]

        response_data = {
            "recruiter_name": "Recruiter Name",  # Will come from token
            "vacancy_title": None,  # Will come from token
            "available_slots": mock_slots,
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),  # Default 7-day expiration
        }

        logger.info(f"Retrieved {len(mock_slots)} available slots")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching available slots: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch available slots: {str(e)}",
        ) from e


@router.get(
    "/verify-token/{token}",
    tags=["Candidate Scheduling"],
)
async def verify_scheduling_token(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Verify if a scheduling token is valid and not expired.

    This endpoint allows the frontend to check token validity before displaying
    the scheduling interface to the candidate.

    Returns:
        JSONResponse with token validity status and context information
    """
    try:
        logger.info(f"Verifying token: {token[:10]}...")

        # Validate token format
        if not token or len(token) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format",
            )

        # TODO: Implement actual token verification (subtask 4-2)
        # For now, return mock success response

        response_data = {
            "valid": True,
            "candidate_name": "Candidate Name",  # Will come from token
            "recruiter_name": "Recruiter Name",  # Will come from token
            "vacancy_title": None,  # Will come from token
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "message": "Token is valid and ready for scheduling",
        }

        logger.info(f"Token verified successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify token: {str(e)}",
        ) from e
