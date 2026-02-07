"""
Matching analyzers for skill matching and gap analysis.

This package provides intelligent skill matching capabilities including:
- Enhanced matching with synonyms, fuzzy matching, and compound skills
- Vector-based semantic similarity matching
- Skill gap analysis with bridgeability scoring
"""

from .enhanced_matcher import EnhancedSkillMatcher
from .vector_matcher import VectorSimilarityMatcher, VectorMatchResult

__all__ = [
    "EnhancedSkillMatcher",
    "VectorSimilarityMatcher",
    "VectorMatchResult",
]
