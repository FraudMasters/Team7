"""
BuiltResume model for storing resume builder data
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class BuiltResume(Base, UUIDMixin, TimestampMixin):
    """
    BuiltResume model for storing resume builder data

    This model stores resumes created by job seekers using the resume builder
    feature. It contains structured content that can be rendered using templates.

    Attributes:
        id: UUID primary key
        user_id: User that owns this resume
        organization_id: Organization that this resume belongs to
        template_id: Template to use for rendering this resume
        title: Name/title of this resume
        content: JSON structure containing all resume sections
            (personal_info, summary, work_experience, education, skills, etc.)
        target_job_id: Optional job vacancy ID for skill gap analysis
        ats_score: Current ATS optimization score (0-100)
        version: Version number of this resume
        is_draft: Whether this is a draft or published resume
        last_ai_suggestions: JSON field storing recent AI improvement suggestions
        created_at: Timestamp when resume was created (inherited from TimestampMixin)
        updated_at: Timestamp when resume was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "built_resumes"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    target_job_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ats_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<BuiltResume(id={self.id}, user_id={self.user_id}, title={self.title}, version={self.version})>"
