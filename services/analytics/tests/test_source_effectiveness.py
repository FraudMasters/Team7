"""
Tests for source effectiveness calculator.

Tests cover source effectiveness metrics calculation, filtering by source type,
and top sources retrieval.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from calculators.source_effectiveness import (
    SourceEffectivenessCalculator,
    SourceEffectivenessMetrics,
    SourceMetrics,
)


class TestSourceMetrics:
    """Tests for SourceMetrics model."""

    def test_valid_source_metrics(self):
        """Test creation of valid source metrics."""
        metrics = SourceMetrics(
            source_type="JOB_BOARD",
            source_name="LinkedIn",
            total_applications=450,
            hired_count=38,
            conversion_rate=0.084,
            average_quality_score=78.5,
            average_cost_per_application=12.50,
            total_cost=5625.0,
            cost_per_hire=148.03,
            average_time_to_hire_days=28.5,
        )

        assert metrics.source_type == "JOB_BOARD"
        assert metrics.source_name == "LinkedIn"
        assert metrics.total_applications == 450
        assert metrics.hired_count == 38
        assert metrics.conversion_rate == 0.084

    def test_source_metrics_with_minimal_fields(self):
        """Test creation of source metrics with only required fields."""
        metrics = SourceMetrics(
            source_type="REFERRAL",
            source_name="Employee Referral",
            total_applications=100,
        )

        assert metrics.source_type == "REFERRAL"
        assert metrics.source_name == "Employee Referral"
        assert metrics.total_applications == 100
        assert metrics.hired_count == 0
        assert metrics.conversion_rate == 0.0
        assert metrics.average_quality_score is None

    def test_source_metrics_conversion_calculation(self):
        """Test that conversion rate is calculated correctly."""
        metrics = SourceMetrics(
            source_type="JOB_BOARD",
            source_name="Indeed",
            total_applications=100,
            hired_count=10,
            conversion_rate=0.10,
        )

        assert metrics.conversion_rate == 0.10
        assert metrics.hired_count / metrics.total_applications == 0.10


class TestSourceEffectivenessMetrics:
    """Tests for SourceEffectivenessMetrics model."""

    def test_valid_effectiveness_metrics(self):
        """Test creation of valid effectiveness metrics."""
        source1 = SourceMetrics(
            source_type="JOB_BOARD",
            source_name="LinkedIn",
            total_applications=450,
            hired_count=38,
            conversion_rate=0.084,
        )
        source2 = SourceMetrics(
            source_type="REFERRAL",
            source_name="Employee Referral",
            total_applications=125,
            hired_count=28,
            conversion_rate=0.224,
        )

        metrics = SourceEffectivenessMetrics(
            sources=[source1, source2],
            total_applications=575,
            total_hired=66,
            overall_conversion_rate=0.115,
            best_source_by_conversion="Employee Referral",
        )

        assert len(metrics.sources) == 2
        assert metrics.total_applications == 575
        assert metrics.total_hired == 66
        assert metrics.best_source_by_conversion == "Employee Referral"

    def test_effectiveness_metrics_with_empty_sources(self):
        """Test effectiveness metrics with no sources."""
        metrics = SourceEffectivenessMetrics(
            sources=[],
            total_applications=0,
            total_hired=0,
            overall_conversion_rate=0.0,
        )

        assert len(metrics.sources) == 0
        assert metrics.total_applications == 0
        assert metrics.overall_conversion_rate == 0.0


class TestSourceEffectivenessCalculator:
    """Tests for SourceEffectivenessCalculator."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def calculator(self, mock_db):
        """Create a calculator instance with mock DB."""
        return SourceEffectivenessCalculator(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_returns_metrics(self, calculator):
        """Test that calculate returns valid metrics."""
        metrics = await calculator.calculate()

        assert isinstance(metrics, SourceEffectivenessMetrics)
        assert metrics.total_applications > 0
        assert metrics.total_hired > 0
        assert 0 <= metrics.overall_conversion_rate <= 1
        assert len(metrics.sources) > 0

    @pytest.mark.asyncio
    async def test_calculate_with_date_range(self, calculator):
        """Test calculate with date range filters."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        metrics = await calculator.calculate(
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(metrics, SourceEffectivenessMetrics)
        assert metrics.total_applications > 0

    @pytest.mark.asyncio
    async def test_calculate_identifies_best_sources(self, calculator):
        """Test that calculate identifies best sources by different metrics."""
        metrics = await calculator.calculate()

        assert metrics.best_source_by_conversion is not None
        assert metrics.best_source_by_quality is not None
        assert metrics.best_source_by_cost is not None

    @pytest.mark.asyncio
    async def test_calculate_computes_overall_metrics(self, calculator):
        """Test that overall metrics are computed correctly."""
        metrics = await calculator.calculate()

        # Verify that total applications is sum of individual sources
        calculated_total = sum(s.total_applications for s in metrics.sources)
        assert metrics.total_applications == calculated_total

        # Verify that total hired is sum of individual sources
        calculated_hired = sum(s.hired_count for s in metrics.sources)
        assert metrics.total_hired == calculated_hired

        # Verify overall conversion rate
        if metrics.total_applications > 0:
            expected_rate = metrics.total_hired / metrics.total_applications
            assert abs(metrics.overall_conversion_rate - expected_rate) < 0.001

    @pytest.mark.asyncio
    async def test_calculate_computes_cost_metrics(self, calculator):
        """Test that cost metrics are computed correctly."""
        metrics = await calculator.calculate()

        assert metrics.total_recruiting_cost is not None
        assert metrics.total_recruiting_cost > 0
        assert metrics.average_cost_per_hire is not None
        assert metrics.average_cost_per_hire > 0

    @pytest.mark.asyncio
    async def test_calculate_by_source_type(self, calculator):
        """Test filtering by source type."""
        sources = await calculator.calculate_by_source_type("JOB_BOARD")

        assert isinstance(sources, list)
        assert len(sources) > 0
        assert all(s.source_type == "JOB_BOARD" for s in sources)

    @pytest.mark.asyncio
    async def test_calculate_by_source_type_with_dates(self, calculator):
        """Test filtering by source type with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        sources = await calculator.calculate_by_source_type(
            "REFERRAL",
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(sources, list)
        assert all(s.source_type == "REFERRAL" for s in sources)

    @pytest.mark.asyncio
    async def test_get_top_sources_by_conversion(self, calculator):
        """Test getting top sources by conversion rate."""
        top_sources = await calculator.get_top_sources(
            metric="conversion_rate",
            limit=3
        )

        assert isinstance(top_sources, list)
        assert len(top_sources) <= 3

        # Verify sources are sorted by conversion rate (descending)
        for i in range(len(top_sources) - 1):
            assert top_sources[i].conversion_rate >= top_sources[i + 1].conversion_rate

    @pytest.mark.asyncio
    async def test_get_top_sources_by_quality(self, calculator):
        """Test getting top sources by quality score."""
        top_sources = await calculator.get_top_sources(
            metric="average_quality_score",
            limit=3
        )

        assert isinstance(top_sources, list)
        assert len(top_sources) <= 3
        assert all(s.average_quality_score is not None for s in top_sources)

        # Verify sources are sorted by quality score (descending)
        for i in range(len(top_sources) - 1):
            assert top_sources[i].average_quality_score >= top_sources[i + 1].average_quality_score

    @pytest.mark.asyncio
    async def test_get_top_sources_by_cost(self, calculator):
        """Test getting top sources by cost per hire (lower is better)."""
        top_sources = await calculator.get_top_sources(
            metric="cost_per_hire",
            limit=3
        )

        assert isinstance(top_sources, list)
        assert len(top_sources) <= 3
        assert all(s.cost_per_hire is not None for s in top_sources)

        # Verify sources are sorted by cost per hire (ascending - lower is better)
        for i in range(len(top_sources) - 1):
            assert top_sources[i].cost_per_hire <= top_sources[i + 1].cost_per_hire

    @pytest.mark.asyncio
    async def test_get_top_sources_with_limit(self, calculator):
        """Test that limit parameter is respected."""
        top_sources = await calculator.get_top_sources(
            metric="conversion_rate",
            limit=2
        )

        assert len(top_sources) <= 2

    @pytest.mark.asyncio
    async def test_get_top_sources_with_date_range(self, calculator):
        """Test getting top sources with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        top_sources = await calculator.get_top_sources(
            metric="conversion_rate",
            limit=5,
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(top_sources, list)
        assert len(top_sources) <= 5

    @pytest.mark.asyncio
    async def test_get_top_sources_invalid_metric(self, calculator):
        """Test that invalid metric raises ValueError."""
        with pytest.raises(ValueError, match="Invalid metric"):
            await calculator.get_top_sources(
                metric="invalid_metric",
                limit=5
            )

    @pytest.mark.asyncio
    async def test_source_metrics_have_required_fields(self, calculator):
        """Test that all returned source metrics have required fields."""
        metrics = await calculator.calculate()

        for source in metrics.sources:
            assert source.source_type is not None
            assert source.source_name is not None
            assert source.total_applications >= 0
            assert source.hired_count >= 0
            assert 0 <= source.conversion_rate <= 1

    @pytest.mark.asyncio
    async def test_best_source_by_conversion_is_accurate(self, calculator):
        """Test that best source by conversion is correctly identified."""
        metrics = await calculator.calculate()

        if metrics.best_source_by_conversion:
            # Find the source with the highest conversion rate
            max_conversion = max(s.conversion_rate for s in metrics.sources)
            best_source = next(
                s for s in metrics.sources
                if s.conversion_rate == max_conversion
            )
            assert best_source.source_name == metrics.best_source_by_conversion

    @pytest.mark.asyncio
    async def test_best_source_by_quality_is_accurate(self, calculator):
        """Test that best source by quality is correctly identified."""
        metrics = await calculator.calculate()

        if metrics.best_source_by_quality:
            # Find the source with the highest quality score
            sources_with_quality = [
                s for s in metrics.sources
                if s.average_quality_score is not None
            ]
            if sources_with_quality:
                max_quality = max(s.average_quality_score for s in sources_with_quality)
                best_source = next(
                    s for s in sources_with_quality
                    if s.average_quality_score == max_quality
                )
                assert best_source.source_name == metrics.best_source_by_quality

    @pytest.mark.asyncio
    async def test_best_source_by_cost_is_accurate(self, calculator):
        """Test that best source by cost is correctly identified (lowest cost)."""
        metrics = await calculator.calculate()

        if metrics.best_source_by_cost:
            # Find the source with the lowest cost per hire
            sources_with_cost = [
                s for s in metrics.sources
                if s.cost_per_hire is not None
            ]
            if sources_with_cost:
                min_cost = min(s.cost_per_hire for s in sources_with_cost)
                best_source = next(
                    s for s in sources_with_cost
                    if s.cost_per_hire == min_cost
                )
                assert best_source.source_name == metrics.best_source_by_cost
