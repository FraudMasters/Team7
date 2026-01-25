"""
CustomSynonym model for storing organization-specific skill synonyms
"""
from typing import Optional

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CustomSynonym(Base, UUIDMixin, TimestampMixin):
    """
    CustomSynonym model for storing organization-specific skill synonyms

    Attributes:
        id: UUID primary key
        organization_id: Foreign key or reference to organization
        canonical_skill: The canonical/standard skill name
        custom_synonyms: JSON array of organization-specific synonyms
        context: Optional context for when to use these synonyms
        created_by: User ID who created this synonym mapping
        is_active: Whether this synonym mapping is currently active
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "custom_synonyms"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    canonical_skill: Mapped[str] = mapped_column(nullable=False)
    custom_synonyms: Mapped[list] = mapped_column(JSON, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<CustomSynonym(id={self.id}, org={self.organization_id}, skill={self.canonical_skill})>"
