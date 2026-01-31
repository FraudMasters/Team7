"""
Integration tests for model retraining workflow.

This test suite validates the end-to-end integration between:
- Model retraining trigger API endpoint
- Celery task execution for training data processing
- ML model version creation and tracking
- Performance metrics recording in database
- Notification system for retraining completion

Test Coverage:
- Trigger retraining via API endpoint
- Celery task processing feedback data
- New model version creation in database
- Performance metrics recording
- Notification delivery
- Complete retraining workflow end-to-end
"""
import time
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from celery import Celery

# Import the FastAPI application
import sys
sys.path.insert(0, str(__file__).parent.parent.parent)

from main import app
from tasks.model_retraining import (
    automated_retraining_task,
    manual_retraining_task,
    should_trigger_retraining,
    get_current_performance_metrics,
    check_performance_degradation,
    count_recent_feedback,
    MIN_FEEDBACK_SAMPLES_FOR_TRAINING,
    MIN_PERFORMANCE_DEGRADATION_THRESHOLD,
)
from tasks.notifications import send_model_retraining_notification


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_db_session() -> Mock:
    """
    Create a mock database session for testing.

    Returns:
        Mock database session
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_celery_app() -> Celery:
    """
    Create a mock Celery app for testing.

    Returns:
        Celery app instance
    """
    celery_app = Celery('test_tasks', broker='memory://')
    return celery_app


@pytest.fixture
def sample_retraining_request() -> Dict[str, Any]:
    """
    Sample retraining request data.

    Returns:
        Dictionary with retraining request parameters
    """
    return {
        "model_name": "ranking",
        "days_back": 30,
        "requested_by": "admin123",
    }


@pytest.fixture
def sample_model_version() -> Dict[str, Any]:
    """
    Sample model version data.

    Returns:
        Dictionary with model version information
    """
    return {
        "id": "model-version-001",
        "model_name": "ranking",
        "version": "v2.1.0",
        "is_active": False,
        "is_experiment": True,
        "performance_score": 91.0,
        "model_metadata": {
            "algorithm": "bert-base-uncased",
            "training_date": "2026-01-31",
        },
        "accuracy_metrics": {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.94,
            "f1_score": 0.91,
            "sample_size": 150,
        },
    }


@pytest.fixture
def sample_performance_metrics() -> Dict[str, Any]:
    """
    Sample performance metrics.

    Returns:
        Dictionary with performance metrics
    """
    return {
        "accuracy": 0.92,
        "precision": 0.89,
        "recall": 0.94,
        "f1_score": 0.91,
        "auc_score": 0.95,
    }


class TestRetrainingTrigger:
    """Tests for retraining trigger via API."""

    def test_trigger_retraining_via_api(self, client: TestClient):
        """Test triggering retraining via API endpoint."""
        request_data = {
            "model_name": "ranking",
        }

        response = client.post("/api/model-versions/retrain", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "retraining" in data["message"].lower()
        assert "task_id" in data or "job_id" in data

    def test_trigger_retraining_invalid_model_name(self, client: TestClient):
        """Test triggering retraining with invalid model name."""
        request_data = {
            "model_name": "",
        }

        response = client.post("/api/model-versions/retrain", json=request_data)

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_trigger_retraining_supported_models(self, client: TestClient):
        """Test triggering retraining for different supported models."""
        supported_models = ["ranking", "skill_matching", "resume_parser"]

        for model_name in supported_models:
            request_data = {"model_name": model_name}
            response = client.post("/api/model-versions/retrain", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data


class TestCeleryTaskProcessing:
    """Tests for Celery task processing of training data."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "test-task-123"
        task.update_state = MagicMock()
        return task

    def test_task_processes_training_data(self, mock_task_instance):
        """Test that Celery task processes training data correctly."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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
                auto_activate=False,
                notify=False,
            )

            assert result["should_retrain"] is True
            assert result["training_triggered"] is True
            assert result["status"] == "completed"
            assert "training_samples" in result
            assert result["training_samples"] > 0

    def test_task_handles_insufficient_feedback(self, mock_task_instance):
        """Test that task handles insufficient feedback gracefully."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": False,
                "reasons": ["Insufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": False,
                "interval_satisfied": True,
            }

            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=False,
            )

            assert result["should_retrain"] is False
            assert result["training_triggered"] is False
            assert result["status"] == "skipped"

    def test_task_updates_progress_during_execution(self, mock_task_instance):
        """Test that task updates progress during execution."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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

                # Verify update_state was called multiple times
                assert mock_task_instance.update_state.call_count >= 5

    def test_task_records_processing_time(self, mock_task_instance):
        """Test that task records processing time metrics."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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


class TestModelVersionCreation:
    """Tests for new model version creation."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "test-task-456"
        task.update_state = MagicMock()
        return task

    def test_new_model_version_created(self, mock_task_instance):
        """Test that new model version is created after training."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Performance degraded"],
                "performance_degraded": True,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification'):
            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                auto_activate=False,
                notify=False,
            )

            assert result["training_triggered"] is True
            assert "new_version" in result
            assert "new_version_id" in result
            assert result["is_active"] is False
            assert result["is_experiment"] is True

    def test_model_version_with_auto_activation(self, mock_task_instance):
        """Test model version creation with auto-activation."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Performance degraded"],
                "performance_degraded": True,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification'):
            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                auto_activate=True,
                performance_threshold=0.85,
                notify=False,
            )

            assert result["training_triggered"] is True
            assert result["is_active"] is True
            assert result["is_experiment"] is False

    def test_model_version_metadata_recorded(self, mock_task_instance):
        """Test that model version metadata is properly recorded."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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
                model_name="skill_matching",
                days_back=30,
                notify=False,
            )

            assert "new_version" in result
            assert "training_event_id" in result


class TestPerformanceMetricsRecording:
    """Tests for performance metrics recording."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "test-task-789"
        task.update_state = MagicMock()
        return task

    def test_performance_metrics_recorded(self, mock_task_instance):
        """Test that performance metrics are recorded after training."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Sufficient feedback"],
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

            assert "performance_metrics" in result
            metrics = result["performance_metrics"]

            assert "accuracy" in metrics
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1_score" in metrics

            # Verify metric values are in valid range
            assert 0 <= metrics["accuracy"] <= 1
            assert 0 <= metrics["precision"] <= 1
            assert 0 <= metrics["recall"] <= 1
            assert 0 <= metrics["f1_score"] <= 1

    def test_improvement_over_baseline_calculated(self, mock_task_instance):
        """Test that improvement over baseline is calculated."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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

            assert "improvement_over_baseline" in result
            improvement = result["improvement_over_baseline"]
            assert isinstance(improvement, (int, float))

    def test_training_samples_counted(self, mock_task_instance):
        """Test that training samples are counted and recorded."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Sufficient feedback"],
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

            assert "training_samples" in result
            assert result["training_samples"] >= MIN_FEEDBACK_SAMPLES_FOR_TRAINING


class TestNotificationSending:
    """Tests for notification sending after retraining."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "test-task-notif-001"
        task.update_state = MagicMock()
        return task

    def test_notification_sent_on_completion(self, mock_task_instance):
        """Test that notification is sent when retraining completes."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Manual trigger"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.return_value = {"status": "sent", "delivery_successful": True}

            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=True,
            )

            # Verify notification was sent
            assert mock_notify.called
            assert result["notification_sent"] is True
            assert "notification_result" in result

    def test_notification_sent_on_failure(self, mock_task_instance):
        """Test that notification is sent when retraining fails."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.side_effect = Exception("Training failed")

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.return_value = {"status": "sent", "delivery_successful": True}

            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=True,
            )

            # Verify failure notification was sent
            assert mock_notify.called
            assert result["status"] == "failed"

    def test_notification_sent_on_skip(self, mock_task_instance):
        """Test that notification is sent when retraining is skipped."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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
                notify=True,
            )

            # Verify skip notification was sent
            assert mock_notify.called
            assert result["status"] == "skipped"
            assert result["notification_sent"] is True

    def test_notification_failure_doesnt_break_task(self, mock_task_instance):
        """Test that notification failure doesn't break the task."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": False,
                "reasons": ["Insufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": False,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.side_effect = Exception("Email service down")

            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=True,
            )

            # Task should still complete despite notification failure
            assert result["status"] == "skipped"
            assert result["notification_sent"] is False


class TestCompleteRetrainingWorkflow:
    """End-to-end workflow tests for complete retraining process."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "workflow-test-001"
        task.update_state = MagicMock()
        return task

    @pytest.mark.slow
    def test_complete_retraining_workflow_success(self, client: TestClient, mock_task_instance):
        """
        Test complete retraining workflow from API trigger to completion.

        Workflow steps:
        1. Trigger retraining via API
        2. Verify Celery task processes training data
        3. Verify new model version created
        4. Verify performance metrics recorded
        5. Verify notification sent
        """
        # Step 1: Trigger retraining via API
        request_data = {"model_name": "ranking"}
        api_response = client.post("/api/model-versions/retrain", json=request_data)
        assert api_response.status_code == 200
        api_data = api_response.json()
        assert "message" in api_data

        # Step 2 & 3 & 4 & 5: Simulate Celery task execution
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Performance degraded", "Sufficient feedback"],
                "performance_degraded": True,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.return_value = {
                "status": "sent",
                "delivery_successful": True,
                "recipients_count": 1,
            }

            # Execute the task
            task_result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                auto_activate=False,
                notify=True,
            )

            # Verify training was triggered
            assert task_result["should_retrain"] is True
            assert task_result["training_triggered"] is True
            assert task_result["status"] == "completed"

            # Verify training data was processed
            assert task_result["training_samples"] > 0

            # Verify new model version was created
            assert "new_version" in task_result
            assert "new_version_id" in task_result
            assert task_result["is_experiment"] is True

            # Verify performance metrics were recorded
            assert "performance_metrics" in task_result
            metrics = task_result["performance_metrics"]
            assert "f1_score" in metrics
            assert 0 <= metrics["f1_score"] <= 1

            # Verify improvement calculated
            assert "improvement_over_baseline" in task_result

            # Verify notification was sent
            assert mock_notify.called
            assert task_result["notification_sent"] is True

            # Verify processing time recorded
            assert "processing_time_ms" in task_result
            assert task_result["processing_time_ms"] > 0

    @pytest.mark.slow
    def test_retraining_workflow_with_auto_activation(self, client: TestClient, mock_task_instance):
        """
        Test retraining workflow with auto-activation enabled.

        Workflow:
        1. Trigger retraining via API
        2. Execute training with auto-activation
        3. Verify model is activated based on performance
        """
        # Trigger via API
        request_data = {"model_name": "skill_matching"}
        api_response = client.post("/api/model-versions/retrain", json=request_data)
        assert api_response.status_code == 200

        # Execute task with auto-activation
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": True,
                "reasons": ["Sufficient feedback"],
                "performance_degraded": False,
                "sufficient_feedback": True,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification'):
            task_result = automated_retraining_task(
                mock_task_instance,
                model_name="skill_matching",
                days_back=30,
                auto_activate=True,
                performance_threshold=0.85,
                notify=False,
            )

            # Verify model was activated (F1=0.91 >= 0.85 threshold)
            assert task_result["training_triggered"] is True
            assert task_result["is_active"] is True
            assert task_result["is_experiment"] is False

    @pytest.mark.slow
    def test_retraining_workflow_skipped_scenario(self, client: TestClient, mock_task_instance):
        """
        Test retraining workflow when conditions aren't met.

        Workflow:
        1. Trigger retraining via API
        2. Task evaluates conditions
        3. Training skipped due to insufficient feedback
        4. Notification sent about skip
        """
        # Trigger via API
        request_data = {"model_name": "ranking"}
        api_response = client.post("/api/model-versions/retrain", json=request_data)
        assert api_response.status_code == 200

        # Execute task that will be skipped
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.return_value = {
                "should_retrain": False,
                "reasons": ["Insufficient feedback samples"],
                "performance_degraded": False,
                "sufficient_feedback": False,
                "interval_satisfied": True,
            }

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.return_value = {"status": "sent"}

            task_result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=True,
            )

            # Verify training was not triggered
            assert task_result["should_retrain"] is False
            assert task_result["training_triggered"] is False
            assert task_result["status"] == "skipped"

            # Verify notification was still sent
            assert mock_notify.called
            assert task_result["notification_sent"] is True

    def test_manual_retraining_workflow(self, mock_task_instance):
        """Test manual retraining triggered by admin."""
        with patch('tasks.model_retraining.automated_retraining_task') as mock_auto:
            mock_auto.return_value = {
                "should_retrain": True,
                "training_triggered": True,
                "status": "completed",
                "new_version": "v2.2.0",
            }

            result = manual_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                requested_by="admin123",
                auto_activate=False,
            )

            assert result["status"] == "completed"
            assert result["requested_by"] == "admin123"
            assert result["trigger_type"] == "manual"


class TestErrorHandling:
    """Tests for error handling in retraining workflow."""

    @pytest.fixture
    def mock_task_instance(self):
        """Create a mock Celery task instance."""
        task = MagicMock()
        task.request.id = "error-test-001"
        task.update_state = MagicMock()
        return task

    def test_task_handles_training_failure(self, mock_task_instance):
        """Test that task handles training failure gracefully."""
        from celery.exceptions import SoftTimeLimitExceeded

        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
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
            assert "error" in result
            assert result["training_triggered"] is False
            assert mock_notify.called  # Notification still sent

    def test_task_handles_generic_exception(self, mock_task_instance):
        """Test that task handles generic exceptions."""
        with patch('tasks.model_retraining.should_trigger_retraining') as mock_should_trigger:
            mock_should_trigger.side_effect = Exception("Unexpected database error")

        with patch('tasks.model_retraining.send_model_retraining_notification') as mock_notify:
            mock_notify.return_value = {"status": "sent"}

            result = automated_retraining_task(
                mock_task_instance,
                model_name="ranking",
                days_back=30,
                notify=True,
            )

            assert result["status"] == "failed"
            assert "Unexpected database error" in result["error"]
            assert result["training_triggered"] is False


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
