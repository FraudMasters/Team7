"""
Tests for resume comparator module.

Tests cover comparison analysis, competitive positioning,
skill gap analysis, and ranking prediction.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from analyzers.resume_comparator import (
    ResumeComparator,
    ComparisonMetric,
    ComparisonResult,
    get_resume_comparator,
)


class TestComparisonMetric:
    """Tests for ComparisonMetric dataclass."""

    def test_metric_creation(self):
        """Test creating a comparison metric."""
        metric = ComparisonMetric(
            metric_name="skills_count",
            candidate_value=10.0,
            top_performers_avg=12.0,
            top_performers_max=20.0,
        )
        assert metric.metric_name == "skills_count"
        assert metric.candidate_value == 10.0
        assert metric.top_performers_avg == 12.0
        assert metric.top_performers_max == 20.0

    def test_metric_with_all_fields(self):
        """Test metric with all optional fields."""
        metric = ComparisonMetric(
            metric_name="experience",
            candidate_value=60.0,
            top_performers_avg=48.0,
            top_performers_max=120.0,
            percentile=75.0,
            gap=12.0,
            competitive_position="leading",
        )
        assert metric.percentile == 75.0
        assert metric.gap == 12.0
        assert metric.competitive_position == "leading"

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        metric = ComparisonMetric(
            metric_name="score",
            candidate_value=85.5,
            top_performers_avg=70.0,
            top_performers_max=95.0,
            percentile=90.0,
            gap=15.5,
            competitive_position="leading",
        )
        result = metric.to_dict()

        assert result["metric_name"] == "score"
        assert result["candidate_value"] == 85.5
        assert result["percentile"] == 90.0
        assert result["competitive_position"] == "leading"


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_result_creation(self):
        """Test creating a comparison result."""
        resume_id = uuid4()
        result = ComparisonResult(
            candidate_resume_id=resume_id,
            job_role="Software Engineer",
            top_performers_count=10,
        )
        assert result.candidate_resume_id == resume_id
        assert result.job_role == "Software Engineer"
        assert result.top_performers_count == 10

    def test_result_with_metrics(self):
        """Test result with metrics."""
        resume_id = uuid4()
        metrics = [
            ComparisonMetric("skill_count", 15.0, 12.0, 20.0),
            ComparisonMetric("experience", 60.0, 48.0, 96.0),
        ]
        result = ComparisonResult(
            candidate_resume_id=resume_id,
            metrics=metrics,
        )
        assert len(result.metrics) == 2

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        resume_id = uuid4()
        result = ComparisonResult(
            candidate_resume_id=resume_id,
            job_role="Python Developer",
            top_performers_count=5,
            overall_competitiveness_score=75.5,
            competitiveness_tier="strong",
        )
        d = result.to_dict()

        assert d["candidate_resume_id"] == str(resume_id)
        assert d["job_role"] == "Python Developer"
        assert d["overall_competitiveness_score"] == 75.5
        assert d["competitiveness_tier"] == "strong"


class TestResumeComparatorInit:
    """Tests for ResumeComparator initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        comparator = ResumeComparator()
        assert comparator.top_tier_threshold == 80.0
        assert comparator.strong_tier_threshold == 60.0
        assert comparator.average_tier_threshold == 40.0
        assert comparator.leading_threshold == 1.1
        assert comparator.competitive_threshold == 0.9
        assert comparator.min_top_performers == 3

    def test_custom_thresholds(self):
        """Test custom thresholds."""
        comparator = ResumeComparator(
            top_tier_threshold=90.0,
            strong_tier_threshold=70.0,
            average_tier_threshold=50.0,
        )
        assert comparator.top_tier_threshold == 90.0
        assert comparator.strong_tier_threshold == 70.0
        assert comparator.average_tier_threshold == 50.0


class TestDetermineCompetitivePosition:
    """Tests for _determine_competitive_position method."""

    def test_leading_position(self):
        """Test leading competitive position."""
        comparator = ResumeComparator()
        position = comparator._determine_competitive_position(110.0, 100.0)
        assert position == "leading"

    def test_competitive_position(self):
        """Test competitive position."""
        comparator = ResumeComparator()
        position = comparator._determine_competitive_position(95.0, 100.0)
        assert position == "competitive"

    def test_trailing_position(self):
        """Test trailing position."""
        comparator = ResumeComparator()
        position = comparator._determine_competitive_position(80.0, 100.0)
        assert position == "trailing"

    def test_zero_average(self):
        """Test with zero average."""
        comparator = ResumeComparator()
        position = comparator._determine_competitive_position(50.0, 0.0)
        assert position == "unknown"


class TestCalculatePercentile:
    """Tests for _calculate_percentile method."""

    def test_percentile_calculation(self):
        """Test percentile calculation."""
        comparator = ResumeComparator()
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        percentile = comparator._calculate_percentile(30.0, values)
        assert 40.0 <= percentile <= 60.0

    def test_percentile_highest(self):
        """Test percentile for highest value."""
        comparator = ResumeComparator()
        values = [10.0, 20.0, 30.0, 40.0]
        percentile = comparator._calculate_percentile(50.0, values)
        assert percentile == 100.0

    def test_percentile_lowest(self):
        """Test percentile for lowest value."""
        comparator = ResumeComparator()
        values = [20.0, 30.0, 40.0, 50.0]
        percentile = comparator._calculate_percentile(10.0, values)
        assert percentile == 0.0

    def test_percentile_empty_values(self):
        """Test percentile with empty values."""
        comparator = ResumeComparator()
        percentile = comparator._calculate_percentile(50.0, [])
        assert percentile == 50.0


class TestCompareMetric:
    """Tests for _compare_metric method."""

    def test_compare_single_metric(self):
        """Test comparing a single metric."""
        comparator = ResumeComparator()
        metric = comparator._compare_metric(
            metric_name="skills_count",
            candidate_value=15.0,
            top_performers_values=[10.0, 12.0, 14.0, 16.0],
        )
        assert metric.metric_name == "skills_count"
        assert metric.candidate_value == 15.0
        assert metric.top_performers_avg == 13.0
        assert metric.top_performers_max == 16.0
        assert metric.gap == 2.0

    def test_compare_metric_empty_values(self):
        """Test comparing with empty top performer values."""
        comparator = ResumeComparator()
        metric = comparator._compare_metric(
            metric_name="experience",
            candidate_value=60.0,
            top_performers_values=[],
        )
        assert metric.candidate_value == 60.0
        assert metric.top_performers_avg == 0.0
        assert metric.top_performers_max == 0.0


class TestExtractStrengthsAndGaps:
    """Tests for _extract_strengths_and_gaps method."""

    def test_extract_strengths(self):
        """Test extracting strengths from metrics."""
        comparator = ResumeComparator()
        metrics = [
            ComparisonMetric("skill1", 110.0, 100.0, 100.0, competitive_position="leading"),
            ComparisonMetric("skill2", 95.0, 100.0, 100.0, competitive_position="competitive"),
        ]
        strengths, improvements = comparator._extract_strengths_and_gaps(metrics)

        assert len(strengths) == 1
        assert "skill1" in strengths[0]
        assert len(improvements) == 0

    def test_extract_improvement_areas(self):
        """Test extracting improvement areas."""
        comparator = ResumeComparator()
        metrics = [
            ComparisonMetric("skill1", 80.0, 100.0, 100.0, competitive_position="trailing", gap=-20.0),
        ]
        strengths, improvements = comparator._extract_strengths_and_gaps(metrics)

        assert len(improvements) == 1
        assert "skill1" in improvements[0]
        assert len(strengths) == 0

    def test_mixed_metrics(self):
        """Test extracting from mixed metrics."""
        comparator = ResumeComparator()
        metrics = [
            ComparisonMetric("skill1", 110.0, 100.0, 100.0, competitive_position="leading", percentile=90.0),
            ComparisonMetric("skill2", 80.0, 100.0, 100.0, competitive_position="trailing", gap=-20.0),
            ComparisonMetric("skill3", 95.0, 100.0, 100.0, competitive_position="competitive"),
        ]
        strengths, improvements = comparator._extract_strengths_and_gaps(metrics)

        assert len(strengths) == 1
        assert len(improvements) == 1


class TestCompareSkills:
    """Tests for _compare_skills method."""

    def test_compare_skills_matching(self):
        """Test skill comparison with matching skills."""
        comparator = ResumeComparator()
        candidate_skills = ["python", "javascript", "react"]
        top_performers_skills = [
            ["python", "javascript", "nodejs"],
            ["python", "react", "typescript"],
        ]
        competitive, missing = comparator._compare_skills(
            candidate_skills, top_performers_skills
        )

        # python appears in both top performers, should be competitive
        assert "python" in competitive
        # javascript appears in 1/2 (50%), should be competitive
        assert "javascript" in competitive or "react" in competitive

    def test_compare_skills_missing(self):
        """Test skill comparison with missing skills."""
        comparator = ResumeComparator()
        candidate_skills = ["python"]
        top_performers_skills = [
            ["python", "docker", "kubernetes"],
            ["python", "docker", "aws"],
        ]
        competitive, missing = comparator._compare_skills(
            candidate_skills, top_performers_skills
        )

        # docker appears in both top performers, should be missing
        assert "docker" in missing

    def test_compare_skills_empty_top_performers(self):
        """Test skill comparison with empty top performers."""
        comparator = ResumeComparator()
        competitive, missing = comparator._compare_skills(["python"], [])

        assert len(competitive) == 0
        assert len(missing) == 0


class TestCalculateOverallScore:
    """Tests for _calculate_overall_score method."""

    def test_calculate_score_average(self):
        """Test score calculation as average of percentiles."""
        comparator = ResumeComparator()
        metrics = [
            ComparisonMetric("m1", 0, 0, 0, percentile=60.0),
            ComparisonMetric("m2", 0, 0, 0, percentile=80.0),
        ]
        score = comparator._calculate_overall_score(metrics)
        assert score == 70.0

    def test_calculate_score_empty(self):
        """Test score calculation with empty metrics."""
        comparator = ResumeComparator()
        score = comparator._calculate_overall_score([])
        assert score == 0.0


class TestDetermineTier:
    """Tests for _determine_tier method."""

    def test_top_tier(self):
        """Test top tier classification."""
        comparator = ResumeComparator()
        assert comparator._determine_tier(85.0) == "top"
        assert comparator._determine_tier(95.0) == "top"

    def test_strong_tier(self):
        """Test strong tier classification."""
        comparator = ResumeComparator()
        assert comparator._determine_tier(65.0) == "strong"
        assert comparator._determine_tier(79.0) == "strong"

    def test_average_tier(self):
        """Test average tier classification."""
        comparator = ResumeComparator()
        assert comparator._determine_tier(45.0) == "average"
        assert comparator._determine_tier(59.0) == "average"

    def test_weak_tier(self):
        """Test weak tier classification."""
        comparator = ResumeComparator()
        assert comparator._determine_tier(30.0) == "weak"
        assert comparator._determine_tier(10.0) == "weak"


class TestGenerateRecommendations:
    """Tests for _generate_recommendations method."""

    def test_recommendations_for_missing_skills(self):
        """Test recommendations for missing skills."""
        comparator = ResumeComparator()
        recommendations = comparator._generate_recommendations(
            improvement_areas=[],
            missing_skills=["docker", "kubernetes"],
            competitiveness_tier="average",
        )
        assert len(recommendations) > 0
        assert any("docker" in r.lower() or "kubernetes" in r.lower() for r in recommendations)

    def test_recommendations_for_weak_tier(self):
        """Test recommendations for weak tier."""
        comparator = ResumeComparator()
        recommendations = comparator._generate_recommendations(
            improvement_areas=[],
            missing_skills=[],
            competitiveness_tier="weak",
        )
        assert any("restructuring" in r.lower() for r in recommendations)

    def test_recommendations_for_strong_tier(self):
        """Test recommendations for strong tier."""
        comparator = ResumeComparator()
        recommendations = comparator._generate_recommendations(
            improvement_areas=[],
            missing_skills=[],
            competitiveness_tier="strong",
        )
        assert any("refine" in r.lower() or "polish" in r.lower() for r in recommendations)


class TestBuildBenchmarkSummary:
    """Tests for _build_benchmark_summary method."""

    def test_summary_top_tier(self):
        """Test summary for top tier."""
        comparator = ResumeComparator()
        summary = comparator._build_benchmark_summary(
            competitiveness_tier="top",
            overall_score=85.0,
            top_performers_count=10,
        )
        assert "85.0" in summary
        assert "top" in summary.lower()

    def test_summary_weak_tier(self):
        """Test summary for weak tier."""
        comparator = ResumeComparator()
        summary = comparator._build_benchmark_summary(
            competitiveness_tier="weak",
            overall_score=25.0,
            top_performers_count=5,
        )
        assert "25.0" in summary
        assert "below average" in summary.lower()


class TestGetResumeComparator:
    """Tests for get_resume_comparator factory function."""

    def test_get_comparator_singleton(self):
        """Test that factory returns same instance."""
        # Reset singleton
        import analyzers.resume_comparator as module
        module._default_comparator = None

        comparator1 = get_resume_comparator()
        comparator2 = get_resume_comparator()

        assert comparator1 is comparator2

    def test_get_comparator_returns_instance(self):
        """Test that factory returns ResumeComparator instance."""
        import analyzers.resume_comparator as module
        module._default_comparator = None

        comparator = get_resume_comparator()
        assert isinstance(comparator, ResumeComparator)


class TestCompareAgainstTopPerformersIntegration:
    """Integration tests for compare_against_top_performers method."""

    @pytest.mark.asyncio
    async def test_compare_insufficient_top_performers(self):
        """Test comparison with insufficient top performers."""
        comparator = ResumeComparator(min_top_performers=3)

        # Mock database with only 2 top performers
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(id=uuid4())
        mock_db.execute.return_value = mock_result

        # Mock top performers query to return only 2
        mock_top_result = MagicMock()
        mock_top_result.scalars.return_value.all.return_value = [
            MagicMock(resume_id=uuid4()),
            MagicMock(resume_id=uuid4()),
        ]

        def side_effect(query):
            # First call gets resume, second gets top performers
            if not hasattr(side_effect, 'call_count'):
                side_effect.call_count = 0
            side_effect.call_count += 1

            if side_effect.call_count <= 2:
                return mock_result
            else:
                return mock_top_result

        mock_db.execute.side_effect = side_effect

        with pytest.raises(ValueError, match="Insufficient top performers"):
            await comparator.compare_against_top_performers(
                db=mock_db,
                candidate_resume_id=uuid4(),
            )
