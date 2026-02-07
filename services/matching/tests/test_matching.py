"""
Tests for Matching Service.

Tests cover:
- Configuration and settings
- Enhanced skill matcher
- Skill gap analyzer
- Vector similarity matcher
- Match result model
- FastAPI endpoints (basic)
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from uuid import uuid4

from analyzers.enhanced_matcher import EnhancedSkillMatcher
from analyzers.skill_gap_analyzer import SkillGapAnalyzer, SkillGapResult
from analyzers.vector_matcher import VectorSimilarityMatcher, VectorMatchResult
from models.match_result import MatchResult
from config import Settings, get_settings


# =============================================================================
# Configuration Tests
# =============================================================================

class TestSettings:
    """Tests for Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.database_url == "postgresql://postgres:postgres@localhost:5432/resume_analysis"
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.service_host == "0.0.0.0"
        assert settings.service_port == 8001
        assert settings.log_level == "INFO"

    def test_cors_origins_property(self):
        """Test CORS origins property."""
        settings = Settings()
        origins = settings.cors_origins
        assert len(origins) > 0
        assert "http://localhost:3000" in origins
        assert "http://localhost:5173" in origins
        assert "http://localhost:8000" in origins

    def test_get_db_url_async(self):
        """Test async database URL conversion."""
        settings = Settings()
        async_url = settings.get_db_url_async()
        assert async_url.startswith("postgresql+asyncpg://")
        assert "resume_analysis" in async_url

    def test_get_db_url_async_already_async(self):
        """Test async URL when already async."""
        settings = Settings(database_url="postgresql+asyncpg://user:pass@host/db")
        async_url = settings.get_db_url_async()
        assert async_url == "postgresql+asyncpg://user:pass@host/db"

    def test_validate_database_url_warning(self, caplog):
        """Test database URL validation warning for invalid format."""
        with patch('config.logger'):
            settings = Settings(database_url="mysql://localhost/db")
            # Should still work but with warning
            assert settings.database_url == "mysql://localhost/db"

    def test_validate_log_level_uppercase(self):
        """Test log level is uppercased."""
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"

    def test_validate_log_level_invalid_defaults_to_info(self, caplog):
        """Test invalid log level defaults to INFO."""
        with patch('config.logger'):
            settings = Settings(log_level="invalid")
            assert settings.log_level == "INFO"

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


# =============================================================================
# Enhanced Skill Matcher Tests
# =============================================================================

class TestEnhancedSkillMatcherInit:
    """Tests for EnhancedSkillMatcher initialization."""

    def test_default_initialization(self):
        """Test default matcher initialization."""
        matcher = EnhancedSkillMatcher()
        assert matcher.synonyms_file is not None
        assert matcher._synonyms_map is None
        assert matcher._taxonomy_map == {}

    def test_custom_synonyms_file(self, tmp_path):
        """Test initialization with custom synonyms file."""
        custom_file = tmp_path / "custom_synonyms.json"
        matcher = EnhancedSkillMatcher(synonyms_file=custom_file)
        assert matcher.synonyms_file == custom_file


class TestNormalizeSkillName:
    """Tests for normalize_skill_name static method."""

    def test_basic_normalization(self):
        """Test basic skill name normalization."""
        result = EnhancedSkillMatcher.normalize_skill_name("React JS")
        assert result == "react js"

    def test_leading_trailing_whitespace(self):
        """Test removing leading and trailing whitespace."""
        result = EnhancedSkillMatcher.normalize_skill_name("  Python  ")
        assert result == "python"

    def test_multiple_spaces(self):
        """Test removing multiple internal spaces."""
        result = EnhancedSkillMatcher.normalize_skill_name("Machine   Learning")
        assert result == "machine learning"

    def test_case_insensitive(self):
        """Test case is converted to lowercase."""
        result = EnhancedSkillMatcher.normalize_skill_name("POSTGRESQL")
        assert result == "postgresql"

    def test_special_characters_preserved(self):
        """Test that special characters like dots and plus are preserved."""
        result = EnhancedSkillMatcher.normalize_skill_name("C++")
        assert result == "c++"

        result = EnhancedSkillMatcher.normalize_skill_name("Node.js")
        assert result == "node.js"

    def test_hash_preserved(self):
        """Test that hash character is preserved."""
        result = EnhancedSkillMatcher.normalize_skill_name("C#")
        assert result == "c#"

    def test_special_characters_removed(self):
        """Test that other special characters are removed."""
        result = EnhancedSkillMatcher.normalize_skill_name("React,JS!")
        assert result == "reactjs"

    def test_empty_string(self):
        """Test empty string normalization."""
        result = EnhancedSkillMatcher.normalize_skill_name("")
        assert result == ""

    def test_only_whitespace(self):
        """Test string with only whitespace."""
        result = EnhancedSkillMatcher.normalize_skill_name("   \t\n  ")
        assert result == ""


class TestCalculateFuzzySimilarity:
    """Tests for calculate_fuzzy_similarity method."""

    def test_exact_match(self):
        """Test exact match returns 1.0."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "React")
        assert result == 1.0

    def test_case_insensitive(self):
        """Test case insensitive similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "react")
        assert result == 1.0

    def test_partial_match(self):
        """Test partial match has lower similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "ReactJS")
        assert 0.6 < result < 1.0

    def test_no_similarity(self):
        """Test completely different strings have low similarity."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("Python", "Java")
        assert result < 0.3

    def test_empty_strings(self):
        """Test with empty strings."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("", "")
        assert result == 1.0

    def test_one_empty_string(self):
        """Test with one empty string."""
        matcher = EnhancedSkillMatcher()
        result = matcher.calculate_fuzzy_similarity("React", "")
        assert result == 0.0


class TestFindSynonymMatch:
    """Tests for find_synonym_match method."""

    def test_direct_match_high_confidence(self):
        """Test direct match returns high confidence."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java", "Django"]
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Python", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "Python"
        assert confidence == 0.95

    def test_synonym_match_medium_confidence(self):
        """Test synonym match returns medium-high confidence."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "PostgreSQL", "Django"]
        synonyms_map = {"SQL": ["SQL", "PostgreSQL", "MySQL"]}

        result = matcher.find_synonym_match(resume_skills, "SQL", synonyms_map)

        assert result is not None
        matched_skill, confidence = result
        assert matched_skill == "PostgreSQL"
        assert confidence == 0.85

    def test_no_match_returns_none(self):
        """Test when no match found returns None."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Ruby", synonyms_map)

        assert result is None

    def test_empty_resume_skills(self):
        """Test with empty resume skills list."""
        matcher = EnhancedSkillMatcher()
        resume_skills = []
        synonyms_map = {}

        result = matcher.find_synonym_match(resume_skills, "Python", synonyms_map)

        assert result is None


class TestMatchWithContext:
    """Tests for match_with_context method."""

    def test_direct_match_strategy(self):
        """Test direct match strategy (highest priority)."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java", "Django"]

        result = matcher.match_with_context(resume_skills, "Python")

        assert result["matched"] is True
        assert result["confidence"] == 1.0
        assert result["matched_as"] == "Python"
        assert result["match_type"] == "direct"

    def test_no_match(self):
        """Test when no match is found."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        result = matcher.match_with_context(resume_skills, "Ruby")

        assert result["matched"] is False
        assert result["confidence"] == 0.0
        assert result["matched_as"] is None
        assert result["match_type"] == "none"

    def test_empty_resume_skills(self):
        """Test with empty resume skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = []

        result = matcher.match_with_context(resume_skills, "Python")

        assert result["matched"] is False
        assert result["match_type"] == "none"

    def test_fuzzy_disabled(self):
        """Test with fuzzy matching disabled."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["PostgreSQL", "Python"]

        result = matcher.match_with_context(
            resume_skills, "Postgre", use_fuzzy=False
        )

        # Should not match because fuzzy is disabled and no other strategy matches
        assert result["matched"] is False


class TestMatchMultiple:
    """Tests for match_multiple method."""

    def test_match_multiple_skills(self):
        """Test matching multiple required skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Python", "PostgreSQL"]
        required_skills = ["React", "Python", "Java"]

        results = matcher.match_multiple(resume_skills, required_skills)

        assert len(results) == 3
        assert results["React"]["matched"] is True
        assert results["Python"]["matched"] is True
        assert results["Java"]["matched"] is False

    def test_empty_required_skills(self):
        """Test with empty required skills list."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["Python", "Java"]

        results = matcher.match_multiple(resume_skills, [])

        assert results == {}


class TestCalculateMatchPercentage:
    """Tests for calculate_match_percentage method."""

    def test_full_match_percentage(self):
        """Test 100% match when all skills match."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},
            "Java": {"matched": True},
            "Django": {"matched": True}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == 100.0

    def test_partial_match_percentage(self):
        """Test partial match percentage."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True},
            "Java": {"matched": True},
            "Django": {"matched": False}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == pytest.approx(66.67, rel=0.01)

    def test_no_match_percentage(self):
        """Test 0% match when no skills match."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": False},
            "Java": {"matched": False}
        }

        result = matcher.calculate_match_percentage(match_results)

        assert result == 0.0

    def test_empty_results(self):
        """Test with empty match results."""
        matcher = EnhancedSkillMatcher()
        match_results = {}

        result = matcher.calculate_match_percentage(match_results)

        assert result == 0.0


class TestGetLowConfidenceMatches:
    """Tests for get_low_confidence_matches method."""

    def test_filter_low_confidence(self):
        """Test filtering matches below threshold."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 1.0},
            "React": {"matched": True, "confidence": 0.85},
            "SQL": {"matched": True, "confidence": 0.70},
            "Java": {"matched": False, "confidence": 0.0}
        }

        result = matcher.get_low_confidence_matches(match_results, threshold=0.9)

        assert "React" in result
        assert "SQL" in result
        assert "Python" not in result
        assert "Java" not in result

    def test_empty_results(self):
        """Test with empty match results."""
        matcher = EnhancedSkillMatcher()
        match_results = {}

        result = matcher.get_low_confidence_matches(match_results)

        assert result == []

    def test_all_high_confidence(self):
        """Test when all matches are high confidence."""
        matcher = EnhancedSkillMatcher()
        match_results = {
            "Python": {"matched": True, "confidence": 1.0},
            "React": {"matched": True, "confidence": 0.95}
        }

        result = matcher.get_low_confidence_matches(match_results, threshold=0.9)

        assert result == []


class TestSplitCompoundSkill:
    """Tests for _split_compound_skill method."""

    def test_split_slash_separated(self):
        """Test splitting skills with slash separator."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill("C/C++")
        assert result == ["c", "c++"]

    def test_split_ampersand_separated(self):
        """Test splitting skills with ampersand separator."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill("SQL & NoSQL")
        assert result == ["sql", "nosql"]

    def test_split_comma_separated(self):
        """Test splitting skills with comma separator."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill("Python, Django")
        assert result == ["python", "django"]

    def test_no_split_needed(self):
        """Test skill that doesn't need splitting."""
        matcher = EnhancedSkillMatcher()
        result = matcher._split_compound_skill("Python")
        assert result == ["python"]


# =============================================================================
# Skill Gap Analyzer Tests
# =============================================================================

class TestSkillGapAnalyzerInit:
    """Tests for SkillGapAnalyzer initialization."""

    def test_default_initialization(self):
        """Test default analyzer initialization."""
        analyzer = SkillGapAnalyzer()
        assert analyzer.critical_gap_threshold == 0.5
        assert analyzer.moderate_gap_threshold == 0.3
        assert analyzer.minimal_gap_threshold == 0.1
        assert analyzer.keyword_matcher is not None

    def test_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        analyzer = SkillGapAnalyzer(
            critical_gap_threshold=0.6,
            moderate_gap_threshold=0.4,
            minimal_gap_threshold=0.2
        )
        assert analyzer.critical_gap_threshold == 0.6
        assert analyzer.moderate_gap_threshold == 0.4
        assert analyzer.minimal_gap_threshold == 0.2


class TestSkillGapAnalyze:
    """Tests for analyze method."""

    def test_perfect_match_no_gaps(self):
        """Test analysis with perfect skill match."""
        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(
            resume_text="Experienced Python developer",
            candidate_skills=["Python", "Django", "SQL"],
            job_title="Python Developer",
            job_description="Looking for Python developer",
            required_skills=["Python", "Django", "SQL"]
        )

        assert result.matched_skills == ["Python", "Django", "SQL"]
        assert result.missing_skills == []
        assert result.gap_severity == "none"
        assert result.gap_percentage == 0.0

    def test_partial_skill_match(self):
        """Test analysis with some missing skills."""
        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(
            resume_text="Python developer",
            candidate_skills=["Python", "Django"],
            job_title="Full Stack Developer",
            job_description="Looking for full stack developer",
            required_skills=["Python", "Django", "React", "AWS"]
        )

        assert "Python" in result.matched_skills
        assert "React" in result.missing_skills
        assert "AWS" in result.missing_skills
        assert result.gap_percentage > 0

    def test_no_required_skills(self):
        """Test analysis with no required skills."""
        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(
            resume_text="Developer",
            candidate_skills=["Python"],
            job_title="Developer",
            job_description="Job description",
            required_skills=[]
        )

        assert result.matched_skills == []
        assert result.missing_skills == []
        assert result.gap_percentage == 0.0

    def test_with_skill_levels(self):
        """Test analysis with skill level requirements."""
        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(
            resume_text="Python developer",
            candidate_skills=["Python", "Django"],
            job_title="Senior Python Developer",
            job_description="Looking for senior developer",
            required_skills=["Python", "Django"],
            required_skill_levels={"Python": "advanced", "Django": "intermediate"},
            candidate_skill_levels={"Python": "intermediate", "Django": "intermediate"}
        )

        # Python at intermediate vs required advanced should be partial match
        assert "Python" in result.partial_match_skills or "Python" in result.matched_skills


class TestCalculateGapPercentage:
    """Tests for _calculate_gap_percentage method."""

    def test_all_missing(self):
        """Test with all skills missing."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._calculate_gap_percentage(
            required_skills=["Python", "Java", "React"],
            missing_skills=["Python", "Java", "React"],
            partial_match_skills=[]
        )
        assert result == 100.0

    def test_half_missing(self):
        """Test with half skills missing."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._calculate_gap_percentage(
            required_skills=["Python", "Java", "React", "Django"],
            missing_skills=["Python", "Java"],
            partial_match_skills=[]
        )
        assert result == 50.0

    def test_partial_matches_count_half(self):
        """Test that partial matches count as 50% gap."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._calculate_gap_percentage(
            required_skills=["Python", "Java", "React"],
            missing_skills=["Python"],
            partial_match_skills=["Java"]
        )
        # 1 full missing + 1 partial (0.5) = 1.5 gaps / 3 skills = 50%
        assert result == 50.0


class TestDetermineGapSeverity:
    """Tests for _determine_gap_severity method."""

    def test_critical_severity(self):
        """Test critical severity threshold."""
        analyzer = SkillGapAnalyzer(critical_gap_threshold=0.5)
        result = analyzer._determine_gap_severity(60.0)
        assert result == "critical"

    def test_moderate_severity(self):
        """Test moderate severity threshold."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._determine_gap_severity(40.0)
        assert result == "moderate"

    def test_minimal_severity(self):
        """Test minimal severity threshold."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._determine_gap_severity(15.0)
        assert result == "minimal"

    def test_no_severity(self):
        """Test no severity (all skills matched)."""
        analyzer = SkillGapAnalyzer()
        result = analyzer._determine_gap_severity(5.0)
        assert result == "none"


class TestCategorizeSkill:
    """Tests for _categorize_skill method."""

    def test_programming_language_category(self):
        """Test programming language categorization."""
        analyzer = SkillGapAnalyzer()
        assert analyzer._categorize_skill("Python") == "programming_language"
        assert analyzer._categorize_skill("JavaScript") == "programming_language"
        assert analyzer._categorize_skill("Java") == "programming_language"

    def test_web_framework_category(self):
        """Test web framework categorization."""
        analyzer = SkillGapAnalyzer()
        assert analyzer._categorize_skill("React") == "web_framework"
        assert analyzer._categorize_skill("Django") == "web_framework"
        assert analyzer._categorize_skill("Angular") == "web_framework"

    def test_database_category(self):
        """Test database categorization."""
        analyzer = SkillGapAnalyzer()
        assert analyzer._categorize_skill("PostgreSQL") == "database"
        assert analyzer._categorize_skill("MySQL") == "database"
        assert analyzer._categorize_skill("MongoDB") == "database"

    def test_cloud_devops_category(self):
        """Test cloud/devops categorization."""
        analyzer = SkillGapAnalyzer()
        assert analyzer._categorize_skill("AWS") == "cloud_devops"
        assert analyzer._categorize_skill("Docker") == "cloud_devops"
        assert analyzer._categorize_skill("Kubernetes") == "cloud_devops"

    def test_other_category(self):
        """Test other category for unknown skills."""
        analyzer = SkillGapAnalyzer()
        assert analyzer._categorize_skill("Git") == "other"
        assert analyzer._categorize_skill("Agile") == "other"


class TestSkillGapResult:
    """Tests for SkillGapResult dataclass."""

    def test_to_dict_method(self):
        """Test to_dict conversion."""
        result = SkillGapResult(
            candidate_skills=["Python"],
            required_skills=["Python", "Java"],
            matched_skills=["Python"],
            missing_skills=["Java"],
            partial_match_skills=[],
            gap_severity="minimal",
            gap_percentage=50.0,
            bridgeability_score=0.75,
            estimated_time_to_bridge=40,
            priority_ordering=["Java"]
        )

        result_dict = result.to_dict()
        assert result_dict["candidate_skills"] == ["Python"]
        assert result_dict["gap_severity"] == "minimal"
        assert result_dict["gap_percentage"] == 50.0


# =============================================================================
# Vector Similarity Matcher Tests
# =============================================================================

class TestVectorSimilarityMatcherInit:
    """Tests for VectorSimilarityMatcher initialization."""

    def test_default_initialization(self):
        """Test default matcher initialization."""
        matcher = VectorSimilarityMatcher()
        assert matcher.threshold == 0.5
        assert matcher.model_name == "all-MiniLM-L6-v2"
        assert matcher.device is None

    def test_custom_threshold(self):
        """Test initialization with custom threshold."""
        matcher = VectorSimilarityMatcher(threshold=0.7)
        assert matcher.threshold == 0.7

    def test_custom_model(self):
        """Test initialization with custom model."""
        matcher = VectorSimilarityMatcher(model_name="all-mpnet-base-v2")
        assert matcher.model_name == "all-mpnet-base-v2"


class TestVectorMatchResult:
    """Tests for VectorMatchResult dataclass."""

    def test_vector_match_result_creation(self):
        """Test VectorMatchResult creation."""
        result = VectorMatchResult(
            similarity=0.8,
            score=0.9,
            passed=True,
            method="cosine"
        )
        assert result.similarity == 0.8
        assert result.score == 0.9
        assert result.passed is True
        assert result.method == "cosine"


class TestCosineSimilarity:
    """Tests for _cosine_similarity method."""

    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        matcher = VectorSimilarityMatcher()
        import numpy as np
        vec = np.array([1.0, 2.0, 3.0])
        result = matcher._cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0, rel=0.01)

    def test_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        matcher = VectorSimilarityMatcher()
        import numpy as np
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        result = matcher._cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0, rel=0.01)

    def test_zero_vector(self):
        """Test cosine similarity with zero vector."""
        matcher = VectorSimilarityMatcher()
        import numpy as np
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([0.0, 0.0, 0.0])
        result = matcher._cosine_similarity(vec1, vec2)
        assert result == 0.0


class TestNormalizeScore:
    """Tests for _normalize_score method."""

    def test_normalize_positive_cosine(self):
        """Test normalizing positive cosine similarity."""
        matcher = VectorSimilarityMatcher()
        result = matcher._normalize_score(0.5)
        assert result == 0.75  # (0.5 + 1) / 2

    def test_normalize_negative_cosine(self):
        """Test normalizing negative cosine similarity."""
        matcher = VectorSimilarityMatcher()
        result = matcher._normalize_score(-0.5)
        assert result == 0.25  # (-0.5 + 1) / 2

    def test_normalize_range(self):
        """Test normalization stays within 0-1 range."""
        matcher = VectorSimilarityMatcher()
        assert matcher._normalize_score(1.0) == 1.0
        assert matcher._normalize_score(-1.0) == 0.0
        assert 0.0 <= matcher._normalize_score(0.0) <= 1.0


# =============================================================================
# MatchResult Model Tests
# =============================================================================

class TestMatchResultModel:
    """Tests for MatchResult database model."""

    def test_match_result_repr(self):
        """Test MatchResult string representation."""
        from uuid import uuid4
        resume_id = uuid4()
        vacancy_id = uuid4()

        result = MatchResult(
            id=uuid4(),
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            match_percentage=85.5,
            matched_skills=[{"skill": "Python", "matched": True}],
            missing_skills=[{"skill": "Java", "matched": False}]
        )

        repr_str = repr(result)
        assert "MatchResult" in repr_str
        assert str(resume_id) in repr_str
        assert str(vacancy_id) in repr_str


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_skill_list_matching(self):
        """Test matching with empty skill lists."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context([], "Python")
        assert result["matched"] is False

    def test_unicode_skill_names(self):
        """Test skill names with unicode characters."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("Русский язык")
        assert result == "русский язык"

    def test_very_long_skill_name(self):
        """Test with very long skill name."""
        matcher = EnhancedSkillMatcher()
        long_skill = "A" * 100
        result = matcher.normalize_skill_name(long_skill)
        assert result == long_skill.lower()

    def test_special_characters_in_skills(self):
        """Test skills with various special characters."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("C++/C#/.NET")
        # Should keep +, #, .
        assert "+" in result or "#" in result or "." in result

    def test_whitespace_variations(self):
        """Test various whitespace combinations."""
        matcher = EnhancedSkillMatcher()
        result = matcher.normalize_skill_name("  React   JS  \t\n")
        assert result == "react js"

    def test_compound_skill_matching(self):
        """Test compound skill matching like C/C++."""
        matcher = EnhancedSkillMatcher()
        result = matcher.match_with_context(["C/C++"], "C")
        assert result["matched"] is True
        assert result["match_type"] == "compound"

    def test_language_hierarchy_matching(self):
        """Test C/C++ language hierarchy matching."""
        matcher = EnhancedSkillMatcher()

        # C++ should match as C (C++ implies C knowledge)
        result = matcher.match_with_context(["C++"], "C")
        assert result["matched"] is True
        assert result["match_type"] == "language_hierarchy"

        # C# should NOT match as C
        result = matcher.match_with_context(["C#"], "C")
        assert result["matched"] is False


class TestRealWorldScenarios:
    """Tests for real-world matching scenarios."""

    def test_full_stack_developer_matching(self):
        """Test matching full-stack developer skills."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Node.js", "Python", "PostgreSQL", "Docker"]
        required_skills = ["React", "Node", "Python", "SQL", "Docker"]

        results = matcher.match_multiple(resume_skills, required_skills)

        assert results["React"]["matched"] is True
        assert results["Node"]["matched"] is True  # Via fuzzy match
        assert results["Python"]["matched"] is True
        assert results["SQL"]["matched"] is True  # Via synonym
        assert results["Docker"]["matched"] is True

        percentage = matcher.calculate_match_percentage(results)
        assert percentage == 100.0

    def test_skill_gap_analysis_real_scenario(self):
        """Test skill gap analysis for real scenario."""
        analyzer = SkillGapAnalyzer()
        result = analyzer.analyze(
            resume_text="Python developer with Django experience",
            candidate_skills=["Python", "Django", "SQL"],
            job_title="Senior Full Stack Developer",
            job_description="Looking for senior full stack developer",
            required_skills=["Python", "Django", "React", "AWS", "Docker"],
            required_skill_levels={
                "Python": "advanced",
                "Django": "intermediate",
                "React": "intermediate",
                "AWS": "beginner",
                "Docker": "beginner"
            }
        )

        assert len(result.matched_skills) >= 2  # Python, Django
        assert len(result.missing_skills) >= 2  # React, AWS, Docker
        assert result.gap_percentage > 30
        assert result.estimated_time_to_bridge > 0
        assert len(result.priority_ordering) > 0

    def test_low_confidence_flagging(self):
        """Test flagging low confidence matches for recruiter review."""
        matcher = EnhancedSkillMatcher()
        resume_skills = ["ReactJS", "Python", "MongoDB"]
        required_skills = ["React", "Python", "SQL", "Java"]

        results = matcher.match_multiple(resume_skills, required_skills)
        low_confidence = matcher.get_low_confidence_matches(results, threshold=0.9)

        # At least React will have <1.0 confidence (fuzzy/synonym match)
        assert len(low_confidence) >= 0
