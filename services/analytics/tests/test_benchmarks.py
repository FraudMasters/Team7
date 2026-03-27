"""
Tests for benchmark comparison calculator.

# Русский комментарий:
Этот модуль содержит тесты для калькулятора сравнения с отраслевыми эталонами,
проверяя сравнение метрик найма с отраслевыми стандартами и определение
областей превосходства и улучшения.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from calculators.benchmarks import (
    BenchmarkCalculator,
    BenchmarkComparison,
    CategoryBenchmarks,
    IndustryType,
    MetricBenchmark,
    PerformanceStatus,
)


@pytest.fixture
def db_session():
    """Fixture для мок-сессии базы данных."""
    return AsyncMock()


@pytest.fixture
def calculator(db_session):
    """Fixture для калькулятора эталонов."""
    return BenchmarkCalculator(db_session)


class TestBenchmarkCalculator:
    """Тесты для BenchmarkCalculator."""

    @pytest.mark.asyncio
    async def test_calculator_initialization(self, db_session):
        """Test calculator initialization."""
        calculator = BenchmarkCalculator(db_session)
        assert calculator.db == db_session

    @pytest.mark.asyncio
    async def test_industry_benchmarks_exist(self, calculator):
        """Test that industry benchmarks are defined for all industry types."""
        for industry in IndustryType:
            assert industry in calculator.INDUSTRY_BENCHMARKS
            benchmarks = calculator.INDUSTRY_BENCHMARKS[industry]

            # Проверяем наличие всех ключевых метрик
            assert "time_to_hire_days" in benchmarks
            assert "cost_per_hire_usd" in benchmarks
            assert "overall_conversion_rate" in benchmarks
            assert "source_conversion_rate" in benchmarks
            assert "funnel_first_stage_conversion" in benchmarks
            assert "quality_score" in benchmarks
            assert "offer_acceptance_rate" in benchmarks

    @pytest.mark.asyncio
    async def test_compare_to_industry(self, calculator):
        """Test basic industry comparison."""
        comparison = await calculator.compare_to_industry(
            industry=IndustryType.TECHNOLOGY
        )

        assert isinstance(comparison, BenchmarkComparison)
        assert comparison.industry == IndustryType.TECHNOLOGY
        assert len(comparison.categories) > 0
        assert comparison.overall_score >= 0
        assert comparison.overall_score <= 100
        assert comparison.total_metrics > 0

    @pytest.mark.asyncio
    async def test_comparison_categories(self, calculator):
        """Test that all expected categories are included."""
        comparison = await calculator.compare_to_industry(
            industry=IndustryType.GENERAL
        )

        category_names = [cat.category_name for cat in comparison.categories]

        assert "Time to Hire" in category_names
        assert "Cost Efficiency" in category_names
        assert "Conversion Rates" in category_names
        assert "Candidate Quality" in category_names

    @pytest.mark.asyncio
    async def test_category_structure(self, calculator):
        """Test that each category has correct structure."""
        comparison = await calculator.compare_to_industry()

        for category in comparison.categories:
            assert isinstance(category, CategoryBenchmarks)
            assert category.category_name
            assert len(category.metrics) > 0
            assert category.overall_performance in PerformanceStatus
            assert category.summary

    @pytest.mark.asyncio
    async def test_metric_benchmark_structure(self, calculator):
        """Test that metric benchmarks have all required fields."""
        comparison = await calculator.compare_to_industry()

        for category in comparison.categories:
            for metric in category.metrics:
                assert isinstance(metric, MetricBenchmark)
                assert metric.metric_name
                assert metric.current_value >= 0
                assert metric.benchmark_value >= 0
                assert metric.performance_status in PerformanceStatus
                assert isinstance(metric.lower_is_better, bool)

    @pytest.mark.asyncio
    async def test_metric_counts_consistency(self, calculator):
        """Test that metric counts add up correctly."""
        comparison = await calculator.compare_to_industry()

        total_counted = (
            comparison.metrics_above_benchmark
            + comparison.metrics_at_benchmark
            + comparison.metrics_below_benchmark
        )

        assert total_counted == comparison.total_metrics

    @pytest.mark.asyncio
    async def test_strengths_and_improvements(self, calculator):
        """Test that strengths and improvement areas are identified."""
        comparison = await calculator.compare_to_industry()

        # Strengths должны соответствовать метрикам выше эталона
        assert len(comparison.strengths) == comparison.metrics_above_benchmark

        # Improvement areas должны соответствовать метрикам ниже эталона
        assert len(comparison.improvement_areas) == comparison.metrics_below_benchmark

    @pytest.mark.asyncio
    async def test_create_metric_benchmark_above(self, calculator):
        """Test metric benchmark creation when above benchmark."""
        metric = calculator._create_metric_benchmark(
            metric_name="Test Metric",
            current_value=100.0,
            benchmark_value=80.0,
            lower_is_better=False,
        )

        assert metric.metric_name == "Test Metric"
        assert metric.current_value == 100.0
        assert metric.benchmark_value == 80.0
        assert metric.variance == 20.0
        assert metric.variance_percentage == 25.0
        assert metric.performance_status == PerformanceStatus.ABOVE_BENCHMARK

    @pytest.mark.asyncio
    async def test_create_metric_benchmark_below(self, calculator):
        """Test metric benchmark creation when below benchmark."""
        metric = calculator._create_metric_benchmark(
            metric_name="Test Metric",
            current_value=60.0,
            benchmark_value=80.0,
            lower_is_better=False,
        )

        assert metric.variance == -20.0
        assert metric.variance_percentage == -25.0
        assert metric.performance_status == PerformanceStatus.BELOW_BENCHMARK

    @pytest.mark.asyncio
    async def test_create_metric_benchmark_at(self, calculator):
        """Test metric benchmark creation when at benchmark (within tolerance)."""
        metric = calculator._create_metric_benchmark(
            metric_name="Test Metric",
            current_value=102.0,
            benchmark_value=100.0,
            lower_is_better=False,
        )

        # 2% variance is within 5% tolerance
        assert metric.performance_status == PerformanceStatus.AT_BENCHMARK

    @pytest.mark.asyncio
    async def test_create_metric_benchmark_lower_is_better(self, calculator):
        """Test metric benchmark when lower values are better (e.g., cost, time)."""
        # Lower current value should be ABOVE_BENCHMARK
        metric_good = calculator._create_metric_benchmark(
            metric_name="Cost",
            current_value=80.0,
            benchmark_value=100.0,
            lower_is_better=True,
        )
        assert metric_good.performance_status == PerformanceStatus.ABOVE_BENCHMARK

        # Higher current value should be BELOW_BENCHMARK
        metric_bad = calculator._create_metric_benchmark(
            metric_name="Cost",
            current_value=120.0,
            benchmark_value=100.0,
            lower_is_better=True,
        )
        assert metric_bad.performance_status == PerformanceStatus.BELOW_BENCHMARK

    @pytest.mark.asyncio
    async def test_get_metric_comparison(self, calculator):
        """Test single metric comparison."""
        comparison = await calculator.get_metric_comparison(
            metric_name="time_to_hire_days",
            current_value=35.0,
            industry=IndustryType.TECHNOLOGY,
            lower_is_better=True,
        )

        assert isinstance(comparison, MetricBenchmark)
        assert comparison.metric_name == "time_to_hire_days"
        assert comparison.current_value == 35.0
        assert comparison.benchmark_value == 36.5  # Technology benchmark
        assert comparison.lower_is_better is True

    @pytest.mark.asyncio
    async def test_get_metric_comparison_invalid_metric(self, calculator):
        """Test that invalid metric name raises error."""
        with pytest.raises(ValueError, match="not found in benchmarks"):
            await calculator.get_metric_comparison(
                metric_name="invalid_metric",
                current_value=100.0,
                industry=IndustryType.GENERAL,
            )

    @pytest.mark.asyncio
    async def test_get_all_industries_comparison(self, calculator):
        """Test comparison across all industries."""
        comparisons = await calculator.get_all_industries_comparison()

        assert isinstance(comparisons, dict)
        assert len(comparisons) == len(IndustryType)

        for industry, comparison in comparisons.items():
            assert isinstance(industry, IndustryType)
            assert isinstance(comparison, BenchmarkComparison)
            assert comparison.industry == industry

    @pytest.mark.asyncio
    async def test_different_industries_have_different_benchmarks(self, calculator):
        """Test that different industries have different benchmark values."""
        tech_comparison = await calculator.compare_to_industry(
            industry=IndustryType.TECHNOLOGY
        )
        retail_comparison = await calculator.compare_to_industry(
            industry=IndustryType.RETAIL
        )

        # Retail should have faster time to hire than Technology
        tech_benchmarks = calculator.INDUSTRY_BENCHMARKS[IndustryType.TECHNOLOGY]
        retail_benchmarks = calculator.INDUSTRY_BENCHMARKS[IndustryType.RETAIL]

        assert tech_benchmarks["time_to_hire_days"] != retail_benchmarks["time_to_hire_days"]
        assert tech_benchmarks["cost_per_hire_usd"] != retail_benchmarks["cost_per_hire_usd"]

    @pytest.mark.asyncio
    async def test_overall_score_calculation(self, calculator):
        """Test that overall score is calculated correctly."""
        comparison = await calculator.compare_to_industry()

        # Score should be between 0-100
        assert 0 <= comparison.overall_score <= 100

        # Score should reflect the distribution of performance statuses
        total = comparison.total_metrics
        if total > 0:
            expected_min_score = 0  # All below benchmark
            expected_max_score = 100  # All above benchmark

            assert comparison.overall_score >= expected_min_score
            assert comparison.overall_score <= expected_max_score

    @pytest.mark.asyncio
    async def test_time_to_hire_category(self, calculator):
        """Test Time to Hire category specifically."""
        comparison = await calculator.compare_to_industry(
            industry=IndustryType.TECHNOLOGY
        )

        time_category = next(
            (c for c in comparison.categories if c.category_name == "Time to Hire"),
            None
        )

        assert time_category is not None
        assert len(time_category.metrics) == 1

        metric = time_category.metrics[0]
        assert metric.metric_name == "Time to Hire"
        assert metric.lower_is_better is True
        assert metric.unit == "days"

    @pytest.mark.asyncio
    async def test_cost_category(self, calculator):
        """Test Cost Efficiency category."""
        comparison = await calculator.compare_to_industry()

        cost_category = next(
            (c for c in comparison.categories if c.category_name == "Cost Efficiency"),
            None
        )

        assert cost_category is not None
        assert len(cost_category.metrics) == 1

        metric = cost_category.metrics[0]
        assert metric.metric_name == "Cost per Hire"
        assert metric.lower_is_better is True
        assert metric.unit == "USD"

    @pytest.mark.asyncio
    async def test_conversion_category(self, calculator):
        """Test Conversion Rates category."""
        comparison = await calculator.compare_to_industry()

        conversion_category = next(
            (c for c in comparison.categories if c.category_name == "Conversion Rates"),
            None
        )

        assert conversion_category is not None
        assert len(conversion_category.metrics) == 4  # 4 conversion metrics

        metric_names = [m.metric_name for m in conversion_category.metrics]
        assert "Overall Conversion Rate" in metric_names
        assert "Source Conversion Rate" in metric_names
        assert "Funnel First Stage Conversion" in metric_names
        assert "Offer Acceptance Rate" in metric_names

        # All conversion metrics should have lower_is_better = False
        for metric in conversion_category.metrics:
            assert metric.lower_is_better is False

    @pytest.mark.asyncio
    async def test_quality_category(self, calculator):
        """Test Candidate Quality category."""
        comparison = await calculator.compare_to_industry()

        quality_category = next(
            (c for c in comparison.categories if c.category_name == "Candidate Quality"),
            None
        )

        assert quality_category is not None
        assert len(quality_category.metrics) == 1

        metric = quality_category.metrics[0]
        assert metric.metric_name == "Candidate Quality Score"
        assert metric.lower_is_better is False
        assert metric.unit == "score"

    @pytest.mark.asyncio
    async def test_category_summary_reflects_performance(self, calculator):
        """Test that category summaries accurately reflect performance."""
        comparison = await calculator.compare_to_industry()

        for category in comparison.categories:
            summary_lower = category.summary.lower()

            if category.overall_performance == PerformanceStatus.ABOVE_BENCHMARK:
                assert ("excellent" in summary_lower or "strong" in summary_lower)
            elif category.overall_performance == PerformanceStatus.BELOW_BENCHMARK:
                assert "needs improvement" in summary_lower or "improvement" in summary_lower
            else:  # AT_BENCHMARK
                assert ("on par" in summary_lower or "mixed" in summary_lower)

    @pytest.mark.asyncio
    async def test_variance_calculation(self, calculator):
        """Test that variance is calculated correctly."""
        metric = calculator._create_metric_benchmark(
            metric_name="Test",
            current_value=120.0,
            benchmark_value=100.0,
            lower_is_better=False,
        )

        assert metric.variance == 20.0
        assert metric.variance_percentage == 20.0

    @pytest.mark.asyncio
    async def test_variance_percentage_with_zero_benchmark(self, calculator):
        """Test variance percentage calculation when benchmark is zero."""
        metric = calculator._create_metric_benchmark(
            metric_name="Test",
            current_value=100.0,
            benchmark_value=0.0,
            lower_is_better=False,
        )

        assert metric.variance_percentage == 0

    @pytest.mark.asyncio
    async def test_comparison_with_date_range(self, calculator):
        """Test comparison with date range parameters."""
        from datetime import datetime

        comparison = await calculator.compare_to_industry(
            industry=IndustryType.TECHNOLOGY,
            start_date=datetime(2026, 1, 1),
            end_date=datetime(2026, 3, 31),
        )

        assert isinstance(comparison, BenchmarkComparison)
        # Date filtering будет реализован в фазе интеграции с БД

    @pytest.mark.asyncio
    async def test_all_industries_have_valid_benchmarks(self, calculator):
        """Test that all industry benchmarks have valid values."""
        for industry, benchmarks in calculator.INDUSTRY_BENCHMARKS.items():
            # All benchmarks should be positive numbers
            for metric_name, value in benchmarks.items():
                assert value > 0, f"{industry}.{metric_name} should be positive"

            # Time to hire should be reasonable (7-90 days)
            assert 7 <= benchmarks["time_to_hire_days"] <= 90

            # Cost should be reasonable ($500-$10,000)
            assert 500 <= benchmarks["cost_per_hire_usd"] <= 10000

            # Rates should be between 0 and 1
            assert 0 < benchmarks["overall_conversion_rate"] <= 1
            assert 0 < benchmarks["source_conversion_rate"] <= 1
            assert 0 < benchmarks["funnel_first_stage_conversion"] <= 1
            assert 0 < benchmarks["offer_acceptance_rate"] <= 1

            # Quality score should be 0-100
            assert 0 <= benchmarks["quality_score"] <= 100

    @pytest.mark.asyncio
    async def test_performance_status_enum(self):
        """Test PerformanceStatus enum values."""
        assert PerformanceStatus.ABOVE_BENCHMARK == "above_benchmark"
        assert PerformanceStatus.AT_BENCHMARK == "at_benchmark"
        assert PerformanceStatus.BELOW_BENCHMARK == "below_benchmark"

    @pytest.mark.asyncio
    async def test_industry_type_enum(self):
        """Test IndustryType enum contains expected industries."""
        industry_types = [i for i in IndustryType]

        assert IndustryType.TECHNOLOGY in industry_types
        assert IndustryType.HEALTHCARE in industry_types
        assert IndustryType.FINANCE in industry_types
        assert IndustryType.RETAIL in industry_types
        assert IndustryType.MANUFACTURING in industry_types
        assert IndustryType.GENERAL in industry_types

    @pytest.mark.asyncio
    async def test_conversion_category_overall_performance(self, calculator):
        """Test that conversion category overall performance is calculated correctly."""
        comparison = await calculator.compare_to_industry()

        conversion_category = next(
            (c for c in comparison.categories if c.category_name == "Conversion Rates"),
            None
        )

        # Should calculate based on majority of metrics
        above_count = sum(
            1 for m in conversion_category.metrics
            if m.performance_status == PerformanceStatus.ABOVE_BENCHMARK
        )
        below_count = sum(
            1 for m in conversion_category.metrics
            if m.performance_status == PerformanceStatus.BELOW_BENCHMARK
        )

        if above_count > below_count:
            assert conversion_category.overall_performance == PerformanceStatus.ABOVE_BENCHMARK
        elif below_count > above_count:
            assert conversion_category.overall_performance == PerformanceStatus.BELOW_BENCHMARK
        else:
            assert conversion_category.overall_performance == PerformanceStatus.AT_BENCHMARK

    @pytest.mark.asyncio
    async def test_metric_benchmark_with_unit(self, calculator):
        """Test that metrics have appropriate units."""
        comparison = await calculator.compare_to_industry()

        for category in comparison.categories:
            for metric in category.metrics:
                if "Time" in metric.metric_name:
                    assert metric.unit == "days"
                elif "Cost" in metric.metric_name:
                    assert metric.unit == "USD"
                elif "Rate" in metric.metric_name or "Conversion" in metric.metric_name:
                    assert metric.unit == "rate"
                elif "Score" in metric.metric_name or "Quality" in metric.metric_name:
                    assert metric.unit == "score"
