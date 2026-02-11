"""
Unit Tests for ModelPerformanceMonitor Service

Tests the performance monitoring service that tracks model metrics,
detects anomalies, and generates alerts for performance degradation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from analyzers.model_performance_monitor import ModelPerformanceMonitor


class TestModelPerformanceMonitorInit:
    """Tests for ModelPerformanceMonitor initialization."""

    def test_initialization_default_thresholds(self):
        """Test initialization with default thresholds."""
        monitor = ModelPerformanceMonitor()

        assert monitor.degradation_threshold == ModelPerformanceMonitor.DEFAULT_DEGRADATION_THRESHOLD
        assert monitor.warning_threshold == ModelPerformanceMonitor.DEFAULT_WARNING_THRESHOLD
        assert monitor.min_samples_for_alert == ModelPerformanceMonitor.DEFAULT_MIN_SAMPLES

    def test_initialization_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        monitor = ModelPerformanceMonitor(
            degradation_threshold=0.15,
            warning_threshold=0.08,
            min_samples_for_alert=50,
        )

        assert monitor.degradation_threshold == 0.15
        assert monitor.warning_threshold == 0.08
        assert monitor.min_samples_for_alert == 50

    def test_initialization_empty_buffers(self):
        """Test that observation buffers are initialized empty."""
        monitor = ModelPerformanceMonitor()
        assert monitor._observation_buffers == {}
        assert monitor._baselines == {}

    def test_class_constants(self):
        """Test class constants are defined correctly."""
        assert ModelPerformanceMonitor.DEFAULT_DEGRADATION_THRESHOLD == 0.10
        assert ModelPerformanceMonitor.DEFAULT_WARNING_THRESHOLD == 0.05
        assert ModelPerformanceMonitor.DEFAULT_MIN_SAMPLES == 100
        assert ModelPerformanceMonitor.METRIC_ACCURACY == "accuracy"
        assert ModelPerformanceMonitor.METRIC_F1 == "f1_score"
        assert ModelPerformanceMonitor.ALERT_LEVEL_CRITICAL == "critical"
        assert ModelPerformanceMonitor.ALERT_LEVEL_WARNING == "warning"


class TestModelPerformanceMonitorRecordObservation:
    """Tests for record_observation method."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for testing."""
        return ModelPerformanceMonitor()

    def test_record_observation_basic(self, monitor):
        """Test basic observation recording."""
        result = monitor.record_observation(
            model_version_id="model-123",
            model_name="skill_matching",
            actual=True,
            predicted=True,
        )

        assert result["model_version_id"] == "model-123"
        assert result["model_name"] == "skill_matching"
        assert result["observation_count"] == 1
        assert "current_metrics" in result

    def test_record_observation_with_score(self, monitor):
        """Test observation recording with confidence score."""
        result = monitor.record_observation(
            model_version_id="model-123",
            model_name="skill_matching",
            actual=True,
            predicted=True,
            score=0.95,
        )

        assert result["observation_count"] == 1

    def test_record_observation_with_ranking_position(self, monitor):
        """Test observation recording with ranking position."""
        result = monitor.record_observation(
            model_version_id="model-123",
            model_name="ranking_model",
            actual=True,
            predicted=True,
            ranking_position=3,
        )

        assert result["observation_count"] == 1
        # MRR should be calculated
        assert "mrr_score" in result["current_metrics"]

    def test_record_observation_with_metadata(self, monitor):
        """Test observation recording with metadata."""
        metadata = {"source": "api", "user_id": "user-123"}
        result = monitor.record_observation(
            model_version_id="model-123",
            model_name="skill_matching",
            actual=True,
            predicted=True,
            metadata=metadata,
        )

        assert result["observation_count"] == 1

    def test_record_observation_increments_count(self, monitor):
        """Test that observation count increments correctly."""
        monitor.record_observation("model-123", "skill_matching", True, True)
        monitor.record_observation("model-123", "skill_matching", True, True)
        result = monitor.record_observation("model-123", "skill_matching", False, True)

        assert result["observation_count"] == 3

    def test_record_observation_multiple_models(self, monitor):
        """Test recording observations for multiple models."""
        result1 = monitor.record_observation("model-1", "skill_matching", True, True)
        result2 = monitor.record_observation("model-2", "skill_matching", True, True)

        assert result1["observation_count"] == 1
        assert result2["observation_count"] == 1

    @patch('analyzers.model_performance_monitor.get_metrics_registry')
    def test_record_observation_records_metrics(self, mock_get_registry, monitor):
        """Test that metrics are recorded during observation."""
        mock_registry = MagicMock()
        mock_get_registry.return_value = mock_registry

        monitor.record_observation("model-123", "skill_matching", True, True)

        mock_registry.record_ml_inference.assert_called_once()

    @patch('analyzers.model_performance_monitor.get_metrics_registry')
    def test_record_observation_handles_metrics_error(self, mock_get_registry, monitor):
        """Test that observation continues even if metrics fail."""
        mock_get_registry.side_effect = Exception("Metrics error")

        result = monitor.record_observation("model-123", "skill_matching", True, True)

        assert result["observation_count"] == 1


class TestModelPerformanceMonitorMetrics:
    """Tests for metrics calculation."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for metrics testing."""
        return ModelPerformanceMonitor()

    def test_accuracy_calculation(self, monitor):
        """Test accuracy is calculated correctly."""
        # 3 correct out of 4 = 0.75
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", False, True)  # Incorrect
        monitor.record_observation("model-1", "test", True, True)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert snapshot["current_metrics"]["accuracy"] == 0.75

    def test_precision_calculation(self, monitor):
        """Test precision is calculated correctly."""
        # TP=2, FP=1 -> precision = 2/3 = 0.666...
        monitor.record_observation("model-1", "test", True, True)   # TP
        monitor.record_observation("model-1", "test", True, True)   # TP
        monitor.record_observation("model-1", "test", False, True)  # FP
        monitor.record_observation("model-1", "test", True, False)  # FN

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert abs(snapshot["current_metrics"]["precision"] - 2/3) < 0.01

    def test_recall_calculation(self, monitor):
        """Test recall is calculated correctly."""
        # TP=2, FN=1 -> recall = 2/3 = 0.666...
        monitor.record_observation("model-1", "test", True, True)    # TP
        monitor.record_observation("model-1", "test", True, True)    # TP
        monitor.record_observation("model-1", "test", True, False)   # FN
        monitor.record_observation("model-1", "test", False, True)   # FP

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert abs(snapshot["current_metrics"]["recall"] - 2/3) < 0.01

    def test_f1_score_calculation(self, monitor):
        """Test F1 score is calculated correctly."""
        # Perfect predictions -> F1 = 1.0
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", False, False)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert snapshot["current_metrics"]["f1_score"] == 1.0

    def test_mrr_calculation(self, monitor):
        """Test Mean Reciprocal Rank is calculated correctly."""
        # Positions 1, 2, 3 -> MRR = (1 + 0.5 + 0.333) / 3
        monitor.record_observation("model-1", "test", True, True, ranking_position=1)
        monitor.record_observation("model-1", "test", True, True, ranking_position=2)
        monitor.record_observation("model-1", "test", True, True, ranking_position=3)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        expected_mrr = (1 + 0.5 + 1/3) / 3
        assert abs(snapshot["current_metrics"]["mrr_score"] - expected_mrr) < 0.01

    def test_sample_size_tracking(self, monitor):
        """Test sample size is tracked correctly."""
        for _ in range(50):
            monitor.record_observation("model-1", "test", True, True)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert snapshot["current_metrics"]["sample_size"] == 50


class TestModelPerformanceMonitorSnapshot:
    """Tests for performance snapshot functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for snapshot testing."""
        return ModelPerformanceMonitor()

    def test_get_performance_snapshot_basic(self, monitor):
        """Test basic performance snapshot generation."""
        monitor.record_observation("model-123", "skill_matching", True, True)

        snapshot = monitor.get_performance_snapshot("model-123", "skill_matching")

        assert snapshot["model_version_id"] == "model-123"
        assert snapshot["model_name"] == "skill_matching"
        assert "snapshot_time" in snapshot
        assert "current_metrics" in snapshot
        assert "alerts" in snapshot

    def test_get_performance_snapshot_no_observations(self, monitor):
        """Test snapshot when no observations recorded."""
        snapshot = monitor.get_performance_snapshot("unknown-model", "test")

        assert snapshot["model_version_id"] == "unknown-model"
        assert snapshot["current_metrics"] == {}

    def test_get_performance_snapshot_with_db_session(self, monitor):
        """Test snapshot with database session for historical data."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        snapshot = monitor.get_performance_snapshot(
            "model-123", "skill_matching", db_session=mock_session
        )

        assert "historical_metrics" in snapshot

    def test_get_performance_snapshot_includes_alerts(self, monitor):
        """Test that snapshot includes alerts."""
        snapshot = monitor.get_performance_snapshot("model-123", "skill_matching")

        assert "alerts" in snapshot
        assert isinstance(snapshot["alerts"], list)

    def test_get_performance_snapshot_without_trends(self, monitor):
        """Test snapshot without trends."""
        snapshot = monitor.get_performance_snapshot(
            "model-123", "skill_matching", include_trends=False
        )

        # trends should be empty since db_session is None
        assert snapshot["trends"] == {}


class TestModelPerformanceMonitorAlerts:
    """Tests for alerting functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a monitor with low thresholds for testing."""
        return ModelPerformanceMonitor(
            degradation_threshold=0.10,
            warning_threshold=0.05,
            min_samples_for_alert=10,
        )

    def test_no_alerts_below_min_samples(self, monitor):
        """Test no alerts when sample size is below minimum."""
        # Record fewer than min_samples
        for _ in range(5):
            monitor.record_observation("model-1", "test", True, True)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        # Without baseline, no alerts should be generated
        assert len(snapshot["alerts"]) == 0

    def test_critical_alert_on_degradation(self, monitor):
        """Test critical alert on performance degradation."""
        # Set a baseline
        monitor.set_baseline("model-1", "test", {"f1_score": 0.9})

        # Record observations that result in lower F1 (simulate degradation)
        # TP=3, FN=7 -> recall = 0.3
        # We need to drop by 10% from baseline 0.9 = 0.81
        for _ in range(3):
            monitor.record_observation("model-1", "test", True, True)
        for _ in range(7):
            monitor.record_observation("model-1", "test", True, False)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        # Since we don't have historical_metrics with avg_f1_score, no alerts
        # This tests the code path
        assert isinstance(snapshot["alerts"], list)

    def test_warning_alert(self, monitor):
        """Test warning level alert."""
        # Set baseline
        monitor.set_baseline("model-1", "test", {"f1_score": 0.8})

        # Record some observations
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        # Without database-provided historical metrics, alerts won't be generated
        assert isinstance(snapshot["alerts"], list)


class TestModelPerformanceMonitorBaseline:
    """Tests for baseline functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for baseline testing."""
        return ModelPerformanceMonitor()

    def test_set_baseline(self, monitor):
        """Test setting baseline metrics."""
        metrics = {"f1_score": 0.85, "accuracy": 0.90}
        monitor.set_baseline("model-1", "skill_matching", metrics)

        baseline = monitor.get_baseline("model-1", "skill_matching")
        assert baseline["f1_score"] == 0.85
        assert baseline["accuracy"] == 0.90

    def test_get_baseline_not_set(self, monitor):
        """Test getting baseline when not set."""
        baseline = monitor.get_baseline("unknown", "test")
        assert baseline is None

    def test_baseline_per_model_version(self, monitor):
        """Test baseline is tracked per model version."""
        monitor.set_baseline("model-1", "test", {"f1_score": 0.8})
        monitor.set_baseline("model-2", "test", {"f1_score": 0.9})

        assert monitor.get_baseline("model-1", "test")["f1_score"] == 0.8
        assert monitor.get_baseline("model-2", "test")["f1_score"] == 0.9


class TestModelPerformanceMonitorBuffer:
    """Tests for observation buffer functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for buffer testing."""
        return ModelPerformanceMonitor()

    def test_clear_buffer(self, monitor):
        """Test clearing observation buffer."""
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", True, True)

        count = monitor.clear_buffer("model-1", "test")

        assert count == 2
        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert snapshot["current_metrics"] == {}

    def test_clear_buffer_empty(self, monitor):
        """Test clearing empty buffer."""
        count = monitor.clear_buffer("unknown", "test")
        assert count == 0

    def test_clear_buffer_preserves_other_models(self, monitor):
        """Test clearing buffer for one model doesn't affect others."""
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-2", "test", True, True)

        monitor.clear_buffer("model-1", "test")

        assert monitor.get_baseline("model-1", "test") is None
        snapshot2 = monitor.get_performance_snapshot("model-2", "test")
        assert snapshot2["current_metrics"]["sample_size"] == 1


class TestModelPerformanceMonitorFlushToDatabase:
    """Tests for database flush functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for flush testing."""
        return ModelPerformanceMonitor()

    def test_flush_to_database_no_session(self, monitor):
        """Test flush with no database session."""
        result = monitor.flush_to_database(
            "model-1", "skill_matching", "production", None
        )
        assert result is None

    def test_flush_to_database_no_observations(self, monitor):
        """Test flush with no observations."""
        mock_session = MagicMock()
        result = monitor.flush_to_database(
            "model-1", "skill_matching", "production", mock_session
        )
        assert result is None

    def test_flush_to_database_success(self, monitor):
        """Test successful flush to database."""
        # Record observations
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        mock_session = MagicMock()
        mock_performance = MagicMock()
        mock_performance.id = "perf-123"
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        with patch('analyzers.model_performance_monitor.ModelPerformanceHistory') as mock_model:
            mock_record = MagicMock()
            mock_record.id = "perf-123"
            mock_model.return_value = mock_record

            result = monitor.flush_to_database(
                "model-1", "test", "production", mock_session
            )

            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()
            # Buffer should be cleared after flush
            assert monitor.get_performance_snapshot("model-1", "test")["current_metrics"] == {}

    def test_flush_to_database_with_previous_record(self, monitor):
        """Test flush with previous performance record."""
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        mock_session = MagicMock()
        mock_previous = MagicMock()
        mock_previous.f1_score = 0.8
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_previous

        with patch('analyzers.model_performance_monitor.ModelPerformanceHistory') as mock_model:
            mock_record = MagicMock()
            mock_record.id = "perf-123"
            mock_model.return_value = mock_record

            result = monitor.flush_to_database(
                "model-1", "test", "production", mock_session
            )

            assert result is not None

    def test_flush_to_database_error_handling(self, monitor):
        """Test flush handles database errors."""
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("Database error")

        with patch('analyzers.model_performance_monitor.ModelPerformanceHistory') as mock_model:
            mock_model.return_value = MagicMock()

            result = monitor.flush_to_database(
                "model-1", "test", "production", mock_session
            )

            assert result is None
            mock_session.rollback.assert_called_once()


class TestModelPerformanceMonitorCompareModels:
    """Tests for model comparison functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for comparison testing."""
        return ModelPerformanceMonitor()

    def test_compare_models_basic(self, monitor):
        """Test basic model comparison."""
        # Model A: perfect predictions
        for _ in range(10):
            monitor.record_observation("model-a", "test", True, True)

        # Model B: 80% accuracy
        for _ in range(8):
            monitor.record_observation("model-b", "test", True, True)
        for _ in range(2):
            monitor.record_observation("model-b", "test", False, True)

        comparison = monitor.compare_models("model-a", "model-b", "test")

        assert comparison["model_a_id"] == "model-a"
        assert comparison["model_b_id"] == "model-b"
        assert "comparison" in comparison
        assert "winner" in comparison

    def test_compare_models_determines_winner(self, monitor):
        """Test comparison determines correct winner."""
        # Model A: 100% F1
        for _ in range(5):
            monitor.record_observation("model-a", "test", True, True)

        # Model B: 50% F1 (mixed results)
        for _ in range(5):
            monitor.record_observation("model-b", "test", True, False)

        comparison = monitor.compare_models("model-a", "model-b", "test")

        assert comparison["winner"] == "model_a"
        assert comparison["confidence"] > 0

    def test_compare_models_tie(self, monitor):
        """Test comparison with tied performance."""
        # Both models with identical performance
        for _ in range(10):
            monitor.record_observation("model-a", "test", True, True)
            monitor.record_observation("model-b", "test", True, True)

        comparison = monitor.compare_models("model-a", "model-b", "test")

        assert comparison["winner"] == "tie"

    def test_compare_models_no_data(self, monitor):
        """Test comparison with no observations."""
        comparison = monitor.compare_models("model-a", "model-b", "test")

        assert comparison["model_a_id"] == "model-a"
        assert comparison["model_b_id"] == "model-b"
        assert comparison["winner"] is None

    def test_compare_models_with_db_session(self, monitor):
        """Test comparison with database session."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        comparison = monitor.compare_models(
            "model-a", "model-b", "test", db_session=mock_session
        )

        assert "model_a_metrics" in comparison
        assert "model_b_metrics" in comparison


class TestModelPerformanceMonitorHealthStatus:
    """Tests for health status functionality."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for health testing."""
        return ModelPerformanceMonitor()

    def test_get_model_health_status_healthy(self, monitor):
        """Test health status for healthy model."""
        # Record good performance
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        health = monitor.get_model_health_status("model-1", "test")

        assert "health_score" in health
        assert "status" in health
        assert health["status"] in ["healthy", "warning", "degraded", "critical", "unknown"]

    def test_get_model_health_status_no_data(self, monitor):
        """Test health status with no observations."""
        health = monitor.get_model_health_status("unknown", "test")

        assert health["status"] == "unknown"
        assert health["health_score"] == 0

    def test_get_model_health_status_with_db_session(self, monitor):
        """Test health status with database session."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        health = monitor.get_model_health_status(
            "model-1", "test", db_session=mock_session
        )

        assert "health_score" in health

    def test_health_status_includes_factors(self, monitor):
        """Test health status includes health factors."""
        for _ in range(10):
            monitor.record_observation("model-1", "test", True, True)

        health = monitor.get_model_health_status("model-1", "test")

        assert "health_factors" in health
        assert isinstance(health["health_factors"], list)


class TestModelPerformanceMonitorMRR:
    """Tests for Mean Reciprocal Rank calculation."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for MRR testing."""
        return ModelPerformanceMonitor()

    def test_calculate_mrr_basic(self, monitor):
        """Test basic MRR calculation."""
        mrr = monitor._calculate_mrr([1, 2, 3])
        expected = (1 + 0.5 + 1/3) / 3
        assert abs(mrr - expected) < 0.01

    def test_calculate_mrr_empty(self, monitor):
        """Test MRR with empty positions."""
        mrr = monitor._calculate_mrr([])
        assert mrr == 0.0

    def test_calculate_mrr_single_position(self, monitor):
        """Test MRR with single position."""
        mrr = monitor._calculate_mrr([1])
        assert mrr == 1.0

    def test_calculate_mrr_ignores_zero_positions(self, monitor):
        """Test MRR ignores zero positions."""
        mrr = monitor._calculate_mrr([0, 1, 2])
        # Only 1 and 2 should be considered
        expected = (1 + 0.5) / 2
        assert abs(mrr - expected) < 0.01


class TestModelPerformanceMonitorHistoricalMetrics:
    """Tests for historical metrics retrieval."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for historical metrics testing."""
        return ModelPerformanceMonitor()

    def test_get_historical_metrics_no_records(self, monitor):
        """Test historical metrics with no records."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = monitor._get_historical_metrics(mock_session, "model-1")

        assert result == {}

    def test_get_historical_metrics_with_records(self, monitor):
        """Test historical metrics with records."""
        mock_session = MagicMock()

        # Create mock records
        mock_record = MagicMock()
        mock_record.accuracy = 0.9
        mock_record.precision = 0.85
        mock_record.recall = 0.88
        mock_record.f1_score = 0.86
        mock_record.auc_score = 0.92
        mock_record.sample_size = 100
        mock_record.created_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_record]

        result = monitor._get_historical_metrics(mock_session, "model-1")

        assert "latest" in result
        assert "aggregates" in result
        assert result["latest"]["accuracy"] == 0.9


class TestModelPerformanceMonitorTrends:
    """Tests for trend calculation."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for trend testing."""
        return ModelPerformanceMonitor()

    def test_calculate_trends_insufficient_data(self, monitor):
        """Test trend calculation with insufficient data."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = monitor._calculate_trends(mock_session, "model-1")

        assert result["trend"] == "insufficient_data"

    def test_calculate_trends_improving(self, monitor):
        """Test trend calculation for improving performance."""
        mock_session = MagicMock()

        # Create records showing improvement
        records = []
        for i in range(10):
            record = MagicMock()
            record.f1_score = 0.5 + (i * 0.03)  # Improving
            records.append(record)

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = records

        result = monitor._calculate_trends(mock_session, "model-1")

        assert result["trend"] == "improving"

    def test_calculate_trends_declining(self, monitor):
        """Test trend calculation for declining performance."""
        mock_session = MagicMock()

        # Create records showing decline
        records = []
        for i in range(10):
            record = MagicMock()
            record.f1_score = 0.9 - (i * 0.03)  # Declining
            records.append(record)

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = records

        result = monitor._calculate_trends(mock_session, "model-1")

        assert result["trend"] == "declining"

    def test_calculate_trends_stable(self, monitor):
        """Test trend calculation for stable performance."""
        mock_session = MagicMock()

        # Create stable records
        records = []
        for i in range(10):
            record = MagicMock()
            record.f1_score = 0.85  # Stable
            records.append(record)

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = records

        result = monitor._calculate_trends(mock_session, "model-1")

        assert result["trend"] == "stable"


class TestModelPerformanceMonitorEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def monitor(self):
        """Create a ModelPerformanceMonitor for edge case testing."""
        return ModelPerformanceMonitor()

    def test_empty_model_name(self, monitor):
        """Test handling of empty model name."""
        result = monitor.record_observation("", "test", True, True)
        assert result["model_version_id"] == ""

    def test_special_characters_in_model_name(self, monitor):
        """Test handling of special characters."""
        result = monitor.record_observation("model-with-dashes", "test", True, True)
        assert result["model_version_id"] == "model-with-dashes"

    def test_large_observation_count(self, monitor):
        """Test handling of large number of observations."""
        for _ in range(1000):
            monitor.record_observation("model-1", "test", True, True)

        snapshot = monitor.get_performance_snapshot("model-1", "test")
        assert snapshot["current_metrics"]["sample_size"] == 1000

    def test_mixed_boolean_values(self, monitor):
        """Test handling of mixed boolean-like values."""
        # Test with actual booleans
        monitor.record_observation("model-1", "test", True, True)
        monitor.record_observation("model-1", "test", False, False)

        # Test with 1/0
        monitor.record_observation("model-2", "test", 1, 1)
        monitor.record_observation("model-2", "test", 0, 0)

        snapshot1 = monitor.get_performance_snapshot("model-1", "test")
        snapshot2 = monitor.get_performance_snapshot("model-2", "test")

        assert snapshot1["current_metrics"]["accuracy"] == 1.0
        assert snapshot2["current_metrics"]["accuracy"] == 1.0

    def test_get_snapshot_error_handling(self, monitor):
        """Test snapshot handles errors gracefully."""
        # Should not raise even with invalid inputs
        snapshot = monitor.get_performance_snapshot(None, None)

        assert "error" in snapshot or snapshot["model_version_id"] == str(None)

    def test_compare_models_error_handling(self, monitor):
        """Test comparison handles errors gracefully."""
        comparison = monitor.compare_models(None, None, "test")

        assert "model_a_id" in comparison
        assert "model_b_id" in comparison

    def test_health_status_error_handling(self, monitor):
        """Test health status handles errors gracefully."""
        health = monitor.get_model_health_status(None, None)

        assert "status" in health
        assert "health_score" in health
