"""
EmailTemplate model for customizable email templates with organization branding
"""
from typing import Optional

from sqlalchemy import JSON, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EmailTemplate(Base, UUIDMixin, TimestampMixin):
    """
    EmailTemplate model for customizable email templates with organization branding

    Attributes:
        id: UUID primary key
        organization_id: ID of the organization this template belongs to
        template_type: Type of email template (e.g., 'candidate_feedback', 'batch_notification')
        subject: Email subject line with template variables (e.g., '{{candidate_name}} Feedback')
        body: Email body content with template variables
        is_default: Whether this is the default template for this type in the organization
        is_active: Whether this template is active
        created_by: ID of the user who created this template
        created_at: Timestamp when template was created (inherited)
        updated_at: Timestamp when template was last updated (inherited)
    """

    __tablename__ = "email_templates"

    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<EmailTemplate(id={self.id}, type={self.template_type}, org={self.organization_id})>"
