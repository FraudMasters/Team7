"""
JobApplication model for storing job seeker applications
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class ApplicationStatus(str, enum.Enum):
    """Status of a job application in the hiring pipeline"""

    # Application submission stages
    PENDING = "PENDING"           # Draft/submission in progress
    SUBMITTED = "SUBMITTED"       # Submitted to employer

    # Hiring pipeline stages
    UNDER_REVIEW = "UNDER_REVIEW"  # Being reviewed by recruiter
    REJECTED = "REJECTED"         # Application rejected
    ACCEPTED = "ACCEPTED"         # Application accepted


class JobApplication(Base, UUIDMixin, TimestampMixin):
    """
    JobApplication model for storing job applications submitted by job seekers

    Attributes:
        id: UUID primary key
        user_id: Foreign key to User (the job seeker)
        vacancy_id: Foreign key to JobVacancy (the job being applied for)
        resume_id: Foreign key to Resume (the resume submitted with application)
        email: Contact email provided at application time
        phone: Contact phone number provided at application time
        cover_letter: Cover letter text submitted by applicant
        status: Current application status
        created_at: Timestamp when application was created (inherited)
        updated_at: Timestamp when application was last updated (inherited)
    """

    __tablename__ = "job_applications"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.PENDING, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="job_applications"
    )
    vacancy: Mapped["JobVacancy"] = relationship(
        "JobVacancy",
        back_populates="applications"
    )
    resume: Mapped[Optional["Resume"]] = relationship(
        "Resume",
        back_populates="job_applications"
    )

    def __repr__(self) -> str:
        return f"<JobApplication(id={self.id}, user_id={self.user_id}, vacancy_id={self.vacancy_id}, status={self.status.value})>"
