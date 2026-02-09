"""
WorkHistory model for storing job seeker work experience
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Date
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EmploymentType(str, enum.Enum):
    """Type of employment"""

    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    FREELANCE = "FREELANCE"
    TEMPORARY = "TEMPORARY"
    OTHER = "OTHER"


class WorkHistory(Base, UUIDMixin, TimestampMixin):
    """
    WorkHistory model for storing job seeker work experience entries

    Attributes:
        id: UUID primary key
        resume_id: Resume that this work history belongs to
        company_name: Name of the company/organization
        position_title: Job title/position held
        start_date: When the position started
        end_date: When the position ended (null if current)
        description: Description of responsibilities and achievements
        location: City, state or country of work location
        employment_type: Type of employment (full-time, part-time, etc.)
        created_at: Timestamp when record was created (inherited from TimestampMixin)
        updated_at: Timestamp when record was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "work_history"

    resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[object] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False
    )

    def __repr__(self) -> str:
        return f"<WorkHistory(id={self.id}, company={self.company_name}, position={self.position_title}, start={self.start_date})>"
