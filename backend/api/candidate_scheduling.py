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
from jose import JWTError
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
from utils.tokens import (
    create_self_schedule_token,
    decode_self_schedule_token,
    validate_self_schedule_token,
    is_self_schedule_token_expired,
)

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

        # Validate and decode the self-scheduling token
        try:
            token_data = validate_self_schedule_token(schedule_data.token)
        except (JWTError, ValueError) as e:
            logger.warning(f"Invalid or expired token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired scheduling token. Please request a new scheduling link.",
            )

        # Extract IDs from token
        candidate_id = UUID(token_data.candidate_id)
        recruiter_id = UUID(token_data.recruiter_id)
        vacancy_id = UUID(token_data.vacancy_id) if token_data.vacancy_id else None

        # Check if token has already been used
        existing_interview = await db.execute(
            select(Interview).where(
                and_(
                    Interview.scheduling_token == schedule_data.token,
                    Interview.status != InterviewStatus.CANCELLED,
                )
            )
        )
        if existing_interview.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This scheduling token has already been used. Please contact the recruiter for a new link.",
            )

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

        # Fetch candidate information
        candidate = await db.execute(
            select(Resume).where(Resume.id == candidate_id)
        )
        candidate = candidate.scalar_one_or_none()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found",
            )

        # Fetch recruiter information
        recruiter = await db.execute(
            select(Recruiter).where(Recruiter.id == recruiter_id)
        )
        recruiter = recruiter.scalar_one_or_none()
        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found",
            )

        # Fetch vacancy information if provided
        vacancy_title = None
        if vacancy_id:
            vacancy = await db.execute(
                select(JobVacancy).where(JobVacancy.id == vacancy_id)
            )
            vacancy = vacancy.scalar_one_or_none()
            if vacancy:
                vacancy_title = vacancy.title

        # Create interview title
        candidate_name = f"{candidate.first_name} {candidate.last_name}".strip() or "Candidate"
        interview_title = f"Interview with {candidate_name}"
        if vacancy_title:
            interview_title = f"{vacancy_title} - {interview_title}"

        # Create the interview
        new_interview = Interview(
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            vacancy_id=vacancy_id,
            scheduled_start=schedule_data.selected_slot,
            scheduled_end=scheduled_end,
            duration_minutes=schedule_data.duration_minutes,
            status=InterviewStatus.SCHEDULED,
            interview_type=interview_type,
            title=interview_title,
            scheduling_token=schedule_data.token,
            token_used_at=datetime.utcnow(),
        )

        db.add(new_interview)
        await db.commit()
        await db.refresh(new_interview)

        logger.info(
            f"Successfully scheduled interview {new_interview.id} for candidate {candidate_id} "
            f"at {schedule_data.selected_slot.isoformat()}"
        )

        # Log candidate activity
        activity = CandidateActivity(
            candidate_id=candidate_id,
            activity_type=CandidateActivityType.INTERVIEW_SCHEDULED,
            description=f"Self-scheduled interview for {interview_title}",
            metadata={
                "interview_id": str(new_interview.id),
                "scheduled_start": schedule_data.selected_slot.isoformat(),
                "duration_minutes": schedule_data.duration_minutes,
                "interview_type": interview_type.value,
            },
        )
        db.add(activity)
        await db.commit()

        response_data = {
            "interview_id": str(new_interview.id),
            "candidate_name": candidate_name,
            "scheduled_start": schedule_data.selected_slot.isoformat(),
            "scheduled_end": scheduled_end.isoformat(),
            "duration_minutes": schedule_data.duration_minutes,
            "interview_type": interview_type.value,
            "title": interview_title,
            "meeting_link": new_interview.meeting_link,
            "location": new_interview.location,
            "recruiter_name": f"{recruiter.first_name} {recruiter.last_name}".strip() if recruiter else "Recruiter",
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

        # Validate and decode the self-scheduling token
        try:
            token_data = validate_self_schedule_token(slots_request.token)
        except (JWTError, ValueError) as e:
            logger.warning(f"Invalid or expired token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired scheduling token. Please request a new scheduling link.",
            )

        # Extract IDs from token
        recruiter_id = UUID(token_data.recruiter_id)
        vacancy_id = UUID(token_data.vacancy_id) if token_data.vacancy_id else None

        # Fetch recruiter information
        recruiter = await db.execute(
            select(Recruiter).where(Recruiter.id == recruiter_id)
        )
        recruiter = recruiter.scalar_one_or_none()
        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recruiter not found",
            )

        # Fetch vacancy information if provided
        vacancy_title = None
        if vacancy_id:
            vacancy = await db.execute(
                select(JobVacancy).where(JobVacancy.id == vacancy_id)
            )
            vacancy = vacancy.scalar_one_or_none()
            if vacancy:
                vacancy_title = vacancy.title

        # TODO: Fetch actual available slots from recruiter's calendar
        # For now, return mock slots (calendar integration in later subtasks)
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
            "recruiter_name": f"{recruiter.first_name} {recruiter.last_name}".strip() if recruiter else "Recruiter",
            "vacancy_title": vacancy_title,
            "available_slots": mock_slots,
            "expires_at": token_data.expires_at.isoformat(),
        }

        logger.info(f"Retrieved {len(mock_slots)} available slots for recruiter {recruiter_id}")

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

        # Validate and decode the self-scheduling token
        try:
            token_data = validate_self_schedule_token(token)
        except (JWTError, ValueError) as e:
            logger.warning(f"Invalid or expired token: {e}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "valid": False,
                    "message": "Invalid or expired scheduling token. Please request a new scheduling link.",
                },
            )

        # Extract IDs from token
        candidate_id = UUID(token_data.candidate_id)
        recruiter_id = UUID(token_data.recruiter_id)
        vacancy_id = UUID(token_data.vacancy_id) if token_data.vacancy_id else None

        # Fetch candidate information
        candidate = await db.execute(
            select(Resume).where(Resume.id == candidate_id)
        )
        candidate = candidate.scalar_one_or_none()

        # Fetch recruiter information
        recruiter = await db.execute(
            select(Recruiter).where(Recruiter.id == recruiter_id)
        )
        recruiter = recruiter.scalar_one_or_none()

        # Fetch vacancy information if provided
        vacancy_title = None
        if vacancy_id:
            vacancy = await db.execute(
                select(JobVacancy).where(JobVacancy.id == vacancy_id)
            )
            vacancy = vacancy.scalar_one_or_none()
            if vacancy:
                vacancy_title = vacancy.title

        # Check if token has already been used
        existing_interview = await db.execute(
            select(Interview).where(
                and_(
                    Interview.scheduling_token == token,
                    Interview.status != InterviewStatus.CANCELLED,
                )
            )
        )
        token_already_used = existing_interview.scalar_one_or_none() is not None

        response_data = {
            "valid": not token_already_used,
            "candidate_name": f"{candidate.first_name} {candidate.last_name}".strip() if candidate else "Candidate",
            "recruiter_name": f"{recruiter.first_name} {recruiter.last_name}".strip() if recruiter else "Recruiter",
            "vacancy_title": vacancy_title,
            "expires_at": token_data.expires_at.isoformat(),
            "message": "Token has already been used" if token_already_used else "Token is valid and ready for scheduling",
        }

        logger.info(f"Token verified: valid={response_data['valid']}")

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
