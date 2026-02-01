"""
MatchingWeightsProfile model for storing custom matching algorithm weight configurations
"""
from typing import Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class MatchingWeightsProfile(Base, UUIDMixin, TimestampMixin):
    """
    MatchingWeightsProfile model for storing custom matching algorithm weight configurations

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this weight profile
        name: Human-readable name for this profile (e.g., "Technical Role Focus")
        description: Optional description of when to use this profile
        keyword_weight: Weight for keyword matching (0.0 to 1.0)
        tfidf_weight: Weight for TF-IDF matching (0.0 to 1.0)
        vector_weight: Weight for vector similarity matching (0.0 to 1.0)
        is_default: Whether this is the default profile for the organization
        is_preset: Whether this is a system preset (vs custom user-created)
        preset_type: Type of preset if applicable (technical, creative, executive, balanced)
        created_by: User ID who created this profile
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "matching_weights_profiles"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    keyword_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    tfidf_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    vector_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_preset: Mapped[bool] = mapped_column(nullable=False, default=False)
    preset_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<MatchingWeightsProfile(id={self.id}, org={self.organization_id}, "
            f"name={self.name}, keyword={self.keyword_weight}, "
            f"tfidf={self.tfidf_weight}, vector={self.vector_weight})>"
        )
