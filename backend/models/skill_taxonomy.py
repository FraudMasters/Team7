"""
SkillTaxonomy model for storing industry-specific skill taxonomies
"""
from typing import Optional

from sqlalchemy import JSON
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

    def __repr__(self) -> str:
        return f"<SkillTaxonomy(id={self.id}, industry={self.industry}, skill={self.skill_name})>"
