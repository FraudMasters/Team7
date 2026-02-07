"""
Interview model for scheduling and tracking candidate interviews
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class InterviewStatus(str, enum.Enum):
    """Status of an interview in the scheduling lifecycle"""

    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class InterviewType(str, enum.Enum):
    """Types of interview formats"""

    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    TECHNICAL = "technical"
    PANEL = "panel"


class Interview(Base, UUIDMixin, TimestampMixin):
    """
    Interview model for scheduling and tracking candidate interviews

    This model manages the complete interview scheduling process, including
    timing details, participants, location information, and integration with
    external calendar systems. It supports various interview formats and
    tracks the status through the scheduling lifecycle.

    Attributes:
        id: UUID primary key
        candidate_id: Foreign key to Resume (candidate being interviewed)
        vacancy_id: Optional foreign key to JobVacancy (related position)
        scheduled_start: Interview start time with timezone
        scheduled_end: Interview end time with timezone
        duration_minutes: Duration of interview in minutes
        status: Current status of the interview
        interview_type: Format/type of interview
        title: Interview title or description
        description: Detailed agenda or notes for the interview
        location: Physical location for onsite interviews
        meeting_link: Virtual meeting link for remote interviews
        meeting_room: Meeting room name/number for onsite interviews
        recruiter_id: Foreign key to Recruiter who scheduled the interview
        calendar_event_id: Optional external calendar event ID
        calendar_provider: Provider of connected calendar (google/outlook)
        is_reminder_sent: Whether reminder notification has been sent
        created_at: Timestamp when interview was created (inherited)
        updated_at: Timestamp when interview was last updated (inherited)
    """

    __tablename__ = "interviews"

    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scheduled_start: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    scheduled_end: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus), default=InterviewStatus.SCHEDULED, nullable=False, index=True
    )
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meeting_room: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    calendar_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_reminder_sent: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Interview(id={self.id}, title={self.title}, start={self.scheduled_start}, status={self.status})>"


class ParticipantRole(str, enum.Enum):
    """Role of a participant in an interview"""

    LEAD_INTERVIEWER = "lead_interviewer"
    INTERVIEWER = "interviewer"
    NOTE_TAKER = "note_taker"
    OBSERVER = "observer"
    HIRING_MANAGER = "hiring_manager"


class ParticipantStatus(str, enum.Enum):
    """Response status of an interview participant"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class InterviewParticipant(Base, UUIDMixin, TimestampMixin):
    """
    InterviewParticipant model for managing interview participants

    This model serves as a junction table between Interview and Recruiter,
    tracking the participants invited to each interview along with their
    roles and response status. This enables multiple interviewers with
    different roles per interview and tracks their acceptance.

    Attributes:
        id: UUID primary key
        interview_id: Foreign key to Interview
        recruiter_id: Foreign key to Recruiter (the participant)
        role: The participant's role in the interview
        status: Whether the participant has accepted, declined, or is pending
        response_timestamp: When the participant last responded
        notes: Optional notes from the participant (e.g., talking points, questions)
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "interview_participants"

    interview_id: Mapped[UUID] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ParticipantRole] = mapped_column(
        Enum(ParticipantRole), default=ParticipantRole.INTERVIEWER, nullable=False
    )
    status: Mapped[ParticipantStatus] = mapped_column(
        Enum(ParticipantStatus), default=ParticipantStatus.PENDING, nullable=False, index=True
    )
    response_timestamp: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<InterviewParticipant(id={self.id}, interview={self.interview_id}, recruiter={self.recruiter_id}, role={self.role}, status={self.status})>"
