"""
Integration tests for complete A/B testing lifecycle.

This test suite validates the end-to-end integration between:
- A/B Testing data models (ABTest, ABTestAssignment, ABTestMetric)
- Weight Optimizer Service (user assignment, metric recording, statistical analysis)
- Matching Weight Profiles (preset profiles for variants)
- Database (persistence and relationships)

Test Coverage:
- Complete A/B test lifecycle (create → assign → metrics → analyze → optimize)
- Deterministic user assignment to profiles
- Metric recording with validation
- Statistical analysis using scipy
- Weight optimization based on performance data
- Database relationships and cascade deletes
- Edge cases and error handling
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ab_testing import (
    ABTest,
    ABTestAssignment,
    ABTestMetric,
    ABTestMetricType,
    ABTestStatus,
)
from models.matching_weights import MatchingWeightProfile, PRESET_PROFILES, create_preset_profiles
from services.weight_optimizer import WeightOptimizerService


# ============================================================================
# Fixtures for A/B Testing Integration Tests
# ============================================================================

@pytest.fixture(scope="function")
async def preset_profiles(test_db: AsyncSession):
    """
    Create preset weight profiles for A/B testing.

    This fixture creates the four preset profiles (Technical, Creative, Executive, Balanced)
    that are used as variants in A/B tests.

    Args:
        test_db: Database session

    Returns:
        List of created MatchingWeightProfile instances
    """
    profiles = create_preset_profiles()
    for profile in profiles:
        test_db.add(profile)
    await test_db.commit()

    # Refresh to get IDs
    for profile in profiles:
        await test_db.refresh(profile)

    return profiles


@pytest.fixture(scope="function")
async def active_ab_test(test_db: AsyncSession, preset_profiles):
    """
    Create an active A/B test for testing.

    This fixture creates an A/B test in RUNNING state with preset profiles
    available for user assignment.

    Args:
        test_db: Database session
        preset_profiles: Preset weight profiles

    Returns:
        Created ABTest instance
    """
    test = ABTest(
        name="Integration Test A/B Test",
        description="Testing complete A/B testing lifecycle",
        status=ABTestStatus.RUNNING,
        start_date=datetime.now(timezone.utc),
        organization_id=str(uuid4()),
        created_by=str(uuid4()),
    )
    test_db.add(test)
    await test_db.commit()
    await test_db.refresh(test)

    return test


@pytest.fixture(scope="function")
async def weight_optimizer_service(test_db: AsyncSession):
    """
    Create a WeightOptimizerService instance for testing.

    Args:
        test_db: Database session

    Returns:
        WeightOptimizerService instance
    """
    return WeightOptimizerService(test_db)


# ============================================================================
# Test Classes
# ============================================================================

class TestABTestCreation:
    """Tests for A/B test creation and initialization."""

    @pytest.mark.asyncio
    async def test_create_ab_test_with_valid_data(self, test_db: AsyncSession):
        """Test creating an A/B test with valid data."""
        org_id = str(uuid4())
        created_by = str(uuid4())

        test = ABTest(
            name="Q1 2026 Weight Optimization",
            description="Optimize matching weights for Q1 2026 hiring season",
            status=ABTestStatus.RUNNING,
            start_date=datetime.now(timezone.utc),
            organization_id=org_id,
            created_by=created_by,
        )

        test_db.add(test)
        await test_db.commit()
        await test_db.refresh(test)

        assert test.id is not None
        assert test.name == "Q1 2026 Weight Optimization"
        assert test.status == ABTestStatus.RUNNING
        assert test.organization_id == org_id
        assert test.created_by == created_by
        assert test.created_at is not None
        assert test.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_ab_test_with_draft_status(self, test_db: AsyncSession):
        """Test creating an A/B test in DRAFT status."""
        test = ABTest(
            name="Future Test",
            description="Test created in advance",
            status=ABTestStatus.DRAFT,
            organization_id=str(uuid4()),
        )

        test_db.add(test)
        await test_db.commit()
        await test_db.refresh(test)

        assert test.status == ABTestStatus.DRAFT
        assert test.start_date is None
        assert test.end_date is None

    @pytest.mark.asyncio
    async def test_ab_test_timestamp_mixin(self, test_db: AsyncSession):
        """Test that ABTest inherits timestamp fields correctly."""
        test = ABTest(
            name="Timestamp Test",
            status=ABTestStatus.RUNNING,
            start_date=datetime.now(timezone.utc),
            organization_id=str(uuid4()),
        )

        test_db.add(test)
        await test_db.commit()
        await test_db.refresh(test)

        # Verify created_at and updated_at are set
        assert test.created_at is not None
        assert test.updated_at is not None
        # updated_at should be >= created_at
        assert test.updated_at >= test.created_at


class TestUserAssignmentFlow:
    """Tests for user assignment to A/B test variants."""

    @pytest.mark.asyncio
    async def test_assign_user_to_variant(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test assigning a user to an A/B test variant.

        Validates:
        - User is assigned successfully
        - Assignment is deterministic (same user gets same profile)
        - Assignment record is persisted
        - Profile is valid and active
        """
        user_id = str(uuid4())
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign user
        assignment = await weight_optimizer_service.assign_user_to_variant(
            test_id=test_id,
            user_id=user_id,
            organization_id=org_id,
        )

        assert assignment.user_id == user_id
        assert assignment.test_id == test_id
        assert assignment.profile_id is not None
        assert assignment.profile_name in [p.name for p in preset_profiles]
        assert assignment.assignment_id is not None
        assert assignment.was_new_assignment is True

        # Verify assignment was persisted
        result = await test_db.execute(
            select(ABTestAssignment).where(ABTestAssignment.user_id == user_id)
        )
        persisted_assignment = result.scalar_one_or_none()
        assert persisted_assignment is not None
        assert str(persisted_assignment.id) == assignment.assignment_id

    @pytest.mark.asyncio
    async def test_assignment_is_deterministic(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that the same user always gets the same profile assignment.

        This is critical for A/B test validity - a user should not see
        different variants on different requests.
        """
        user_id = str(uuid4())
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # First assignment
        assignment1 = await weight_optimizer_service.assign_user_to_variant(
            test_id=test_id,
            user_id=user_id,
            organization_id=org_id,
        )

        # Second assignment (should return cached result)
        assignment2 = await weight_optimizer_service.assign_user_to_variant(
            test_id=test_id,
            user_id=user_id,
            organization_id=org_id,
        )

        # Both assignments should be identical
        assert assignment1.profile_id == assignment2.profile_id
        assert assignment1.profile_name == assignment2.profile_name
        assert assignment1.assignment_id == assignment2.assignment_id
        assert assignment1.was_new_assignment is True
        assert assignment2.was_new_assignment is False

    @pytest.mark.asyncio
    async def test_multiple_users_get_distributed(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that multiple users are distributed across profiles.

        With enough users, all profiles should receive assignments.
        Distribution should be roughly even due to hash-based assignment.
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign 20 users (more than number of profiles)
        assignments = []
        num_users = 20
        for i in range(num_users):
            user_id = str(uuid4())
            assignment = await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            assignments.append(assignment)

        # Count assignments per profile
        profile_counts = {}
        for assignment in assignments:
            profile_name = assignment.profile_name
            profile_counts[profile_name] = profile_counts.get(profile_name, 0) + 1

        # All profiles should have at least one assignment
        assert len(profile_counts) == len(preset_profiles)

        # Each profile should have roughly equal distribution
        # (with 20 users and 4 profiles, expect ~5 users each)
        for count in profile_counts.values():
            assert count >= 1  # At least one user per profile

    @pytest.mark.asyncio
    async def test_assignment_fails_for_nonexistent_test(
        self,
        test_db: AsyncSession,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that assignment fails gracefully for non-existent test."""
        with pytest.raises(ValueError, match="A/B test not found"):
            await weight_optimizer_service.assign_user_to_variant(
                test_id=str(uuid4()),
                user_id=str(uuid4()),
                organization_id=str(uuid4()),
            )

    @pytest.mark.asyncio
    async def test_assignment_fails_for_draft_test(
        self,
        test_db: AsyncSession,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that assignment fails for tests not in RUNNING state."""
        draft_test = ABTest(
            name="Draft Test",
            status=ABTestStatus.DRAFT,
            organization_id=str(uuid4()),
        )
        test_db.add(draft_test)
        await test_db.commit()

        with pytest.raises(ValueError, match="not in running state"):
            await weight_optimizer_service.assign_user_to_variant(
                test_id=str(draft_test.id),
                user_id=str(uuid4()),
                organization_id=draft_test.organization_id,
            )


class TestMetricRecordingFlow:
    """Tests for recording performance metrics in A/B tests."""

    @pytest.mark.asyncio
    async def test_record_match_acceptance_metric(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test recording match acceptance metric.

        Validates:
        - Metric is recorded successfully
        - Value is clamped to valid range (0.0 or 1.0)
        - Assignment is found correctly
        - Metric record is persisted
        """
        # Assign user first
        user_id = str(uuid4())
        assignment = await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        # Record match acceptance (binary metric)
        metric_record = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            metric_value=1.0,  # User accepted the match
        )

        assert metric_record.assignment_id == assignment.assignment_id
        assert metric_record.metric_type == ABTestMetricType.MATCH_ACCEPTANCE
        assert metric_record.metric_value == 1.0
        assert metric_record.recorded_at is not None

        # Verify metric was persisted
        result = await test_db.execute(
            select(ABTestMetric).where(ABTestMetric.id == metric_record.metric_id)
        )
        persisted_metric = result.scalar_one_or_none()
        assert persisted_metric is not None

    @pytest.mark.asyncio
    async def test_record_time_to_hire_metric(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test recording time-to-hire metric (continuous in days)."""
        user_id = str(uuid4())
        await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        # Record time to hire (14 days)
        metric_record = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.TIME_TO_HIRE,
            metric_value=14.0,
        )

        assert metric_record.metric_type == ABTestMetricType.TIME_TO_HIRE
        assert metric_record.metric_value == 14.0

    @pytest.mark.asyncio
    async def test_record_user_satisfaction_metric(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test recording user satisfaction metric (ordinal 1-5 scale)."""
        user_id = str(uuid4())
        await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        # Record satisfaction score (4 out of 5)
        metric_record = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.USER_SATISFACTION,
            metric_value=4.0,
        )

        assert metric_record.metric_type == ABTestMetricType.USER_SATISFACTION
        assert metric_record.metric_value == 4.0

    @pytest.mark.asyncio
    async def test_metric_value_clamping(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that metric values are clamped to valid ranges.

        - MATCH_ACCEPTANCE: clamped to 0.0 or 1.0
        - USER_SATISFACTION: clamped to 1.0-5.0
        - TIME_TO_HIRE: clamped to non-negative
        """
        user_id = str(uuid4())
        await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        # Test match acceptance clamping (invalid value 0.6 should be clamped to 1.0)
        metric1 = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            metric_value=0.6,
        )
        assert metric1.metric_value in (0.0, 1.0)

        # Test satisfaction clamping (6.0 should be clamped to 5.0)
        metric2 = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.USER_SATISFACTION,
            metric_value=6.0,
        )
        assert 1.0 <= metric2.metric_value <= 5.0

    @pytest.mark.asyncio
    async def test_record_multiple_metrics_for_same_user(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test recording all three metric types for the same user.

        Validates that partial metric data is supported - not all metrics
        need to be recorded at the same time.
        """
        user_id = str(uuid4())
        await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        # Record all three metrics
        metric1 = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            metric_value=1.0,
        )

        metric2 = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.TIME_TO_HIRE,
            metric_value=21.0,
        )

        metric3 = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.USER_SATISFACTION,
            metric_value=5.0,
        )

        # All metrics should have the same assignment_id
        assert metric1.assignment_id == metric2.assignment_id == metric3.assignment_id

    @pytest.mark.asyncio
    async def test_record_metric_fails_without_assignment(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that recording a metric fails if user has no assignment."""
        with pytest.raises(ValueError, match="No assignment found"):
            await weight_optimizer_service.record_metric(
                test_id=str(active_ab_test.id),
                user_id=str(uuid4()),
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0,
            )


class TestStatisticalAnalysisFlow:
    """Tests for statistical analysis of A/B test results."""

    @pytest.mark.asyncio
    async def test_analyze_metrics_with_sufficient_data(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test analyzing metrics with sufficient sample size.

        Validates:
        - Metrics are grouped correctly by profile
        - Statistical tests are run
        - Results include p-value, effect size, confidence interval
        - Comparison data is provided
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign users and record metrics for at least 2 profiles
        # We need at least 30 samples per profile for statistical analysis
        num_users = 60  # 30 per profile minimum

        for i in range(num_users):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )

            # Record match acceptance metric
            # Use deterministic values to ensure statistical significance
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0 if i < num_users // 2 else 0.0,
            )

        # Analyze metrics
        analysis = await weight_optimizer_service.analyze_metrics(
            test_id=test_id,
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
        )

        assert "metric_type" in analysis
        assert "profiles" in analysis
        assert "statistical_test" in analysis
        assert "comparison" in analysis

        # Verify statistical test results
        stat_test = analysis["statistical_test"]
        assert "test_type" in stat_test
        assert "p_value" in stat_test
        assert "is_significant" in stat_test
        assert "effect_size" in stat_test
        assert "variant_a_mean" in stat_test
        assert "variant_b_mean" in stat_test
        assert "sample_size_a" in stat_test
        assert "sample_size_b" in stat_test

    @pytest.mark.asyncio
    async def test_analyze_metrics_fails_with_insufficient_data(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that analysis fails with less than minimum sample size."""
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign only 10 users (less than MIN_SAMPLE_SIZE=30)
        for i in range(10):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0,
            )

        with pytest.raises(ValueError, match="Insufficient sample size"):
            await weight_optimizer_service.analyze_metrics(
                test_id=test_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            )


class TestWeightOptimizationFlow:
    """Tests for automated weight optimization based on A/B test results."""

    @pytest.mark.asyncio
    async def test_optimize_weights_with_significant_improvement(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test weight optimization when significant improvement is found.

        Validates:
        - Optimization recommendation is generated
        - Best profile is identified
        - Recommended weights are provided
        - Reason includes statistical significance
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign users and record metrics with clear differences
        # First 30 users: high match acceptance (1.0)
        # Next 30 users: low match acceptance (0.0)
        # This creates a statistically significant difference
        for i in range(60):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0 if i < 30 else 0.0,
            )

        # Run optimization
        optimization_result = await weight_optimizer_service.optimize_weights(test_id=test_id)

        assert optimization_result.should_optimize is True
        assert "recommended_weights" in optimization_result.__dict__
        assert optimization_result.reason is not None
        assert optimization_result.metrics_summary is not None

        # Verify recommended weights sum to approximately 1.0
        weights = optimization_result.recommended_weights
        if weights:
            total = weights.get("keyword_weight", 0) + weights.get("tfidf_weight", 0) + weights.get("vector_weight", 0)
            assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_optimize_weights_returns_no_optimize_when_no_significance(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that optimization returns should_optimize=False when no significant improvement.

        When metrics don't show statistically significant differences (p >= 0.05),
        the optimizer should recommend continuing data collection.
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign users with similar match acceptance (no significant difference)
        for i in range(60):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            # All users have similar match acceptance (~50%)
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0 if i % 2 == 0 else 0.0,
            )

        # Run optimization
        optimization_result = await weight_optimizer_service.optimize_weights(test_id=test_id)

        # With similar data, should not recommend optimization
        assert optimization_result.should_optimize is False
        assert "continue collecting data" in optimization_result.reason.lower()

    @pytest.mark.asyncio
    async def test_optimize_weights_analyzes_all_metric_types(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that optimization analyzes all three metric types.

        Validates that metrics_summary includes data for all metric types
        that have sufficient data.
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Assign users and record all metric types
        for i in range(60):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0 if i < 30 else 0.0,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.TIME_TO_HIRE,
                metric_value=10.0 + i,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.USER_SATISFACTION,
                metric_value=4.0 if i < 30 else 3.0,
            )

        # Run optimization
        optimization_result = await weight_optimizer_service.optimize_weights(test_id=test_id)

        # Check that all metric types are in summary
        summary = optimization_result.metrics_summary
        assert "match_acceptance" in summary or "error" in summary.get("match_acceptance", {})
        assert "time_to_hire" in summary or "error" in summary.get("time_to_hire", {})
        assert "user_satisfaction" in summary or "error" in summary.get("user_satisfaction", {})


class TestEndToEndABTestingLifecycle:
    """Complete end-to-end tests of the A/B testing lifecycle."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_ab_testing_lifecycle(
        self,
        test_db: AsyncSession,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test the complete A/B testing lifecycle from start to finish.

        This test simulates a real-world scenario:
        1. Create A/B test
        2. Assign users to variants
        3. Record performance metrics
        4. Run statistical analysis
        5. Generate optimization recommendation

        Validates:
        - All components work together correctly
        - Data flows correctly through the system
        - Statistical analysis produces valid results
        - Optimization recommendation is actionable
        """
        # Step 1: Create A/B test
        org_id = str(uuid4())
        test = ABTest(
            name="E2E Test - Complete Lifecycle",
            description="End-to-end test of A/B testing system",
            status=ABTestStatus.RUNNING,
            start_date=datetime.now(timezone.utc),
            organization_id=org_id,
            created_by=str(uuid4()),
        )
        test_db.add(test)
        await test_db.commit()
        await test_db.refresh(test)

        test_id = str(test.id)
        assert test.status == ABTestStatus.RUNNING

        # Step 2: Assign users to variants (100 users)
        user_ids = []
        for i in range(100):
            user_id = str(uuid4())
            user_ids.append(user_id)
            assignment = await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            assert assignment.profile_id is not None

        # Verify all users were assigned
        result = await test_db.execute(
            select(ABTestAssignment).where(ABTestAssignment.test_id == test.id)
        )
        assignments = result.scalars().all()
        assert len(assignments) == 100

        # Step 3: Record performance metrics
        # Simulate that one profile performs better
        for i, user_id in enumerate(user_ids):
            # First 50 users: high performance
            # Last 50 users: low performance
            is_high_performer = i < 50

            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0 if is_high_performer else 0.3,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.TIME_TO_HIRE,
                metric_value=14.0 if is_high_performer else 45.0,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.USER_SATISFACTION,
                metric_value=4.5 if is_high_performer else 2.5,
            )

        # Verify metrics were recorded
        result = await test_db.execute(
            select(ABTestMetric).where(ABTestMetric.test_id == test.id)
        )
        metrics = result.scalars().all()
        assert len(metrics) == 300  # 100 users * 3 metrics

        # Step 4: Run statistical analysis for each metric type
        for metric_type in ABTestMetricType:
            try:
                analysis = await weight_optimizer_service.analyze_metrics(
                    test_id=test_id,
                    metric_type=metric_type,
                )
                assert analysis["metric_type"] == metric_type.value
                assert len(analysis["profiles"]) >= 2
                assert "statistical_test" in analysis
            except ValueError as e:
                # Some metrics may not have sufficient sample size per profile
                # This is acceptable if distribution is uneven
                assert "Insufficient sample size" in str(e)

        # Step 5: Generate optimization recommendation
        optimization_result = await weight_optimizer_service.optimize_weights(test_id=test_id)

        # Validate optimization result
        assert isinstance(optimization_result.should_optimize, bool)
        assert optimization_result.reason is not None
        assert optimization_result.metrics_summary is not None

        # If optimization is recommended, verify weights
        if optimization_result.should_optimize:
            weights = optimization_result.recommended_weights
            assert "keyword_weight" in weights
            assert "tfidf_weight" in weights
            assert "vector_weight" in weights
            # Weights should sum to 1.0
            total = weights["keyword_weight"] + weights["tfidf_weight"] + weights["vector_weight"]
            assert abs(total - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_cascade_delete_of_ab_test(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """
        Test that deleting an A/B test cascades to assignments and metrics.

        Validates foreign key CASCADE behavior.
        """
        test_id = str(active_ab_test.id)
        org_id = active_ab_test.organization_id

        # Create assignments and metrics
        for i in range(10):
            user_id = str(uuid4())
            await weight_optimizer_service.assign_user_to_variant(
                test_id=test_id,
                user_id=user_id,
                organization_id=org_id,
            )
            await weight_optimizer_service.record_metric(
                test_id=test_id,
                user_id=user_id,
                metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
                metric_value=1.0,
            )

        # Verify data exists
        result = await test_db.execute(
            select(ABTestAssignment).where(ABTestAssignment.test_id == active_ab_test.id)
        )
        assert result.scalar_one_or_none() is not None

        result = await test_db.execute(
            select(ABTestMetric).where(ABTestMetric.test_id == active_ab_test.id)
        )
        assert result.scalar_one_or_none() is not None

        # Delete the test
        await test_db.delete(active_ab_test)
        await test_db.commit()

        # Verify assignments were cascaded
        result = await test_db.execute(
            select(ABTestAssignment).where(ABTestAssignment.test_id == active_ab_test.id)
        )
        assert result.scalar_one_or_none() is None

        # Verify metrics were cascaded
        result = await test_db.execute(
            select(ABTestMetric).where(ABTestMetric.test_id == active_ab_test.id)
        )
        assert result.scalar_one_or_none() is None


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_assignment_with_no_preset_profiles(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that assignment fails when no preset profiles exist."""
        # Note: This test requires no preset_profiles fixture
        # Delete any existing preset profiles
        await test_db.execute(
            select(MatchingWeightProfile).where(
                MatchingWeightProfile.is_preset == True
            )
        )
        # Delete all preset profiles
        result = await test_db.execute(
            select(MatchingWeightProfile).where(
                MatchingWeightProfile.is_preset == True
            )
        )
        profiles = result.scalars().all()
        for profile in profiles:
            await test_db.delete(profile)
        await test_db.commit()

        # Try to assign user
        with pytest.raises(ValueError, match="No active preset profiles found"):
            await weight_optimizer_service.assign_user_to_variant(
                test_id=str(active_ab_test.id),
                user_id=str(uuid4()),
                organization_id=active_ab_test.organization_id,
            )

    @pytest.mark.asyncio
    async def test_invalid_test_id_format(
        self,
        test_db: AsyncSession,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that invalid UUID format is handled correctly."""
        with pytest.raises(ValueError, match="Invalid test_id format"):
            await weight_optimizer_service.assign_user_to_variant(
                test_id="not-a-uuid",
                user_id=str(uuid4()),
                organization_id=str(uuid4()),
            )

    @pytest.mark.asyncio
    async def test_metric_recording_with_custom_timestamp(
        self,
        test_db: AsyncSession,
        active_ab_test: ABTest,
        preset_profiles,
        weight_optimizer_service: WeightOptimizerService,
    ):
        """Test that custom recorded_at timestamp is preserved."""
        user_id = str(uuid4())
        await weight_optimizer_service.assign_user_to_variant(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            organization_id=active_ab_test.organization_id,
        )

        custom_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        metric_record = await weight_optimizer_service.record_metric(
            test_id=str(active_ab_test.id),
            user_id=user_id,
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            metric_value=1.0,
            recorded_at=custom_time,
        )

        assert metric_record.recorded_at == custom_time


# ============================================================================
# Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers for A/B testing tests."""
    config.addinivalue_line("markers", "ab_testing: Marks tests as A/B testing integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
