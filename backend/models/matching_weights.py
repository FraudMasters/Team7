"""
Matching weight profile model.

This model stores custom weight configurations for the unified matching algorithm,
allowing organizations to customize the relative importance of Keyword, TF-IDF,
and Vector similarity matching methods.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

logger = logging.getLogger(__name__)


class MatchingWeightProfile(Base, UUIDMixin, TimestampMixin):
    """
    Custom weight profile for unified matching algorithm.

    Stores weight configurations for the three matching methods:
    - Keyword matching (direct, synonym, fuzzy matching)
    - TF-IDF matching (importance-based scoring)
    - Vector matching (semantic similarity)

    Profiles can be:
    - System presets (is_preset=True, organization_id=None)
    - Organization-specific (is_preset=False, organization_id set)
    - Vacancy-specific (is_preset=False, vacancy_id set)
    """

    __tablename__ = "matching_weight_profiles"

    # Profile metadata
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Human-readable name for this profile"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Description of when to use this profile"
    )

    # Organization/Scope
    organization_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Organization ID for custom profiles (null for presets)"
    )

    vacancy_id: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("job_vacancies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Vacancy ID for vacancy-specific profiles (null for general)"
    )

    # Profile flags
    is_preset: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True for system presets (Technical, Creative, Executive)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this profile is active"
    )

    # Matching weights (should sum to 1.0)
    keyword_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="Weight for keyword matching (0.0-1.0)"
    )

    tfidf_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.3,
        comment="Weight for TF-IDF matching (0.0-1.0)"
    )

    vector_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.2,
        comment="Weight for vector similarity matching (0.0-1.0)"
    )

    # Tracking
    created_by: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User ID who created this profile"
    )

    updated_by: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User ID who last updated this profile"
    )

    # Audit metadata
    version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Version tracking for weight changes"
    )

    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for the last weight change"
    )

    # Relationships
    vacancy: Mapped[Optional["JobVacancy"]] = relationship(
        "JobVacancy",
        back_populates="weight_profiles"
    )

    # Version history relationship
    version_history: Mapped[list["MatchingWeightVersion"]] = relationship(
        "MatchingWeightVersion",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(MatchingWeightVersion.created_at)"
    )

    # Unique constraints
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_matching_weight_profile_org_name",
        ),
        UniqueConstraint(
            "vacancy_id",
            name="uq_matching_weight_profile_vacancy",
        ),
        # Add check constraint that weights sum to approximately 1.0
        # Note: Check constraints will be added in migration
    )

    def __repr__(self) -> str:
        return (
            f"<MatchingWeightProfile(id={self.id}, name='{self.name}', "
            f"keyword={self.keyword_weight}, tfidf={self.tfidf_weight}, "
            f"vector={self.vector_weight})>"
        )

    def validate_weights(self) -> bool:
        """
        Validate that weights sum to approximately 1.0 (with small tolerance).

        Returns:
            True if weights are valid
        """
        total = self.keyword_weight + self.tfidf_weight + self.vector_weight
        return abs(total - 1.0) < 0.01

    def normalize_weights(self) -> None:
        """
        Normalize weights so they sum to 1.0.

        Modifies the instance in place.
        """
        total = self.keyword_weight + self.tfidf_weight + self.vector_weight
        if total > 0:
            self.keyword_weight = round(self.keyword_weight / total, 3)
            self.tfidf_weight = round(self.tfidf_weight / total, 3)
            self.vector_weight = round(self.vector_weight / total, 3)

    def get_weights_as_dict(self) -> dict[str, float]:
        """
        Get weights as a dictionary.

        Returns:
            Dictionary with keyword_weight, tfidf_weight, vector_weight
        """
        return {
            "keyword_weight": self.keyword_weight,
            "tfidf_weight": self.tfidf_weight,
            "vector_weight": self.vector_weight,
        }

    def get_weights_as_percentage(self) -> dict[str, int]:
        """
        Get weights as percentages (0-100).

        Returns:
            Dictionary with keyword, tfidf, vector as percentages
        """
        return {
            "keyword": round(self.keyword_weight * 100),
            "tfidf": round(self.tfidf_weight * 100),
            "vector": round(self.vector_weight * 100),
        }


class MatchingWeightVersion(Base, UUIDMixin, TimestampMixin):
    """
    Version history for matching weight profiles.

    Tracks all changes to weight profiles for audit purposes.
    """

    __tablename__ = "matching_weight_versions"

    profile_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("matching_weight_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the weight profile"
    )

    # Snapshot of weights at this version
    keyword_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Keyword weight at this version"
    )

    tfidf_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="TF-IDF weight at this version"
    )

    vector_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Vector weight at this version"
    )

    # Change tracking
    changed_by: Mapped[Optional[str]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="User who made the change"
    )

    version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Version identifier (e.g., 'v1.0', 'v1.1')"
    )

    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for this change"
    )

    # Relationships
    profile: Mapped["MatchingWeightProfile"] = relationship(
        "MatchingWeightProfile",
        back_populates="version_history"
    )

    def __repr__(self) -> str:
        return (
            f"<MatchingWeightVersion(id={self.id}, profile_id={self.profile_id}, "
            f"version='{self.version}')>"
        )


# Preset profiles definitions
PRESET_PROFILES = [
    {
        "name": "Technical",
        "description": "Keyword-heavy matching for technical roles requiring exact skill matching",
        "keyword_weight": 0.60,
        "tfidf_weight": 0.25,
        "vector_weight": 0.15,
    },
    {
        "name": "Creative",
        "description": "Vector-heavy matching for creative roles requiring conceptual understanding",
        "keyword_weight": 0.20,
        "tfidf_weight": 0.25,
        "vector_weight": 0.55,
    },
    {
        "name": "Executive",
        "description": "Balanced matching for executive roles requiring comprehensive evaluation",
        "keyword_weight": 0.33,
        "tfidf_weight": 0.34,
        "vector_weight": 0.33,
    },
    {
        "name": "Balanced",
        "description": "Even distribution across all matching methods",
        "keyword_weight": 0.34,
        "tfidf_weight": 0.33,
        "vector_weight": 0.33,
    },
]


def create_preset_profiles() -> list[MatchingWeightProfile]:
    """
    Create preset weight profiles.

    Returns:
        List of preset MatchingWeightProfile instances
    """
    profiles = []
    for preset in PRESET_PROFILES:
        profile = MatchingWeightProfile(
            name=preset["name"],
            description=preset["description"],
            keyword_weight=preset["keyword_weight"],
            tfidf_weight=preset["tfidf_weight"],
            vector_weight=preset["vector_weight"],
            is_preset=True,
            is_active=True,
            version="v1.0",
        )
        profiles.append(profile)
    return profiles
