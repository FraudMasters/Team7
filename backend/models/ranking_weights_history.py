"""
Ranking weight version history model.

This model stores version snapshots of ranking weight profiles for audit
and history tracking purposes.
"""
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class RankingWeightVersion(Base, UUIDMixin, TimestampMixin):
    """
    Version history for ranking weight profiles.

    Tracks all changes to ranking weight profiles for audit purposes.
    Each version represents a snapshot of the profile's weights at a point in time.

    Attributes:
        id: UUID primary key
        profile_id: UUID of the profile being versioned
        overall_match_score_weight: Overall match score weight at this version
        keyword_score_weight: Keyword score weight at this version
        tfidf_score_weight: TF-IDF score weight at this version
        vector_score_weight: Vector score weight at this version
        skills_match_ratio_weight: Skills match ratio weight at this version
        experience_months_weight: Experience months weight at this version
        experience_relevance_weight: Experience relevance weight at this version
        education_level_weight: Education level weight at this version
        recent_experience_weight: Recent experience weight at this version
        skill_rarity_weight: Skill rarity weight at this version
        title_similarity_weight: Title similarity weight at this version
        freshness_score_weight: Freshness score weight at this version
        completeness_score_weight: Completeness score weight at this version
        changed_by: User ID who made the change
        version: Version identifier (e.g., 'v1.0', 'v1.1')
        change_reason: Reason for this change
        created_at: Timestamp when the version was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "ranking_weight_versions"

    profile_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ranking_weight_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the weight profile"
    )

    # Snapshot of weights at this version (13 ranking features)
    overall_match_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Overall match score weight at this version"
    )

    keyword_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Keyword score weight at this version"
    )

    tfidf_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="TF-IDF score weight at this version"
    )

    vector_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Vector score weight at this version"
    )

    skills_match_ratio_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Skills match ratio weight at this version"
    )

    experience_months_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Experience months weight at this version"
    )

    experience_relevance_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Experience relevance weight at this version"
    )

    education_level_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Education level weight at this version"
    )

    recent_experience_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Recent experience weight at this version"
    )

    skill_rarity_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Skill rarity weight at this version"
    )

    title_similarity_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Title similarity weight at this version"
    )

    freshness_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Freshness score weight at this version"
    )

    completeness_score_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Completeness score weight at this version"
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
    profile: Mapped["RankingWeightProfile"] = relationship(
        "RankingWeightProfile",
        back_populates="version_history"
    )

    def __repr__(self) -> str:
        return (
            f"<RankingWeightVersion(id={self.id}, profile_id={self.profile_id}, "
            f"version='{self.version}')>"
        )
