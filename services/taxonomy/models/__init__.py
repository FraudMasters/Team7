"""Models package for Taxonomy Service."""
from .base import Base, TimestampMixin, UUIDMixin
from .skill_taxonomy import SkillTaxonomy

__all__ = ["Base", "TimestampMixin", "UUIDMixin", "SkillTaxonomy"]
