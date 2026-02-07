"""
CommunicationTemplate model for customizable communication templates
"""
from typing import Optional

from sqlalchemy import JSON, String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CommunicationTemplate(Base, UUIDMixin, TimestampMixin):
    """
    CommunicationTemplate model for customizable communication templates

    Attributes:
        id: UUID primary key
        organization_id: ID of the organization this template belongs to
        name: Name of the template
        type: Type of communication (e.g., 'email', 'sms', 'phone')
        subject: Subject line (for emails)
        body: Body content of the communication
        variables: JSON object defining template variables
        is_active: Whether this template is active
        language: Language code (e.g., 'en', 'ru')
        created_by: ID of the user who created this template
        created_at: Timestamp when template was created (inherited)
        updated_at: Timestamp when template was last updated (inherited)
    """

    __tablename__ = "communication_templates"

    organization_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    language: Mapped[str] = mapped_column(String(10), nullable=False, server_default="en")
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<CommunicationTemplate(id={self.id}, name={self.name}, type={self.type}, org={self.organization_id})>"
