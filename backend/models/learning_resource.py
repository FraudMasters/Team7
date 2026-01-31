"""
LearningResource model for storing courses, certifications, and training materials
"""
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class LearningResource(Base, UUIDMixin, TimestampMixin):
    """
    LearningResource model for storing courses, certifications, and training materials

    This model stores learning resources that can be recommended to candidates
    to bridge skill gaps. Resources can be courses, certifications, tutorials,
    documentation, or other learning materials.

    Attributes:
        id: UUID primary key
        skill_gap_report_id: Foreign key to SkillGapReport (optional, for linked resources)

        # Basic information
        title: Title of the learning resource
        description: Detailed description of the resource
        resource_type: Type of resource (course, certification, tutorial, documentation, video, article, book)
        source_platform: Platform offering the resource (Coursera, Udemy, edX, YouTube, etc.)

        # Resource content
        skills_taught: JSON array of skills that this resource teaches
        skill_level: Level of difficulty (beginner, intermediate, advanced, expert)
        topics_covered: JSON array of topics covered in the resource
        prerequisites: JSON array of skills/topics required before starting
        learning_objectives: JSON array of learning objectives

        # Access information
        url: URL to access the resource
        access_type: Type of access (free, freemium, paid, subscription)
        cost_amount: Cost in USD (null for free resources)
        currency: Currency code (default: USD)

        # Time investment
        duration_hours: Estimated duration in hours
        duration_weeks: Estimated duration in weeks (if part-time)
        is_self_paced: Whether the resource is self-paced

        # Quality metrics
        rating: Average rating (0-5)
        rating_count: Number of ratings
        review_count: Number of reviews
        popularity_score: Calculated popularity score based on enrollments, ratings, etc.
        quality_score: Calculated quality score (0-1)

        # Provider information
        provider_name: Name of the institution/organization providing the resource
        instructor_name: Name of the instructor (if applicable)
        certificate_offered: Whether completion certificate is offered
        certificate_url: URL to sample certificate (if applicable)

        # Additional metadata
        language: Language of the resource (default: en)
        is_active: Whether this resource is currently active/recommended
        is_verified: Whether this resource has been verified by the system
        external_id: External identifier from the source platform
        resource_metadata: JSON object for additional resource-specific data

        # Usage tracking
        recommendation_count: Number of times this resource has been recommended
        click_count: Number of times this resource has been clicked
        enrollment_count: Number of enrollments (if tracked)
        completion_rate: Average completion rate (0-1)
        last_recommended_at: Timestamp when this resource was last recommended

        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "learning_resources"

    skill_gap_report_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_gap_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Basic information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # course, certification, tutorial, documentation, video, article, book
    source_platform: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True
    )  # Coursera, Udemy, edX, YouTube, etc.

    # Resource content
    skills_taught: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    skill_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # beginner, intermediate, advanced, expert
    topics_covered: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    prerequisites: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Access information
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    access_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )  # free, freemium, paid, subscription
    cost_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2), nullable=True, default=None
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Time investment
    duration_hours: Mapped[Optional[float]] = mapped_column(
        Numeric(8, 2), nullable=True, default=None
    )
    duration_weeks: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 2), nullable=True, default=None
    )
    is_self_paced: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Quality metrics
    rating: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True, default=None
    )  # 0-5
    rating_count: Mapped[int] = mapped_column(nullable=False, default=0)
    review_count: Mapped[int] = mapped_column(nullable=False, default=0)
    popularity_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )  # 0-1
    quality_score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )  # 0-1

    # Provider information
    provider_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    instructor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    certificate_offered: Mapped[bool] = mapped_column(nullable=False, default=False)
    certificate_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Additional metadata
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)
    external_id: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, index=True
    )
    resource_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Usage tracking
    recommendation_count: Mapped[int] = mapped_column(nullable=False, default=0)
    click_count: Mapped[int] = mapped_column(nullable=False, default=0)
    enrollment_count: Mapped[int] = mapped_column(nullable=False, default=0)
    completion_rate: Mapped[Optional[float]] = mapped_column(
        Numeric(4, 3), nullable=True, default=None
    )  # 0-1
    last_recommended_at: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<LearningResource(id={self.id}, title='{self.title}', "
            f"type={self.resource_type}, platform={self.source_platform})>"
        )
