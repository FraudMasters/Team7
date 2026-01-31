"""
Unified skill matcher combining multiple matching strategies.

This module provides a comprehensive matcher that combines:
1. Enhanced keyword matching (synonyms, fuzzy, compound skills)
2. TF-IDF weighted matching (importance-based scoring)
3. Vector semantic similarity (sentence-transformers)

The unified approach provides the best of all worlds:
- Precise keyword matching
- Weighted importance scoring
- Semantic understanding
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .enhanced_matcher import EnhancedSkillMatcher
from .tfidf_matcher import TfidfSkillMatcher, TfidfMatchResult
from .vector_matcher import VectorSimilarityMatcher, VectorMatchResult, _HAS_SENTENCE_TRANSFORMERS

logger = logging.getLogger(__name__)


@dataclass
class UnifiedMatchResult:
    """Comprehensive result from unified matching."""

    # Overall scores
    overall_score: float
    passed: bool

    # Individual method results
    keyword_score: float
    keyword_passed: bool
    keyword_matches: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    tfidf_score: float = 0.0
    tfidf_passed: bool = False
    tfidf_matched: List[str] = field(default_factory=list)
    tfidf_missing: List[str] = field(default_factory=list)

    vector_score: float = 0.0
    vector_passed: bool = False
    vector_similarity: float = 0.0

    # Detailed match info
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)

    # Recommendation
    recommendation: str = "neutral"

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "keyword_score": self.keyword_score,
            "keyword_passed": self.keyword_passed,
            "tfidf_score": self.tfidf_score,
            "tfidf_passed": self.tfidf_passed,
            "tfidf_matched": self.tfidf_matched,
            "tfidf_missing": self.tfidf_missing,
            "vector_score": self.vector_score,
            "vector_passed": self.vector_passed,
            "vector_similarity": self.vector_similarity,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "recommendation": self.recommendation,
        }


class UnifiedSkillMatcher:
    """
    Unified skill matcher combining multiple strategies.

    Uses three complementary approaches:
    1. Enhanced matching: Direct, synonym, fuzzy, compound skill matching
    2. TF-IDF matching: Weighted scoring based on keyword importance
    3. Vector matching: Semantic similarity using embeddings

    The overall score is a weighted combination of all three methods.

    Example:
        >>> matcher = UnifiedSkillMatcher()
        >>> result = matcher.match(
        ...     resume_text="Experienced with React and Python",
        ...     resume_skills=["React", "Python"],
        ...     job_title="Senior React Developer",
        ...     job_description="Looking for React expert",
        ...     required_skills=["React", "Python", "TypeScript"]
        ... )
        >>> print(result.overall_score)
        0.75
        >>> print(result.recommendation)
        'good_match'
    """

    def __init__(
        self,
        # Weights for overall score (should sum to 1.0)
        keyword_weight: float = 0.5,
        tfidf_weight: float = 0.3,
        vector_weight: float = 0.2,

        # Individual method thresholds
        keyword_threshold: Optional[float] = None,  # Uses EnhancedSkillMatcher default
        tfidf_threshold: float = 0.3,
        vector_threshold: float = 0.5,

        # Overall pass threshold
        overall_threshold: float = 0.5,

        # Model configuration
        vector_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the unified skill matcher.

        Args:
            keyword_weight: Weight for keyword matching in overall score
            tfidf_weight: Weight for TF-IDF matching in overall score
            vector_weight: Weight for vector matching in overall score
            keyword_threshold: Threshold for keyword matching pass/fail
            tfidf_threshold: Threshold for TF-IDF matching pass/fail
            vector_threshold: Threshold for vector matching pass/fail
            overall_threshold: Threshold for overall pass/fail
            vector_model: Name of sentence-transformers model
        """
        # Normalize weights
        total_weight = keyword_weight + tfidf_weight + vector_weight
        self.keyword_weight = keyword_weight / total_weight
        self.tfidf_weight = tfidf_weight / total_weight
        self.vector_weight = vector_weight / total_weight

        self.tfidf_threshold = tfidf_threshold
        self.vector_threshold = vector_threshold
        self.overall_threshold = overall_threshold

        # Initialize matchers
        self.keyword_matcher = EnhancedSkillMatcher()
        self.tfidf_matcher = TfidfSkillMatcher(threshold=tfidf_threshold)

        if _HAS_SENTENCE_TRANSFORMERS:
            self.vector_matcher = VectorSimilarityMatcher(
                threshold=vector_threshold,
                model_name=vector_model,
            )
        else:
            self.vector_matcher = None
            logger.warning("Vector matching disabled (sentence-transformers not available)")

        logger.info(
            f"UnifiedSkillMatcher initialized with weights: "
            f"keyword={self.keyword_weight:.2f}, "
            f"tfidf={self.tfidf_weight:.2f}, "
            f"vector={self.vector_weight:.2f}"
        )

    def match(
        self,
        resume_text: str,
        resume_skills: List[str],
        job_title: str,
        job_description: str,
        required_skills: List[str],
        context: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> UnifiedMatchResult:
        """
        Perform unified matching using all three methods.

        Args:
            resume_text: Full resume text
            resume_skills: List of skills extracted from resume
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            context: Optional context hint for keyword matching
            weights: Optional custom weights dict with 'keyword_weight', 'tfidf_weight', 'vector_weight'

        Returns:
            UnifiedMatchResult with comprehensive match information
        """
        # Use custom weights if provided, otherwise use instance weights
        if weights:
            total = weights.get('keyword_weight', 0) + weights.get('tfidf_weight', 0) + weights.get('vector_weight', 0)
            kw = weights.get('keyword_weight', self.keyword_weight) / total if total > 0 else self.keyword_weight
            tw = weights.get('tfidf_weight', self.tfidf_weight) / total if total > 0 else self.tfidf_weight
            vw = weights.get('vector_weight', self.vector_weight) / total if total > 0 else self.vector_weight
        else:
            kw = self.keyword_weight
            tw = self.tfidf_weight
            vw = self.vector_weight

        # 1. Enhanced keyword matching
        keyword_results = self.keyword_matcher.match_multiple(
            resume_skills=resume_skills,
            required_skills=required_skills,
            context=context,
        )

        matched_skills = [
            skill for skill, result in keyword_results.items()
            if result.get("matched", False)
        ]
        missing_skills = [
            skill for skill, result in keyword_results.items()
            if not result.get("matched", False)
        ]

        keyword_pct = self.keyword_matcher.calculate_match_percentage(keyword_results)
        keyword_score = keyword_pct / 100
        keyword_passed = keyword_score >= 0.3  # At least 30% skill match

        # 2. TF-IDF matching
        tfidf_result = self.tfidf_matcher.match(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            required_skills=required_skills,
        )

        # 3. Vector matching
        vector_score = 0.0
        vector_passed = False
        vector_similarity = 0.0

        if self.vector_matcher:
            vector_result = self.vector_matcher.match(
                resume_text=resume_text,
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
            )
            vector_score = vector_result.score
            vector_passed = vector_result.passed
            vector_similarity = vector_result.similarity

        # Calculate overall score (weighted combination)
        overall_score = (
            kw * keyword_score +
            tw * tfidf_result.score +
            vw * vector_score
        )

        overall_passed = overall_score >= self.overall_threshold

        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_score, keyword_passed, tfidf_result.passed, vector_passed
        )

        return UnifiedMatchResult(
            overall_score=round(overall_score, 3),
            passed=overall_passed,
            keyword_score=round(keyword_score, 3),
            keyword_passed=keyword_passed,
            keyword_matches=keyword_results,
            tfidf_score=round(tfidf_result.score, 3),
            tfidf_passed=tfidf_result.passed,
            tfidf_matched=tfidf_result.matched_keywords,
            tfidf_missing=tfidf_result.missing_keywords,
            vector_score=round(vector_score, 3),
            vector_passed=vector_passed,
            vector_similarity=round(vector_similarity, 3),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendation=recommendation,
        )

    def update_weights(
        self,
        keyword_weight: Optional[float] = None,
        tfidf_weight: Optional[float] = None,
        vector_weight: Optional[float] = None,
    ) -> None:
        """
        Update the matching weights dynamically.

        Args:
            keyword_weight: New keyword weight (0-1)
            tfidf_weight: New TF-IDF weight (0-1)
            vector_weight: New vector weight (0-1)

        Note:
            If all three are provided, they will be normalized to sum to 1.0.
            If only some are provided, only those will be updated (may not sum to 1.0).
        """
        # If all weights provided, normalize them
        if all(w is not None for w in [keyword_weight, tfidf_weight, vector_weight]):
            total = keyword_weight + tfidf_weight + vector_weight  # type: ignore
            self.keyword_weight = round(keyword_weight / total, 3)  # type: ignore
            self.tfidf_weight = round(tfidf_weight / total, 3)  # type: ignore
            self.vector_weight = round(vector_weight / total, 3)  # type: ignore
        else:
            # Update only provided weights
            if keyword_weight is not None:
                self.keyword_weight = round(keyword_weight, 3)
            if tfidf_weight is not None:
                self.tfidf_weight = round(tfidf_weight, 3)
            if vector_weight is not None:
                self.vector_weight = round(vector_weight, 3)

        logger.info(
            f"UnifiedSkillMatcher weights updated: "
            f"keyword={self.keyword_weight:.2f}, "
            f"tfidf={self.tfidf_weight:.2f}, "
            f"vector={self.vector_weight:.2f}"
        )

    def get_weights(self) -> Dict[str, float]:
        """
        Get current matching weights.

        Returns:
            Dict with 'keyword_weight', 'tfidf_weight', 'vector_weight'
        """
        return {
            "keyword_weight": self.keyword_weight,
            "tfidf_weight": self.tfidf_weight,
            "vector_weight": self.vector_weight,
        }

    def _generate_recommendation(
        self,
        overall_score: float,
        keyword_passed: bool,
        tfidf_passed: bool,
        vector_passed: bool,
    ) -> str:
        """
        Generate hiring recommendation based on match results.

        Args:
            overall_score: Overall match score
            keyword_passed: Whether keyword matching passed
            tfidf_passed: Whether TF-IDF matching passed
            vector_passed: Whether vector matching passed

        Returns:
            Recommendation string: 'excellent', 'good', 'maybe', 'poor'
        """
        if overall_score >= 0.8 and keyword_passed:
            return "excellent"
        elif overall_score >= 0.6 and keyword_passed and tfidf_passed:
            return "good"
        elif overall_score >= 0.4:
            return "maybe"
        else:
            return "poor"

    def match_resume_to_vacancy(
        self,
        resume_text: str,
        resume_skills: List[str],
        vacancy_title: str,
        vacancy_description: str,
        vacancy_skills: List[str],
    ) -> UnifiedMatchResult:
        """
        Match a resume to a specific vacancy.

        Convenience method with clearer naming for vacancy matching.

        Args:
            resume_text: Full resume text
            resume_skills: Extracted skills from resume
            vacancy_title: Vacancy title
            vacancy_description: Vacancy description
            vacancy_skills: Required skills for vacancy

        Returns:
            UnifiedMatchResult with comprehensive match information
        """
        return self.match(
            resume_text=resume_text,
            resume_skills=resume_skills,
            job_title=vacancy_title,
            job_description=vacancy_description,
            required_skills=vacancy_skills,
        )

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        job_title: str,
        job_description: str,
        required_skills: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple candidates for a job posting.

        Args:
            candidates: List of candidate dicts with 'resume_text', 'resume_skills', 'id', 'name'
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills

        Returns:
            List of candidates with added 'match_result' field, sorted by overall_score
        """
        results = []

        for candidate in candidates:
            match_result = self.match(
                resume_text=candidate.get("resume_text", ""),
                resume_skills=candidate.get("resume_skills", []),
                job_title=job_title,
                job_description=job_description,
                required_skills=required_skills,
            )

            results.append({
                **candidate,
                "match_result": match_result.to_dict(),
                "overall_score": match_result.overall_score,
            })

        # Sort by overall score descending
        results.sort(key=lambda x: x["overall_score"], reverse=True)
        return results


# Singleton instance
_default_matcher: Optional[UnifiedSkillMatcher] = None


def get_unified_matcher(
    keyword_weight: Optional[float] = None,
    tfidf_weight: Optional[float] = None,
    vector_weight: Optional[float] = None,
) -> UnifiedSkillMatcher:
    """
    Get or create default unified matcher instance.

    Args:
        keyword_weight: Optional keyword weight for new instance
        tfidf_weight: Optional TF-IDF weight for new instance
        vector_weight: Optional vector weight for new instance

    Returns:
        UnifiedSkillMatcher instance

    Note:
        If weights are provided, a new matcher is created with those weights.
        Otherwise, returns the default singleton instance.
    """
    global _default_matcher

    # If custom weights requested, create a new matcher
    if any(w is not None for w in [keyword_weight, tfidf_weight, vector_weight]):
        kw = keyword_weight if keyword_weight is not None else 0.5
        tw = tfidf_weight if tfidf_weight is not None else 0.3
        vw = vector_weight if vector_weight is not None else 0.2
        return UnifiedSkillMatcher(keyword_weight=kw, tfidf_weight=tw, vector_weight=vw)

    # Return default singleton
    if _default_matcher is None:
        _default_matcher = UnifiedSkillMatcher()
    return _default_matcher
