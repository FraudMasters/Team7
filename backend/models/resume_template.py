"""
ResumeTemplate model for customizable resume formatting templates
"""
from typing import Optional

from sqlalchemy import JSON, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ResumeTemplate(Base, UUIDMixin, TimestampMixin):
    """
    ResumeTemplate model for customizable resume formatting templates

    Attributes:
        id: UUID primary key
        organization_id: ID of the organization this template belongs to (None for global templates)
        name: Template name (e.g., 'Modern', 'Classic', 'Creative')
        description: Optional description of the template style
        template_type: Type of resume template (e.g., 'modern', 'classic', 'creative', 'ats_friendly')
        layout_config: JSON configuration for layout (margins, sections, spacing, etc.)
        style_config: JSON configuration for styling (colors, fonts, headings, etc.)
        section_config: JSON configuration for which sections to include and their order
        preview_url: Optional URL to a preview image of the template
        is_default: Whether this is the default template for the organization/global
        is_active: Whether this template is active and available for use
        is_ats_compliant: Whether this template is ATS-friendly (optimized for applicant tracking systems)
        created_by: ID of the user who created this template
        created_at: Timestamp when template was created (inherited)
        updated_at: Timestamp when template was last updated (inherited)
    """

    __tablename__ = "resume_templates"

    organization_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    layout_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    style_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    section_config: Mapped[dict] = mapped_column(JSON, nullable=True)
    preview_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_ats_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<ResumeTemplate(id={self.id}, name={self.name}, type={self.template_type})>"
