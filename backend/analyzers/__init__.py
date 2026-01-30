"""
Analyzers module for resume text processing.

This module provides various text analysis functions for resume processing,
including keyword extraction, named entity recognition, grammar checking,
and experience calculation.
"""

from .keyword_extractor import (
    extract_keywords,
    extract_resume_keywords as extract_resume_keywords_old,
    extract_top_skills,
)
from .hf_skill_extractor import (
    extract_skills_ner,
    extract_skills_zero_shot,
    extract_skills_pattern_matching,
    extract_resume_skills,
    extract_top_skills as extract_top_skills_hf,
    extract_resume_keywords,
    extract_resume_keywords as extract_resume_keywords_hf,
)
from .skill_extractor_fallback import (
    extract_skills_with_fallback,
    extract_top_skills_auto,
)
from .ner_extractor import (
    extract_entities,
    extract_organizations,
    extract_dates,
    extract_resume_entities,
)
from .grammar_checker import (
    check_grammar,
    check_grammar_resume,
    get_error_suggestions_summary,
)
from .experience_calculator import (
    calculate_total_experience,
    calculate_skill_experience,
    calculate_multiple_skills_experience,
    format_experience_summary,
)
from .error_detector import (
    detect_resume_errors,
    get_error_summary,
    format_errors_for_display,
)
from .enhanced_matcher import (
    EnhancedSkillMatcher,
)
from .tfidf_matcher import (
    TfidfSkillMatcher,
    TfidfMatchResult,
    get_tfidf_matcher,
)
from .vector_matcher import (
    VectorSimilarityMatcher,
    VectorMatchResult,
    get_vector_matcher,
)
from .unified_matcher import (
    UnifiedSkillMatcher,
    UnifiedMatchResult,
    get_unified_matcher,
)
from .taxonomy_loader import (
    TaxonomyLoader,
)
from .model_versioning import (
    ModelVersionManager,
)
from .accuracy_benchmark import (
    AccuracyBenchmark,
)

__all__ = [
    "extract_keywords",
    "extract_top_skills",
    "extract_resume_keywords",
    "extract_skills_ner",
    "extract_skills_zero_shot",
    "extract_skills_pattern_matching",
    "extract_resume_skills",
    "extract_top_skills_hf",
    "extract_resume_keywords_hf",
    "extract_skills_with_fallback",
    "extract_top_skills_auto",
    "extract_entities",
    "extract_organizations",
    "extract_dates",
    "extract_resume_entities",
    "check_grammar",
    "check_grammar_resume",
    "get_error_suggestions_summary",
    "calculate_total_experience",
    "calculate_skill_experience",
    "calculate_multiple_skills_experience",
    "format_experience_summary",
    "detect_resume_errors",
    "get_error_summary",
    "format_errors_for_display",
    "EnhancedSkillMatcher",
    "TfidfSkillMatcher",
    "TfidfMatchResult",
    "get_tfidf_matcher",
    "VectorSimilarityMatcher",
    "VectorMatchResult",
    "get_vector_matcher",
    "UnifiedSkillMatcher",
    "UnifiedMatchResult",
    "get_unified_matcher",
    "TaxonomyLoader",
    "ModelVersionManager",
    "AccuracyBenchmark",
    "save_resume_analysis",
    "get_resume_analysis",
    "delete_resume_analysis",
    "calculate_quality_score",
]
