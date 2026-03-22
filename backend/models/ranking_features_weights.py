"""
RankingFeaturesWeights model for storing custom ranking feature weight configurations
"""
from typing import Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RankingFeaturesWeights(Base, UUIDMixin, TimestampMixin):
    """
    RankingFeaturesWeights model for storing custom ranking feature weight configurations

    Attributes:
        id: UUID primary key
        organization_id: Organization that owns this weight profile
        name: Human-readable name for this profile (e.g., "Technical Role Focus")
        description: Optional description of when to use this profile
        skill_match_weight: Weight for skill matching (0.0 to 1.0)
        experience_weight: Weight for experience matching (0.0 to 1.0)
        education_weight: Weight for education matching (0.0 to 1.0)
        location_weight: Weight for location matching (0.0 to 1.0)
        keyword_weight: Weight for keyword matching (0.0 to 1.0)
        tfidf_weight: Weight for TF-IDF matching (0.0 to 1.0)
        vector_weight: Weight for vector similarity matching (0.0 to 1.0)
        recency_weight: Weight for recency (0.0 to 1.0)
        culture_fit_weight: Weight for culture fit (0.0 to 1.0)
        salary_match_weight: Weight for salary matching (0.0 to 1.0)
        availability_weight: Weight for availability (0.0 to 1.0)
        certifications_weight: Weight for certifications (0.0 to 1.0)
        industry_experience_weight: Weight for industry experience (0.0 to 1.0)
        is_default: Whether this is the default profile for the organization
        is_preset: Whether this is a system preset (vs custom user-created)
        preset_type: Type of preset if applicable (technical, creative, executive, balanced)
        created_by: User ID who created this profile
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ranking_features_weights"

    organization_id: Mapped[str] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    skill_match_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.15)
    experience_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.12)
    education_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.08)
    location_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    keyword_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.10)
    tfidf_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.10)
    vector_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.10)
    recency_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.08)
    culture_fit_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.07)
    salary_match_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    availability_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.05)
    certifications_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.03)
    industry_experience_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.02)
    is_default: Mapped[bool] = mapped_column(nullable=False, default=False)
    is_preset: Mapped[bool] = mapped_column(nullable=False, default=False)
    preset_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return (
            f"<RankingFeaturesWeights(id={self.id}, org={self.organization_id}, "
            f"name={self.name}, skill={self.skill_match_weight}, "
            f"experience={self.experience_weight}, education={self.education_weight})>"
        )
