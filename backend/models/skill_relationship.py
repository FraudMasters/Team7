"""
SkillRelationship model for storing relationships between skills
(e.g., parent/child, similar skills, prerequisites)
"""
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class RelationshipType(str, PyEnum):
    """Types of relationships between skills"""

    PARENT_CHILD = "parent_child"  # Hierarchical relationship (e.g., Frontend -> React)
    SIMILAR = "similar"  # Similar skills that can be substituted (e.g., React ~ Vue)
    PREREQUISITE = "prerequisite"  # One skill is required before another
    RELATED = "related"  # General relationship (skills often used together)


class SkillRelationship(Base, UUIDMixin, TimestampMixin):
    """
    SkillRelationship model for storing relationships between skills

    Attributes:
        id: UUID primary key
        source_skill_id: UUID of the source skill in the relationship
        target_skill_id: UUID of the target skill in the relationship
        relationship_type: Type of relationship (parent_child, similar, prerequisite, related)
        weight: Optional weight/strength of the relationship (0.0 to 1.0)
        extra_metadata: JSON object with additional relationship metadata
        is_active: Whether this relationship is currently active
        organization_id: Organization that owns this relationship
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "skill_relationships"

    source_skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_taxonomies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_skill_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("skill_taxonomies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<SkillRelationship(id={self.id}, type={self.relationship_type}, source={self.source_skill_id}, target={self.target_skill_id})>"
