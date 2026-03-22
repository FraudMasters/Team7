"""
Interview scheduling and management endpoints.

This module provides endpoints for:
- Creating, updating, and canceling interviews
- Listing interviews with filters
- Managing interview participants
- Interview history tracking

Supports the complete interview scheduling workflow with calendar integration.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.interview import Interview, InterviewParticipant, InterviewStatus, InterviewType, ParticipantRole, ParticipantStatus
from models.resume import Resume
from models.recruiter import Recruiter
from models.job_vacancy import JobVacancy
from models.candidate_activity import CandidateActivity, CandidateActivityType
from models.calendar_connection import CalendarConnection, CalendarProvider

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class InterviewParticipantCreate(BaseModel):
    """Request model for adding a participant to an interview."""

    recruiter_id: UUID = Field(..., description="ID of the recruiter to add as participant")
    role: str = Field(
        default=ParticipantRole.INTERVIEWER.value,
        description="Role of the participant in the interview"
    )


class InterviewParticipantUpdate(BaseModel):
    """Request model for updating a participant's status."""

    status: str = Field(..., description="New status for the participant")
    notes: Optional[str] = Field(None, description="Optional notes from the participant")


class InterviewParticipantResponse(BaseModel):
    """Response model for an interview participant."""

    id: str = Field(..., description="Unique identifier for the participant")
    interview_id: str = Field(..., description="ID of the interview")
    recruiter_id: str = Field(..., description="ID of the recruiter")
    recruiter_name: Optional[str] = Field(None, description="Name of the recruiter")
    recruiter_email: Optional[str] = Field(None, description="Email of the recruiter")
    role: str = Field(..., description="Role of the participant")
    status: str = Field(..., description="Response status of the participant")
    response_timestamp: Optional[str] = Field(
        None, description="When the participant last responded"
    )
    notes: Optional[str] = Field(None, description="Notes from the participant")
    created_at: str = Field(..., description="Timestamp when record was created")
    updated_at: str = Field(..., description="Timestamp when record was last updated")

    class Config:
        from_attributes = True


class InterviewCreate(BaseModel):
    """Request model for creating a new interview."""

    candidate_id: UUID = Field(..., description="ID of the candidate (resume)")
    vacancy_id: Optional[UUID] = Field(None, description="Optional ID of the job vacancy")
    scheduled_start: datetime = Field(..., description="Interview start time with timezone")
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=480,
        description="Duration of interview in minutes (15-480)"
    )
    interview_type: str = Field(..., description="Type/format of interview")
    title: str = Field(..., min_length=1, max_length=255, description="Interview title")
    description: Optional[str] = Field(None, description="Detailed agenda or notes")
    location: Optional[str] = Field(None, max_length=500, description="Physical location for onsite")
    meeting_link: Optional[str] = Field(
        None, max_length=500, description="Virtual meeting link for remote interviews"
    )
    meeting_room: Optional[str] = Field(
        None, max_length=255, description="Meeting room name/number"
    )
    recruiter_id: Optional[UUID] = Field(None, description="ID of the recruiter scheduling the interview")
    participant_ids: Optional[List[UUID]] = Field(
        None,
        description="List of recruiter IDs to add as interview participants"
    )


class InterviewUpdate(BaseModel):
    """Request model for updating an existing interview."""

    scheduled_start: Optional[datetime] = Field(
        None, description="Updated interview start time"
    )
    duration_minutes: Optional[int] = Field(
        None,
        ge=15,
        le=480,
        description="Updated duration in minutes"
    )
    status: Optional[str] = Field(None, description="Updated interview status")
    interview_type: Optional[str] = Field(None, description="Updated interview type")
    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Updated title"
    )
    description: Optional[str] = Field(None, description="Updated description/agenda")
    location: Optional[str] = Field(
        None, max_length=500, description="Updated location"
    )
    meeting_link: Optional[str] = Field(
        None, max_length=500, description="Updated meeting link"
    )
    meeting_room: Optional[str] = Field(
        None, max_length=255, description="Updated meeting room"
    )
    vacancy_id: Optional[UUID] = Field(None, description="Updated vacancy ID")


class InterviewResponse(BaseModel):
    """Response model for an interview."""

    id: str = Field(..., description="Unique identifier for the interview")
    candidate_id: str = Field(..., description="ID of the candidate")
    candidate_name: Optional[str] = Field(None, description="Name of the candidate")
    vacancy_id: Optional[str] = Field(None, description="ID of the related vacancy")
    vacancy_title: Optional[str] = Field(None, description="Title of the related vacancy")
    scheduled_start: str = Field(..., description="Interview start time")
    scheduled_end: str = Field(..., description="Interview end time")
    duration_minutes: int = Field(..., description="Duration in minutes")
    status: str = Field(..., description="Current status")
    interview_type: str = Field(..., description="Type of interview")
    title: str = Field(..., description="Interview title")
    description: Optional[str] = Field(None, description="Interview description/agenda")
    location: Optional[str] = Field(None, description="Physical location")
    meeting_link: Optional[str] = Field(None, description="Virtual meeting link")
    meeting_room: Optional[str] = Field(None, description="Meeting room")
    recruiter_id: Optional[str] = Field(None, description="ID of scheduling recruiter")
    recruiter_name: Optional[str] = Field(None, description="Name of scheduling recruiter")
    calendar_event_id: Optional[str] = Field(None, description="External calendar event ID")
    calendar_provider: Optional[str] = Field(None, description="Calendar provider (google/outlook)")
    is_reminder_sent: bool = Field(..., description="Whether reminder was sent")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    participants: Optional[List[InterviewParticipantResponse]] = Field(
        None, description="List of interview participants"
    )

    class Config:
        from_attributes = True


@router.get(
    "/",
    tags=["Interviews"],
)
async def list_interviews(
    request: Request,
    candidate_id: Optional[str] = None,
    vacancy_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    interviewer_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all interviews with optional filters.

    Returns a paginated list of interviews. Can be filtered by candidate,
    vacancy, status, interviewer, and date range.
    """
    try:
        logger.info(
            f"Fetching interviews - candidate_id: {candidate_id}, vacancy_id: {vacancy_id}, "
            f"status: {status_filter}, interviewer_id: {interviewer_id}"
        )

        query = select(Interview).order_by(Interview.scheduled_start.desc())

        if candidate_id:
            try:
                candidate_uuid = UUID(candidate_id)
                query = query.where(Interview.candidate_id == candidate_uuid)
            except ValueError:
                logger.warning(f"Invalid candidate_id format: {candidate_id}")

        if vacancy_id:
            try:
                vacancy_uuid = UUID(vacancy_id)
                query = query.where(Interview.vacancy_id == vacancy_uuid)
            except ValueError:
                logger.warning(f"Invalid vacancy_id format: {vacancy_id}")

        if status_filter:
            try:
                InterviewStatus(status_filter)
                query = query.where(Interview.status == status_filter)
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")

        if interviewer_id:
            try:
                interviewer_uuid = UUID(interviewer_id)
                query = query.join(
                    InterviewParticipant,
                    InterviewParticipant.interview_id == Interview.id
                ).where(InterviewParticipant.recruiter_id == interviewer_uuid)
            except ValueError:
                logger.warning(f"Invalid interviewer_id format: {interviewer_id}")

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.where(Interview.scheduled_start >= start_dt)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.where(Interview.scheduled_start <= end_dt)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")

        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        interviews = result.scalars().all()

        interview_list = []
        for interview in interviews:
            candidate_query = select(Resume).where(Resume.id == interview.candidate_id)
            candidate_result = await db.execute(candidate_query)
            candidate = candidate_result.scalar_one_or_none()

            vacancy_title = None
            if interview.vacancy_id:
                vacancy_query = select(JobVacancy).where(JobVacancy.id == interview.vacancy_id)
                vacancy_result = await db.execute(vacancy_query)
                vacancy = vacancy_result.scalar_one_or_none()
                vacancy_title = vacancy.title if vacancy else None

            recruiter_name = None
            if interview.recruiter_id:
                recruiter_query = select(Recruiter).where(Recruiter.id == interview.recruiter_id)
                recruiter_result = await db.execute(recruiter_query)
                recruiter = recruiter_result.scalar_one_or_none()
                if recruiter:
                    recruiter_name = f"{recruiter.first_name} {recruiter.last_name}"

            participants_query = (
                select(InterviewParticipant, Recruiter)
                .outerjoin(Recruiter, InterviewParticipant.recruiter_id == Recruiter.id)
                .where(InterviewParticipant.interview_id == interview.id)
            )
            participants_result = await db.execute(participants_query)
            participants_rows = participants_result.all()

            participants_data = []
            for participant, recruiter in participants_rows:
                participants_data.append({
                    "id": str(participant.id),
                    "interview_id": str(participant.interview_id),
                    "recruiter_id": str(participant.recruiter_id),
                    "recruiter_name": f"{recruiter.first_name} {recruiter.last_name}" if recruiter else None,
                    "recruiter_email": recruiter.email if recruiter else None,
                    "role": participant.role.value,
                    "status": participant.status.value,
                    "response_timestamp": participant.response_timestamp.isoformat() if participant.response_timestamp else None,
                    "notes": participant.notes,
                    "created_at": participant.created_at.isoformat() if participant.created_at else None,
                    "updated_at": participant.updated_at.isoformat() if participant.updated_at else None,
                })

            interview_list.append({
                "id": str(interview.id),
                "candidate_id": str(interview.candidate_id),
                "candidate_name": candidate.filename if candidate else None,
                "vacancy_id": str(interview.vacancy_id) if interview.vacancy_id else None,
                "vacancy_title": vacancy_title,
                "scheduled_start": interview.scheduled_start.isoformat() if interview.scheduled_start else None,
                "scheduled_end": interview.scheduled_end.isoformat() if interview.scheduled_end else None,
                "duration_minutes": interview.duration_minutes,
                "status": interview.status.value,
                "interview_type": interview.interview_type.value,
                "title": interview.title,
                "description": interview.description,
                "location": interview.location,
                "meeting_link": interview.meeting_link,
                "meeting_room": interview.meeting_room,
                "recruiter_id": str(interview.recruiter_id) if interview.recruiter_id else None,
                "recruiter_name": recruiter_name,
                "calendar_event_id": interview.calendar_event_id,
                "calendar_provider": interview.calendar_provider,
                "is_reminder_sent": interview.is_reminder_sent,
                "created_at": interview.created_at.isoformat() if interview.created_at else None,
                "updated_at": interview.updated_at.isoformat() if interview.updated_at else None,
                "participants": participants_data,
            })

        logger.info(f"Retrieved {len(interview_list)} interviews")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=interview_list,
        )

    except Exception as e:
        logger.error(f"Error listing interviews: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list interviews: {str(e)}",
        ) from e


@router.post(
    "/",
    tags=["Interviews"],
)
async def create_interview(
    request: Request,
    interview_data: InterviewCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Create a new interview."""
    try:
        logger.info(f"Creating interview for candidate {interview_data.candidate_id}")

        candidate_query = select(Resume).where(Resume.id == interview_data.candidate_id)
        candidate_result = await db.execute(candidate_query)
        candidate = candidate_result.scalar_one_or_none()

        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate not found: {interview_data.candidate_id}",
            )

        if interview_data.vacancy_id:
            vacancy_query = select(JobVacancy).where(JobVacancy.id == interview_data.vacancy_id)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()
            if not vacancy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Vacancy not found: {interview_data.vacancy_id}",
                )

        scheduled_end = interview_data.scheduled_start + timedelta(minutes=interview_data.duration_minutes)

        try:
            interview_type = InterviewType(interview_data.interview_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview type: {interview_data.interview_type}",
            )

        interview = Interview(
            candidate_id=interview_data.candidate_id,
            vacancy_id=interview_data.vacancy_id,
            scheduled_start=interview_data.scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=interview_data.duration_minutes,
            status=InterviewStatus.SCHEDULED,
            interview_type=interview_type,
            title=interview_data.title,
            description=interview_data.description,
            location=interview_data.location,
            meeting_link=interview_data.meeting_link,
            meeting_room=interview_data.meeting_room,
            recruiter_id=interview_data.recruiter_id,
        )

        db.add(interview)
        await db.commit()
        await db.refresh(interview)

        if interview_data.participant_ids:
            for participant_id in interview_data.participant_ids:
                recruiter_query = select(Recruiter).where(Recruiter.id == participant_id)
                recruiter_result = await db.execute(recruiter_query)
                recruiter = recruiter_result.scalar_one_or_none()

                if recruiter:
                    participant = InterviewParticipant(
                        interview_id=interview.id,
                        recruiter_id=participant_id,
                        role=ParticipantRole.INTERVIEWER,
                        status=ParticipantStatus.PENDING,
                    )
                    db.add(participant)

            await db.commit()

        activity = CandidateActivity(
            candidate_id=interview_data.candidate_id,
            activity_type=CandidateActivityType.INTERVIEW_SCHEDULED,
            metadata={
                "interview_id": str(interview.id),
                "interview_title": interview_data.title,
                "scheduled_start": interview.scheduled_start.isoformat(),
                "duration_minutes": interview_data.duration_minutes,
                "interview_type": interview_data.interview_type,
            },
        )
        db.add(activity)
        await db.commit()

        # Trigger calendar event creation if recruiter has connected calendar
        if interview.recruiter_id:
            calendar_query = select(CalendarConnection).where(
                and_(
                    CalendarConnection.recruiter_id == interview.recruiter_id,
                    CalendarConnection.status == 'active'
                )
            )
            calendar_result = await db.execute(calendar_query)
            calendar_connection = calendar_result.scalar_one_or_none()

            if calendar_connection:
                from tasks.calendar_tasks import create_calendar_event

                # Gather attendee email addresses
                attendees = []

                # Add organizer/recruiter email
                organizer_query = select(Recruiter).where(Recruiter.id == interview.recruiter_id)
                organizer_result = await db.execute(organizer_query)
                organizer = organizer_result.scalar_one_or_none()
                if organizer and organizer.email:
                    attendees.append(organizer.email)

                # Add participant emails
                if interview_data.participant_ids:
                    for participant_id in interview_data.participant_ids:
                        participant_query = select(Recruiter).where(Recruiter.id == participant_id)
                        participant_result = await db.execute(participant_query)
                        participant_recruiter = participant_result.scalar_one_or_none()
                        if participant_recruiter and participant_recruiter.email:
                            attendees.append(participant_recruiter.email)

                # Add candidate email if available
                if hasattr(candidate, 'email') and candidate.email:
                    attendees.append(candidate.email)

                event_details = {
                    "title": interview.title,
                    "description": interview.description or "",
                    "start_time": interview.scheduled_start.isoformat(),
                    "end_time": interview.scheduled_end.isoformat(),
                    "duration_minutes": interview.duration_minutes,
                    "location": interview.location,
                    "meeting_link": interview.meeting_link,
                    "interview_type": interview.interview_type.value,
                    "candidate_id": str(interview.candidate_id),
                    "candidate_name": candidate.full_name or candidate.filename or "Candidate",
                    "attendees": attendees,
                }

                try:
                    create_calendar_event.delay(
                        interview_id=str(interview.id),
                        calendar_provider=calendar_connection.provider,
                        recruiter_id=str(interview.recruiter_id),
                        event_details=event_details,
                    )
                    logger.info(f"Calendar event creation task queued for interview {interview.id} with {len(attendees)} attendees")
                except Exception as e:
                    logger.error(f"Failed to queue calendar event creation task: {e}")
                    # Don't fail the interview creation if calendar task fails
            else:
                logger.info(f"No active calendar connection found for recruiter {interview.recruiter_id}, skipping calendar event creation")

        logger.info(f"Interview created successfully: {interview.id}")

        interview_uuid_str = str(interview.id)
        return await get_interview(request, interview_uuid_str, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating interview: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interview: {str(e)}",
        ) from e


@router.get(
    "/{interview_id}",
    tags=["Interviews"],
)
async def get_interview(
    request: Request,
    interview_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get a specific interview by ID."""
    try:
        logger.info(f"Fetching interview: {interview_id}")

        try:
            interview_uuid = UUID(interview_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview ID format: {interview_id}",
            )

        query = select(Interview).where(Interview.id == interview_uuid)
        result = await db.execute(query)
        interview = result.scalar_one_or_none()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview not found: {interview_id}",
            )

        candidate_query = select(Resume).where(Resume.id == interview.candidate_id)
        candidate_result = await db.execute(candidate_query)
        candidate = candidate_result.scalar_one_or_none()

        vacancy_title = None
        if interview.vacancy_id:
            vacancy_query = select(JobVacancy).where(JobVacancy.id == interview.vacancy_id)
            vacancy_result = await db.execute(vacancy_query)
            vacancy = vacancy_result.scalar_one_or_none()
            vacancy_title = vacancy.title if vacancy else None

        recruiter_name = None
        if interview.recruiter_id:
            recruiter_query = select(Recruiter).where(Recruiter.id == interview.recruiter_id)
            recruiter_result = await db.execute(recruiter_query)
            recruiter = recruiter_result.scalar_one_or_none()
            if recruiter:
                recruiter_name = f"{recruiter.first_name} {recruiter.last_name}"

        participants_query = (
            select(InterviewParticipant, Recruiter)
            .outerjoin(Recruiter, InterviewParticipant.recruiter_id == Recruiter.id)
            .where(InterviewParticipant.interview_id == interview.id)
        )
        participants_result = await db.execute(participants_query)
        participants_rows = participants_result.all()

        participants_data = []
        for participant, recruiter in participants_rows:
            participants_data.append({
                "id": str(participant.id),
                "interview_id": str(participant.interview_id),
                "recruiter_id": str(participant.recruiter_id),
                "recruiter_name": f"{recruiter.first_name} {recruiter.last_name}" if recruiter else None,
                "recruiter_email": recruiter.email if recruiter else None,
                "role": participant.role.value,
                "status": participant.status.value,
                "response_timestamp": participant.response_timestamp.isoformat() if participant.response_timestamp else None,
                "notes": participant.notes,
                "created_at": participant.created_at.isoformat() if participant.created_at else None,
                "updated_at": participant.updated_at.isoformat() if participant.updated_at else None,
            })

        interview_data = {
            "id": str(interview.id),
            "candidate_id": str(interview.candidate_id),
            "candidate_name": candidate.filename if candidate else None,
            "vacancy_id": str(interview.vacancy_id) if interview.vacancy_id else None,
            "vacancy_title": vacancy_title,
            "scheduled_start": interview.scheduled_start.isoformat() if interview.scheduled_start else None,
            "scheduled_end": interview.scheduled_end.isoformat() if interview.scheduled_end else None,
            "duration_minutes": interview.duration_minutes,
            "status": interview.status.value,
            "interview_type": interview.interview_type.value,
            "title": interview.title,
            "description": interview.description,
            "location": interview.location,
            "meeting_link": interview.meeting_link,
            "meeting_room": interview.meeting_room,
            "recruiter_id": str(interview.recruiter_id) if interview.recruiter_id else None,
            "recruiter_name": recruiter_name,
            "calendar_event_id": interview.calendar_event_id,
            "calendar_provider": interview.calendar_provider,
            "is_reminder_sent": interview.is_reminder_sent,
            "created_at": interview.created_at.isoformat() if interview.created_at else None,
            "updated_at": interview.updated_at.isoformat() if interview.updated_at else None,
            "participants": participants_data,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=interview_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting interview {interview_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get interview: {str(e)}",
        ) from e


@router.put(
    "/{interview_id}",
    tags=["Interviews"],
)
async def update_interview(
    request: Request,
    interview_id: str,
    interview_data: InterviewUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Update an existing interview."""
    try:
        logger.info(f"Updating interview {interview_id}")

        try:
            interview_uuid = UUID(interview_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview ID format: {interview_id}",
            )

        query = select(Interview).where(Interview.id == interview_uuid)
        result = await db.execute(query)
        interview = result.scalar_one_or_none()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview not found: {interview_id}",
            )

        if interview_data.scheduled_start is not None:
            interview.scheduled_start = interview_data.scheduled_start
            if interview_data.duration_minutes is not None:
                interview.scheduled_end = interview_data.scheduled_start + timedelta(minutes=interview_data.duration_minutes)
            else:
                interview.scheduled_end = interview_data.scheduled_start + timedelta(minutes=interview.duration_minutes)

        if interview_data.duration_minutes is not None:
            interview.duration_minutes = interview_data.duration_minutes
            interview.scheduled_end = interview.scheduled_start + timedelta(minutes=interview_data.duration_minutes)

        if interview_data.status is not None:
            try:
                interview.status = InterviewStatus(interview_data.status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {interview_data.status}",
                )

        if interview_data.interview_type is not None:
            try:
                interview.interview_type = InterviewType(interview_data.interview_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid interview type: {interview_data.interview_type}",
                )

        if interview_data.title is not None:
            interview.title = interview_data.title

        if interview_data.description is not None:
            interview.description = interview_data.description

        if interview_data.location is not None:
            interview.location = interview_data.location

        if interview_data.meeting_link is not None:
            interview.meeting_link = interview_data.meeting_link

        if interview_data.meeting_room is not None:
            interview.meeting_room = interview_data.meeting_room

        if interview_data.vacancy_id is not None:
            interview.vacancy_id = interview_data.vacancy_id

        await db.commit()
        await db.refresh(interview)

        # Sync with calendar if event exists
        if interview.calendar_event_id and interview.calendar_provider:
            from tasks.calendar_tasks import update_calendar_event

            event_details = {
                "title": interview.title,
                "description": interview.description or "",
                "start_time": interview.scheduled_start.isoformat(),
                "end_time": interview.scheduled_end.isoformat(),
                "duration_minutes": interview.duration_minutes,
                "location": interview.location,
                "meeting_link": interview.meeting_link,
                "interview_type": interview.interview_type.value,
            }

            try:
                update_calendar_event.delay(
                    interview_id=str(interview.id),
                    calendar_provider=interview.calendar_provider,
                    recruiter_id=str(interview.recruiter_id) if interview.recruiter_id else None,
                    event_id=interview.calendar_event_id,
                    event_details=event_details,
                )
                logger.info(f"Calendar event update task queued for interview {interview.id}")
            except Exception as e:
                logger.error(f"Failed to queue calendar event update task: {e}")
                # Don't fail the interview update if calendar task fails

        logger.info(f"Interview updated successfully: {interview.id}")

        return await get_interview(request, interview_id, db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating interview {interview_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interview: {str(e)}",
        ) from e


@router.delete(
    "/{interview_id}",
    tags=["Interviews"],
)
async def delete_interview(
    request: Request,
    interview_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Delete/cancel an interview."""
    try:
        logger.info(f"Deleting interview {interview_id}")

        try:
            interview_uuid = UUID(interview_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview ID format: {interview_id}",
            )

        query = select(Interview).where(Interview.id == interview_uuid)
        result = await db.execute(query)
        interview = result.scalar_one_or_none()

        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview not found: {interview_id}",
            )

        # Delete calendar event if exists
        calendar_event_id = interview.calendar_event_id
        calendar_provider = interview.calendar_provider
        recruiter_id = interview.recruiter_id

        await db.delete(interview)
        await db.commit()

        # Delete calendar event asynchronously
        if calendar_event_id and calendar_provider:
            from tasks.calendar_tasks import delete_calendar_event

            try:
                delete_calendar_event.delay(
                    interview_id=interview_id,
                    calendar_provider=calendar_provider,
                    recruiter_id=str(recruiter_id) if recruiter_id else None,
                    event_id=calendar_event_id,
                )
                logger.info(f"Calendar event deletion task queued for interview {interview_id}")
            except Exception as e:
                logger.error(f"Failed to queue calendar event deletion task: {e}")
                # Don't fail the interview deletion if calendar task fails

        logger.info(f"Interview deleted successfully: {interview_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Interview deleted successfully",
                "interview_id": interview_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting interview {interview_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete interview: {str(e)}",
        ) from e
