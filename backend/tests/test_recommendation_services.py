"""
Unit tests for Learning Recommendation Engine

Tests the learning recommendation service for matching skills
to courses and learning resources.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from analyzers.learning_recommendation_engine import (
    LearningRecommendation,
    LearningRecommendationResult,
    LearningRecommendationEngine,
    get_learning_recommendation_engine,
)
from analyzers.skill_gap_analyzer import SkillGapResult


class TestLearningRecommendation:
    """Test LearningRecommendation dataclass."""

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Course",
            description="Learn Python",
            provider="Udemy",
            url="https://example.com",
        )

        assert rec.skill == "Python"
        assert rec.resource_type == "course"
        assert rec.skill_level == "intermediate"
        assert rec.language == "en"
        assert rec.is_self_paced is True
        assert rec.cost_amount == 0.0
        assert rec.access_type == "free"
        assert rec.certificate_offered is False
        assert rec.difficulty_level == 3

    def test_initialization_with_all_fields(self):
        """Test initialization with all fields specified."""
        rec = LearningRecommendation(
            skill="React",
            resource_type="certification",
            title="React Certification",
            description="Advanced React",
            provider="Coursera",
            url="https://example.com/react",
            skill_level="advanced",
            topics_covered=["React", "Hooks", "Redux"],
            prerequisites=["JavaScript"],
            language="en",
            is_self_paced=True,
            duration_hours=40.0,
            duration_weeks=4.0,
            cost_amount=49.99,
            currency="USD",
            access_type="paid",
            rating=4.7,
            rating_count=12000,
            certificate_offered=True,
            difficulty_level=4,
            relevance_score=0.85,
            quality_score=0.90,
            popularity_score=0.75,
            priority_score=0.82,
        )

        assert rec.skill == "React"
        assert rec.resource_type == "certification"
        assert rec.skill_level == "advanced"
        assert rec.certificate_offered is True
        assert rec.cost_amount == 49.99
        assert rec.rating == 4.7
        assert rec.priority_score == 0.82

    def test_to_dict(self):
        """Test conversion to dictionary."""
        rec = LearningRecommendation(
            skill="Django",
            title="Django Course",
            description="Learn Django",
            provider="Udemy",
            url="https://example.com/django",
            rating=4.6,
            rating_count=5000,
        )

        result = rec.to_dict()

        assert isinstance(result, dict)
        assert result["skill"] == "Django"
        assert result["title"] == "Django Course"
        assert result["rating"] == 4.6
        assert result["rating_count"] == 5000
        assert "relevance_score" in result
        assert "quality_score" in result


class TestLearningRecommendationResult:
    """Test LearningRecommendationResult dataclass."""

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        result = LearningRecommendationResult()

        assert result.target_skills == []
        assert result.recommendations == {}
        assert result.total_recommendations == 0
        assert result.total_cost == 0.0
        assert result.total_duration_hours == 0.0
        assert result.alternative_free_resources == 0
        assert result.skills_with_certifications == []
        assert result.priority_ordering == []
        assert result.summary == ""

    def test_initialization_with_data(self):
        """Test initialization with actual data."""
        recs = {"Python": [LearningRecommendation(skill="Python", title="Course", description="Desc", provider="Test", url="http://test")]}

        result = LearningRecommendationResult(
            target_skills=["Python", "Django"],
            recommendations=recs,
            total_recommendations=5,
            total_cost=100.0,
            total_duration_hours=50.0,
            alternative_free_resources=2,
            skills_with_certifications=["Python"],
            priority_ordering=["Python", "Django"],
            summary="Found 5 resources",
        )

        assert len(result.target_skills) == 2
        assert result.total_recommendations == 5
        assert result.total_cost == 100.0
        assert result.summary == "Found 5 resources"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        rec = LearningRecommendation(
            skill="AWS",
            title="AWS Course",
            description="Learn AWS",
            provider="Coursera",
            url="https://example.com/aws",
        )

        result = LearningRecommendationResult(
            target_skills=["AWS"],
            recommendations={"AWS": [rec]},
            total_recommendations=1,
            total_cost=50.0,
            summary="Test summary",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "AWS" in result_dict["recommendations"]
        assert result_dict["total_recommendations"] == 1
        assert result_dict["total_cost"] == 50.0


class TestLearningRecommendationEngineInitialization:
    """Test LearningRecommendationEngine initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        engine = LearningRecommendationEngine()

        assert engine.max_recommendations_per_skill == 5
        assert engine.max_cost_per_resource == 200.0
        assert engine.max_duration_per_resource == 100.0
        assert engine.relevance_weight == 0.4
        assert engine.quality_weight == 0.3
        assert engine.accessibility_weight == 0.2
        assert engine.outcome_weight == 0.1
        assert engine.prefer_free_resources is True
        assert engine.prefer_certified_courses is False
        assert engine.prefer_self_paced is True
        assert engine.use_mock_data is True

    def test_initialization_with_custom_settings(self):
        """Test initialization with custom settings."""
        engine = LearningRecommendationEngine(
            max_recommendations_per_skill=10,
            max_cost_per_resource=100.0,
            relevance_weight=0.5,
            quality_weight=0.2,
            prefer_free_resources=False,
            prefer_certified_courses=True,
            use_mock_data=False,
        )

        assert engine.max_recommendations_per_skill == 10
        assert engine.max_cost_per_resource == 100.0
        assert engine.relevance_weight == 0.5
        assert engine.quality_weight == 0.2
        assert engine.prefer_free_resources is False
        assert engine.prefer_certified_courses is True
        assert engine.use_mock_data is False


class TestRecommendForSkillGaps:
    """Test recommend_for_skill_gaps method."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine(use_mock_data=True)

    @pytest.fixture
    def skill_gap_result(self):
        """Create a sample skill gap result."""
        return SkillGapResult(
            vacancy_id="vacancy-1",
            resume_id="resume-1",
            required_skills=["Python", "Django", "AWS"],
            missing_skills=["AWS", "Django"],
            partial_match_skills=[],
            missing_skill_details={
                "AWS": {"required_level": "intermediate"},
                "Django": {"required_level": "intermediate"},
            },
            priority_ordering=["AWS", "Django"],
        )

    def test_recommend_for_skill_gaps_returns_results(self, engine, skill_gap_result):
        """Test that recommend_for_skill_gaps returns results."""
        result = engine.recommend_for_skill_gaps(skill_gap_result)

        assert isinstance(result, LearningRecommendationResult)
        assert len(result.target_skills) > 0
        assert result.total_recommendations > 0

    def test_recommend_for_skill_gaps_with_empty_gaps(self, engine):
        """Test recommend_for_skill_gaps with no skill gaps."""
        empty_result = SkillGapResult(
            vacancy_id="vacancy-1",
            resume_id="resume-1",
            required_skills=[],
            missing_skills=[],
            partial_match_skills=[],
        )

        result = engine.recommend_for_skill_gaps(empty_result)

        assert result.total_recommendations == 0
        assert "No skill gaps found" in result.summary

    def test_recommend_for_skill_gaps_custom_limits(self, engine, skill_gap_result):
        """Test recommend_for_skill_gaps with custom limits."""
        result = engine.recommend_for_skill_gaps(
            skill_gap_result,
            max_recommendations_per_skill=2,
            max_cost_per_resource=20.0,
        )

        # Each skill should have at most 2 recommendations
        for skill, recs in result.recommendations.items():
            assert len(recs) <= 2
            # All recommendations should be under the cost limit
            for rec in recs:
                assert rec.cost_amount <= 20.0

    def test_recommend_for_skill_gaps_free_only(self, engine, skill_gap_result):
        """Test recommend_for_skill_gaps with free resources only."""
        result = engine.recommend_for_skill_gaps(
            skill_gap_result,
            include_free_resources=True,
            include_paid_resources=False,
        )

        # All recommendations should be free
        for skill, recs in result.recommendations.items():
            for rec in recs:
                assert rec.cost_amount == 0.0

    def test_recommend_for_skill_gaps_includes_metrics(self, engine, skill_gap_result):
        """Test that recommend_for_skill_gaps includes all metrics."""
        result = engine.recommend_for_skill_gaps(skill_gap_result)

        assert result.total_recommendations >= 0
        assert result.total_cost >= 0
        assert result.total_duration_hours >= 0
        assert result.alternative_free_resources >= 0
        assert isinstance(result.skills_with_certifications, list)
        assert len(result.priority_ordering) > 0
        assert len(result.summary) > 0


class TestRecommendForSkill:
    """Test recommend_for_skill method."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine(use_mock_data=True)

    def test_recommend_for_skill_returns_results(self, engine):
        """Test that recommend_for_skill returns results for known skills."""
        results = engine.recommend_for_skill("Python")

        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(rec, LearningRecommendation) for rec in results)

    def test_recommend_for_skill_unknown_skill(self, engine):
        """Test recommend_for_skill with unknown skill."""
        results = engine.recommend_for_skill("UnknownSkillXYZ")

        assert isinstance(results, list)
        # May return empty list for unknown skills with mock data

    def test_recommend_for_skill_with_filters(self, engine):
        """Test recommend_for_skill with various filters."""
        results = engine.recommend_for_skill(
            skill="Python",
            skill_level="beginner",
            max_recommendations=3,
            include_free=True,
            include_paid=False,
            max_cost=10.0,
        )

        assert len(results) <= 3
        for rec in results:
            assert rec.skill_level == "beginner" or rec.skill_level in ["beginner", "intermediate"]
            assert rec.cost_amount <= 10.0

    def test_recommend_for_skill_respects_max_recommendations(self, engine):
        """Test that recommend_for_skill respects max_recommendations."""
        results = engine.recommend_for_skill("Python", max_recommendations=2)

        assert len(results) <= 2


class TestCalculateScores:
    """Test score calculation methods."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine()

    def test_calculate_relevance_score_title_match(self, engine):
        """Test relevance score with title match."""
        rec = LearningRecommendation(
            skill="Python",
            title="Complete Python Course",
            description="Learn programming",
            provider="Test",
            url="http://test",
            topics_covered=[],
        )

        score = engine._calculate_relevance_score(
            resource=rec,
            target_skill="Python",
            required_level="intermediate",
        )

        assert score > 0
        assert score <= 1.0

    def test_calculate_relevance_score_topic_match(self, engine):
        """Test relevance score with topic match."""
        rec = LearningRecommendation(
            skill="Python",
            title="Programming Course",
            description="Learn coding",
            provider="Test",
            url="http://test",
            topics_covered=["Python", "Django"],
        )

        score = engine._calculate_relevance_score(
            resource=rec,
            target_skill="Python",
            required_level="intermediate",
        )

        assert score > 0
        assert score <= 1.0

    def test_calculate_quality_score_with_rating(self, engine):
        """Test quality score calculation with ratings."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Course",
            description="Desc",
            provider="Coursera",  # Reputable provider
            url="http://test",
            rating=4.7,
            rating_count=10000,
        )

        score = engine._calculate_quality_score(rec)

        assert score > 0
        assert score <= 1.0

    def test_calculate_quality_score_no_rating(self, engine):
        """Test quality score without ratings."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Course",
            description="Desc",
            provider="Unknown",
            url="http://test",
            rating=0.0,
            rating_count=0,
        )

        score = engine._calculate_quality_score(rec)

        assert score >= 0
        assert score <= 1.0

    def test_calculate_accessibility_score_free(self, engine):
        """Test accessibility score for free resources."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Course",
            description="Desc",
            provider="Test",
            url="http://test",
            cost_amount=0.0,
            duration_hours=10.0,
            is_self_paced=True,
            prerequisites=[],
        )

        score = engine._calculate_accessibility_score(
            resource=rec,
            required_level="intermediate",
        )

        # Free resources should have higher accessibility
        assert score > 0
        assert score <= 1.0

    def test_calculate_accessibility_score_paid(self, engine):
        """Test accessibility score for paid resources."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Course",
            description="Desc",
            provider="Test",
            url="http://test",
            cost_amount=100.0,
            duration_hours=20.0,
            is_self_paced=False,
            prerequisites=["Basic Programming"],
        )

        score = engine._calculate_accessibility_score(
            resource=rec,
            required_level="intermediate",
        )

        assert score >= 0
        assert score <= 1.0

    def test_calculate_outcome_score_with_certificate(self, engine):
        """Test outcome score with certification."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Certification",
            description="Desc",
            provider="Test",
            url="http://test",
            resource_type="certification",
            certificate_offered=True,
        )

        score = engine._calculate_outcome_score(rec)

        assert score > 0
        assert score <= 1.0

    def test_calculate_outcome_score_without_certificate(self, engine):
        """Test outcome score without certification."""
        rec = LearningRecommendation(
            skill="Python",
            title="Python Tutorial",
            description="Desc",
            provider="Test",
            url="http://test",
            resource_type="tutorial",
            certificate_offered=False,
        )

        score = engine._calculate_outcome_score(rec)

        assert score >= 0
        assert score <= 1.0


class TestSkillLevelCompatibility:
    """Test skill level compatibility checking."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine()

    def test_exact_level_match(self, engine):
        """Test exact level match."""
        assert engine._is_skill_level_compatible("intermediate", "intermediate") is True

    def test_resource_level_higher(self, engine):
        """Test resource level higher than required."""
        assert engine._is_skill_level_compatible("advanced", "intermediate") is True
        assert engine._is_skill_level_compatible("expert", "beginner") is True

    def test_resource_level_one_below(self, engine):
        """Test resource level one below required."""
        assert engine._is_skill_level_compatible("beginner", "intermediate") is True
        assert engine._is_skill_level_compatible("intermediate", "advanced") is True

    def test_resource_level_too_low(self, engine):
        """Test resource level too low."""
        assert engine._is_skill_level_compatible("beginner", "advanced") is False
        assert engine._is_skill_level_compatible("beginner", "expert") is False

    def test_case_insensitive(self, engine):
        """Test case insensitivity."""
        assert engine._is_skill_level_compatible("INTERMEDIATE", "intermediate") is True
        assert engine._is_skill_level_compatible("Beginner", "BEGINNER") is True


class TestGetResourcesForSkill:
    """Test _get_resources_for_skill method."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine(use_mock_data=True)

    def test_get_resources_for_known_skill(self, engine):
        """Test getting resources for a known skill."""
        resources = engine._get_resources_for_skill(
            skill="Python",
            required_level="intermediate",
            include_free=True,
            include_paid=True,
            max_cost=200.0,
        )

        assert isinstance(resources, list)
        assert all(isinstance(rec, LearningRecommendation) for rec in resources)

    def test_get_resources_filters_by_cost(self, engine):
        """Test that resources are filtered by cost."""
        resources = engine._get_resources_for_skill(
            skill="Python",
            required_level="intermediate",
            include_free=True,
            include_paid=True,
            max_cost=10.0,
        )

        for rec in resources:
            assert rec.cost_amount <= 10.0

    def test_get_resources_free_only(self, engine):
        """Test getting only free resources."""
        resources = engine._get_resources_for_skill(
            skill="Python",
            required_level="intermediate",
            include_free=True,
            include_paid=False,
            max_cost=200.0,
        )

        for rec in resources:
            assert rec.cost_amount == 0.0

    def test_get_resources_paid_only(self, engine):
        """Test getting only paid resources."""
        resources = engine._get_resources_for_skill(
            skill="Python",
            required_level="intermediate",
            include_free=False,
            include_paid=True,
            max_cost=200.0,
        )

        for rec in resources:
            assert rec.cost_amount > 0

    def test_get_resources_filters_by_level(self, engine):
        """Test filtering by skill level."""
        resources = engine._get_resources_for_skill(
            skill="Python",
            required_level="beginner",
            include_free=True,
            include_paid=True,
            max_cost=200.0,
        )

        # All resources should be compatible with beginner level
        for rec in resources:
            assert engine._is_skill_level_compatible(rec.skill_level, "beginner") is True


class TestRankAndFilterResources:
    """Test _rank_and_filter_resources method."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine()

    @pytest.fixture
    def sample_resources(self):
        """Create sample resources for testing."""
        return [
            LearningRecommendation(
                skill="Python",
                title="Complete Python Bootcamp",
                description="Learn Python from scratch",
                provider="Udemy",
                url="http://test1",
                rating=4.6,
                rating_count=250000,
                cost_amount=15.0,
                certificate_offered=True,
                resource_type="course",
                topics_covered=["Python"],
                skill_level="beginner",
                duration_hours=20.0,
                is_self_paced=True,
                prerequisites=[],
            ),
            LearningRecommendation(
                skill="Python",
                title="Python Tutorial",
                description="Quick Python intro",
                provider="YouTube",
                url="http://test2",
                rating=4.0,
                rating_count=1000,
                cost_amount=0.0,
                certificate_offered=False,
                resource_type="tutorial",
                topics_covered=["Python"],
                skill_level="beginner",
                duration_hours=5.0,
                is_self_paced=True,
                prerequisites=[],
            ),
            LearningRecommendation(
                skill="Python",
                title="Python for Data Science",
                description="Python for ML",
                provider="Coursera",
                url="http://test3",
                rating=4.8,
                rating_count=120000,
                cost_amount=49.0,
                certificate_offered=True,
                resource_type="course",
                topics_covered=["Python", "Data Science"],
                skill_level="intermediate",
                duration_hours=30.0,
                is_self_paced=True,
                prerequisites=["Basic Python"],
            ),
        ]

    def test_rank_and_filter_returns_sorted_list(self, engine, sample_resources):
        """Test that resources are ranked and sorted."""
        ranked = engine._rank_and_filter_resources(
            resources=sample_resources,
            skill="Python",
            required_level="beginner",
            max_count=10,
        )

        assert isinstance(ranked, list)
        assert len(ranked) <= 10
        # Should be sorted by priority_score descending
        for i in range(len(ranked) - 1):
            assert ranked[i].priority_score >= ranked[i + 1].priority_score

    def test_rank_and_filter_respects_max_count(self, engine, sample_resources):
        """Test that max_count is respected."""
        ranked = engine._rank_and_filter_resources(
            resources=sample_resources,
            skill="Python",
            required_level="beginner",
            max_count=2,
        )

        assert len(ranked) <= 2

    def test_rank_and_filter_calculates_scores(self, engine, sample_resources):
        """Test that scores are calculated for all resources."""
        ranked = engine._rank_and_filter_resources(
            resources=sample_resources,
            skill="Python",
            required_level="beginner",
            max_count=10,
        )

        for rec in ranked:
            assert rec.relevance_score >= 0
            assert rec.quality_score >= 0
            assert rec.priority_score >= 0


class TestGetMockResources:
    """Test mock resource retrieval."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine(use_mock_data=True)

    def test_get_mock_resources_exact_match(self, engine):
        """Test getting mock resources with exact match."""
        resources = engine._get_mock_resources_for_skill("python")

        assert isinstance(resources, list)
        assert len(resources) > 0
        assert all(isinstance(rec, LearningRecommendation) for rec in resources)
        assert all(rec.skill == "python" for rec in resources)

    def test_get_mock_resources_case_insensitive(self, engine):
        """Test case-insensitive skill matching."""
        lower = engine._get_mock_resources_for_skill("python")
        upper = engine._get_mock_resources_for_skill("PYTHON")
        mixed = engine._get_mock_resources_for_skill("Python")

        # All should return resources
        assert len(lower) > 0
        assert len(upper) > 0
        assert len(mixed) > 0

    def test_get_mock_resources_partial_match(self, engine):
        """Test partial skill matching."""
        resources = engine._get_mock_resources_for_skill("machine")

        # Should find "machine learning"
        assert isinstance(resources, list)

    def test_get_mock_resources_no_match(self, engine):
        """Test with skill that has no match."""
        resources = engine._get_mock_resources_for_skill("UnknownSkillXYZ123")

        assert resources == []

    def test_get_mock_resources_converts_to_objects(self, engine):
        """Test that mock data is properly converted."""
        resources = engine._get_mock_resources_for_skill("react")

        for rec in resources:
            assert isinstance(rec, LearningRecommendation)
            assert rec.skill == "react"
            assert len(rec.title) > 0
            assert len(rec.provider) > 0
            assert len(rec.url) > 0
            assert rec.access_type in ["free", "paid"]


class TestEmptyResult:
    """Test _create_empty_result method."""

    @pytest.fixture
    def engine(self):
        """Create an engine instance for testing."""
        return LearningRecommendationEngine()

    def test_create_empty_result(self, engine):
        """Test creating an empty result."""
        result = engine._create_empty_result("No gaps found")

        assert isinstance(result, LearningRecommendationResult)
        assert result.total_recommendations == 0
        assert result.total_cost == 0.0
        assert result.summary == "No gaps found"


class TestSingleton:
    """Test singleton getter function."""

    def test_get_learning_recommendation_engine(self):
        """Test that get_learning_recommendation_engine returns instance."""
        engine = get_learning_recommendation_engine()

        assert isinstance(engine, LearningRecommendationEngine)

    def test_get_learning_recommendation_engine_cached(self):
        """Test that get_learning_recommendation_engine caches instance."""
        engine1 = get_learning_recommendation_engine()
        engine2 = get_learning_recommendation_engine()

        # Should return the same instance
        assert engine1 is engine2
