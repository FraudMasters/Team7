"""
Unit Tests for Model Retraining Celery Tasks

Tests the automated model retraining tasks that evaluate performance
degradation, collect feedback, and retrain ML models.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from celery import Celery
from datetime import datetime, timedelta
import time

from tasks.model_retraining import (
    get_current_performance_metrics,
    check_performance_degradation,
    count_recent_feedback,
    should_trigger_retraining,
    automated_retraining_task,
    manual_retraining_task,
    MIN_PERFORMANCE_DEGRADATION_THRESHOLD,
    MIN_FEEDBACK_SAMPLES_FOR_TRAINING,
    MIN_RETRAINING_INTERVAL_DAYS,
    AUTO_ACTIVATION_PERFORMANCE_THRESHOLD,
)
from models.ml_model_version import MLModelVersion
from models.model_performance_history import ModelPerformanceHistory
from models.model_training_event import ModelTrainingEvent
from models.skill_feedback import SkillFeedback


class TestGetCurrentPerformanceMetrics:
    """Tests for get_current_performance_metrics function."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def sample_performance_records(self):
        """Create sample performance history records."""
        return {
            "validation": {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.94,
                "f1_score": 0.91,
                "auc_score": 0.95,
                "performance_delta": 0.02,
                "created_at": datetime.now(),
            },
            "test": {
                "accuracy": 0.88,
                "precision": 0.86,
                "recall": 0.90,
                "f1_score": 0.88,
                "auc_score": 0.92,
                "performance_delta": -0.01,
                "created_at": datetime.now(),
            },
        }

    def test_get_performance_metrics_success(self, mock_db_session, sample_performance_records):
        """Test successfully retrieving performance metrics."""
        # Mock the query execution
        mock_perf_history = MagicMock()
        mock_perf_history.accuracy = 0.92
        mock_perf_history.precision = 0.89
        mock_perf_history.recall = 0.94
        mock_perf_history.f1_score = 0.91
        mock_perf_history.auc_score = 0.95
        mock_perf_history.performance_delta = 0.02
        mock_perf_history.created_at = datetime.now()
        mock_perf_history.model_version_id = "version-1"

        mock_model_version = MagicMock()
        mock_model_version.model_name = "ranking"

        mock_db_session.execute.return_value.first.return_value = (
            mock_perf_history,
            mock_model_version,
        )

        result = get_current_performance_metrics(
            model_name="ranking",
            dataset_types=["validation"],
            db_session=mock_db_session,
        )

        assert "validation" in result
        assert result["validation"] is not None
        assert result["validation"]["accuracy"] == 0.92
        assert result["validation"]["f1_score"] == 0.91

    def test_get_performance_metrics_no_data(self, mock_db_session):
        """Test when no performance metrics exist."""
        mock_db_session.execute.return_value.first.return_value = None

        result = get_current_performance_metrics(
            model_name="ranking",
            dataset_types=["validation"],
            db_session=mock_db_session,
        )

        assert "validation" in result
        assert result["validation"] is None

    def test_get_performance_metrics_multiple_datasets(self, mock_db_session):
        """Test retrieving metrics for multiple dataset types."""
        def mock_execute_side_effect(query):
            mock_result = MagicMock()
            if "validation" in str(query):
                mock_perf = MagicMock(accuracy=0.92, f1_score=0.91, created_at=datetime.now())
            else:
                mock_perf = MagicMock(accuracy=0.88, f1_score=0.88, created_at=datetime.now())
            mock_result.first.return_value = (mock_perf, MagicMock())
            return mock_result

        mock_db_session.execute.side_effect = mock_execute_side_effect

        result = get_current_performance_metrics(
            model_name="ranking",
            dataset_types=["validation", "test"],
            db_session=mock_db_session,
        )

        assert "validation" in result
        assert "test" in result
        assert result["validation"]["accuracy"] == 0.92
        assert result["test"]["accuracy"] == 0.88

    def test_get_performance_metrics_handles_nulls(self, mock_db_session):
        """Test handling of null metric values."""
        mock_perf_history = MagicMock()
        mock_perf_history.accuracy = None
        mock_perf_history.precision = 0.89
        mock_perf_history.recall = None
        mock_perf_history.f1_score = 0.91
        mock_perf_history.auc_score = None
        mock_perf_history.performance_delta = None
        mock_perf_history.created_at = datetime.now()
        mock_perf_history.model_version_id = "version-1"

        mock_db_session.execute.return_value.first.return_value = (
            mock_perf_history,
            MagicMock(),
        )

        result = get_current_performance_metrics(
            model_name="ranking",
            dataset_types=["validation"],
            db_session=mock_db_session,
        )

        assert result["validation"]["accuracy"] is None
        assert result["validation"]["precision"] == 0.89
        assert result["validation"]["recall"] is None
        assert result["validation"]["f1_score"] == 0.91


class TestCheckPerformanceDegradation:
    """Tests for check_performance_degradation function."""

    @pytest.fixture
    def baseline_metrics(self):
        """Create baseline performance metrics."""
        return {
            "validation": {
                "accuracy": 0.90,
                "precision": 0.88,
                "recall": 0.92,
                "f1_score": 0.90,
            },
            "test": {
                "accuracy": 0.85,
                "precision": 0.83,
                "recall": 0.87,
                "f1_score": 0.85,
            },
        }

    @pytest.fixture
    def degraded_metrics(self):
        """Create degraded performance metrics."""
        return {
            "validation": {
                "accuracy": 0.82,  # 8% drop
                "precision": 0.83,
                "recall": 0.84,
                "f1_score": 0.82,  # 8% drop
            },
            "test": {
                "accuracy": 0.80,
                "precision": 0.78,
                "recall": 0.82,
                "f1_score": 0.80,
            },
        }

    @pytest.fixture
    def improved_metrics(self):
        """Create improved performance metrics."""
        return {
            "validation": {
                "accuracy": 0.92,
                "precision": 0.90,
                "recall": 0.94,
                "f1_score": 0.92,
            }
        }

    def test_performance_degradation_detected(self, baseline_metrics, degraded_metrics):
        """Test detection of significant performance degradation."""
        is_degraded, details = check_performance_degradation(
            current_metrics=degraded_metrics,
            baseline_metrics=baseline_metrics,
            threshold=0.05,
            model_name="ranking",
        )

        assert is_degraded is True
        assert details["max_degradation"] >= 0.05
        assert "validation_f1_score" in details
        assert details["validation_f1_score"] >= 0.05

    def test_no_performance_degradation(self, baseline_metrics, improved_metrics):
        """Test when performance has not degraded."""
        is_degraded, details = check_performance_degradation(
            current_metrics=improved_metrics,
            baseline_metrics=baseline_metrics,
            threshold=0.05,
            model_name="ranking",
        )

        assert is_degraded is False
        assert details["max_degradation"] == 0.0

    def test_degradation_below_threshold(self, baseline_metrics):
        """Test when degradation is below threshold."""
        slightly_degraded = {
            "validation": {
                "accuracy": 0.88,  # 2% drop (below threshold)
                "precision": 0.87,
                "recall": 0.90,
                "f1_score": 0.88,
            }
        }

        is_degraded, details = check_performance_degradation(
            current_metrics=slightly_degraded,
            baseline_metrics=baseline_metrics,
            threshold=0.05,
            model_name="ranking",
        )

        assert is_degraded is False
        assert details["max_degradation"] < 0.05

    def test_handles_missing_metrics(self):
        """Test handling of missing metric data."""
        current = {"validation": {"accuracy": 0.85, "f1_score": 0.85}}
        baseline = {"test": {"accuracy": 0.90, "f1_score": 0.90}}

        is_degraded, details = check_performance_degradation(
            current_metrics=current,
            baseline_metrics=baseline,
            threshold=0.05,
            model_name="ranking",
        )

        # Should not degrade when datasets don't match
        assert is_degraded is False
        assert details["max_degradation"] == 0.0

    def test_handles_null_values(self):
        """Test handling of null metric values."""
        current = {
            "validation": {
                "accuracy": None,
                "precision": 0.85,
                "recall": 0.85,
                "f1_score": None,
            }
        }
        baseline = {
            "validation": {
                "accuracy": 0.90,
                "precision": 0.88,
                "recall": 0.92,
                "f1_score": 0.90,
            }
        }

        is_degraded, details = check_performance_degradation(
            current_metrics=current,
            baseline_metrics=baseline,
            threshold=0.05,
            model_name="ranking",
        )

        # Should only compare non-null values
        assert isinstance(is_degraded, bool)


class TestCountRecentFeedback:
    """Tests for count_recent_feedback function."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    def test_count_feedback_success(self, mock_db_session):
        """Test successfully counting feedback entries."""
        mock_db_session.execute.return_value.scalar.return_value = 150

        count = count_recent_feedback(
            model_name="ranking",
            days_back=30,
            db_session=mock_db_session,
        )

        assert count == 150
        mock_db_session.execute.assert_called_once()

    def test_count_feedback_no_entries(self, mock_db_session):
        """Test when no feedback entries exist."""
        mock_db_session.execute.return_value.scalar.return_value = 0

        count = count_recent_feedback(
            model_name="ranking",
            days_back=30,
            db_session=mock_db_session,
        )

        assert count == 0

    def test_count_feedback_none_result(self, mock_db_session):
        """Test when query returns None."""
        mock_db_session.execute.return_value.scalar.return_value = None

        count = count_recent_feedback(
            model_name="ranking",
            days_back=30,
            db_session=mock_db_session,
        )

        # Should return 0 instead of None
        assert count == 0

    def test_count_feedback_different_time_periods(self, mock_db_session):
        """Test counting feedback for different time periods."""
        mock_db_session.execute.return_value.scalar.return_value = 50

        count = count_recent_feedback(
            model_name="ranking",
            days_back=7,
            db_session=mock_db_session,
        )

        assert count == 50

    def test_count_feedback_handles_errors(self, mock_db_session):
        """Test error handling in feedback counting."""
        mock_db_session.execute.side_effect = Exception("Database error")

        count = count_recent_feedback(
            model_name="ranking",
            days_back=30,
            db_session=mock_db_session,
        )

        # Should return 0 on error
        assert count == 0


class TestShouldTriggerRetraining:
    """Tests for should_trigger_retraining function."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_active_model(self):
        """Create a mock active model."""
        model = MagicMock()
        model.is_active = True
        model.is_experiment = False
        model.accuracy_metrics = {
            "accuracy": 0.90,
            "precision": 0.88,
            "recall": 0.92,
            "f1_score": 0.90,
        }
        return model

    @pytest.mark.db
    def test_should_retrain_with_degradation(self, mock_db_session, mock_active_model):
        """Test that retraining is triggered with performance degradation."""
        # Mock active model query
        mock_db_session.query.return_value.where.return_value.first.return_value = (
            mock_active_model
        )

        # Mock performance metrics query
        mock_perf_history = MagicMock()
        mock_perf_history.accuracy = 0.82
        mock_perf_history.f1_score = 0.82
        mock_perf_history.created_at = datetime.now()

        mock_db_session.execute.return_value.first.return_value = (
            mock_perf_history,
            MagicMock(),
        )

        # Mock feedback count
        mock_db_session.execute.return_value.scalar.return_value = 150

        # Mock last training event (outside interval)
        last_training = MagicMock()
        last_training.completed_at = (datetime.now() - timedelta(days=10)).isoformat()
        mock_db_session.query.return_value.order_by.return_value.first.return_value = (
            last_training
        )

        result = should_trigger_retraining(
            model_name="ranking",
            db_session=mock_db_session,
            performance_threshold=0.05,
            min_feedback_samples=100,
            min_interval_days=7,
        )

        assert result["should_retrain"] is True
        assert result["performance_degraded"] is True
        assert result["sufficient_feedback"] is True
        assert result["interval_satisfied"] is True
        assert len(result["reasons"]) > 0

    @pytest.mark.db
    def test_should_retrain_with_sufficient_feedback(self, mock_db_session):
        """Test that retraining is triggered with sufficient feedback."""
        # Mock no active model
        mock_db_session.query.return_value.where.return_value.first.return_value = None

        # Mock sufficient feedback
        mock_db_session.execute.return_value.scalar.return_value = 200

        # Mock no recent training
        mock_db_session.query.return_value.order_by.return_value.first.return_value = None

        result = should_trigger_retraining(
            model_name="ranking",
            db_session=mock_db_session,
            min_feedback_samples=100,
            min_interval_days=7,
        )

        assert result["should_retrain"] is True
        assert result["sufficient_feedback"] is True

    @pytest.mark.db
    def test_should_not_retrain_insufficient_feedback(self, mock_db_session):
        """Test that retraining is not triggered with insufficient feedback."""
        mock_db_session.query.return_value.where.return_value.first.return_value = None
        mock_db_session.execute.return_value.scalar.return_value = 50  # Below threshold
        mock_db_session.query.return_value.order_by.return_value.first.return_value = None

        result = should_trigger_retraining(
            model_name="ranking",
            db_session=mock_db_session,
            min_feedback_samples=100,
            min_interval_days=7,
        )

        assert result["should_retrain"] is False
        assert result["sufficient_feedback"] is False

    @pytest.mark.db
    def test_should_not_retrain_within_interval(self, mock_db_session):
        """Test that retraining respects minimum interval."""
        mock_db_session.query.return_value.where.return_value.first.return_value = None
        mock_db_session.execute.return_value.scalar.return_value = 150

        # Mock recent training (within interval)
        last_training = MagicMock()
        last_training.completed_at = (datetime.now() - timedelta(days=3)).isoformat()
        mock_db_session.query.return_value.order_by.return_value.first.return_value = (
            last_training
        )

        result = should_trigger_retraining(
            model_name="ranking",
            db_session=mock_db_session,
            min_feedback_samples=100,
            min_interval_days=7,
        )

        assert result["should_retrain"] is False
        assert result["interval_satisfied"] is False


class TestAutomatedRetrainingTask:
    """Tests for automated_retraining_task Celery task."""

    @pytest.fixture
    def mock_celery_app(self):
        """Create a mock Celery app for testing."""
        app = Celery('test_tasks', broker='memory://')
        return app

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "test-task-123"
        task.update_state = MagicMock()
        return task

    def test_task_skipped_when_no_trigger(self, mock_task_instance):
        """Test that task is skipped when retraining should not be triggered."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": False,
                "reasons": ["Insufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": False,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.return_value = {"status": "sent"}

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    auto_activate=False,
                    notify=True,
                )

                assert result["should_retrain"] is False
                assert result["training_triggered"] is False
                assert result["status"] == "skipped"
                assert result["notification_sent"] is True

    def test_task_success_with_auto_activation(self, mock_task_instance):
        """Test successful retraining with auto-activation."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Performance degraded"],
                "performance_degraded": True,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.return_value = {"status": "sent"}

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    auto_activate=True,
                    performance_threshold=0.85,
                    notify=True,
                )

                assert result["should_retrain"] is True
                assert result["training_triggered"] is True
                assert result["status"] == "completed"
                assert "new_version" in result
                assert "performance_metrics" in result
                assert result["performance_metrics"]["f1_score"] == 0.91
                assert result["is_active"] is True  # Auto-activated

    def test_task_success_without_auto_activation(self, mock_task_instance):
        """Test successful retraining without auto-activation."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Sufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.return_value = {"status": "sent"}

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    auto_activate=False,  # No auto-activation
                    notify=True,
                )

                assert result["should_retrain"] is True
                assert result["training_triggered"] is True
                assert result["status"] == "completed"
                assert result["is_active"] is False
                assert result["is_experiment"] is True

    def test_task_updates_progress(self, mock_task_instance):
        """Test that task updates progress during execution."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Manual trigger"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification'):
                automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    notify=False,
                )

                # Verify update_state was called multiple times (for progress updates)
                assert mock_task_instance.update_state.call_count >= 5

                # Check first call for initial progress
                first_call = mock_task_instance.update_state.call_args_list[0]
                assert first_call[1]["meta"]["status"] == "evaluating_trigger"

    def test_task_handles_time_limit_exceeded(self, mock_task_instance):
        """Test handling of SoftTimeLimitExceeded exception."""
        from celery.exceptions import SoftTimeLimitExceeded

        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.side_effect = SoftTimeLimitExceeded()

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.return_value = {"status": "sent"}

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    notify=True,
                )

                assert result["status"] == "failed"
                assert "exceeded maximum time limit" in result["error"]
                assert result["training_triggered"] is False

    def test_task_handles_generic_exception(self, mock_task_instance):
        """Test handling of generic exceptions."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.side_effect = Exception("Unexpected error")

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.return_value = {"status": "sent"}

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    notify=True,
                )

                assert result["status"] == "failed"
                assert "Unexpected error" in result["error"]
                assert result["training_triggered"] is False

    def test_task_notification_failure(self, mock_task_instance):
        """Test that notification failure doesn't break the task."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": False,
                "reasons": ["Insufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": False,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
                mock_notify.side_effect = Exception("Notification failed")

                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    notify=True,
                )

                # Task should still complete successfully
                assert result["status"] == "skipped"
                assert result["notification_sent"] is False

    def test_task_returns_processing_time(self, mock_task_instance):
        """Test that task returns processing time metrics."""
        with patch(
            'tasks.model_retraining.should_trigger_retraining'
        ) as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Manual trigger"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

            with patch('tasks.model_retraining.send_model_retraining_notification'):
                result = automated_retraining_task(
                    mock_task_instance,
                    model_name="ranking",
                    days_back=30,
                    notify=False,
                )

                assert "processing_time_ms" in result
                assert result["processing_time_ms"] > 0
                assert isinstance(result["processing_time_ms"], (int, float))


class TestManualRetrainingTask:
    """Tests for manual_retraining_task Celery task."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "manual-task-456"
        return task

    def test_manual_task_calls_automated_task(self, mock_task_instance):
        """Test that manual task delegates to automated task."""
        with patch(
            'tasks.model_retraining.automated_retraining_task'
        ) as mock_automated:
            mock_automated.return_value = {
                "should_retrain": True,
                "training_triggered": True,
                "status": "completed",
                "new_version": "v2.1.0",
            }

            result = manual_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                requested_by="admin123",
                auto_activate=False,
            )

            assert mock_automated.called
            assert result["status"] == "completed"
            assert result["requested_by"] == "admin123"
            assert result["trigger_type"] == "manual"

    def test_manual_task_with_no_requester(self, mock_task_instance):
        """Test manual task without specifying requester."""
        with patch(
            'tasks.model_retraining.automated_retraining_task'
        ) as mock_automated:
            mock_automated.return_value = {
                "should_retrain": True,
                "training_triggered": True,
                "status": "completed",
            }

            result = manual_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                requested_by=None,
            )

            assert result["requested_by"] is None
            assert result["trigger_type"] == "manual"

    def test_manual_task_passes_parameters(self, mock_task_instance):
        """Test that manual task passes parameters correctly."""
        with patch(
            'tasks.model_retraining.automated_retraining_task'
        ) as mock_automated:
            mock_automated.return_value = {
                "should_retrain": True,
                "training_triggered": True,
                "status": "completed",
            }

            manual_retraining_task(
                mock_task_instance,
                model_name="skill_matching",
                days_back=60,
                requested_by="user456",
                auto_activate=True,
                performance_threshold=0.90,
            )

            # Verify automated_retraining_task was called with correct params
            mock_automated.assert_called_once()
            call_kwargs = mock_automated.call_args[1]
            assert call_kwargs["model_name"] == "skill_matching"
            assert call_kwargs["days_back"] == 60
            assert call_kwargs["auto_activate"] is True
            assert call_kwargs["performance_threshold"] == 0.90


class TestRetrainingThresholds:
    """Tests for retraining threshold constants."""

    def test_performance_degradation_threshold(self):
        """Test that degradation threshold is appropriately set."""
        assert MIN_PERFORMANCE_DEGRADATION_THRESHOLD == 0.05
        assert 0 < MIN_PERFORMANCE_DEGRADATION_THRESHOLD < 1

    def test_minimum_feedback_samples(self):
        """Test that minimum feedback samples is reasonable."""
        assert MIN_FEEDBACK_SAMPLES_FOR_TRAINING == 100
        assert MIN_FEEDBACK_SAMPLES_FOR_TRAINING > 0

    def test_minimum_retraining_interval(self):
        """Test that minimum retraining interval is reasonable."""
        assert MIN_RETRAINING_INTERVAL_DAYS == 7
        assert MIN_RETRAINING_INTERVAL_DAYS > 0

    def test_auto_activation_threshold(self):
        """Test that auto-activation threshold is appropriately set."""
        assert AUTO_ACTIVATION_PERFORMANCE_THRESHOLD == 0.85
        assert 0 < AUTO_ACTIVATION_PERFORMANCE_THRESHOLD <= 1.0


@pytest.mark.parametrize(
    "current_f1,baseline_f1,threshold,should_degrade",
    [
        (0.85, 0.90, 0.05, True),  # 5% drop
        (0.88, 0.90, 0.05, False),  # 2% drop (below threshold)
        (0.80, 0.90, 0.05, True),  # 10% drop
        (0.92, 0.90, 0.05, False),  # Improvement
        (0.90, 0.90, 0.05, False),  # No change
    ],
)
def test_degradation_detection_variations(current_f1, baseline_f1, threshold, should_degrade):
    """Test performance degradation detection with various scenarios."""
    current = {"validation": {"f1_score": current_f1}}
    baseline = {"validation": {"f1_score": baseline_f1}}

    is_degraded, details = check_performance_degradation(
        current_metrics=current,
        baseline_metrics=baseline,
        threshold=threshold,
        model_name="test_model",
    )

    assert is_degraded == should_degrade


@pytest.mark.parametrize(
    "feedback_count,min_samples,should_train",
    [
        (150, 100, True),  # Sufficient feedback
        (100, 100, True),  # Exactly at threshold
        (50, 100, False),  # Below threshold
        (0, 100, False),  # No feedback
    ],
)
def test_feedback_threshold_variations(feedback_count, min_samples, should_train):
    """Test feedback threshold decision with various counts."""
    with patch('tasks.model_retraining.count_recent_feedback') as mock_count:
        mock_count.return_value = feedback_count

        with patch('tasks.model_retraining.get_current_performance_metrics'):
            with patch('tasks.model_retraining.db.session') as mock_session:
                mock_session.query.return_value.where.return_value.first.return_value = None
                mock_session.query.return_value.order_by.return_value.first.return_value = None

                result = should_trigger_retraining(
                    model_name="test",
                    db_session=mock_session,
                    min_feedback_samples=min_samples,
                )

                assert result["sufficient_feedback"] == should_train
