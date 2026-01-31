"""
TF-IDF based skill matcher with weighted keyword scoring.

This module provides intelligent skill matching using TF-IDF (Term Frequency-Inverse Document Frequency)
to rank keyword importance and provide weighted matching scores.

Key features:
- Weighted scoring based on term importance
- Missing keywords ranked by TF-IDF importance
- N-gram support (1-2 grams) for phrase matching
- Configurable thresholds and feature limits
"""
import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class TfidfMatchResult:
    """Result of TF-IDF based matching."""

    score: float
    passed: bool
    matched_keywords: List[str]
    missing_keywords: List[str]
    keyword_weights: Dict[str, float]


class TfidfSkillMatcher:
    """
    TF-IDF based skill matcher with weighted scoring.

    Uses TF-IDF to calculate the importance of keywords in a job posting
    and matches them against resume text. Provides weighted scores that
    reflect the relative importance of each keyword.

    Example:
        >>> matcher = TfidfSkillMatcher()
        >>> result = matcher.match(
        ...     resume_text="Experienced with React and Python",
        ...     job_title="Senior React Developer",
        ...     job_description="Looking for React expert with Python knowledge",
        ...     required_skills=["React", "Python", "TypeScript"]
        ... )
        >>> print(result.score)
        0.67
        >>> print(result.missing_keywords)
        ['TypeScript']
    """

    def __init__(
        self,
        threshold: float = 0.3,
        max_features: int = 100,
        tfidf_cutoff: float = 0.05,
        max_missing_display: int = 10,
    ):
        """
        Initialize the TF-IDF matcher.

        Args:
            threshold: Minimum score to pass (0.0-1.0)
            max_features: Maximum number of TF-IDF features
            tfidf_cutoff: Minimum TF-IDF score to consider a keyword significant
            max_missing_display: Maximum number of missing keywords to return
        """
        self.threshold = threshold
        self.max_features = max_features
        self.tfidf_cutoff = tfidf_cutoff
        self.max_missing_display = max_missing_display

    def _create_vectorizer(self) -> TfidfVectorizer:
        """
        Create TF-IDF vectorizer with optimized settings.

        Returns:
            Configured TfidfVectorizer instance
        """
        return TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),  # Include bigrams for phrases like "machine learning"
            max_features=self.max_features,
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
            lowercase=True,
        )

    def _extract_keywords_from_job(
        self,
        job_title: str,
        job_description: str,
        required_skills: List[str],
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Extract significant keywords from job posting using TF-IDF.

        Args:
            job_title: Job title
            job_description: Job description text
            required_skills: List of required skills

        Returns:
            Tuple of (significant_keywords, tfidf_scores)
        """
        # Combine job text
        job_text = f"{job_title} {job_description} {' '.join(required_skills)}"

        if not job_text.strip():
            return [], {}

        # Create and fit vectorizer
        vectorizer = self._create_vectorizer()

        try:
            vectorizer.fit([job_text.lower()])
        except ValueError:
            logger.warning("Could not fit TF-IDF vectorizer on job text")
            return required_skills, {kw: 0.1 for kw in required_skills}

        # Get TF-IDF scores
        feature_names = vectorizer.get_feature_names_out()
        tfidf_matrix = vectorizer.transform([job_text.lower()])
        tfidf_scores = dict(zip(feature_names, tfidf_matrix.toarray()[0]))

        # Extract significant keywords
        significant_keywords = {
            term for term, score in tfidf_scores.items()
            if score > self.tfidf_cutoff
        }

        # Always include explicitly required skills
        for skill in required_skills:
            significant_keywords.add(skill.lower())

        return list(significant_keywords), tfidf_scores

    def _find_keyword_matches(
        self,
        resume_text: str,
        keywords: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        Find which keywords are present in resume text.

        Args:
            resume_text: Lowercase resume text
            keywords: List of keywords to search for

        Returns:
            Tuple of (matched_keywords, missing_keywords)
        """
        matched = []
        missing = []

        for keyword in keywords:
            # Use word boundary pattern for accurate matching
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, resume_text):
                matched.append(keyword)
            else:
                missing.append(keyword)

        return matched, missing

    def match(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        required_skills: List[str],
        threshold: Optional[float] = None,
    ) -> TfidfMatchResult:
        """
        Match resume against job posting using TF-IDF weighted scoring.

        Args:
            resume_text: Resume text content
            job_title: Job posting title
            job_description: Job posting description
            required_skills: List of required skills from job posting
            threshold: Override default threshold

        Returns:
            TfidfMatchResult with score, passed status, and keyword details
        """
        if threshold is None:
            threshold = self.threshold

        # Normalize resume text
        resume_lower = resume_text.lower()

        # Extract significant keywords from job
        keywords, tfidf_scores = self._extract_keywords_from_job(
            job_title, job_description, required_skills
        )

        if not keywords:
            # No keywords to match
            return TfidfMatchResult(
                score=1.0,
                passed=True,
                matched_keywords=[],
                missing_keywords=[],
                keyword_weights={},
            )

        # Find matches
        matched, missing = self._find_keyword_matches(resume_lower, keywords)

        # Calculate weighted score
        matched_weight = sum(tfidf_scores.get(kw, 0.1) for kw in matched)
        total_weight = sum(tfidf_scores.get(kw, 0.1) for kw in keywords)
        score = matched_weight / total_weight if total_weight > 0 else 1.0

        # Sort missing by TF-IDF importance (most important first)
        missing_sorted = sorted(
            missing,
            key=lambda kw: tfidf_scores.get(kw, 0),
            reverse=True,
        )[:self.max_missing_display]

        # Build keyword weights for matched
        keyword_weights = {kw: tfidf_scores.get(kw, 0.1) for kw in matched}

        return TfidfMatchResult(
            score=float(score),
            passed=bool(score >= threshold),
            matched_keywords=matched,
            missing_keywords=missing_sorted,
            keyword_weights=keyword_weights,
        )

    def match_resume_to_vacancy(
        self,
        resume_text: str,
        resume_skills: List[str],
        vacancy_title: str,
        vacancy_description: str,
        vacancy_skills: List[str],
    ) -> TfidfMatchResult:
        """
        Match a resume to a specific vacancy.

        Convenience method that combines resume skills with full text
        for comprehensive matching.

        Args:
            resume_text: Full resume text
            resume_skills: Extracted skills from resume
            vacancy_title: Vacancy title
            vacancy_description: Vacancy description
            vacancy_skills: Required skills for vacancy

        Returns:
            TfidfMatchResult with match details
        """
        # Combine resume text with skills for better matching
        enhanced_resume = f"{resume_text} {' '.join(resume_skills)}"

        return self.match(
            resume_text=enhanced_resume,
            job_title=vacancy_title,
            job_description=vacancy_description,
            required_skills=vacancy_skills,
        )

    def get_missing_importance(
        self,
        result: TfidfMatchResult,
        top_n: int = 5,
    ) -> List[Tuple[str, float]]:
        """
        Get top missing keywords by importance.

        Args:
            result: TfidfMatchResult from match()
            top_n: Number of top keywords to return

        Returns:
            List of (keyword, importance_score) tuples
        """
        # This would require storing tfidf_scores in the result
        # For now, return missing keywords
        return [(kw, 0.0) for kw in result.missing_keywords[:top_n]]


# Singleton instance for convenience
_default_matcher: Optional[TfidfSkillMatcher] = None


def get_tfidf_matcher() -> TfidfSkillMatcher:
    """Get or create default TF-IDF matcher instance."""
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = TfidfSkillMatcher()
    return _default_matcher
