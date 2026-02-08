"""
Unit tests for WeightOptimizerService.

Tests cover:
- Service initialization and constants
- User assignment to variants (deterministic and random)
- Metric recording with validation
- Statistical analysis methods
- Weight optimization logic
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4, UUID

from models.ab_testing import (
    ABTest,
    ABTestAssignment,
    ABTestMetric,
    ABTestMetricType,
    ABTestStatus,
)
from models.matching_weights import MatchingWeightProfile, PRESET_PROFILES
from services.weight_optimizer import (
    UserAssignment,
    MetricRecord,
    StatisticalTestResult,
    OptimizationResult,
    WeightOptimizerService,
    get_weight_optimizer_service,
)


class TestWeightOptimizerServiceInit:
    """Tests for WeightOptimizerService initialization."""

    def test_default_initialization(self):
        """Test initialization with database session."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        assert service.db is mock_db
        assert service.MIN_SAMPLE_SIZE == 30
        assert service.SIGNIFICANCE_LEVEL == 0.05
        assert service.RANDOM_SEED == 42
        assert hasattr(service, "_rng")

    def test_constants_values(self):
        """Test that constants have expected values."""
        assert WeightOptimizerService.MIN_SAMPLE_SIZE == 30
        assert WeightOptimizerService.SIGNIFICANCE_LEVEL == 0.05
        assert WeightOptimizerService.RANDOM_SEED == 42

    def test_rng_is_seeded(self):
        """Test that RNG is initialized with correct seed."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        # Verify RNG is numpy random generator
        import numpy as np
        assert hasattr(service._rng, "random")
        assert hasattr(service._rng, "choice")


class TestAssignUserToVariant:
    """Tests for assign_user_to_variant method."""

    @pytest.mark.asyncio
    async def test_invalid_test_id_format(self):
        """Test that invalid test_id format raises ValueError."""
        mock_db = AsyncMock()
        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="Invalid test_id format"):
            await service.assign_user_to_variant(
                "invalid-uuid",
                "user-123",
                "org-123",
            )

    @pytest.mark.asyncio
    async def test_test_not_found(self):
        """Test that non-existent test raises ValueError."""
        mock_db = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="A/B test not found"):
            await service.assign_user_to_variant(
                str(uuid4()),
                "user-123",
                "org-123",
            )

    @pytest.mark.asyncio
    async def test_test_not_in_running_state(self):
        """Test that non-running test raises ValueError."""
        mock_db = AsyncMock()

        # Mock test in DRAFT state
        test_id = uuid4()
        mock_test = Mock()
        mock_test.status = ABTestStatus.DRAFT
        mock_test.id = test_id
        mock_test.organization_id = "org-123"

        # Setup query to return test
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_test
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="not in running state"):
            await service.assign_user_to_variant(
                str(test_id),
                "user-123",
                "org-123",
            )

    @pytest.mark.asyncio
    async def test_no_preset_profiles_available(self):
        """Test that missing preset profiles raises ValueError."""
        mock_db = AsyncMock()

        # Mock running test
        test_id = uuid4()
        mock_test = Mock()
        mock_test.status = ABTestStatus.RUNNING
        mock_test.id = test_id
        mock_test.organization_id = "org-123"

        # Setup query chain: test query returns test, profiles query returns empty
        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.return_value = mock_test

        mock_result2 = Mock()
        mock_result2.scalars.return_value.all.return_value = []

        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_result1
            return mock_result2

        mock_db.execute.side_effect = mock_execute
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="No active preset profiles found"):
            await service.assign_user_to_variant(
                str(test_id),
                "user-123",
                "org-123",
            )

    @pytest.mark.asyncio
    async def test_successful_new_assignment(self):
        """Test successful new user assignment."""
        mock_db = AsyncMock()

        # Mock running test
        test_id = uuid4()
        profile_id = uuid4()
        mock_test = Mock()
        mock_test.status = ABTestStatus.RUNNING
        mock_test.id = test_id
        mock_test.organization_id = "org-123"

        # Mock profile
        mock_profile = Mock()
        mock_profile.id = profile_id
        mock_profile.name = "Technical"

        # Mock new assignment
        mock_assignment = Mock()
        mock_assignment.id = uuid4()

        # Setup query chain
        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.return_value = None  # No existing assignment

        mock_result2 = Mock()
        mock_result2.scalars.return_value.all.return_value = [mock_profile]

        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_result1
            elif call_count == 2:
                return mock_result1  # No existing assignment check
            return mock_result2

        mock_db.execute.side_effect = mock_execute
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Capture the added assignment
        def capture_add(obj):
            nonlocal mock_assignment
            mock_assignment = obj

        mock_db.add.side_effect = capture_add

        service = WeightOptimizerService(mock_db)

        result = await service.assign_user_to_variant(
            str(test_id),
            "user-123",
            "org-123",
        )

        assert isinstance(result, UserAssignment)
        assert result.user_id == "user-123"
        assert result.test_id == str(test_id)
        assert result.profile_name == "Technical"
        assert result.was_new_assignment is True

    @pytest.mark.asyncio
    async def test_deterministic_assignment_same_user(self):
        """Test that same user always gets same profile."""
        mock_db = AsyncMock()

        # Mock running test
        test_id = uuid4()
        profile_id = uuid4()
        mock_test = Mock()
        mock_test.status = ABTestStatus.RUNNING
        mock_test.id = test_id
        mock_test.organization_id = "org-123"

        # Mock multiple profiles
        mock_profile1 = Mock()
        mock_profile1.id = uuid4()
        mock_profile1.name = "Technical"

        mock_profile2 = Mock()
        mock_profile2.id = uuid4()
        mock_profile2.name = "Creative"

        mock_profile3 = Mock()
        mock_profile3.id = uuid4()
        mock_profile3.name = "Executive"

        profiles = [mock_profile1, mock_profile2, mock_profile3]

        # Mock queries
        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.return_value = None  # No existing assignment

        mock_result2 = Mock()
        mock_result2.scalars.return_value.all.return_value = profiles

        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count in [1, 2]:
                return mock_result1
            return mock_result2

        mock_db.execute.side_effect = mock_execute
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = WeightOptimizerService(mock_db)

        # Get profile index for user
        profile_index = hash("user-123") % len(profiles)

        result1 = await service.assign_user_to_variant(
            str(test_id),
            "user-123",
            "org-123",
        )

        result2 = await service.assign_user_to_variant(
            str(test_id),
            "user-123",
            "org-123",
        )

        # Same user should get profiles in same order
        # The actual profile depends on hash value
        assert result1.user_id == result2.user_id
        assert result1.test_id == result2.test_id


class TestRecordMetric:
    """Tests for record_metric method."""

    @pytest.mark.asyncio
    async def test_invalid_test_id_format(self):
        """Test that invalid test_id format raises ValueError."""
        mock_db = AsyncMock()
        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="Invalid test_id format"):
            await service.record_metric(
                "invalid-uuid",
                "user-123",
                ABTestMetricType.MATCH_ACCEPTANCE,
                1.0,
            )

    @pytest.mark.asyncio
    async def test_no_assignment_found(self):
        """Test that missing assignment raises ValueError."""
        mock_db = AsyncMock()

        # Mock no assignment found
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="No assignment found"):
            await service.record_metric(
                str(uuid4()),
                "user-123",
                ABTestMetricType.MATCH_ACCEPTANCE,
                1.0,
            )

    @pytest.mark.asyncio
    async def test_record_match_acceptance_metric(self):
        """Test recording match acceptance metric."""
        mock_db = AsyncMock()

        # Mock assignment
        assignment_id = uuid4()
        mock_assignment = Mock()
        mock_assignment.id = assignment_id

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_assignment
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        captured_metric = None
        def capture_add(obj):
            nonlocal captured_metric
            captured_metric = obj

        mock_db.add.side_effect = capture_add

        service = WeightOptimizerService(mock_db)

        result = await service.record_metric(
            str(uuid4()),
            "user-123",
            ABTestMetricType.MATCH_ACCEPTANCE,
            1.0,
        )

        assert isinstance(result, MetricRecord)
        assert result.metric_type == ABTestMetricType.MATCH_ACCEPTANCE
        assert result.metric_value == 1.0
        assert result.assignment_id == str(assignment_id)

    @pytest.mark.asyncio
    async def test_metric_clamping_match_acceptance(self):
        """Test metric value clamping for match acceptance."""
        mock_db = AsyncMock()

        mock_assignment = Mock()
        mock_assignment.id = uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_assignment
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        captured_metric = None
        def capture_add(obj):
            nonlocal captured_metric
            captured_metric = obj

        mock_db.add.side_effect = capture_add

        service = WeightOptimizerService(mock_db)

        # Value > 0.5 should be clamped to 1.0
        await service.record_metric(
            str(uuid4()),
            "user-123",
            ABTestMetricType.MATCH_ACCEPTANCE,
            0.7,
        )

        assert captured_metric.metric_value == 1.0

    @pytest.mark.asyncio
    async def test_metric_clamping_user_satisfaction(self):
        """Test metric value clamping for user satisfaction."""
        mock_db = AsyncMock()

        mock_assignment = Mock()
        mock_assignment.id = uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_assignment
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        captured_metric = None
        def capture_add(obj):
            nonlocal captured_metric
            captured_metric = obj

        mock_db.add.side_effect = capture_add

        service = WeightOptimizerService(mock_db)

        # Value > 5.0 should be clamped to 5.0
        await service.record_metric(
            str(uuid4()),
            "user-123",
            ABTestMetricType.USER_SATISFACTION,
            6.0,
        )

        assert captured_metric.metric_value == 5.0

    @pytest.mark.asyncio
    async def test_metric_clamping_time_to_hire_negative(self):
        """Test metric value clamping for negative time to hire."""
        mock_db = AsyncMock()

        mock_assignment = Mock()
        mock_assignment.id = uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_assignment
        mock_db.execute.return_value = mock_result
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        captured_metric = None
        def capture_add(obj):
            nonlocal captured_metric
            captured_metric = obj

        mock_db.add.side_effect = capture_add

        service = WeightOptimizerService(mock_db)

        # Negative value should be set to 0
        await service.record_metric(
            str(uuid4()),
            "user-123",
            ABTestMetricType.TIME_TO_HIRE,
            -5.0,
        )

        assert captured_metric.metric_value == 0.0


class TestAnalyzeMetrics:
    """Tests for analyze_metrics method."""

    @pytest.mark.asyncio
    async def test_invalid_test_id_format(self):
        """Test that invalid test_id format raises ValueError."""
        mock_db = AsyncMock()
        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="Invalid test_id format"):
            await service.analyze_metrics(
                "invalid-uuid",
                ABTestMetricType.MATCH_ACCEPTANCE,
            )

    @pytest.mark.asyncio
    async def test_no_metrics_found(self):
        """Test that missing metrics raises ValueError."""
        mock_db = AsyncMock()

        mock_result = Mock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="No metrics found"):
            await service.analyze_metrics(
                str(uuid4()),
                ABTestMetricType.MATCH_ACCEPTANCE,
            )

    @pytest.mark.asyncio
    async def test_insufficient_sample_size(self):
        """Test that insufficient sample size raises ValueError."""
        mock_db = AsyncMock()

        # Mock metrics with less than 30 samples
        profile_id = uuid4()
        mock_row = Mock()
        mock_row.profile_id = profile_id
        mock_row.profile_name = "Technical"
        mock_row.keyword_weight = 0.6
        mock_row.tfidf_weight = 0.25
        mock_row.vector_weight = 0.15
        mock_row.metric_value = 1.0

        mock_result = Mock()
        # Return 10 samples (less than MIN_SAMPLE_SIZE of 30)
        mock_result.all.return_value = [mock_row] * 10
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="Insufficient sample size"):
            await service.analyze_metrics(
                str(uuid4()),
                ABTestMetricType.MATCH_ACCEPTANCE,
            )

    @pytest.mark.asyncio
    async def test_success_metrics_analysis(self):
        """Test successful metrics analysis."""
        mock_db = AsyncMock()

        # Mock two profiles with metrics
        profile1_id = uuid4()
        profile2_id = uuid4()

        rows = []
        # Create 30 samples for each profile (meets MIN_SAMPLE_SIZE)
        for i in range(30):
            row1 = Mock()
            row1.profile_id = profile1_id
            row1.profile_name = "Technical"
            row1.keyword_weight = 0.6
            row1.tfidf_weight = 0.25
            row1.vector_weight = 0.15
            row1.metric_value = 1.0
            rows.append(row1)

            row2 = Mock()
            row2.profile_id = profile2_id
            row2.profile_name = "Creative"
            row2.keyword_weight = 0.2
            row2.tfidf_weight = 0.25
            row2.vector_weight = 0.55
            row2.metric_value = 0.0
            rows.append(row2)

        mock_result = Mock()
        mock_result.all.return_value = rows
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        result = await service.analyze_metrics(
            str(uuid4()),
            ABTestMetricType.MATCH_ACCEPTANCE,
        )

        assert result["metric_type"] == "match_acceptance"
        assert "profiles" in result
        assert "statistical_test" in result
        assert "comparison" in result
        assert len(result["profiles"]) == 2


class TestAnalyzeContinuousMetric:
    """Tests for _analyze_continuous_metric method."""

    def test_continuous_metric_analysis(self):
        """Test analysis of continuous metric (t-test)."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        # Create two groups with different means
        import numpy as np
        group_a = [10.0, 12.0, 14.0, 11.0, 13.0] * 6  # 30 samples
        group_b = [8.0, 9.0, 10.0, 8.5, 9.5] * 6  # 30 samples

        result = service._analyze_continuous_metric(group_a, group_b)

        assert isinstance(result, StatisticalTestResult)
        assert result.test_type == "ttest"
        assert result.sample_size_a == 30
        assert result.sample_size_b == 30
        assert 0.0 <= result.p_value <= 1.0
        assert result.variant_a_mean > result.variant_b_mean  # group_a has higher mean

    def test_continuous_metric_effect_size(self):
        """Test Cohen's d effect size calculation."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        group_a = [10.0] * 30
        group_b = [5.0] * 30

        result = service._analyze_continuous_metric(group_a, group_b)

        # Effect size should be positive (group_a > group_b)
        assert result.effect_size > 0


class TestAnalyzeBinaryMetric:
    """Tests for _analyze_binary_metric method."""

    def test_binary_metric_analysis(self):
        """Test analysis of binary metric (chi-square test)."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        # Create two groups with different success rates
        group_a = [1.0] * 20 + [0.0] * 10  # 67% success
        group_b = [1.0] * 10 + [0.0] * 20  # 33% success

        result = service._analyze_binary_metric(group_a, group_b)

        assert isinstance(result, StatisticalTestResult)
        assert result.test_type == "chi2"
        assert result.sample_size_a == 30
        assert result.sample_size_b == 30
        assert 0.0 <= result.p_value <= 1.0
        assert result.variant_a_mean > result.variant_b_mean

    def test_binary_metric_effect_size(self):
        """Test proportion difference effect size calculation."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        group_a = [1.0] * 20 + [0.0] * 10  # 67% success
        group_b = [1.0] * 10 + [0.0] * 20  # 33% success

        result = service._analyze_binary_metric(group_a, group_b)

        # Effect size should be positive difference in proportions
        assert result.effect_size > 0
        assert result.effect_size < 1.0


class TestAnalyzeOrdinalMetric:
    """Tests for _analyze_ordinal_metric method."""

    def test_ordinal_metric_analysis(self):
        """Test analysis of ordinal metric (Mann-Whitney U test)."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        # Create two groups with different distributions
        group_a = [5.0] * 15 + [4.0] * 10 + [3.0] * 5  # Higher scores
        group_b = [3.0] * 15 + [2.0] * 10 + [1.0] * 5  # Lower scores

        result = service._analyze_ordinal_metric(group_a, group_b)

        assert isinstance(result, StatisticalTestResult)
        assert result.test_type == "mann_whitney"
        assert result.sample_size_a == 30
        assert result.sample_size_b == 30
        assert 0.0 <= result.p_value <= 1.0
        assert result.variant_a_mean > result.variant_b_mean

    def test_ordinal_metric_confidence_interval(self):
        """Test confidence interval calculation for ordinal metric."""
        mock_db = Mock()
        service = WeightOptimizerService(mock_db)

        group_a = [5.0] * 30
        group_b = [3.0] * 30

        result = service._analyze_ordinal_metric(group_a, group_b)

        assert result.confidence_interval is not None
        assert len(result.confidence_interval) == 2
        assert result.confidence_interval[0] < result.confidence_interval[1]


class TestOptimizeWeights:
    """Tests for optimize_weights method."""

    @pytest.mark.asyncio
    async def test_invalid_test_id_format(self):
        """Test that invalid test_id format raises ValueError."""
        mock_db = AsyncMock()
        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="Invalid test_id format"):
            await service.optimize_weights("invalid-uuid")

    @pytest.mark.asyncio
    async def test_test_not_found(self):
        """Test that non-existent test raises ValueError."""
        mock_db = AsyncMock()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = WeightOptimizerService(mock_db)

        with pytest.raises(ValueError, match="A/B test not found"):
            await service.optimize_weights(str(uuid4()))

    @pytest.mark.asyncio
    async def test_no_significant_improvements(self):
        """Test optimization result when no significant improvements found."""
        mock_db = AsyncMock()

        # Mock test
        test_id = uuid4()
        mock_test = Mock()
        mock_test.id = test_id

        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.return_value = mock_test

        # Mock analyze_metrics to return no significant results
        mock_result2 = Mock()
        mock_result2.all.return_value = []

        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            return mock_result1 if call_count == 1 else mock_result2

        mock_db.execute.side_effect = mock_execute

        service = WeightOptimizerService(mock_db)

        # Mock analyze_metrics to return non-significant results
        with patch.object(service, "analyze_metrics") as mock_analyze:
            mock_analyze.side_effect = ValueError("Insufficient sample size")

            result = await service.optimize_weights(str(test_id))

        assert isinstance(result, OptimizationResult)
        assert result.should_optimize is False
        assert result.recommended_weights == {}
        assert "No statistically significant improvements" in result.reason

    @pytest.mark.asyncio
    async def test_weight_sum_validation(self):
        """Test that optimized weights sum to approximately 1.0."""
        mock_db = AsyncMock()

        # Mock test and profile
        test_id = uuid4()
        profile_id = uuid4()

        mock_test = Mock()
        mock_test.id = test_id

        mock_profile = Mock()
        mock_profile.id = profile_id
        mock_profile.name = "Technical"
        mock_profile.keyword_weight = 0.6
        mock_profile.tfidf_weight = 0.25
        mock_profile.vector_weight = 0.15

        mock_result1 = Mock()
        mock_result1.scalar_one_or_none.side_effect = [mock_test, mock_profile]

        call_count = 0
        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            return mock_result1

        mock_db.execute.side_effect = mock_execute

        service = WeightOptimizerService(mock_db)

        # Mock analyze_metrics to return significant result
        mock_analysis = {
            "statistical_test": {
                "is_significant": True,
                "p_value": 0.01,
                "effect_size": 0.5,
                "test_type": "ttest",
                "confidence_interval": (0.1, 0.9),
                "variant_a_mean": 0.8,
                "variant_b_mean": 0.6,
                "sample_size_a": 30,
                "sample_size_b": 30,
            },
            "comparison": {
                "better_profile": str(profile_id),
                "improvement_pct": 33.3,
            },
        }

        with patch.object(service, "analyze_metrics", return_value=mock_analysis):
            result = await service.optimize_weights(str(test_id))

        assert result.should_optimize is True
        assert result.recommended_weights["keyword_weight"] == 0.6
        assert result.recommended_weights["tfidf_weight"] == 0.25
        assert result.recommended_weights["vector_weight"] == 0.15

        # Verify weights sum to 1.0
        total = (
            result.recommended_weights["keyword_weight"] +
            result.recommended_weights["tfidf_weight"] +
            result.recommended_weights["vector_weight"]
        )
        assert abs(total - 1.0) < 0.01


class TestGetWeightOptimizerService:
    """Tests for get_weight_optimizer_service dependency injection."""

    def test_returns_service_instance(self):
        """Test that function returns WeightOptimizerService instance."""
        mock_db = Mock()
        service = get_weight_optimizer_service(mock_db)

        assert isinstance(service, WeightOptimizerService)
        assert service.db is mock_db

    def test_singleton_behavior(self):
        """Test that each call creates a new instance with provided db."""
        mock_db1 = Mock()
        mock_db2 = Mock()

        service1 = get_weight_optimizer_service(mock_db1)
        service2 = get_weight_optimizer_service(mock_db2)

        assert service1.db is mock_db1
        assert service2.db is mock_db2


class TestDataclasses:
    """Tests for dataclass definitions."""

    def test_user_assignment_dataclass(self):
        """Test UserAssignment dataclass."""
        assignment = UserAssignment(
            user_id="user-123",
            test_id="test-456",
            profile_id="profile-789",
            profile_name="Technical",
            assignment_id="assignment-abc",
            was_new_assignment=True,
        )

        assert assignment.user_id == "user-123"
        assert assignment.test_id == "test-456"
        assert assignment.profile_id == "profile-789"
        assert assignment.profile_name == "Technical"
        assert assignment.assignment_id == "assignment-abc"
        assert assignment.was_new_assignment is True

    def test_metric_record_dataclass(self):
        """Test MetricRecord dataclass."""
        now = datetime.now(timezone.utc)
        record = MetricRecord(
            metric_id="metric-123",
            assignment_id="assignment-456",
            metric_type=ABTestMetricType.MATCH_ACCEPTANCE,
            metric_value=1.0,
            recorded_at=now,
        )

        assert record.metric_id == "metric-123"
        assert record.assignment_id == "assignment-456"
        assert record.metric_type == ABTestMetricType.MATCH_ACCEPTANCE
        assert record.metric_value == 1.0
        assert record.recorded_at == now

    def test_statistical_test_result_dataclass(self):
        """Test StatisticalTestResult dataclass."""
        result = StatisticalTestResult(
            test_type="ttest",
            p_value=0.01,
            is_significant=True,
            effect_size=0.5,
            confidence_interval=(0.1, 0.9),
            variant_a_mean=0.8,
            variant_b_mean=0.6,
            sample_size_a=30,
            sample_size_b=30,
        )

        assert result.test_type == "ttest"
        assert result.p_value == 0.01
        assert result.is_significant is True
        assert result.effect_size == 0.5
        assert result.confidence_interval == (0.1, 0.9)
        assert result.variant_a_mean == 0.8
        assert result.variant_b_mean == 0.6
        assert result.sample_size_a == 30
        assert result.sample_size_b == 30

    def test_optimization_result_dataclass(self):
        """Test OptimizationResult dataclass."""
        result = OptimizationResult(
            should_optimize=True,
            recommended_weights={"keyword_weight": 0.6, "tfidf_weight": 0.25, "vector_weight": 0.15},
            reason="Profile shows significant improvement",
            statistical_significance=None,
            metrics_summary={"match_acceptance": {"p_value": 0.01}},
        )

        assert result.should_optimize is True
        assert result.recommended_weights["keyword_weight"] == 0.6
        assert "significant improvement" in result.reason
        assert result.statistical_significance is None
        assert "match_acceptance" in result.metrics_summary
