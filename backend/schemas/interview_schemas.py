"""
Pydantic schemas for interview scheduling and management
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class InterviewStatus(str):
    """Status of an interview in the scheduling lifecycle"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class InterviewType(str):
    """Types of interview formats"""
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    PANEL = "panel"


class ParticipantRole(str):
    """Role of a participant in an interview"""
    LEAD_INTERVIEWER = "lead_interviewer"
    INTERVIEWER = "interviewer"
    NOTE_TAKER = "note_taker"
    OBSERVER = "observer"
    HIRING_MANAGER = "hiring_manager"


class ParticipantStatus(str):
    """Response status of an interview participant"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class InterviewParticipantCreate(BaseModel):
    """Request model for adding a participant to an interview"""

    recruiter_id: UUID = Field(..., description="ID of the recruiter to add as participant")
    role: str = Field(
        ParticipantRole.INTERVIEWER,
        description="Role of the participant in the interview"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        valid_roles = [
            ParticipantRole.LEAD_INTERVIEWER,
            ParticipantRole.INTERVIEWER,
            ParticipantRole.NOTE_TAKER,
            ParticipantRole.OBSERVER,
            ParticipantRole.HIRING_MANAGER,
        ]
        if v not in valid_roles:
            raise ValueError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return v


class InterviewParticipantUpdate(BaseModel):
    """Request model for updating a participant's status"""

    status: str = Field(..., description="New status for the participant")
    notes: Optional[str] = Field(None, description="Optional notes from the participant")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        valid_statuses = [
            ParticipantStatus.PENDING,
            ParticipantStatus.ACCEPTED,
            ParticipantStatus.DECLINED,
            ParticipantStatus.TENTATIVE,
        ]
        if v not in valid_statuses:
            raise ValueError(
                f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        return v


class InterviewParticipantResponse(BaseModel):
    """Response model for an interview participant"""

    id: UUID = Field(..., description="Unique identifier for the participant")
    interview_id: UUID = Field(..., description="ID of the interview")
    recruiter_id: UUID = Field(..., description="ID of the recruiter")
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
    """Request model for creating a new interview"""

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

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v):
        valid_types = [
            InterviewType.PHONE,
            InterviewType.VIDEO,
            InterviewType.ONSITE,
            InterviewType.TECHNICAL,
            InterviewType.PANEL,
        ]
        if v not in valid_types:
            raise ValueError(
                f"Invalid interview type. Must be one of: {', '.join(valid_types)}"
            )
        return v


class InterviewUpdate(BaseModel):
    """Request model for updating an existing interview"""

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

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [
                InterviewStatus.SCHEDULED,
                InterviewStatus.CONFIRMED,
                InterviewStatus.CANCELLED,
                InterviewStatus.COMPLETED,
                InterviewStatus.NO_SHOW,
                InterviewStatus.RESCHEDULED,
            ]
            if v not in valid_statuses:
                raise ValueError(
                    f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
        return v

    @field_validator("interview_type")
    @classmethod
    def validate_interview_type(cls, v):
        if v is not None:
            valid_types = [
                InterviewType.PHONE,
                InterviewType.VIDEO,
                InterviewType.ONSITE,
                InterviewType.TECHNICAL,
                InterviewType.PANEL,
            ]
            if v not in valid_types:
                raise ValueError(
                    f"Invalid interview type. Must be one of: {', '.join(valid_types)}"
                )
        return v


class InterviewResponse(BaseModel):
    """Response model for an interview"""

    id: UUID = Field(..., description="Unique identifier for the interview")
    candidate_id: UUID = Field(..., description="ID of the candidate")
    vacancy_id: Optional[UUID] = Field(None, description="ID of the related vacancy")
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
    recruiter_id: Optional[UUID] = Field(None, description="ID of scheduling recruiter")
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


class InterviewListResponse(BaseModel):
    """Response model for a paginated list of interviews"""

    items: List[InterviewResponse] = Field(..., description="List of interviews")
    total: int = Field(..., description="Total number of interviews")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class InterviewAvailabilityCheck(BaseModel):
    """Request model for checking interview availability"""

    candidate_id: UUID = Field(..., description="ID of the candidate")
    recruiter_ids: List[UUID] = Field(
        ...,
        min_length=1,
        description="List of recruiter IDs to check availability for"
    )
    preferred_start: datetime = Field(..., description="Preferred start time")
    preferred_end: datetime = Field(..., description="Preferred end time")
    duration_minutes: int = Field(
        ...,
        ge=15,
        le=480,
        description="Required interview duration"
    )


class AvailabilitySlot(BaseModel):
    """Response model for an available time slot"""

    start: str = Field(..., description="Start time of available slot")
    end: str = Field(..., description="End time of available slot")
    all_recruiters_available: bool = Field(
        ...,
        description="Whether all recruiters are available"
    )
    available_recruiters: List[UUID] = Field(
        ...,
        description="List of recruiter IDs available for this slot"
    )


class InterviewAvailabilityResponse(BaseModel):
    """Response model for availability check results"""

    candidate_id: UUID = Field(..., description="ID of the candidate")
    recruiter_ids: List[UUID] = Field(..., description="Recruiter IDs checked")
    preferred_start: str = Field(..., description="Requested start time")
    preferred_end: str = Field(..., description="Requested end time")
    duration_minutes: int = Field(..., description="Required duration")
    available_slots: List[AvailabilitySlot] = Field(
        ...,
        description="List of available time slots"
    )
    preferred_slot_available: bool = Field(
        ...,
        description="Whether the preferred time slot is available"
    )
