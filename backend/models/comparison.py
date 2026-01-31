"""
ResumeComparison model for storing saved resume comparison views
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResumeComparison(Base, UUIDMixin, TimestampMixin):
    """
    ResumeComparison model for storing saved multi-resume comparison views

    Attributes:
        id: UUID primary key
        vacancy_id: Foreign key to JobVacancy
        resume_ids: JSON array of resume IDs being compared
        filters: JSON object with filter settings (match range, sort field, etc.)
        comparison_notes: JSON object with recruiter notes about the comparison
        created_by: User identifier who created the comparison
        shared_with: JSON array of user IDs/emails the comparison is shared with
        created_at: Timestamp when comparison was created (inherited)
        updated_at: Timestamp when comparison was last updated (inherited)
    """

    __tablename__ = "resume_comparisons"

    vacancy_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resume_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    comparison_notes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shared_with: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)

    def __repr__(self) -> str:
        return f"<ResumeComparison(id={self.id}, vacancy_id={self.vacancy_id}, resumes={len(self.resume_ids)})>"
