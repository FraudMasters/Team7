"""
SkillTaxonomy model for storing industry-specific skill taxonomies
"""
from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID

from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SkillTaxonomy(Base, UUIDMixin, TimestampMixin):
    """
    SkillTaxonomy model for storing industry-specific skill taxonomies

    Attributes:
        id: UUID primary key
        industry: Industry sector (tech, healthcare, finance, etc.)
        skill_name: Canonical name of the skill
        context: Context category (e.g., web_framework, language, database)
        variants: JSON array of alternative names/spellings for this skill
        extra_metadata: JSON object with additional skill metadata (description, category, etc.)
        is_active: Whether this taxonomy entry is currently active
        version: Version number of this taxonomy entry
        previous_version_id: UUID of the previous version (null for initial version)
        is_latest: Whether this is the latest version of the taxonomy entry
        is_public: Whether this taxonomy entry is publicly shareable
        organization_id: Organization that owns this taxonomy entry
        source_organization: Original organization if this is a shared/copied taxonomy
        view_count: Number of times this taxonomy entry has been viewed
        use_count: Number of times this taxonomy entry has been used in matching
        last_used_at: Timestamp when this taxonomy entry was last used
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "skill_taxonomies"

    industry: Mapped[str] = mapped_column(nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(nullable=False, index=True)
    context: Mapped[Optional[str]] = mapped_column(nullable=True)
    variants: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    previous_version_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_taxonomies.id"), nullable=True
    )
    is_latest: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_public: Mapped[bool] = mapped_column(nullable=False, default=False)
    organization_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    source_organization: Mapped[Optional[str]] = mapped_column(nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<SkillTaxonomy(id={self.id}, industry={self.industry}, skill={self.skill_name})>"
