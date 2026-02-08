"""
OrganizationExplanationPreferences model for explanation tone and style customization
"""
from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class OrganizationExplanationPreferences(Base, UUIDMixin, TimestampMixin):
    """
    OrganizationExplanationPreferences model for customizing AI-generated explanations

    This model enables organizations to customize the tone, style, and detail level
    of natural language explanations generated for candidate rankings. Each organization
    can configure their preferred communication style and what details to include.

    Attributes:
        id: UUID primary key
        organization_id: String identifier for the organization
        tone: Preferred explanation tone (professional, casual, friendly, formal)
        style: Preferred explanation style (detailed, concise, balanced)
        detail_level: Level of detail (high, medium, low)
        include_percentiles: Whether to include percentile-based comparisons
        include_skill_names: Whether to include specific skill names in explanations
        include_experience_details: Whether to include experience duration details
        include_education_details: Whether to include education details
        language: Preferred language for explanations (e.g., en, es, fr)
        custom_prompt_template: Optional custom prompt template for LLM explanations
        is_active: Whether these preferences are currently active
        created_by: User who created these preferences
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "organization_explanation_preferences"

    # Organization reference
    organization_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    # Tone and style settings
    tone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="professional",
        comment="Preferred explanation tone: professional, casual, friendly, formal"
    )
    style: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="balanced",
        comment="Preferred explanation style: detailed, concise, balanced"
    )
    detail_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="medium",
        comment="Level of detail: high, medium, low"
    )

    # Content inclusion flags
    include_percentiles: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to include percentile-based comparisons"
    )
    include_skill_names: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to include specific skill names in explanations"
    )
    include_experience_details: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to include experience duration details"
    )
    include_education_details: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to include education details"
    )

    # Language and customization
    language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Preferred language for explanations (e.g., en, es, fr)"
    )
    custom_prompt_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional custom prompt template for LLM explanations"
    )

    # Status and tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User who created these preferences"
    )

    def __repr__(self) -> str:
        return (
            f"<OrganizationExplanationPreferences("
            f"id={self.id}, "
            f"organization_id={self.organization_id}, "
            f"tone={self.tone}, "
            f"style={self.style}, "
            f"is_active={self.is_active})>"
        )
