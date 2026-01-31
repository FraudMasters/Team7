"""
FeedbackTemplate model for customizable feedback templates
"""
from typing import Optional

from sqlalchemy import JSON, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class FeedbackTemplate(Base, UUIDMixin, TimestampMixin):
    """
    FeedbackTemplate model for customizable feedback templates

    Attributes:
        id: UUID primary key
        organization_id: ID of the organization this template belongs to
        name: Name of the template
        language: Language code (e.g., 'en', 'ru')
        tone: Tone of feedback (e.g., 'constructive', 'formal')
        sections: JSON object defining template sections
        is_default: Whether this is the default template for the organization
        is_active: Whether this template is active
        created_by: ID of the user who created this template
        created_at: Timestamp when template was created (inherited)
        updated_at: Timestamp when template was last updated (inherited)
    """

    __tablename__ = "feedback_templates"

    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    tone: Mapped[str] = mapped_column(String(50), nullable=False, server_default="constructive")
    sections: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<FeedbackTemplate(id={self.id}, name={self.name}, org={self.organization_id})>"
