"""
SavedJob model for storing job seeker's saved/bookmarked jobs
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class SavedJob(Base, UUIDMixin, TimestampMixin):
    """
    SavedJob model for storing jobs that job seekers have saved/bookmarked for later

    Attributes:
        id: UUID primary key
        user_id: Foreign key to User (the job seeker who saved the job)
        vacancy_id: Foreign key to JobVacancy (the job being saved)
        created_at: Timestamp when job was saved (inherited)
        updated_at: Timestamp when saved job was last updated (inherited)
    """

    __tablename__ = "saved_jobs"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="saved_jobs"
    )
    vacancy: Mapped["JobVacancy"] = relationship(
        "JobVacancy",
        back_populates="saved_jobs"
    )

    # Unique constraint to prevent duplicate saves
    __table_args__ = (
        UniqueConstraint("user_id", "vacancy_id", name="uq_saved_jobs_user_vacancy"),
    )

    def __repr__(self) -> str:
        return f"<SavedJob(id={self.id}, user_id={self.user_id}, vacancy_id={self.vacancy_id})>"
