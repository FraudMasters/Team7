"""
EvaluationTemplate model for standardized candidate evaluation scorecards
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EvaluationTemplate(Base, UUIDMixin, TimestampMixin):
    """
    EvaluationTemplate model for standardized candidate evaluation scorecards

    This model enables organizations to create reusable evaluation templates
    with consistent criteria, rating scales, and weights. Templates can be
    organization-wide or tied to specific job vacancies. Version tracking
    allows for template evolution while preserving historical data.

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this template
        vacancy_id: Optional foreign key to JobVacancy (for role-specific templates)
        name: Human-readable name for this template
        description: Optional description of when to use this template
        version: Version number for template tracking (starts at 1)
        is_active: Whether this template is currently active
        is_default: Whether this is the default template for the organization/vacancy
        created_by: User ID who created this template
        created_at: Timestamp when template was created (inherited)
        updated_at: Timestamp when template was last updated (inherited)
    """

    __tablename__ = "evaluation_templates"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<EvaluationTemplate(id={self.id}, org={self.organization_id}, "
            f"name={self.name}, version={self.version}, is_active={self.is_active})>"
        )
