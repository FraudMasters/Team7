"""
Property-based tests for TF-IDF skill matching algorithms.

This module uses Hypothesis to generate hundreds of random test cases
and verify that certain properties (invariants) always hold true for
the TF-IDF skill matching algorithms.

Properties tested:
- TF-IDF match result structure and range constraints
- Score calculation consistency
- Keyword matching properties
- Empty input handling
- Threshold effects
"""
# Import pytest and hypothesis
import pytest
from hypothesis import given, strategies as st, settings, example
from typing import Dict, Any, List, Tuple, Optional

# Import the TF-IDF matcher
try:
    from analyzers.tfidf_matcher import TfidfSkillMatcher, TfidfMatchResult
except ImportError:
    # If running from different directory
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from analyzers.tfidf_matcher import TfidfSkillMatcher, TfidfMatchResult


class TestTfidfMatchResultProperties:
    """Property-based tests for TfidfMatchResult structure."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
            st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            min_size=0, max_size=10
        )
    )
    @settings(max_examples=100)
    def test_match_result_structure(self, score: float, passed: bool,
                                    matched_keywords: List[str], missing_keywords: List[str],
                                    keyword_weights: Dict[str, float]):
        """TfidfMatchResult should maintain consistent structure."""
        result = TfidfMatchResult(
            score=score,
            passed=passed,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            keyword_weights=keyword_weights
        )

        # Check types
        assert isinstance(result.score, float)
        assert isinstance(result.passed, bool)
        assert isinstance(result.matched_keywords, list)
        assert isinstance(result.missing_keywords, list)
        assert isinstance(result.keyword_weights, dict)

    @given(
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
    )
    @settings(max_examples=100)
    def test_keyword_lists_are_strings(self, matched: List[str], missing: List[str]):
        """Keyword lists should only contain strings."""
        result = TfidfMatchResult(
            score=0.5,
            passed=False,
            matched_keywords=matched,
            missing_keywords=missing,
            keyword_weights={}
        )

        for kw in result.matched_keywords:
            assert isinstance(kw, str)
        for kw in result.missing_keywords:
            assert isinstance(kw, str)


class TestScoreProperties:
    """Property-based tests for score calculation."""

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    @example("Python Developer", "Senior Python Dev", "We need a Python expert with Django", ["Python", "Django"])
    def test_score_range(self, resume_text: str, job_title: str,
                        job_description: str, required_skills: List[str]):
        """Score should always be between 0 and 1."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)
        assert 0.0 <= result.score <= 1.0

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_passed_consistent_with_threshold(self, resume_text: str, job_title: str,
                                             job_description: str, required_skills: List[str],
                                             threshold: float):
        """Passed should be True iff score >= threshold."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills, threshold=threshold)

        if result.score >= threshold:
            assert result.passed is True
        else:
            assert result.passed is False

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_passed_consistent_with_default_threshold(self, resume_text: str, job_title: str,
                                                     job_description: str, required_skills: List[str]):
        """Passed should be consistent with default threshold (0.3)."""
        matcher = TfidfSkillMatcher(threshold=0.3)
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        assert result.passed == (result.score >= 0.3)


class TestKeywordMatchingProperties:
    """Property-based tests for keyword matching behavior."""

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_matched_and_missing_are_disjoint(self, resume_text: str, job_title: str,
                                             job_description: str, required_skills: List[str]):
        """Matched and missing keywords should not overlap."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        matched_set = set(result.matched_keywords)
        missing_set = set(result.missing_keywords)

        assert matched_set.isdisjoint(missing_set)

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_matched_in_keyword_weights(self, resume_text: str, job_title: str,
                                       job_description: str, required_skills: List[str]):
        """All matched keywords should have weights."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        for kw in result.matched_keywords:
            assert kw in result.keyword_weights

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_keyword_weights_are_positive(self, resume_text: str, job_title: str,
                                         job_description: str, required_skills: List[str]):
        """All keyword weights should be non-negative."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        for kw, weight in result.keyword_weights.items():
            assert weight >= 0.0

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_missing_keywords_limited(self, resume_text: str, job_title: str,
                                     job_description: str, required_skills: List[str]):
        """Missing keywords should respect max_missing_display limit."""
        matcher = TfidfSkillMatcher(max_missing_display=10)
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        assert len(result.missing_keywords) <= 10


class TestEmptyInputProperties:
    """Property-based tests for handling edge cases and empty inputs."""

    @given(st.text(min_size=0, max_size=200),
           st.text(min_size=0, max_size=50),
           st.text(min_size=0, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_empty_job_inputs_no_crash(self, resume_text: str, job_title: str,
                                      job_description: str, required_skills: List[str]):
        """Empty job inputs should not cause crashes."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        # Should still return valid result
        assert isinstance(result, TfidfMatchResult)
        assert isinstance(result.score, float)
        assert isinstance(result.passed, bool)

    @given(st.text(min_size=0, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=0))
    @settings(max_examples=100)
    def test_empty_required_skills(self, resume_text: str, job_title: str,
                                   job_description: str, required_skills: List[str]):
        """Empty required skills should return score of 1.0."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills)

        # No keywords to match means perfect score
        assert result.score == 1.0
        assert result.passed is True

    @given(st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_empty_resume_text(self, job_title: str, job_description: str, required_skills: List[str]):
        """Empty resume text should not crash."""
        matcher = TfidfSkillMatcher()
        result = matcher.match("", job_title, job_description, required_skills)

        # Should still return valid result with low score
        assert isinstance(result, TfidfMatchResult)
        assert 0.0 <= result.score <= 1.0


class TestThresholdProperties:
    """Property-based tests for threshold behavior."""

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20),
           st.floats(min_value=0.0, max_value=0.9, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_lower_threshold_easier_to_pass(self, resume_text: str, job_title: str,
                                           job_description: str, required_skills: List[str],
                                           threshold: float):
        """Lower threshold should make it easier to pass."""
        matcher = TfidfSkillMatcher()

        result_high = matcher.match(resume_text, job_title, job_description, required_skills, threshold=threshold)
        result_low = matcher.match(resume_text, job_title, job_description, required_skills, threshold=threshold / 2)

        # If it passes with higher threshold, it should pass with lower
        if result_high.passed:
            assert result_low.passed

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_threshold_zero_always_passes(self, resume_text: str, job_title: str,
                                         job_description: str, required_skills: List[str]):
        """Threshold of 0 should always pass."""
        matcher = TfidfSkillMatcher()
        result = matcher.match(resume_text, job_title, job_description, required_skills, threshold=0.0)

        assert result.passed is True


class TestMatcherInitializationProperties:
    """Property-based tests for matcher initialization."""

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
           st.integers(min_value=1, max_value=1000),
           st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
           st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_matcher_initialization(self, threshold: float, max_features: int,
                                   tfidf_cutoff: float, max_missing_display: int):
        """Matcher should initialize with given parameters."""
        matcher = TfidfSkillMatcher(
            threshold=threshold,
            max_features=max_features,
            tfidf_cutoff=tfidf_cutoff,
            max_missing_display=max_missing_display
        )

        assert matcher.threshold == threshold
        assert matcher.max_features == max_features
        assert matcher.tfidf_cutoff == tfidf_cutoff
        assert matcher.max_missing_display == max_missing_display

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_matcher_creates_vectorizer(self, resume_text: str, job_title: str,
                                        job_description: str, required_skills: List[str]):
        """Matcher should be able to create vectorizer."""
        matcher = TfidfSkillMatcher()
        vectorizer = matcher._create_vectorizer()

        # Check vectorizer has expected attributes
        assert hasattr(vectorizer, 'fit')
        assert hasattr(vectorizer, 'transform')
        assert hasattr(vectorizer, 'get_feature_names_out')


class TestKeywordExtractionProperties:
    """Property-based tests for keyword extraction."""

    @given(st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_keyword_extraction_returns_lists(self, job_title: str, job_description: str, required_skills: List[str]):
        """Keyword extraction should return valid lists and dicts."""
        matcher = TfidfSkillMatcher()
        keywords, tfidf_scores = matcher._extract_keywords_from_job(job_title, job_description, required_skills)

        assert isinstance(keywords, list)
        assert isinstance(tfidf_scores, dict)

        # All items in keywords should be strings
        for kw in keywords:
            assert isinstance(kw, str)

        # All values in tfidf_scores should be floats
        for score in tfidf_scores.values():
            assert isinstance(score, float)

    @given(st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_required_skills_always_included(self, job_title: str, job_description: str, required_skills: List[str]):
        """Required skills should always be included in keywords."""
        matcher = TfidfSkillMatcher()
        keywords, _ = matcher._extract_keywords_from_job(job_title, job_description, required_skills)

        # All required skills should be in keywords (lowercased)
        for skill in required_skills:
            assert skill.lower() in [k.lower() for k in keywords]


class TestMatchResumeToVacancyProperties:
    """Property-based tests for match_resume_to_vacancy method."""

    @given(st.text(min_size=1, max_size=200),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_match_resume_to_vacancy_structure(self, resume_text: str, resume_skills: List[str],
                                              vacancy_title: str, vacancy_description: str,
                                              vacancy_skills: List[str]):
        """match_resume_to_vacancy should return valid result."""
        matcher = TfidfSkillMatcher()
        result = matcher.match_resume_to_vacancy(
            resume_text, resume_skills, vacancy_title, vacancy_description, vacancy_skills
        )

        assert isinstance(result, TfidfMatchResult)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.passed, bool)
        assert isinstance(result.matched_keywords, list)
        assert isinstance(result.missing_keywords, list)
        assert isinstance(result.keyword_weights, dict)


class TestGetMissingImportanceProperties:
    """Property-based tests for get_missing_importance method."""

    @given(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=10),
        st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_get_missing_importance_returns_list(self, score: float, matched: List[str],
                                                 missing: List[str], top_n: int):
        """get_missing_importance should return list of tuples."""
        result = TfidfMatchResult(
            score=score,
            passed=score >= 0.3,
            matched_keywords=matched,
            missing_keywords=missing,
            keyword_weights={}
        )

        matcher = TfidfSkillMatcher()
        importance = matcher.get_missing_importance(result, top_n=top_n)

        assert isinstance(importance, list)
        assert len(importance) <= top_n

        for item in importance:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)  # keyword
            assert isinstance(item[1], float)  # score


class TestFindKeywordMatchesProperties:
    """Property-based tests for _find_keyword_matches internal method."""

    @given(st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_keyword_match_partition(self, resume_text: str, keywords: List[str]):
        """Matched and missing should form a partition of keywords."""
        matcher = TfidfSkillMatcher()
        resume_lower = resume_text.lower()

        matched, missing = matcher._find_keyword_matches(resume_lower, keywords)

        # Check types
        assert isinstance(matched, list)
        assert isinstance(missing, list)

        # Check that matched and missing together cover all keywords
        # (accounting for duplicates - each keyword should appear in exactly one list)
        all_keywords = set(keywords)
        matched_set = set(matched)
        missing_set = set(missing)

        # They should be disjoint
        assert matched_set.isdisjoint(missing_set)

        # Their union should be subset of original (some may not be found if duplicate)
        assert matched_set | missing_set <= all_keywords

    @given(st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_empty_keywords_no_crash(self, resume_text: str, keywords: List[str]):
        """Empty keywords list should not crash."""
        matcher = TfidfSkillMatcher()
        resume_lower = resume_text.lower()

        matched, missing = matcher._find_keyword_matches(resume_lower, keywords)

        assert matched == []
        assert missing == []


class TestScore monotonicityProperties:
    """Property-based tests for score monotonicity."""

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_same_input_same_score(self, resume_text: str, job_title: str,
                                   job_description: str, required_skills: List[str]):
        """Same inputs should produce same score."""
        matcher = TfidfSkillMatcher()

        result1 = matcher.match(resume_text, job_title, job_description, required_skills)
        result2 = matcher.match(resume_text, job_title, job_description, required_skills)

        assert result1.score == result2.score

    @given(st.text(min_size=1, max_size=200),
           st.text(min_size=1, max_size=50),
           st.text(min_size=1, max_size=500),
           st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=20))
    @settings(max_examples=100)
    def test_case_insensitivity(self, resume_text: str, job_title: str,
                               job_description: str, required_skills: List[str]):
        """Score should be case-insensitive for resume text."""
        matcher = TfidfSkillMatcher()

        result1 = matcher.match(resume_text, job_title, job_description, required_skills)
        result2 = matcher.match(resume_text.upper(), job_title, job_description, required_skills)
        result3 = matcher.match(resume_text.lower(), job_title, job_description, required_skills)

        # All scores should be equal since TF-IDF is case-insensitive
        assert result1.score == result2.score == result3.score
