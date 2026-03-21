"""
PipelineStageTransition model for tracking candidate movement through hiring stages
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class PipelineStage(str, enum.Enum):
    """Pipeline stages that candidates can be in"""

    NEW = "NEW"                      # Initial application received
    SCREENING = "SCREENING"          # Resume/application screening
    PHONE_SCREEN = "PHONE_SCREEN"    # Phone screening interview
    INTERVIEW = "INTERVIEW"          # In-person/video interview
    TECHNICAL = "TECHNICAL"          # Technical assessment
    BACKGROUND_CHECK = "BACKGROUND_CHECK"  # Background check in progress
    OFFER = "OFFER"                  # Offer extended
    ACCEPTED = "ACCEPTED"            # Offer accepted
    HIRED = "HIRED"                  # Candidate hired
    REJECTED = "REJECTED"            # Candidate rejected
    WITHDRAWN = "WITHDRAWN"          # Candidate withdrew


class TransitionReason(str, enum.Enum):
    """Reasons for stage transitions"""

    AUTOMATIC = "AUTOMATIC"          # Automatic system transition
    MANUAL = "MANUAL"                # Manual recruiter action
    QUALIFIED = "QUALIFIED"          # Candidate qualified for next stage
    NOT_QUALIFIED = "NOT_QUALIFIED"  # Candidate did not qualify
    WITHDREW = "WITHDREW"            # Candidate withdrew
    NO_RESPONSE = "NO_RESPONSE"      # Candidate did not respond
    POSITION_FILLED = "POSITION_FILLED"  # Position was filled by another candidate
    BUDGET_CUT = "BUDGET_CUT"        # Position budget cut
    OTHER = "OTHER"                  # Other reason


class PipelineStageTransition(Base, UUIDMixin, TimestampMixin):
    """
    PipelineStageTransition model for tracking candidate movement through hiring stages

    This model enables time-to-hire analytics and funnel conversion rate calculations
    by recording each transition a candidate makes through the hiring pipeline. It tracks
    the duration in each stage, reasons for transitions, and who initiated the move.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Foreign key to JobVacancy
        from_stage: Previous pipeline stage (null for initial application)
        to_stage: New pipeline stage
        transition_reason: Reason for the stage transition
        recruiter_id: Optional foreign key to Recruiter who performed the transition
        duration_hours: Hours spent in the from_stage (null for initial transition)
        transition_date: Timestamp when the transition occurred
        notes: Optional notes about the transition
        automated: Whether this was an automated transition
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "pipeline_stage_transitions"

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_stage: Mapped[Optional[PipelineStage]] = mapped_column(
        Enum(PipelineStage), nullable=True, index=True
    )
    to_stage: Mapped[PipelineStage] = mapped_column(
        Enum(PipelineStage), nullable=False, index=True
    )
    transition_reason: Mapped[TransitionReason] = mapped_column(
        Enum(TransitionReason), default=TransitionReason.MANUAL, nullable=False
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    duration_hours: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Duration in the from_stage
    transition_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    automated: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    resume: Mapped["Resume"] = relationship(
        "Resume",
        back_populates="stage_transitions",
        foreign_keys=[resume_id]
    )
    vacancy: Mapped[Optional["JobVacancy"]] = relationship(
        "JobVacancy",
        back_populates="stage_transitions",
        foreign_keys=[vacancy_id]
    )
    recruiter: Mapped[Optional["Recruiter"]] = relationship(
        "Recruiter",
        back_populates="stage_transitions",
        foreign_keys=[recruiter_id]
    )

    def __repr__(self) -> str:
        return f"<PipelineStageTransition(id={self.id}, resume={self.resume_id}, {self.from_stage} -> {self.to_stage})>"
