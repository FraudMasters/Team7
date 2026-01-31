"""
Tests for PerformanceTracker.

Tests cover performance metrics calculation, confusion matrix generation,
performance history recording, and degradation detection.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from analyzers.performance_tracker import PerformanceTracker


class TestPerformanceTrackerInit:
    """Tests for PerformanceTracker initialization."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        tracker = PerformanceTracker()

        assert tracker.default_metrics == ["accuracy", "precision", "recall", "f1_score"]

    def test_custom_metrics(self):
        """Test initialization with custom metrics."""
        custom_metrics = ["accuracy", "f1_score"]
        tracker = PerformanceTracker(default_metrics=custom_metrics)

        assert tracker.default_metrics == custom_metrics

    def test_none_metrics_uses_default(self):
        """Test that None uses default metrics."""
        tracker = PerformanceTracker(default_metrics=None)

        assert tracker.default_metrics == ["accuracy", "precision", "recall", "f1_score"]


class TestCalculateMetrics:
    """Tests for calculate_metrics method."""

    def test_basic_metrics_calculation(self):
        """Test basic metrics calculation."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1, 1, 0, 1])
        y_pred = np.array([1, 0, 0, 1, 0, 1])

        metrics = tracker.calculate_metrics(y_true, y_pred)

        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics
        assert "f1_score" in metrics
        assert "auc_score" in metrics
        assert metrics["accuracy"] == 5/6  # 5 correct out of 6

    def test_with_probability_scores(self):
        """Test metrics calculation with probability scores for AUC."""
        tracker = PerformanceTracker()

        y_true = np.array([0, 1, 0, 1])
        y_pred = np.array([0, 1, 0, 1])
        y_scores = np.array([0.1, 0.9, 0.2, 0.8])

        metrics = tracker.calculate_metrics(y_true, y_pred, y_scores=y_scores)

        assert metrics["auc_score"] is not None
        assert 0.0 <= metrics["auc_score"] <= 1.0

    def test_without_probability_scores(self):
        """Test metrics calculation without probability scores."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1, 1])
        y_pred = np.array([1, 0, 0, 1])

        metrics = tracker.calculate_metrics(y_true, y_pred, y_scores=None)

        assert metrics["auc_score"] is None

    def test_multiclass_classification(self):
        """Test metrics calculation for multiclass."""
        tracker = PerformanceTracker()

        y_true = np.array([0, 1, 2, 1, 0])
        y_pred = np.array([0, 2, 2, 1, 0])

        metrics = tracker.calculate_metrics(y_true, y_pred, average="macro")

        assert metrics["accuracy"] == 4/5
        assert metrics["auc_score"] is None  # No AUC for multiclass

    def test_custom_average_parameter(self):
        """Test with custom averaging method."""
        tracker = PerformanceTracker()

        y_true = np.array([0, 1, 2, 1, 0])
        y_pred = np.array([0, 2, 2, 1, 0])

        metrics_micro = tracker.calculate_metrics(y_true, y_pred, average="micro")
        metrics_macro = tracker.calculate_metrics(y_true, y_pred, average="macro")

        # Different averaging methods should give different results
        assert metrics_micro["f1_score"] != metrics_macro["f1_score"]

    def test_zero_division_handling(self):
        """Test zero division handling."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 0, 0])  # All wrong

        metrics = tracker.calculate_metrics(y_true, y_pred, zero_division=0)

        # Should handle zero division gracefully
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0

    def test_perfect_predictions(self):
        """Test with perfect predictions."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 0])

        metrics = tracker.calculate_metrics(y_true, y_pred)

        assert metrics["accuracy"] == 1.0
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1_score"] == 1.0

    def test_exception_handling(self):
        """Test exception handling in metrics calculation."""
        tracker = PerformanceTracker()

        # Mismatched array sizes should raise an error
        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0])

        # Should return default values on error
        with patch.object(tracker, 'calculate_metrics', wraps=tracker.calculate_metrics):
            metrics = tracker.calculate_metrics(y_true, y_pred)

            # Should return error defaults
            assert metrics["accuracy"] == 0.0


class TestCalculateConfusionMatrix:
    """Tests for calculate_confusion_matrix method."""

    def test_binary_classification(self):
        """Test confusion matrix for binary classification."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([1, 0, 0, 1, 1])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        assert "matrix" in result
        assert "shape" in result
        assert "labels" in result
        assert result["shape"] == (2, 2)
        assert "true_negatives" in result
        assert "false_positives" in result
        assert "false_negatives" in result
        assert "true_positives" in result

    def test_multiclass_classification(self):
        """Test confusion matrix for multiclass."""
        tracker = PerformanceTracker()

        y_true = np.array([0, 1, 2, 1, 0, 2])
        y_pred = np.array([0, 2, 2, 1, 0, 1])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        assert result["shape"] == (3, 3)
        assert set(result["labels"]) == {0, 1, 2}
        # No binary-specific fields for multiclass
        assert "true_negatives" not in result

    def test_matrix_serialization(self):
        """Test that matrix is properly serialized."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 0])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        # Matrix should be a list, not numpy array
        assert isinstance(result["matrix"], list)
        assert isinstance(result["labels"], list)

    def test_labels_are_sorted(self):
        """Test that labels are sorted."""
        tracker = PerformanceTracker()

        y_true = np.array([2, 0, 1, 2])
        y_pred = np.array([2, 0, 1, 1])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        assert result["labels"] == [0, 1, 2]

    def test_exception_handling(self):
        """Test exception handling."""
        tracker = PerformanceTracker()

        # Mismatched arrays
        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        # Should return empty defaults on error
        assert result["matrix"] == []
        assert result["shape"] == (0, 0)
        assert result["labels"] == []


class TestRecordPerformance:
    """Tests for record_performance method."""

    def test_successful_recording(self):
        """Test successful performance recording."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.flush = Mock()

        # Mock query to return no previous performance
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1, 1])
        y_pred = np.array([1, 0, 0, 1])

        result = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, "test"
        )

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_no_database_session(self):
        """Test with no database session."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        result = tracker.record_performance(
            None, "model-123", y_true, y_pred, "test"
        )

        assert result is None

    def test_with_previous_performance(self):
        """Test with previous performance for delta calculation."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        # Mock previous performance record
        mock_prev = Mock()
        mock_prev.f1_score = 0.75

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_prev
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1, 1])
        y_pred = np.array([1, 0, 1, 1])  # All correct, F1 = 1.0

        result = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, "test"
        )

        # Performance delta should be calculated
        assert result is not None

    def test_with_custom_metrics(self):
        """Test with custom metrics."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        custom_metrics = {"custom_accuracy": 0.95, "latency_ms": 50}

        result = tracker.record_performance(
            mock_session,
            "model-123",
            y_true,
            y_pred,
            "test",
            custom_metrics=custom_metrics
        )

        assert result is not None
        mock_session.add.assert_called_once()

    def test_with_evaluation_metadata(self):
        """Test with evaluation metadata."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        metadata = {"evaluator": "test-suite", "timestamp": "2024-01-01"}

        result = tracker.record_performance(
            mock_session,
            "model-123",
            y_true,
            y_pred,
            "test",
            evaluation_metadata=metadata
        )

        assert result is not None

    def test_different_dataset_types(self):
        """Test with different dataset types constants."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        # Test training dataset
        result1 = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, tracker.DATASET_TRAINING
        )
        assert result1 is not None

        # Test validation dataset
        result2 = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, tracker.DATASET_VALIDATION
        )
        assert result2 is not None

    def test_exception_handling(self):
        """Test exception handling."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        result = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, "test"
        )

        assert result is None


class TestGetPerformanceHistory:
    """Tests for get_performance_history method."""

    def test_successful_retrieval(self):
        """Test successful performance history retrieval."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        # Mock performance records
        mock_record1 = Mock()
        mock_record1.id = "record-1"
        mock_record1.dataset_type = "test"
        mock_record1.accuracy = 0.85
        mock_record1.precision = 0.90
        mock_record1.recall = 0.80
        mock_record1.f1_score = 0.85
        mock_record1.auc_score = 0.88
        mock_record1.sample_size = 100
        mock_record1.performance_delta = 0.05
        mock_record1.confusion_matrix = {"matrix": [[10, 5], [3, 82]]}
        mock_record1.custom_metrics = {}
        mock_record1.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_record1
        ]
        mock_session.query.return_value = mock_query

        result = tracker.get_performance_history(mock_session, "model-123")

        assert len(result) == 1
        assert result[0]["id"] == "record-1"
        assert result[0]["accuracy"] == 0.85
        assert result[0]["created_at"] == "2024-01-01T12:00:00"

    def test_with_dataset_type_filter(self):
        """Test with dataset type filter."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        mock_record1 = Mock()
        mock_record1.id = "record-1"
        mock_record1.dataset_type = "test"
        mock_record1.accuracy = 0.85
        mock_record1.precision = 0.90
        mock_record1.recall = 0.80
        mock_record1.f1_score = 0.85
        mock_record1.auc_score = None
        mock_record1.sample_size = 100
        mock_record1.performance_delta = None
        mock_record1.confusion_matrix = {}
        mock_record1.custom_metrics = {}
        mock_record1.created_at = datetime(2024, 1, 1)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_record1
        ]
        mock_session.query.return_value = mock_query

        result = tracker.get_performance_history(
            mock_session, "model-123", dataset_type="test"
        )

        assert len(result) == 1
        # Verify filter was called with dataset_type
        assert mock_query.filter.called

    def test_no_database_session(self):
        """Test with no database session."""
        tracker = PerformanceTracker()

        result = tracker.get_performance_history(None, "model-123")

        assert result == []

    def test_empty_history(self):
        """Test with no performance records."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        result = tracker.get_performance_history(mock_session, "model-123")

        assert result == []

    def test_multiple_records_ordered_by_date(self):
        """Test that records are ordered by date descending."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        mock_record1 = Mock()
        mock_record1.id = "record-1"
        mock_record1.dataset_type = "test"
        mock_record1.accuracy = 0.85
        mock_record1.precision = 0.90
        mock_record1.recall = 0.80
        mock_record1.f1_score = 0.85
        mock_record1.auc_score = None
        mock_record1.sample_size = 100
        mock_record1.performance_delta = None
        mock_record1.confusion_matrix = {}
        mock_record1.custom_metrics = {}
        mock_record1.created_at = datetime(2024, 1, 1)

        mock_record2 = Mock()
        mock_record2.id = "record-2"
        mock_record2.dataset_type = "test"
        mock_record2.accuracy = 0.90
        mock_record2.precision = 0.92
        mock_record2.recall = 0.88
        mock_record2.f1_score = 0.90
        mock_record2.auc_score = None
        mock_record2.sample_size = 150
        mock_record2.performance_delta = None
        mock_record2.confusion_matrix = {}
        mock_record2.custom_metrics = {}
        mock_record2.created_at = datetime(2024, 1, 2)

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_record2, mock_record1
        ]
        mock_session.query.return_value = mock_query

        result = tracker.get_performance_history(mock_session, "model-123", limit=10)

        assert len(result) == 2
        # Verify order_by was called
        mock_query.filter.return_value.order_by.assert_called_once()

    def test_with_limit_parameter(self):
        """Test with custom limit parameter."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value = mock_query

        tracker.get_performance_history(mock_session, "model-123", limit=50)

        # Verify limit was called with 50
        mock_query.filter.return_value.order_by.return_value.limit.assert_called_with(50)

    def test_none_values_handling(self):
        """Test handling of None values in records."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        mock_record = Mock()
        mock_record.id = "record-1"
        mock_record.dataset_type = "test"
        mock_record.accuracy = None
        mock_record.precision = None
        mock_record.recall = None
        mock_record.f1_score = None
        mock_record.auc_score = None
        mock_record.sample_size = 100
        mock_record.performance_delta = None
        mock_record.confusion_matrix = {}
        mock_record.custom_metrics = None
        mock_record.created_at = None

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_record
        ]
        mock_session.query.return_value = mock_query

        result = tracker.get_performance_history(mock_session, "model-123")

        assert len(result) == 1
        assert result[0]["accuracy"] is None
        assert result[0]["created_at"] is None
        assert result[0]["custom_metrics"] == {}

    def test_exception_handling(self):
        """Test exception handling."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        result = tracker.get_performance_history(mock_session, "model-123")

        assert result == []


class TestDetectPerformanceDegradation:
    """Tests for detect_performance_degradation method."""

    def test_no_degradation(self):
        """Test when no degradation is detected."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        # Mock history with stable performance
        history = [
            {
                "f1_score": 0.85,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.86,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.84,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", threshold=0.05
            )

        assert result["is_degraded"] is False
        assert result["current_f1"] == 0.85

    def test_performance_degraded(self):
        """Test when performance degradation is detected."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        # Mock history with degradation
        history = [
            {
                "f1_score": 0.75,  # Current - dropped by 0.10
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.85,  # Baseline
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.86,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", threshold=0.05
            )

        assert result["is_degraded"] is True
        assert result["current_f1"] == 0.75
        assert result["drop_amount"] == 0.10
        assert result["threshold"] == 0.05

    def test_insufficient_historical_data(self):
        """Test with insufficient historical data."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        # Only one record
        history = [
            {
                "f1_score": 0.85,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123"
            )

        assert result["is_degraded"] is False
        assert result["reason"] == "Insufficient historical data"

    def test_missing_f1_scores(self):
        """Test with missing F1 scores."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "f1_score": None,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.85,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123"
            )

        assert result["is_degraded"] is False
        assert result["reason"] == "Missing F1 score data"

    def test_insufficient_sample_size(self):
        """Test with insufficient sample size."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "f1_score": 0.85,
                "sample_size": 50,  # Below default min_samples of 100
                "dataset_type": "production"
            },
            {
                "f1_score": 0.90,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", min_samples=100
            )

        assert result["is_degraded"] is False
        assert "Insufficient sample size" in result["reason"]

    def test_custom_threshold(self):
        """Test with custom threshold."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "f1_score": 0.82,  # Dropped by 0.08
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.90,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", threshold=0.10
            )

        # Should not be degraded with higher threshold
        assert result["is_degraded"] is False

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", threshold=0.05
            )

        # Should be degraded with lower threshold
        assert result["is_degraded"] is True

    def test_custom_window_size(self):
        """Test with custom window size."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "f1_score": 0.75,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.85,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.86,
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 0.87,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123", window_size=3
            )

        # Should use 3 records for baseline
        assert result["baseline_f1"] is not None

    def test_drop_percentage_calculation(self):
        """Test drop percentage calculation."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "f1_score": 0.80,  # 20% drop from 1.0 to 0.8
                "sample_size": 200,
                "dataset_type": "production"
            },
            {
                "f1_score": 1.00,
                "sample_size": 200,
                "dataset_type": "production"
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.detect_performance_degradation(
                mock_session, "model-123"
            )

        assert "drop_percentage" in result
        assert result["drop_percentage"] == 0.20  # 20% drop

    def test_exception_handling(self):
        """Test exception handling."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        result = tracker.detect_performance_degradation(
            mock_session, "model-123"
        )

        assert result["is_degraded"] is False
        assert "Error during detection" in result["reason"]


class TestCalculateAggregateMetrics:
    """Tests for calculate_aggregate_metrics method."""

    def test_successful_aggregation(self):
        """Test successful aggregate metrics calculation."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "dataset_type": "test",
                "accuracy": 0.85,
                "precision": 0.90,
                "recall": 0.80,
                "f1_score": 0.85,
                "sample_size": 100
            },
            {
                "dataset_type": "test",
                "accuracy": 0.90,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "sample_size": 150
            },
            {
                "dataset_type": "validation",
                "accuracy": 0.80,
                "precision": 0.85,
                "recall": 0.75,
                "f1_score": 0.80,
                "sample_size": 100
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        assert result["model_version_id"] == "model-123"
        assert result["total_records"] == 3
        assert "by_dataset_type" in result
        assert "test" in result["by_dataset_type"]
        assert "validation" in result["by_dataset_type"]

        # Check test dataset aggregates
        test_agg = result["by_dataset_type"]["test"]
        assert test_agg["record_count"] == 2
        assert test_agg["avg_accuracy"] == 0.875  # (0.85 + 0.90) / 2
        assert test_agg["avg_f1_score"] == 0.875
        assert test_agg["total_samples"] == 250

    def test_no_history(self):
        """Test with no performance history."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        with patch.object(tracker, 'get_performance_history', return_value=[]):
            result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        assert result["model_version_id"] == "model-123"
        assert result["total_records"] == 0
        assert result["by_dataset_type"] == {}

    def test_single_dataset_type(self):
        """Test with only one dataset type."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "dataset_type": "production",
                "accuracy": 0.85,
                "precision": 0.90,
                "recall": 0.80,
                "f1_score": 0.85,
                "sample_size": 200
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        assert result["total_records"] == 1
        assert len(result["by_dataset_type"]) == 1
        assert "production" in result["by_dataset_type"]

    def test_handles_none_values(self):
        """Test handling of None values in metrics."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "dataset_type": "test",
                "accuracy": 0.85,
                "precision": None,
                "recall": 0.80,
                "f1_score": 0.85,
                "sample_size": 100
            },
            {
                "dataset_type": "test",
                "accuracy": 0.90,
                "precision": 0.92,
                "recall": None,
                "f1_score": 0.90,
                "sample_size": 150
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        test_agg = result["by_dataset_type"]["test"]
        # Should average only non-None values
        assert test_agg["avg_accuracy"] == 0.875
        assert test_agg["avg_precision"] == 0.92  # Only one non-None value
        assert test_agg["avg_recall"] == 0.80  # Only one non-None value
        assert test_agg["avg_f1_score"] == 0.875

    def test_latest_f1_score(self):
        """Test that latest_f1_score is captured correctly."""
        tracker = PerformanceTracker()

        mock_session = Mock()

        history = [
            {
                "dataset_type": "test",
                "f1_score": 0.90,
                "sample_size": 100
            },
            {
                "dataset_type": "test",
                "f1_score": 0.85,
                "sample_size": 100
            }
        ]

        with patch.object(tracker, 'get_performance_history', return_value=history):
            result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        # First record should be the latest (most recent)
        test_agg = result["by_dataset_type"]["test"]
        assert test_agg["latest_f1_score"] == 0.90

    def test_exception_handling(self):
        """Test exception handling."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")

        result = tracker.calculate_aggregate_metrics(mock_session, "model-123")

        assert result["total_records"] == 0
        assert result["by_dataset_type"] == {}
        assert result["model_version_id"] == "model-123"


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_arrays_in_calculate_metrics(self):
        """Test calculate_metrics with empty arrays."""
        tracker = PerformanceTracker()

        y_true = np.array([])
        y_pred = np.array([])

        # Should handle gracefully
        metrics = tracker.calculate_metrics(y_true, y_pred)

        # Should return default values
        assert "accuracy" in metrics

    def test_single_prediction(self):
        """Test with single prediction."""
        tracker = PerformanceTracker()

        y_true = np.array([1])
        y_pred = np.array([1])

        metrics = tracker.calculate_metrics(y_true, y_pred)

        assert metrics["accuracy"] == 1.0

    def test_all_same_predictions(self):
        """Test when all predictions are the same."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 0, 1, 0])
        y_pred = np.array([1, 1, 1, 1])  # All predict class 1

        metrics = tracker.calculate_metrics(y_true, y_pred)

        # Should still calculate metrics
        assert metrics["accuracy"] == 0.5

    def test_confusion_matrix_with_single_class(self):
        """Test confusion matrix when only one class present."""
        tracker = PerformanceTracker()

        y_true = np.array([1, 1, 1])
        y_pred = np.array([1, 1, 1])

        result = tracker.calculate_confusion_matrix(y_true, y_pred)

        # Should handle single class
        assert result["matrix"] == [[3]]

    def test_performance_delta_with_no_previous(self):
        """Test performance delta when no previous record exists."""
        tracker = PerformanceTracker()

        mock_session = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        mock_session.query.return_value = mock_query

        y_true = np.array([1, 0, 1])
        y_pred = np.array([1, 0, 1])

        result = tracker.record_performance(
            mock_session, "model-123", y_true, y_pred, "test"
        )

        # Should handle None previous_performance
        assert result is not None
