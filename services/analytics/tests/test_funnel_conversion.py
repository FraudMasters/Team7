"""
Tests for funnel conversion calculator.

Tests cover funnel conversion metrics calculation, stage transitions,
bottleneck identification, and time to hire calculations.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from calculators.funnel_conversion import (
    FunnelConversionCalculator,
    FunnelMetrics,
    StageConversion,
)


class TestStageConversion:
    """Tests for StageConversion model."""

    def test_valid_stage_conversion(self):
        """Test creation of valid stage conversion metrics."""
        stage = StageConversion(
            stage_name="SCREENING",
            candidates_entered=890,
            candidates_advanced=512,
            candidates_dropped=378,
            conversion_rate=0.575,
            drop_rate=0.425,
            average_time_in_stage_hours=48.2,
            average_time_in_stage_days=2.01,
        )

        assert stage.stage_name == "SCREENING"
        assert stage.candidates_entered == 890
        assert stage.candidates_advanced == 512
        assert stage.candidates_dropped == 378
        assert stage.conversion_rate == 0.575
        assert stage.drop_rate == 0.425

    def test_stage_conversion_with_minimal_fields(self):
        """Test creation of stage conversion with only required fields."""
        stage = StageConversion(
            stage_name="NEW",
            candidates_entered=1250,
        )

        assert stage.stage_name == "NEW"
        assert stage.candidates_entered == 1250
        assert stage.candidates_advanced == 0
        assert stage.candidates_dropped == 0
        assert stage.conversion_rate == 0.0
        assert stage.drop_rate == 0.0

    def test_stage_conversion_rates_add_to_one(self):
        """Test that conversion rate and drop rate add to approximately 1.0."""
        stage = StageConversion(
            stage_name="INTERVIEW",
            candidates_entered=298,
            candidates_advanced=156,
            candidates_dropped=142,
            conversion_rate=0.523,
            drop_rate=0.477,
        )

        # Should add up to 1.0 (within floating point precision)
        total = stage.conversion_rate + stage.drop_rate
        assert abs(total - 1.0) < 0.001

    def test_stage_conversion_time_consistency(self):
        """Test that time in hours and days are consistent."""
        stage = StageConversion(
            stage_name="TECHNICAL",
            candidates_entered=156,
            candidates_advanced=89,
            candidates_dropped=67,
            conversion_rate=0.571,
            drop_rate=0.429,
            average_time_in_stage_hours=168.3,
            average_time_in_stage_days=7.01,
        )

        # Hours / 24 should approximately equal days
        calculated_days = stage.average_time_in_stage_hours / 24
        assert abs(calculated_days - stage.average_time_in_stage_days) < 0.1


class TestFunnelMetrics:
    """Tests for FunnelMetrics model."""

    def test_valid_funnel_metrics(self):
        """Test creation of valid funnel metrics."""
        stage1 = StageConversion(
            stage_name="NEW",
            candidates_entered=1250,
            candidates_advanced=890,
            candidates_dropped=360,
            conversion_rate=0.712,
            drop_rate=0.288,
        )
        stage2 = StageConversion(
            stage_name="SCREENING",
            candidates_entered=890,
            candidates_advanced=512,
            candidates_dropped=378,
            conversion_rate=0.575,
            drop_rate=0.425,
        )

        metrics = FunnelMetrics(
            stages=[stage1, stage2],
            total_applications=1250,
            total_hired=512,
            overall_conversion_rate=0.410,
            bottleneck_stage="SCREENING",
        )

        assert len(metrics.stages) == 2
        assert metrics.total_applications == 1250
        assert metrics.total_hired == 512
        assert metrics.overall_conversion_rate == 0.410
        assert metrics.bottleneck_stage == "SCREENING"

    def test_funnel_metrics_with_empty_stages(self):
        """Test funnel metrics with no stages."""
        metrics = FunnelMetrics(
            stages=[],
            total_applications=0,
            total_hired=0,
            overall_conversion_rate=0.0,
        )

        assert len(metrics.stages) == 0
        assert metrics.total_applications == 0
        assert metrics.overall_conversion_rate == 0.0

    def test_funnel_metrics_overall_conversion(self):
        """Test that overall conversion rate is calculated correctly."""
        metrics = FunnelMetrics(
            stages=[],
            total_applications=1000,
            total_hired=50,
            overall_conversion_rate=0.05,
        )

        expected_rate = metrics.total_hired / metrics.total_applications
        assert abs(metrics.overall_conversion_rate - expected_rate) < 0.001


class TestFunnelConversionCalculator:
    """Tests for FunnelConversionCalculator."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def calculator(self, mock_db):
        """Create a calculator instance with mock DB."""
        return FunnelConversionCalculator(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_returns_metrics(self, calculator):
        """Test that calculate returns valid funnel metrics."""
        metrics = await calculator.calculate()

        assert isinstance(metrics, FunnelMetrics)
        assert metrics.total_applications > 0
        assert metrics.total_hired > 0
        assert 0 <= metrics.overall_conversion_rate <= 1
        assert len(metrics.stages) > 0

    @pytest.mark.asyncio
    async def test_calculate_with_date_range(self, calculator):
        """Test calculate with date range filters."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        metrics = await calculator.calculate(
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(metrics, FunnelMetrics)
        assert metrics.total_applications > 0

    @pytest.mark.asyncio
    async def test_calculate_with_vacancy_filter(self, calculator):
        """Test calculate with vacancy_id filter."""
        metrics = await calculator.calculate(vacancy_id="test-vacancy-123")

        assert isinstance(metrics, FunnelMetrics)
        assert metrics.total_applications > 0

    @pytest.mark.asyncio
    async def test_calculate_identifies_bottleneck(self, calculator):
        """Test that calculate identifies the bottleneck stage."""
        metrics = await calculator.calculate()

        assert metrics.bottleneck_stage is not None
        # Bottleneck should be one of the stages (excluding the last one)
        stage_names = [s.stage_name for s in metrics.stages[:-1]]
        assert metrics.bottleneck_stage in stage_names

    @pytest.mark.asyncio
    async def test_calculate_identifies_highest_dropout(self, calculator):
        """Test that calculate identifies stage with highest dropout."""
        metrics = await calculator.calculate()

        assert metrics.highest_dropout_stage is not None
        # Should be one of the stages
        stage_names = [s.stage_name for s in metrics.stages]
        assert metrics.highest_dropout_stage in stage_names

    @pytest.mark.asyncio
    async def test_calculate_computes_overall_conversion(self, calculator):
        """Test that overall conversion rate is computed correctly."""
        metrics = await calculator.calculate()

        expected_rate = metrics.total_hired / metrics.total_applications
        assert abs(metrics.overall_conversion_rate - expected_rate) < 0.001

    @pytest.mark.asyncio
    async def test_calculate_computes_average_funnel_time(self, calculator):
        """Test that average funnel time is computed correctly."""
        metrics = await calculator.calculate()

        assert metrics.average_funnel_time_days is not None
        assert metrics.average_funnel_time_days > 0

        # Verify it's the sum of individual stage times
        stages_with_time = [
            s for s in metrics.stages
            if s.average_time_in_stage_days is not None
        ]
        expected_total = sum(s.average_time_in_stage_days for s in stages_with_time)
        assert abs(metrics.average_funnel_time_days - expected_total) < 0.01

    @pytest.mark.asyncio
    async def test_stages_are_ordered(self, calculator):
        """Test that stages appear in logical funnel order."""
        metrics = await calculator.calculate()

        # First stage should be NEW
        assert metrics.stages[0].stage_name == "NEW"
        # Last stage should be ACCEPTED or HIRED
        assert metrics.stages[-1].stage_name in ["ACCEPTED", "HIRED"]

    @pytest.mark.asyncio
    async def test_stage_candidates_decrease_through_funnel(self, calculator):
        """Test that candidate count decreases (or stays same) through funnel."""
        metrics = await calculator.calculate()

        for i in range(len(metrics.stages) - 1):
            current_stage = metrics.stages[i]
            next_stage = metrics.stages[i + 1]

            # Next stage should have <= candidates than current stage entered
            assert next_stage.candidates_entered <= current_stage.candidates_entered

    @pytest.mark.asyncio
    async def test_stage_conversions_are_valid(self, calculator):
        """Test that all stage conversion rates are valid (0-1)."""
        metrics = await calculator.calculate()

        for stage in metrics.stages:
            assert 0 <= stage.conversion_rate <= 1
            assert 0 <= stage.drop_rate <= 1

    @pytest.mark.asyncio
    async def test_calculate_stage_transition_valid(self, calculator):
        """Test calculating conversion between two specific stages."""
        result = await calculator.calculate_stage_transition(
            from_stage="SCREENING",
            to_stage="PHONE_SCREEN"
        )

        assert result["from_stage"] == "SCREENING"
        assert result["to_stage"] == "PHONE_SCREEN"
        assert result["candidates_from"] > 0
        assert result["candidates_to"] > 0
        assert 0 <= result["conversion_rate"] <= 1

    @pytest.mark.asyncio
    async def test_calculate_stage_transition_with_dates(self, calculator):
        """Test stage transition calculation with date filters."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        result = await calculator.calculate_stage_transition(
            from_stage="NEW",
            to_stage="SCREENING",
            start_date=start_date,
            end_date=end_date
        )

        assert result["conversion_rate"] >= 0

    @pytest.mark.asyncio
    async def test_calculate_stage_transition_invalid_from_stage(self, calculator):
        """Test that invalid from_stage raises ValueError."""
        with pytest.raises(ValueError, match="Stage not found"):
            await calculator.calculate_stage_transition(
                from_stage="INVALID_STAGE",
                to_stage="SCREENING"
            )

    @pytest.mark.asyncio
    async def test_calculate_stage_transition_invalid_to_stage(self, calculator):
        """Test that invalid to_stage raises ValueError."""
        with pytest.raises(ValueError, match="Stage not found"):
            await calculator.calculate_stage_transition(
                from_stage="SCREENING",
                to_stage="INVALID_STAGE"
            )

    @pytest.mark.asyncio
    async def test_get_bottlenecks_with_default_threshold(self, calculator):
        """Test getting bottlenecks with default threshold."""
        bottlenecks = await calculator.get_bottlenecks()

        assert isinstance(bottlenecks, list)
        # All bottlenecks should have conversion rate < 0.5
        for stage in bottlenecks:
            assert stage.conversion_rate < 0.5

    @pytest.mark.asyncio
    async def test_get_bottlenecks_with_custom_threshold(self, calculator):
        """Test getting bottlenecks with custom threshold."""
        threshold = 0.6
        bottlenecks = await calculator.get_bottlenecks(threshold=threshold)

        assert isinstance(bottlenecks, list)
        # All bottlenecks should have conversion rate < threshold
        for stage in bottlenecks:
            assert stage.conversion_rate < threshold

    @pytest.mark.asyncio
    async def test_get_bottlenecks_sorted_by_conversion(self, calculator):
        """Test that bottlenecks are sorted by conversion rate (ascending)."""
        bottlenecks = await calculator.get_bottlenecks(threshold=0.7)

        # Verify sorted order (worst first)
        for i in range(len(bottlenecks) - 1):
            assert bottlenecks[i].conversion_rate <= bottlenecks[i + 1].conversion_rate

    @pytest.mark.asyncio
    async def test_get_bottlenecks_with_date_range(self, calculator):
        """Test getting bottlenecks with date range."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        bottlenecks = await calculator.get_bottlenecks(
            threshold=0.6,
            start_date=start_date,
            end_date=end_date
        )

        assert isinstance(bottlenecks, list)

    @pytest.mark.asyncio
    async def test_get_bottlenecks_high_threshold_returns_many(self, calculator):
        """Test that high threshold returns more bottlenecks."""
        bottlenecks_low = await calculator.get_bottlenecks(threshold=0.3)
        bottlenecks_high = await calculator.get_bottlenecks(threshold=0.9)

        # Higher threshold should return more or equal bottlenecks
        assert len(bottlenecks_high) >= len(bottlenecks_low)

    @pytest.mark.asyncio
    async def test_calculate_time_to_hire_returns_metrics(self, calculator):
        """Test that calculate_time_to_hire returns valid metrics."""
        time_metrics = await calculator.calculate_time_to_hire()

        assert "average_days" in time_metrics
        assert "total_stages" in time_metrics
        assert "slowest_stage" in time_metrics
        assert "fastest_stage" in time_metrics
        assert time_metrics["average_days"] > 0
        assert time_metrics["total_stages"] > 0

    @pytest.mark.asyncio
    async def test_calculate_time_to_hire_with_date_range(self, calculator):
        """Test time to hire calculation with date filters."""
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)

        time_metrics = await calculator.calculate_time_to_hire(
            start_date=start_date,
            end_date=end_date
        )

        assert time_metrics["average_days"] > 0

    @pytest.mark.asyncio
    async def test_calculate_time_to_hire_identifies_slowest_stage(self, calculator):
        """Test that slowest stage is correctly identified."""
        time_metrics = await calculator.calculate_time_to_hire()

        assert time_metrics["slowest_stage"] is not None
        assert time_metrics["slowest_stage_days"] > 0

    @pytest.mark.asyncio
    async def test_calculate_time_to_hire_identifies_fastest_stage(self, calculator):
        """Test that fastest stage is correctly identified."""
        time_metrics = await calculator.calculate_time_to_hire()

        assert time_metrics["fastest_stage"] is not None
        assert time_metrics["fastest_stage_days"] > 0

    @pytest.mark.asyncio
    async def test_calculate_time_to_hire_slowest_vs_fastest(self, calculator):
        """Test that slowest stage takes more time than fastest stage."""
        time_metrics = await calculator.calculate_time_to_hire()

        assert time_metrics["slowest_stage_days"] >= time_metrics["fastest_stage_days"]

    @pytest.mark.asyncio
    async def test_bottleneck_is_stage_with_lowest_conversion(self, calculator):
        """Test that identified bottleneck has the lowest conversion rate."""
        metrics = await calculator.calculate()

        if metrics.bottleneck_stage:
            bottleneck = next(
                s for s in metrics.stages
                if s.stage_name == metrics.bottleneck_stage
            )

            # Bottleneck should have the lowest conversion among non-final stages
            non_final_stages = metrics.stages[:-1]
            min_conversion = min(s.conversion_rate for s in non_final_stages)
            assert bottleneck.conversion_rate == min_conversion

    @pytest.mark.asyncio
    async def test_highest_dropout_has_max_drop_rate(self, calculator):
        """Test that highest dropout stage has the maximum drop rate."""
        metrics = await calculator.calculate()

        if metrics.highest_dropout_stage:
            highest_dropout = next(
                s for s in metrics.stages
                if s.stage_name == metrics.highest_dropout_stage
            )

            # Should have the highest drop rate among all stages
            max_drop_rate = max(s.drop_rate for s in metrics.stages)
            assert highest_dropout.drop_rate == max_drop_rate

    @pytest.mark.asyncio
    async def test_stage_entered_equals_previous_advanced(self, calculator):
        """Test that candidates entering a stage equals those who advanced from previous."""
        metrics = await calculator.calculate()

        # For each stage after the first, candidates_entered should equal
        # candidates_advanced from the previous stage
        for i in range(1, len(metrics.stages)):
            current_stage = metrics.stages[i]
            previous_stage = metrics.stages[i - 1]

            assert current_stage.candidates_entered == previous_stage.candidates_advanced
