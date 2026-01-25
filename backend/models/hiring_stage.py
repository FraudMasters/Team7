"""
HiringStage model for tracking resume progression through hiring pipeline
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class HiringStageName(str, enum.Enum):
    """Hiring pipeline stages"""

    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class HiringStage(Base, UUIDMixin, TimestampMixin):
    """
    HiringStage model for tracking resume progression through hiring pipeline

    This model enables funnel analytics and time-to-hire metrics by recording
    each stage a resume progresses through in the hiring process.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        vacancy_id: Optional foreign key to JobVacancy
        stage_name: Current hiring stage
        notes: Optional notes about this stage transition
        created_at: Timestamp when stage record was created (inherited)
        updated_at: Timestamp when stage record was last updated (inherited)
    """

    __tablename__ = "hiring_stages"

    resume_id: Mapped[UUIDMixin] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUIDMixin]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    stage_name: Mapped[HiringStageName] = mapped_column(
        Enum(HiringStageName), default=HiringStageName.APPLIED, nullable=False, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<HiringStage(id={self.id}, resume_id={self.resume_id}, stage={self.stage_name})>"
