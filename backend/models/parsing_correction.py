"""
ParsingCorrection model for tracking user corrections to parsed resume data

This table stores user corrections to AI-parsed resume fields, enabling:
- Tracking of parsing accuracy
- Learning from corrections to improve future parsing
- Audit trail of data modifications
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ParsingCorrection(Base, UUIDMixin, TimestampMixin):
    """
    ParsingCorrection model for tracking user corrections to parsed fields

    This table stores user-made corrections to AI-parsed resume data,
    creating an audit trail and enabling parser improvement through
    learning from corrections.

    Attributes:
        id: UUID primary key
        resume_id: Foreign key to Resume
        field_name: Name of the corrected field (e.g., "position", "skills", "work_experience")
        original_value: The AI-parsed value before correction (JSON for complex fields)
        corrected_value: The user's corrected value (JSON for complex fields)
        reason: Optional reason for the correction (e.g., "position_was_incorrect", "missing_skill")
        source_text_location: Optional location in source document that was used for parsing
        corrected_by: Optional ID of user who made the correction
    """

    __tablename__ = "parsing_corrections"

    # Reference to resume
    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Field identification
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Values (JSON for flexibility with complex fields like skills, work_experience)
    original_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    corrected_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Correction metadata
    reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_text_location: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Who made the correction (optional, for audit purposes)
    corrected_by: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ParsingCorrection(id={self.id}, resume_id={self.resume_id}, field={self.field_name})>"
