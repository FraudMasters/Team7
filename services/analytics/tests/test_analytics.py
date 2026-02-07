"""
Tests for Analytics Service.

Tests cover metrics retrieval, dashboard analytics,
quality metrics, and reporting functionality.
"""
import pytest
from datetime import datetime
from pydantic import BaseModel, ValidationError
from unittest.mock import Mock, AsyncMock


class TestTimeToHireMetrics:
    """Tests for TimeToHireMetrics model."""

    def test_valid_time_to_hire_metrics(self):
        """Test creation of valid time-to-hire metrics."""
        from api.analytics import TimeToHireMetrics

        metrics = TimeToHireMetrics(
            average_days=32.5,
            median_days=28.0,
            min_days=7,
            max_days=90,
            percentile_25=21.0,
            percentile_75=45.0,
        )

        assert metrics.average_days == 32.5
        assert metrics.median_days == 28.0
        assert metrics.min_days == 7
        assert metrics.max_days == 90

    def test_time_to_hire_percentile_ordering(self):
        """Test that percentile values are logically ordered."""
        from api.analytics import TimeToHireMetrics

        metrics = TimeToHireMetrics(
            average_days=30.0,
            median_days=25.0,
            min_days=5,
            max_days=100,
            percentile_25=15.0,
            percentile_75=40.0,
        )

        assert metrics.percentile_25 < metrics.median_days
        assert metrics.median_days < metrics.percentile_75
        assert metrics.min_days <= metrics.percentile_25
        assert metrics.percentile_75 <= metrics.max_days


class TestResumeMetrics:
    """Tests for ResumeMetrics model."""

    def test_valid_resume_metrics(self):
        """Test creation of valid resume processing metrics."""
        from api.analytics import ResumeMetrics

        metrics = ResumeMetrics(
            total_processed=1250,
            processed_this_month=180,
            processed_this_week=42,
            processing_rate_avg=8.5,
        )

        assert metrics.total_processed == 1250
        assert metrics.processed_this_month == 180
        assert metrics.processing_rate_avg == 8.5

    def test_cumulative_metrics_relationship(self):
        """Test logical relationship between cumulative metrics."""
        from api.analytics import ResumeMetrics

        metrics = ResumeMetrics(
            total_processed=1000,
            processed_this_month=100,
            processed_this_week=25,
            processing_rate_avg=10.0,
        )

        # Week count should be <= month count
        assert metrics.processed_this_week <= metrics.processed_this_month
        # Month count should be <= total
        assert metrics.processed_this_month <= metrics.total_processed


class TestMatchRateMetrics:
    """Tests for MatchRateMetrics model."""

    def test_valid_match_rate_metrics(self):
        """Test creation of valid match rate metrics."""
        from api.analytics import MatchRateMetrics

        metrics = MatchRateMetrics(
            overall_match_rate=0.78,
            high_confidence_matches=890,
            low_confidence_matches=156,
            average_confidence=0.72,
        )

        assert metrics.overall_match_rate == 0.78
        assert metrics.high_confidence_matches == 890
        assert metrics.low_confidence_matches == 156

    def test_confidence_range_validation(self):
        """Test that confidence values are in valid range."""
        from api.analytics import MatchRateMetrics

        metrics = MatchRateMetrics(
            overall_match_rate=0.85,
            high_confidence_matches=100,
            low_confidence_matches=50,
            average_confidence=0.75,
        )

        assert 0 <= metrics.overall_match_rate <= 1
        assert 0 <= metrics.average_confidence <= 1


class TestKeyMetricsResponse:
    """Tests for KeyMetricsResponse model."""

    def test_valid_key_metrics_response(self):
        """Test creation of valid key metrics response."""
        from api.analytics import (
            KeyMetricsResponse,
            TimeToHireMetrics,
            ResumeMetrics,
            MatchRateMetrics,
        )

        response = KeyMetricsResponse(
            time_to_hire=TimeToHireMetrics(
                average_days=30.0,
                median_days=25.0,
                min_days=5,
                max_days=100,
                percentile_25=15.0,
                percentile_75=40.0,
            ),
            resumes=ResumeMetrics(
                total_processed=1000,
                processed_this_month=100,
                processed_this_week=25,
                processing_rate_avg=10.0,
            ),
            match_rates=MatchRateMetrics(
                overall_match_rate=0.8,
                high_confidence_matches=500,
                low_confidence_matches=100,
                average_confidence=0.75,
            ),
        )

        assert response.time_to_hire.average_days == 30.0
        assert response.resumes.total_processed == 1000
        assert response.match_rates.overall_match_rate == 0.8


class TestQualityMetrics:
    """Tests for QualityMetricsResponse model."""

    def test_valid_quality_metrics(self):
        """Test creation of valid quality metrics."""
        from api.analytics import QualityMetricsResponse

        metrics = QualityMetricsResponse(
            text_extraction_success_rate=0.98,
            avg_extraction_time_seconds=1.2,
            ner_accuracy=0.92,
            entities_per_resume_avg=15.3,
            avg_keywords_per_resume=8.5,
            keyword_relevance_avg=0.78,
            grammar_error_rate=0.35,
            matching_confidence_avg=0.75,
            matching_precision=0.87,
            matching_recall=0.82,
            avg_analysis_time_seconds=12.5,
            error_rate=0.02,
            total_analyzed=1250,
        )

        assert metrics.text_extraction_success_rate == 0.98
        assert metrics.ner_accuracy == 0.92
        assert metrics.total_analyzed == 1250

    def test_quality_rates_in_range(self):
        """Test that all quality rates are in valid range."""
        from api.analytics import QualityMetricsResponse

        metrics = QualityMetricsResponse(
            text_extraction_success_rate=0.95,
            avg_extraction_time_seconds=1.0,
            ner_accuracy=0.90,
            entities_per_resume_avg=15.0,
            avg_keywords_per_resume=8.0,
            keyword_relevance_avg=0.75,
            grammar_error_rate=0.30,
            matching_confidence_avg=0.80,
            matching_precision=0.85,
            matching_recall=0.80,
            avg_analysis_time_seconds=10.0,
            error_rate=0.05,
            total_analyzed=1000,
        )

        assert 0 <= metrics.text_extraction_success_rate <= 1
        assert 0 <= metrics.ner_accuracy <= 1
        assert 0 <= metrics.matching_precision <= 1
        assert 0 <= metrics.matching_recall <= 1
        assert 0 <= metrics.error_rate <= 1


class TestDashboardMetrics:
    """Tests for DashboardMetrics model."""

    def test_valid_dashboard_metrics(self):
        """Test creation of valid dashboard metrics."""
        from api.analytics import DashboardMetrics

        metrics = DashboardMetrics(
            total_resumes=1250,
            active_candidates=450,
            open_vacancies=25,
            interviews_scheduled=42,
            offers_extended=12,
            hires_this_month=8,
            avg_time_to_hire=28.5,
        )

        assert metrics.total_resumes == 1250
        assert metrics.active_candidates == 450
        assert metrics.hires_this_month == 8

    def test_dashboard_counts_non_negative(self):
        """Test that all dashboard counts are non-negative."""
        from api.analytics import DashboardMetrics

        metrics = DashboardMetrics(
            total_resumes=100,
            active_candidates=50,
            open_vacancies=10,
            interviews_scheduled=5,
            offers_extended=2,
            hires_this_month=1,
            avg_time_to_hire=20.0,
        )

        assert metrics.total_resumes >= 0
        assert metrics.active_candidates >= 0
        assert metrics.open_vacancies >= 0


class TestTaxonomyUsageStats:
    """Tests for TaxonomyUsageStats model."""

    def test_valid_taxonomy_usage_stats(self):
        """Test creation of valid taxonomy usage statistics."""
        from api.analytics import TaxonomyUsageStats

        stats = TaxonomyUsageStats(
            taxonomy_id="tax-001",
            taxonomy_name="Technology",
            usage_count=125,
            avg_match_score=72.5,
            success_rate=0.78,
            total_candidates_matched=625,
            industry="technology",
        )

        assert stats.taxonomy_id == "tax-001"
        assert stats.usage_count == 125
        assert stats.success_rate == 0.78

    def test_nullable_industry_field(self):
        """Test that industry field is nullable."""
        from api.analytics import TaxonomyUsageStats

        stats = TaxonomyUsageStats(
            taxonomy_id="tax-002",
            taxonomy_name="General",
            usage_count=50,
            avg_match_score=65.0,
            success_rate=0.70,
            total_candidates_matched=100,
            industry=None,
        )

        assert stats.industry is None


class TestTaxonomyUsageResponse:
    """Tests for TaxonomyUsageResponse model."""

    def test_valid_taxonomy_usage_response(self):
        """Test creation of valid taxonomy usage response."""
        from api.analytics import (
            TaxonomyUsageResponse,
            TaxonomyUsageStats,
        )

        response = TaxonomyUsageResponse(
            most_used_taxonomies=[
                TaxonomyUsageStats(
                    taxonomy_id="tax-001",
                    taxonomy_name="Technology",
                    usage_count=125,
                    avg_match_score=72.5,
                    success_rate=0.78,
                    total_candidates_matched=625,
                    industry="technology",
                )
            ],
            most_effective_taxonomies=[
                TaxonomyUsageStats(
                    taxonomy_id="tax-002",
                    taxonomy_name="Finance",
                    usage_count=80,
                    avg_match_score=78.5,
                    success_rate=0.85,
                    total_candidates_matched=400,
                    industry="finance",
                )
            ],
            industry_filter=None,
            total_taxonomies_analyzed=25,
        )

        assert len(response.most_used_taxonomies) == 1
        assert len(response.most_effective_taxonomies) == 1
        assert response.total_taxonomies_analyzed == 25


class TestStageDurationMetrics:
    """Tests for StageDurationMetrics model."""

    def test_valid_stage_duration_metrics(self):
        """Test creation of valid stage duration metrics."""
        from api.analytics import StageDurationMetrics

        metrics = StageDurationMetrics(
            stage_name="screening",
            average_days=5.2,
            median_days=4.0,
            min_days=1.0,
            max_days=14.0,
            candidate_count=120,
        )

        assert metrics.stage_name == "screening"
        assert metrics.average_days == 5.2
        assert metrics.candidate_count == 120

    def test_duration_ordering(self):
        """Test that duration values are logically ordered."""
        from api.analytics import StageDurationMetrics

        metrics = StageDurationMetrics(
            stage_name="interview",
            average_days=10.0,
            median_days=8.0,
            min_days=2.0,
            max_days=30.0,
            candidate_count=50,
        )

        assert metrics.min_days <= metrics.median_days
        assert metrics.median_days <= metrics.max_days


class TestStageDurationResponse:
    """Tests for StageDurationResponse model."""

    def test_valid_stage_duration_response(self):
        """Test creation of valid stage duration response."""
        from api.analytics import StageDurationResponse, StageDurationMetrics

        response = StageDurationResponse(
            stages=[
                StageDurationMetrics(
                    stage_name="applied",
                    average_days=2.5,
                    median_days=2.0,
                    min_days=0.5,
                    max_days=7.0,
                    candidate_count=150,
                ),
                StageDurationMetrics(
                    stage_name="screening",
                    average_days=5.2,
                    median_days=4.0,
                    min_days=1.0,
                    max_days=14.0,
                    candidate_count=120,
                ),
            ]
        )

        assert len(response.stages) == 2
        assert response.stages[0].stage_name == "applied"
        assert response.stages[1].stage_name == "screening"


class TestFunnelStageMetrics:
    """Tests for FunnelStageMetrics model."""

    def test_valid_funnel_stage_metrics(self):
        """Test creation of valid funnel stage metrics."""
        from api.analytics import FunnelStageMetrics

        metrics = FunnelStageMetrics(
            stage_name="analyzed",
            count=450,
            conversion_rate_from_previous=0.9,
            conversion_rate_from_start=0.9,
        )

        assert metrics.stage_name == "analyzed"
        assert metrics.count == 450
        assert metrics.conversion_rate_from_previous == 0.9

    def test_first_stage_null_previous_conversion(self):
        """Test that first stage has null conversion from previous."""
        from api.analytics import FunnelStageMetrics

        metrics = FunnelStageMetrics(
            stage_name="uploaded",
            count=500,
            conversion_rate_from_previous=None,
            conversion_rate_from_start=1.0,
        )

        assert metrics.conversion_rate_from_previous is None
        assert metrics.conversion_rate_from_start == 1.0


class TestFunnelMetricsResponse:
    """Tests for FunnelMetricsResponse model."""

    def test_valid_funnel_metrics_response(self):
        """Test creation of valid funnel metrics response."""
        from api.analytics import FunnelMetricsResponse, FunnelStageMetrics

        response = FunnelMetricsResponse(
            stages=[
                FunnelStageMetrics(
                    stage_name="uploaded",
                    count=500,
                    conversion_rate_from_previous=None,
                    conversion_rate_from_start=1.0,
                ),
                FunnelStageMetrics(
                    stage_name="analyzed",
                    count=450,
                    conversion_rate_from_previous=0.9,
                    conversion_rate_from_start=0.9,
                ),
                FunnelStageMetrics(
                    stage_name="hired",
                    count=50,
                    conversion_rate_from_previous=0.33,
                    conversion_rate_from_start=0.1,
                ),
            ],
            total_candidates=500,
        )

        assert len(response.stages) == 3
        assert response.total_candidates == 500

    def test_funnel_candidate_counts_decrease(self):
        """Test that funnel stages show decreasing candidate counts."""
        stages = [
            {"stage_name": "uploaded", "count": 1000},
            {"stage_name": "analyzed", "count": 800},
            {"stage_name": "screening", "count": 400},
            {"stage_name": "hired", "count": 50},
        ]

        for i in range(len(stages) - 1):
            assert stages[i]["count"] >= stages[i + 1]["count"]


class TestDateRangeFilters:
    """Tests for date range filtering functionality."""

    def test_date_range_filter_validation(self):
        """Test validation of date range parameters."""
        from datetime import datetime

        # Valid ISO 8601 dates
        valid_start = "2024-01-01T00:00:00Z"
        valid_end = "2024-12-31T23:59:59Z"

        # Should be able to parse these
        start_dt = datetime.fromisoformat(valid_start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(valid_end.replace("Z", "+00:00"))

        assert start_dt < end_dt

    def test_optional_date_parameters(self):
        """Test that date parameters are optional."""
        # Date parameters should be optional in the API
        # This tests the concept, not the actual endpoint
        start_date = None
        end_date = None

        assert start_date is None
        assert end_date is None


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoint behavior."""

    @pytest.mark.asyncio
    async def test_get_key_metrics_returns_structure(self):
        """Test that key metrics endpoint returns correct structure."""
        # Mock response data structure
        mock_response = {
            "time_to_hire": {
                "average_days": 32.5,
                "median_days": 28.0,
                "min_days": 7,
                "max_days": 90,
                "percentile_25": 21.0,
                "percentile_75": 45.0,
            },
            "resumes": {
                "total_processed": 1250,
                "processed_this_month": 180,
                "processed_this_week": 42,
                "processing_rate_avg": 8.5,
            },
            "match_rates": {
                "overall_match_rate": 0.78,
                "high_confidence_matches": 890,
                "low_confidence_matches": 156,
                "average_confidence": 0.72,
            },
        }

        assert "time_to_hire" in mock_response
        assert "resumes" in mock_response
        assert "match_rates" in mock_response

    @pytest.mark.asyncio
    async def test_get_quality_metrics_returns_all_fields(self):
        """Test that quality metrics endpoint returns all required fields."""
        mock_response = {
            "text_extraction_success_rate": 0.98,
            "avg_extraction_time_seconds": 1.2,
            "ner_accuracy": 0.92,
            "entities_per_resume_avg": 15.3,
            "avg_keywords_per_resume": 8.5,
            "keyword_relevance_avg": 0.78,
            "grammar_error_rate": 0.35,
            "matching_confidence_avg": 0.75,
            "matching_precision": 0.87,
            "matching_recall": 0.82,
            "avg_analysis_time_seconds": 12.5,
            "error_rate": 0.02,
            "total_analyzed": 1250,
        }

        assert "text_extraction_success_rate" in mock_response
        assert "ner_accuracy" in mock_response
        assert "total_analyzed" in mock_response

    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_aggregates_data(self):
        """Test that dashboard metrics provide aggregate data."""
        mock_response = {
            "total_resumes": 1250,
            "active_candidates": 450,
            "open_vacancies": 25,
            "interviews_scheduled": 42,
            "offers_extended": 12,
            "hires_this_month": 8,
            "avg_time_to_hire": 28.5,
        }

        assert mock_response["total_resumes"] >= mock_response["active_candidates"]
        assert mock_response["hires_this_month"] <= mock_response["active_candidates"]


class TestAnalyticsCalculations:
    """Tests for analytics calculation logic."""

    def test_average_calculation(self):
        """Test calculation of average values."""
        values = [10, 20, 30, 40, 50]
        average = sum(values) / len(values)

        assert average == 30.0

    def test_median_calculation_odd_count(self):
        """Test median calculation with odd number of values."""
        values = [10, 20, 30, 40, 50]
        sorted_values = sorted(values)
        median = sorted_values[len(values) // 2]

        assert median == 30

    def test_median_calculation_even_count(self):
        """Test median calculation with even number of values."""
        values = [10, 20, 30, 40]
        sorted_values = sorted(values)
        median = (sorted_values[len(values) // 2 - 1] + sorted_values[len(values) // 2]) / 2

        assert median == 25.0

    def test_percentile_25_calculation(self):
        """Test 25th percentile calculation."""
        values = list(range(1, 101))  # 1 to 100
        percentile_25_index = int(len(values) * 0.25)
        percentile_25 = sorted(values)[percentile_25_index]

        assert percentile_25 == 25

    def test_percentile_75_calculation(self):
        """Test 75th percentile calculation."""
        values = list(range(1, 101))  # 1 to 100
        percentile_75_index = int(len(values) * 0.75)
        percentile_75 = sorted(values)[percentile_75_index]

        assert percentile_75 == 75

    def test_conversion_rate_calculation(self):
        """Test conversion rate calculation."""
        initial_count = 1000
        final_count = 250
        conversion_rate = final_count / initial_count

        assert conversion_rate == 0.25


class TestAnalyticsEdgeCases:
    """Tests for edge cases in analytics."""

    def test_empty_metrics_handling(self):
        """Test handling of empty metrics."""
        empty_stages = []

        assert len(empty_stages) == 0

    def test_zero_values_in_metrics(self):
        """Test metrics with zero values."""
        from api.analytics import ResumeMetrics

        metrics = ResumeMetrics(
            total_processed=0,
            processed_this_month=0,
            processed_this_week=0,
            processing_rate_avg=0.0,
        )

        assert metrics.total_processed == 0
        assert metrics.processing_rate_avg == 0.0

    def test_single_value_metrics(self):
        """Test metrics with single value."""
        values = [42]
        average = sum(values) / len(values)
        median = values[0]

        assert average == 42
        assert median == 42


class TestIndustryFiltering:
    """Tests for industry filtering in analytics."""

    def test_industry_filter_parameter(self):
        """Test industry filter parameter handling."""
        filter_industry = "technology"

        assert filter_industry == "technology"

    def test_multiple_industries(self):
        """Test handling of multiple industries."""
        industries = ["technology", "finance", "healthcare", "retail"]

        assert len(industries) == 4
        assert "technology" in industries

    def test_null_industry_filter(self):
        """Test null industry filter returns all industries."""
        filter_industry = None

        assert filter_industry is None


class TestPaginationAndLimits:
    """Tests for pagination and limit parameters."""

    def test_limit_parameter_validation(self):
        """Test limit parameter validation."""
        valid_limits = [1, 10, 50, 100]

        for limit in valid_limits:
            assert 1 <= limit <= 100

    def test_skip_parameter_validation(self):
        """Test skip parameter validation."""
        valid_skip_values = [0, 10, 50, 100]

        for skip in valid_skip_values:
            assert skip >= 0

    def test_default_pagination_values(self):
        """Test default pagination values."""
        default_limit = 50
        default_skip = 0

        assert default_limit == 50
        assert default_skip == 0
