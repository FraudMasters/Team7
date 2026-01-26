"""
Skills library module for position-specific skill taxonomies.

This module provides tools for managing and querying position-specific
skill taxonomies, including synonym normalization and fuzzy matching.
"""

from .skills_library import (
    SkillsLibrary,
    load_position_skills,
    get_skills_for_position,
)

__all__ = [
    "SkillsLibrary",
    "load_position_skills",
    "get_skills_for_position",
]
