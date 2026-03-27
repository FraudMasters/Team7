"""
Ranking weight profile model.

This model stores custom weight configurations for the ranking algorithm,
allowing organizations to customize the relative importance of different ranking
features such as skills match, experience, education, and other factors.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDMixin

logger = logging.getLogger(__name__)


class RankingWeightProfile(Base, UUIDMixin, TimestampMixin):
    """
    Custom weight profile for candidate ranking algorithm.

    Stores weight configurations for the 13 ranking features:
    - Overall match score (composite matching score)
    - Keyword score (keyword-based matching)
    - TF-IDF score (term frequency-inverse document frequency)
    - Vector score (semantic similarity)
    - Skills match ratio (percentage of required skills matched)
    - Experience months (total work experience duration)
    - Experience relevance (relevance of past experience)
    - Education level (highest degree attained)
    - Recent experience (recency of relevant work)
    - Skill rarity (scarcity of candidate's skills)
    - Title similarity (job title alignment)
    - Freshness score (profile/resume recency)
    - Completeness score (profile completeness)

    Profiles can be:
    - System presets (is_preset=True, organization_id=None)
    - Organization-specific (is_preset=False, organization_id set)
    - Vacancy-specific (is_preset=False, vacancy_id set)
    """

    __tablename__ = "ranking_weight_profiles"

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
        comment="True for system presets (Technical, Sales, Executive, Balanced)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether this profile is active"
    )

    preset_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of preset profile (technical, sales, executive, balanced)"
    )

    # Ranking feature weights (should sum to 1.0)
    overall_match_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.15,
        comment="Weight for overall composite match score (0.0-1.0)"
    )

    keyword_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.10,
        comment="Weight for keyword-based matching score (0.0-1.0)"
    )

    tfidf_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.08,
        comment="Weight for TF-IDF matching score (0.0-1.0)"
    )

    vector_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.07,
        comment="Weight for vector similarity score (0.0-1.0)"
    )

    skills_match_ratio_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.20,
        comment="Weight for skills match ratio (0.0-1.0)"
    )

    experience_months_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.08,
        comment="Weight for total experience duration (0.0-1.0)"
    )

    experience_relevance_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.10,
        comment="Weight for experience relevance (0.0-1.0)"
    )

    education_level_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.06,
        comment="Weight for education level (0.0-1.0)"
    )

    recent_experience_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.05,
        comment="Weight for recent experience (0.0-1.0)"
    )

    skill_rarity_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.04,
        comment="Weight for skill rarity/uniqueness (0.0-1.0)"
    )

    title_similarity_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.04,
        comment="Weight for job title similarity (0.0-1.0)"
    )

    freshness_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.02,
        comment="Weight for profile/resume freshness (0.0-1.0)"
    )

    completeness_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.01,
        comment="Weight for profile completeness (0.0-1.0)"
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
        back_populates="ranking_weight_profiles"
    )

    # Version history relationship
    version_history: Mapped[list["RankingWeightVersion"]] = relationship(
        "RankingWeightVersion",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(RankingWeightVersion.created_at)"
    )

    # Unique constraints
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_ranking_weight_profile_org_name",
        ),
        UniqueConstraint(
            "vacancy_id",
            name="uq_ranking_weight_profile_vacancy",
        ),
        # Add check constraint that weights sum to approximately 1.0
        # Note: Check constraints will be added in migration
    )

    def __repr__(self) -> str:
        return (
            f"<RankingWeightProfile(id={self.id}, name='{self.name}', "
            f"skills_match={self.skills_match_ratio_weight}, "
            f"overall_match={self.overall_match_score_weight})>"
        )

    def validate_weights(self) -> bool:
        """
        Validate that weights sum to approximately 1.0 (with small tolerance).

        Returns:
            True if weights are valid
        """
        total = (
            self.overall_match_score_weight +
            self.keyword_score_weight +
            self.tfidf_score_weight +
            self.vector_score_weight +
            self.skills_match_ratio_weight +
            self.experience_months_weight +
            self.experience_relevance_weight +
            self.education_level_weight +
            self.recent_experience_weight +
            self.skill_rarity_weight +
            self.title_similarity_weight +
            self.freshness_score_weight +
            self.completeness_score_weight
        )
        return abs(total - 1.0) < 0.01

    def normalize_weights(self) -> None:
        """
        Normalize weights so they sum to 1.0.

        Modifies the instance in place.
        """
        total = (
            self.overall_match_score_weight +
            self.keyword_score_weight +
            self.tfidf_score_weight +
            self.vector_score_weight +
            self.skills_match_ratio_weight +
            self.experience_months_weight +
            self.experience_relevance_weight +
            self.education_level_weight +
            self.recent_experience_weight +
            self.skill_rarity_weight +
            self.title_similarity_weight +
            self.freshness_score_weight +
            self.completeness_score_weight
        )
        if total > 0:
            self.overall_match_score_weight = round(self.overall_match_score_weight / total, 3)
            self.keyword_score_weight = round(self.keyword_score_weight / total, 3)
            self.tfidf_score_weight = round(self.tfidf_score_weight / total, 3)
            self.vector_score_weight = round(self.vector_score_weight / total, 3)
            self.skills_match_ratio_weight = round(self.skills_match_ratio_weight / total, 3)
            self.experience_months_weight = round(self.experience_months_weight / total, 3)
            self.experience_relevance_weight = round(self.experience_relevance_weight / total, 3)
            self.education_level_weight = round(self.education_level_weight / total, 3)
            self.recent_experience_weight = round(self.recent_experience_weight / total, 3)
            self.skill_rarity_weight = round(self.skill_rarity_weight / total, 3)
            self.title_similarity_weight = round(self.title_similarity_weight / total, 3)
            self.freshness_score_weight = round(self.freshness_score_weight / total, 3)
            self.completeness_score_weight = round(self.completeness_score_weight / total, 3)

    def get_weights_as_dict(self) -> dict[str, float]:
        """
        Get weights as a dictionary.

        Returns:
            Dictionary with all 13 feature weights
        """
        return {
            "overall_match_score_weight": self.overall_match_score_weight,
            "keyword_score_weight": self.keyword_score_weight,
            "tfidf_score_weight": self.tfidf_score_weight,
            "vector_score_weight": self.vector_score_weight,
            "skills_match_ratio_weight": self.skills_match_ratio_weight,
            "experience_months_weight": self.experience_months_weight,
            "experience_relevance_weight": self.experience_relevance_weight,
            "education_level_weight": self.education_level_weight,
            "recent_experience_weight": self.recent_experience_weight,
            "skill_rarity_weight": self.skill_rarity_weight,
            "title_similarity_weight": self.title_similarity_weight,
            "freshness_score_weight": self.freshness_score_weight,
            "completeness_score_weight": self.completeness_score_weight,
        }

    def get_weights_as_list(self) -> list[float]:
        """
        Get weights as an ordered list (useful for ML feature vectors).

        Returns:
            List of 13 weights in order
        """
        return [
            self.overall_match_score_weight,
            self.keyword_score_weight,
            self.tfidf_score_weight,
            self.vector_score_weight,
            self.skills_match_ratio_weight,
            self.experience_months_weight,
            self.experience_relevance_weight,
            self.education_level_weight,
            self.recent_experience_weight,
            self.skill_rarity_weight,
            self.title_similarity_weight,
            self.freshness_score_weight,
            self.completeness_score_weight,
        ]

    @classmethod
    def get_feature_names(cls) -> list[str]:
        """
        Get the names of all ranking features in order.

        Returns:
            List of 13 feature names
        """
        return [
            "overall_match_score",
            "keyword_score",
            "tfidf_score",
            "vector_score",
            "skills_match_ratio",
            "experience_months",
            "experience_relevance",
            "education_level",
            "recent_experience",
            "skill_rarity",
            "title_similarity",
            "freshness_score",
            "completeness_score",
        ]


# Preset ranking weight profiles
PRESET_PROFILES = {
    "balanced": {
        "name": "Balanced",
        "description": "Equal consideration of all ranking factors for general-purpose hiring",
        "overall_match_score_weight": 0.077,
        "keyword_score_weight": 0.077,
        "tfidf_score_weight": 0.077,
        "vector_score_weight": 0.077,
        "skills_match_ratio_weight": 0.077,
        "experience_months_weight": 0.077,
        "experience_relevance_weight": 0.077,
        "education_level_weight": 0.077,
        "recent_experience_weight": 0.077,
        "skill_rarity_weight": 0.077,
        "title_similarity_weight": 0.077,
        "freshness_score_weight": 0.077,
        "completeness_score_weight": 0.076,
    },
    "technical": {
        "name": "Technical",
        "description": "Optimized for technical roles - prioritizes skills match, keyword matching, and education",
        "overall_match_score_weight": 0.15,
        "keyword_score_weight": 0.15,
        "tfidf_score_weight": 0.10,
        "vector_score_weight": 0.08,
        "skills_match_ratio_weight": 0.25,
        "experience_months_weight": 0.05,
        "experience_relevance_weight": 0.10,
        "education_level_weight": 0.08,
        "recent_experience_weight": 0.02,
        "skill_rarity_weight": 0.01,
        "title_similarity_weight": 0.01,
        "freshness_score_weight": 0.00,
        "completeness_score_weight": 0.00,
    },
    "sales": {
        "name": "Sales",
        "description": "Optimized for sales roles - prioritizes title similarity, experience relevance, and recent activity",
        "overall_match_score_weight": 0.12,
        "keyword_score_weight": 0.08,
        "tfidf_score_weight": 0.06,
        "vector_score_weight": 0.05,
        "skills_match_ratio_weight": 0.10,
        "experience_months_weight": 0.12,
        "experience_relevance_weight": 0.20,
        "education_level_weight": 0.05,
        "recent_experience_weight": 0.10,
        "skill_rarity_weight": 0.02,
        "title_similarity_weight": 0.08,
        "freshness_score_weight": 0.01,
        "completeness_score_weight": 0.01,
    },
    "executive": {
        "name": "Executive",
        "description": "Optimized for executive/leadership roles - prioritizes experience, education, and title similarity",
        "overall_match_score_weight": 0.10,
        "keyword_score_weight": 0.05,
        "tfidf_score_weight": 0.05,
        "vector_score_weight": 0.05,
        "skills_match_ratio_weight": 0.08,
        "experience_months_weight": 0.20,
        "experience_relevance_weight": 0.22,
        "education_level_weight": 0.12,
        "recent_experience_weight": 0.05,
        "skill_rarity_weight": 0.01,
        "title_similarity_weight": 0.06,
        "freshness_score_weight": 0.00,
        "completeness_score_weight": 0.01,
    },
}


def create_preset_profiles(session) -> list[RankingWeightProfile]:
    """
    Create system preset ranking weight profiles.

    Args:
        session: SQLAlchemy session

    Returns:
        List of created preset profiles
    """
    profiles = []

    for preset_key, preset_data in PRESET_PROFILES.items():
        profile = RankingWeightProfile(
            name=preset_data["name"],
            description=preset_data["description"],
            is_preset=True,
            is_active=True,
            overall_match_score_weight=preset_data["overall_match_score_weight"],
            keyword_score_weight=preset_data["keyword_score_weight"],
            tfidf_score_weight=preset_data["tfidf_score_weight"],
            vector_score_weight=preset_data["vector_score_weight"],
            skills_match_ratio_weight=preset_data["skills_match_ratio_weight"],
            experience_months_weight=preset_data["experience_months_weight"],
            experience_relevance_weight=preset_data["experience_relevance_weight"],
            education_level_weight=preset_data["education_level_weight"],
            recent_experience_weight=preset_data["recent_experience_weight"],
            skill_rarity_weight=preset_data["skill_rarity_weight"],
            title_similarity_weight=preset_data["title_similarity_weight"],
            freshness_score_weight=preset_data["freshness_score_weight"],
            completeness_score_weight=preset_data["completeness_score_weight"],
        )
        session.add(profile)
        profiles.append(profile)
        logger.info(f"Created preset ranking weight profile: {profile.name}")

    session.commit()
    return profiles
