"""
Tests for diversity metrics calculator.

Tests cover diversity metrics calculation, filtering by category,
goal progress tracking, and benchmark comparisons.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from calculators.diversity_metrics import (
    DiversityMetricsCalculator,
    DiversityMetricsResult,
    DemographicGroupMetrics,
    CategorySummary,
)


class TestDemographicGroupMetrics:
    """Tests for DemographicGroupMetrics model."""

    def test_valid_demographic_metrics(self):
        """Test creation of valid demographic group metrics."""
        metrics = DemographicGroupMetrics(
            demographic_category="gender",
            demographic_value="female",
            total_applicants=520,
            candidates_screened=385,
            candidates_interviewed=198,
            candidates_offered=42,
            candidates_hired=38,
            representation_percentage=0.416,
            screening_rate=0.740,
            interview_rate=0.514,
            offer_rate=0.212,
            hire_rate=0.905,
            conversion_rate=0.073,
        )

        assert metrics.demographic_category == "gender"
        assert metrics.demographic_value == "female"
        assert metrics.total_applicants == 520
        assert metrics.candidates_hired == 38
        assert metrics.representation_percentage == 0.416

    def test_demographic_metrics_with_minimal_fields(self):
        """Test creation of demographic metrics with only required fields."""
        metrics = DemographicGroupMetrics(
            demographic_category="ethnicity",
            demographic_value="asian",
        )

        assert metrics.demographic_category == "ethnicity"
        assert metrics.demographic_value == "asian"
        assert metrics.total_applicants == 0
        assert metrics.candidates_hired == 0
        assert metrics.representation_percentage == 0.0

    def test_demographic_metrics_with_goals(self):
        """Test demographic metrics with diversity goals."""
        metrics = DemographicGroupMetrics(
            demographic_category="age_group",
            demographic_value="25-34",
            total_applicants=550,
            representation_percentage=0.440,
            target_representation=0.45,
            goal_met=True,
            variance_from_target=-0.010,
        )

        assert metrics.target_representation == 0.45
        assert metrics.goal_met is True
        assert metrics.variance_from_target == -0.010


class TestCategorySummary:
    """Tests for CategorySummary model."""

    def test_valid_category_summary(self):
        """Test creation of valid category summary."""
        summary = CategorySummary(
            category="gender",
            total_groups=3,
            most_represented_group="male",
            least_represented_group="non-binary",
            diversity_index=0.65,
            goals_on_track=2,
            goals_behind=1,
        )

        assert summary.category == "gender"
        assert summary.total_groups == 3
        assert summary.diversity_index == 0.65
        assert summary.goals_on_track == 2

    def test_category_summary_with_minimal_fields(self):
        """Test category summary with only required fields."""
        summary = CategorySummary(
            category="ethnicity",
        )

        assert summary.category == "ethnicity"
        assert summary.total_groups == 0
        assert summary.diversity_index == 0.0


class TestDiversityMetricsResult:
    """Tests for DiversityMetricsResult model."""

    def test_valid_diversity_result(self):
        """Test creation of valid diversity metrics result."""
        demo1 = DemographicGroupMetrics(
            demographic_category="gender",
            demographic_value="female",
            total_applicants=520,
        )
        demo2 = DemographicGroupMetrics(
            demographic_category="gender",
            demographic_value="male",
            total_applicants=680,
        )
        category = CategorySummary(
            category="gender",
            total_groups=2,
        )

        result = DiversityMetricsResult(
            demographics=[demo1, demo2],
            categories=[category],
            total_applicants=1200,
            total_hired=90,
            overall_diversity_score=0.72,
            diversity_goals_met=5,
            diversity_goals_total=8,
            goals_achievement_rate=0.625,
        )

        assert len(result.demographics) == 2
        assert len(result.categories) == 1
        assert result.total_applicants == 1200
        assert result.overall_diversity_score == 0.72
        assert result.goals_achievement_rate == 0.625


class TestDiversityMetricsCalculator:
    """Tests for DiversityMetricsCalculator."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def calculator(self, mock_db):
        """Create a calculator instance with mock DB."""
        return DiversityMetricsCalculator(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_returns_metrics(self, calculator):
        """Test that calculate returns valid diversity metrics."""
        metrics = await calculator.calculate()

        assert isinstance(metrics, DiversityMetricsResult)
        assert metrics.total_applicants > 0
        assert metrics.total_hired > 0
        assert 0 <= metrics.overall_diversity_score <= 1
        assert len(metrics.demographics) > 0
        assert len(metrics.categories) > 0

    @pytest.mark.asyncio
    async def test_calculate_with_date_range(self, calculator):
        """Test calculate with date range filters."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        metrics = await calculator.calculate(
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(metrics, DiversityMetricsResult)
        assert metrics.total_applicants > 0

    @pytest.mark.asyncio
    async def test_calculate_with_vacancy_filter(self, calculator):
        """Test calculate with vacancy ID filter."""
        metrics = await calculator.calculate(vacancy_id="test-vacancy-id")

        assert isinstance(metrics, DiversityMetricsResult)
        assert metrics.total_applicants > 0

    @pytest.mark.asyncio
    async def test_calculate_includes_multiple_categories(self, calculator):
        """Test that results include multiple demographic categories."""
        metrics = await calculator.calculate()

        categories = {demo.demographic_category for demo in metrics.demographics}
        assert len(categories) > 1
        assert "gender" in categories
        assert "age_group" in categories
        assert "ethnicity" in categories

    @pytest.mark.asyncio
    async def test_calculate_computes_category_summaries(self, calculator):
        """Test that category summaries are computed correctly."""
        metrics = await calculator.calculate()

        assert len(metrics.categories) > 0
        for category in metrics.categories:
            assert category.total_groups > 0
            assert 0 <= category.diversity_index <= 1
            assert category.most_represented_group is not None
            assert category.least_represented_group is not None

    @pytest.mark.asyncio
    async def test_calculate_tracks_diversity_goals(self, calculator):
        """Test that diversity goals are tracked correctly."""
        metrics = await calculator.calculate()

        assert metrics.diversity_goals_total > 0
        assert metrics.diversity_goals_met >= 0
        assert metrics.diversity_goals_met <= metrics.diversity_goals_total
        assert 0 <= metrics.goals_achievement_rate <= 1

        # Verify goal achievement rate calculation
        if metrics.diversity_goals_total > 0:
            expected_rate = metrics.diversity_goals_met / metrics.diversity_goals_total
            assert abs(metrics.goals_achievement_rate - expected_rate) < 0.001

    @pytest.mark.asyncio
    async def test_calculate_identifies_top_and_improvement_categories(self, calculator):
        """Test that top performing and needs improvement categories are identified."""
        metrics = await calculator.calculate()

        assert metrics.top_performing_category is not None
        assert metrics.needs_improvement_category is not None
        assert metrics.top_performing_category != metrics.needs_improvement_category

    @pytest.mark.asyncio
    async def test_calculate_overall_diversity_score(self, calculator):
        """Test that overall diversity score is calculated correctly."""
        metrics = await calculator.calculate()

        assert 0 <= metrics.overall_diversity_score <= 1

        # Overall score should be average of category diversity indices
        if metrics.categories:
            expected_score = sum(c.diversity_index for c in metrics.categories) / len(metrics.categories)
            assert abs(metrics.overall_diversity_score - expected_score) < 0.001

    @pytest.mark.asyncio
    async def test_demographic_metrics_have_required_fields(self, calculator):
        """Test that all demographic metrics have required fields."""
        metrics = await calculator.calculate()

        for demo in metrics.demographics:
            assert demo.demographic_category is not None
            assert demo.demographic_value is not None
            assert demo.total_applicants >= 0
            assert demo.candidates_hired >= 0
            assert 0 <= demo.representation_percentage <= 1
            assert 0 <= demo.conversion_rate <= 1

    @pytest.mark.asyncio
    async def test_calculate_by_category_gender(self, calculator):
        """Test filtering by gender category."""
        gender_metrics = await calculator.calculate_by_category("gender")

        assert isinstance(gender_metrics, list)
        assert len(gender_metrics) > 0
        assert all(m.demographic_category == "gender" for m in gender_metrics)

        # Should have common gender values
        gender_values = {m.demographic_value for m in gender_metrics}
        assert "female" in gender_values or "male" in gender_values

    @pytest.mark.asyncio
    async def test_calculate_by_category_age_group(self, calculator):
        """Test filtering by age_group category."""
        age_metrics = await calculator.calculate_by_category("age_group")

        assert isinstance(age_metrics, list)
        assert len(age_metrics) > 0
        assert all(m.demographic_category == "age_group" for m in age_metrics)

    @pytest.mark.asyncio
    async def test_calculate_by_category_ethnicity(self, calculator):
        """Test filtering by ethnicity category."""
        ethnicity_metrics = await calculator.calculate_by_category("ethnicity")

        assert isinstance(ethnicity_metrics, list)
        assert len(ethnicity_metrics) > 0
        assert all(m.demographic_category == "ethnicity" for m in ethnicity_metrics)

    @pytest.mark.asyncio
    async def test_calculate_by_category_with_dates(self, calculator):
        """Test filtering by category with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        metrics = await calculator.calculate_by_category(
            "gender",
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(metrics, list)
        assert all(m.demographic_category == "gender" for m in metrics)

    @pytest.mark.asyncio
    async def test_calculate_goal_progress(self, calculator):
        """Test goal progress calculation."""
        progress = await calculator.calculate_goal_progress()

        assert isinstance(progress, dict)
        assert "total_goals" in progress
        assert "goals_met" in progress
        assert "goals_on_track" in progress
        assert "goals_behind" in progress
        assert "achievement_rate" in progress
        assert "groups_needing_attention" in progress

        assert progress["total_goals"] >= 0
        assert progress["goals_met"] >= 0
        assert progress["goals_met"] <= progress["total_goals"]
        assert 0 <= progress["achievement_rate"] <= 1

    @pytest.mark.asyncio
    async def test_calculate_goal_progress_identifies_behind_groups(self, calculator):
        """Test that goal progress identifies groups behind on goals."""
        progress = await calculator.calculate_goal_progress()

        assert "groups_needing_attention" in progress
        assert isinstance(progress["groups_needing_attention"], list)

        # Each group needing attention should have required fields
        for group in progress["groups_needing_attention"]:
            assert "category" in group
            assert "value" in group
            assert "current" in group
            assert "target" in group
            assert "variance" in group
            # Variance should be negative (behind target)
            assert group["variance"] < 0

    @pytest.mark.asyncio
    async def test_calculate_goal_progress_with_dates(self, calculator):
        """Test goal progress calculation with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        progress = await calculator.calculate_goal_progress(
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(progress, dict)
        assert progress["total_goals"] >= 0

    @pytest.mark.asyncio
    async def test_compare_to_benchmarks(self, calculator):
        """Test benchmark comparison."""
        comparisons = await calculator.compare_to_benchmarks()

        assert isinstance(comparisons, list)
        assert len(comparisons) > 0

        # Each comparison should have required fields
        for comp in comparisons:
            assert "category" in comp
            assert "group" in comp
            assert "current_representation" in comp
            assert "industry_benchmark" in comp
            assert "variance" in comp
            assert "variance_percentage" in comp
            assert "vs_benchmark_status" in comp

            # Status should be valid
            assert comp["vs_benchmark_status"] in [
                "above_benchmark",
                "below_benchmark",
                "at_benchmark"
            ]

    @pytest.mark.asyncio
    async def test_compare_to_benchmarks_status_logic(self, calculator):
        """Test that benchmark comparison status is correctly determined."""
        comparisons = await calculator.compare_to_benchmarks()

        for comp in comparisons:
            variance = comp["variance"]
            status = comp["vs_benchmark_status"]

            if variance > 0.02:
                assert status == "above_benchmark"
            elif variance < -0.02:
                assert status == "below_benchmark"
            else:
                assert status == "at_benchmark"

    @pytest.mark.asyncio
    async def test_compare_to_benchmarks_sorted_by_variance(self, calculator):
        """Test that benchmark comparisons are sorted by variance."""
        comparisons = await calculator.compare_to_benchmarks()

        # Should be sorted by variance (most negative first)
        for i in range(len(comparisons) - 1):
            assert comparisons[i]["variance"] <= comparisons[i + 1]["variance"]

    @pytest.mark.asyncio
    async def test_compare_to_benchmarks_with_dates(self, calculator):
        """Test benchmark comparison with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        comparisons = await calculator.compare_to_benchmarks(
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(comparisons, list)
        assert len(comparisons) > 0

    @pytest.mark.asyncio
    async def test_category_diversity_index_calculation(self, calculator):
        """Test that category diversity index is calculated correctly (Simpson's Index)."""
        metrics = await calculator.calculate()

        for category in metrics.categories:
            # Diversity index should be between 0 and 1
            assert 0 <= category.diversity_index <= 1

            # Get demographics for this category
            category_demos = [
                d for d in metrics.demographics
                if d.demographic_category == category.category
            ]

            # Manually calculate Simpson's Diversity Index
            # Formula: 1 - sum(p_i^2)
            expected_index = 1 - sum(
                d.representation_percentage ** 2
                for d in category_demos
            )

            # Should match the calculated value
            assert abs(category.diversity_index - expected_index) < 0.001

    @pytest.mark.asyncio
    async def test_representation_percentages_sum_to_one_per_category(self, calculator):
        """Test that representation percentages sum to ~1.0 for each category."""
        metrics = await calculator.calculate()

        # Group by category
        categories = {}
        for demo in metrics.demographics:
            if demo.demographic_category not in categories:
                categories[demo.demographic_category] = []
            categories[demo.demographic_category].append(demo)

        # Check each category sums to approximately 1.0
        for category, demos in categories.items():
            total_representation = sum(d.representation_percentage for d in demos)
            # Allow small rounding errors
            assert abs(total_representation - 1.0) < 0.01, \
                f"Category {category} representations sum to {total_representation}, expected ~1.0"

    @pytest.mark.asyncio
    async def test_conversion_rates_are_valid(self, calculator):
        """Test that all conversion rates are valid (0-1)."""
        metrics = await calculator.calculate()

        for demo in metrics.demographics:
            assert 0 <= demo.screening_rate <= 1
            assert 0 <= demo.interview_rate <= 1
            assert 0 <= demo.offer_rate <= 1
            assert 0 <= demo.hire_rate <= 1
            assert 0 <= demo.conversion_rate <= 1

    @pytest.mark.asyncio
    async def test_variance_from_target_matches_calculation(self, calculator):
        """Test that variance from target is calculated correctly."""
        metrics = await calculator.calculate()

        for demo in metrics.demographics:
            if demo.target_representation is not None and demo.variance_from_target is not None:
                expected_variance = demo.representation_percentage - demo.target_representation
                assert abs(demo.variance_from_target - expected_variance) < 0.001

    @pytest.mark.asyncio
    async def test_goal_met_matches_variance(self, calculator):
        """Test that goal_met status matches variance from target."""
        metrics = await calculator.calculate()

        for demo in metrics.demographics:
            if demo.goal_met is not None and demo.variance_from_target is not None:
                # Goals typically met if within reasonable range of target
                # The exact logic may vary, but we check consistency
                if demo.goal_met:
                    # If goal is met, variance shouldn't be too negative
                    assert demo.variance_from_target >= -0.1
                else:
                    # If goal is not met, there should be some gap
                    # (though positive variance might also not meet goal if exceeded)
                    pass  # Goal not met can have various variances
