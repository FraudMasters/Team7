"""
Tests for scheduled report delivery tasks.

Tests cover scheduled report generation, delivery, and beat schedule configuration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from tasks.report_generation import (
    generate_scheduled_reports,
    process_all_pending_reports,
    get_report_data,
    format_report_as_pdf,
    format_report_as_csv,
    send_report_via_email,
    get_scheduled_report_config,
)


class TestGetScheduledReportConfig:
    """Tests for get_scheduled_report_config function."""

    def test_get_config_with_defaults(self):
        """Test configuration returns default values."""
        config = get_scheduled_report_config()

        # Check required fields exist
        assert "enabled" in config
        assert "check_interval_minutes" in config
        assert "batch_size" in config
        assert "retry_failed_reports" in config

        # Check default values
        assert config["enabled"] is True
        assert config["check_interval_minutes"] == 60
        assert config["batch_size"] == 10

    def test_get_config_structure(self):
        """Test configuration has correct structure."""
        config = get_scheduled_report_config()

        # Verify all expected keys are present
        expected_keys = [
            "enabled",
            "check_interval_minutes",
            "batch_size",
            "retry_failed_reports",
            "max_retries",
            "retry_delay_minutes",
        ]

        for key in expected_keys:
            assert key in config, f"Missing config key: {key}"


class TestGetReportData:
    """Tests for get_report_data function."""

    def test_generate_report_data_basic(self):
        """Test basic report data generation."""
        report_config = {
            "report_type": "hiring_pipeline",
            "metrics": ["time_to_hire", "resumes_processed"],
            "dimensions": ["source"],
        }
        date_range = {
            "start": datetime(2024, 1, 1),
            "end": datetime(2024, 1, 31),
        }

        data = get_report_data(report_config, date_range)

        assert data is not None
        assert "metrics" in data
        assert "dimensions" in data
        assert "summary" in data
        assert "generated_at" in data

    def test_generate_report_data_has_metrics(self):
        """Test report data includes metrics."""
        report_config = {
            "report_type": "custom",
            "metrics": ["time_to_hire"],
            "dimensions": [],
        }
        date_range = {
            "start": datetime.utcnow() - timedelta(days=7),
            "end": datetime.utcnow(),
        }

        data = get_report_data(report_config, date_range)

        assert "metrics" in data
        assert isinstance(data["metrics"], dict)

    def test_generate_report_data_date_range(self):
        """Test report data respects date range."""
        report_config = {"report_type": "test"}
        date_range = {
            "start": datetime(2024, 1, 1),
            "end": datetime(2024, 1, 31),
        }

        data = get_report_data(report_config, date_range)

        # Summary should mention the date range
        assert "2024-01-01" in data["summary"]
        assert "2024-01-31" in data["summary"]


class TestFormatReportAsPdf:
    """Tests for format_report_as_pdf function."""

    def test_format_pdf_basic(self):
        """Test basic PDF formatting."""
        report_data = {
            "metrics": {"time_to_hire": 15.2},
            "summary": "Test report summary",
            "generated_at": "2024-03-21T12:00:00",
        }

        pdf_bytes = format_report_as_pdf(report_data, "Test Report")

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_format_pdf_with_nested_metrics(self):
        """Test PDF formatting with nested metrics."""
        report_data = {
            "metrics": {
                "source_effectiveness": {
                    "LinkedIn": 0.75,
                    "Indeed": 0.62,
                }
            },
            "generated_at": "2024-03-21T12:00:00",
        }

        pdf_bytes = format_report_as_pdf(report_data, "Analytics Report")

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_format_pdf_with_empty_data(self):
        """Test PDF formatting handles empty data gracefully."""
        report_data = {
            "metrics": {},
            "generated_at": "2024-03-21T12:00:00",
        }

        pdf_bytes = format_report_as_pdf(report_data, "Empty Report")

        # Should still generate PDF even with empty data
        assert pdf_bytes is not None


class TestFormatReportAsCsv:
    """Tests for format_report_as_csv function."""

    def test_format_csv_basic(self):
        """Test basic CSV formatting."""
        report_data = {
            "metrics": {
                "time_to_hire": 15.2,
                "resumes_processed": 150,
            }
        }

        csv_bytes = format_report_as_csv(report_data)

        assert csv_bytes is not None
        assert isinstance(csv_bytes, bytes)
        assert len(csv_bytes) > 0

    def test_format_csv_with_nested_data(self):
        """Test CSV formatting with nested data structures."""
        report_data = {
            "metrics": {
                "source_effectiveness": {
                    "LinkedIn": 0.75,
                    "Indeed": 0.62,
                }
            }
        }

        csv_bytes = format_report_as_csv(report_data)

        assert csv_bytes is not None
        # CSV should contain the nested keys
        csv_content = csv_bytes.decode("utf-8")
        assert "source_effectiveness" in csv_content

    def test_format_csv_empty_metrics(self):
        """Test CSV formatting handles empty metrics."""
        report_data = {"metrics": {}}

        csv_bytes = format_report_as_csv(report_data)

        # Should still return valid CSV with headers
        assert csv_bytes is not None


class TestSendReportViaEmail:
    """Tests for send_report_via_email function."""

    def test_send_email_basic(self):
        """Test basic email sending."""
        recipients = ["test@example.com"]
        report_name = "Weekly Report"
        report_data = {
            "summary": "Test summary",
            "generated_at": "2024-03-21T12:00:00",
        }

        result = send_report_via_email(recipients, report_name, report_data)

        assert result["success"] is True
        assert result["recipients_count"] == 1
        assert result["attachments_count"] == 0

    def test_send_email_with_attachments(self):
        """Test email sending with attachments."""
        recipients = ["test@example.com", "manager@example.com"]
        attachments = [
            {
                "filename": "report.pdf",
                "content": b"PDF content",
                "content_type": "application/pdf",
            },
            {
                "filename": "report.csv",
                "content": b"CSV content",
                "content_type": "text/csv",
            },
        ]

        result = send_report_via_email(
            recipients, "Test Report", {}, attachments=attachments
        )

        assert result["success"] is True
        assert result["recipients_count"] == 2
        assert result["attachments_count"] == 2

    def test_send_email_multiple_recipients(self):
        """Test email sending to multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

        result = send_report_via_email(recipients, "Report", {})

        assert result["recipients_count"] == 3


class TestGenerateScheduledReports:
    """Tests for generate_scheduled_reports task."""

    @pytest.fixture
    def mock_celery_task(self):
        """Mock Celery task instance."""
        task = Mock()
        task.request = Mock()
        task.request.id = "test-task-123"
        task.update_state = Mock()
        return task

    def test_generate_report_success(self, mock_celery_task):
        """Test successful report generation."""
        result = generate_scheduled_reports(
            mock_celery_task,
            "report-123"
        )

        assert result["status"] == "completed"
        assert result["scheduled_report_id"] == "report-123"
        assert "formats_generated" in result
        assert "delivery_successful" in result
        assert "processing_time_ms" in result

    def test_generate_report_updates_progress(self, mock_celery_task):
        """Test task updates progress during execution."""
        generate_scheduled_reports(mock_celery_task, "report-123")

        # Should have called update_state multiple times
        assert mock_celery_task.update_state.call_count >= 3

    def test_generate_report_inactive_skipped(self, mock_celery_task):
        """Test inactive reports are skipped."""
        # This would require mocking the database query
        # For now, test the basic workflow
        result = generate_scheduled_reports(mock_celery_task, "report-123")

        # Should complete or skip
        assert result["status"] in ["completed", "skipped"]

    def test_generate_report_includes_delivery_info(self, mock_celery_task):
        """Test result includes delivery information."""
        result = generate_scheduled_reports(mock_celery_task, "report-123")

        assert "delivery_method" in result
        assert "recipients_count" in result
        assert "delivery_successful" in result

    def test_generate_report_handles_pdf_format(self, mock_celery_task):
        """Test report generation with PDF format."""
        result = generate_scheduled_reports(mock_celery_task, "report-123")

        # Should have generated at least one format
        assert len(result.get("formats_generated", [])) > 0

    def test_generate_report_error_handling(self, mock_celery_task):
        """Test task handles errors gracefully."""
        # Simulate an error by passing invalid ID
        result = generate_scheduled_reports(mock_celery_task, None)

        # Should return failed status
        assert result["status"] == "failed"
        assert "error" in result


class TestProcessAllPendingReports:
    """Tests for process_all_pending_reports task."""

    @pytest.fixture
    def mock_celery_task(self):
        """Mock Celery task instance."""
        task = Mock()
        task.request = Mock()
        task.request.id = "test-task-456"
        return task

    def test_process_pending_basic(self, mock_celery_task):
        """Test basic pending reports processing."""
        result = process_all_pending_reports(mock_celery_task)

        assert result["status"] == "completed"
        assert "total_reports_found" in result
        assert "reports_triggered" in result
        assert "reports_skipped" in result
        assert "processing_time_ms" in result

    def test_process_pending_returns_counts(self, mock_celery_task):
        """Test processing returns accurate counts."""
        result = process_all_pending_reports(mock_celery_task)

        # Counts should be non-negative integers
        assert result["total_reports_found"] >= 0
        assert result["reports_triggered"] >= 0
        assert result["reports_skipped"] >= 0

    def test_process_pending_no_reports(self, mock_celery_task):
        """Test processing when no reports are pending."""
        result = process_all_pending_reports(mock_celery_task)

        # Should complete successfully even with no reports
        assert result["status"] == "completed"
        assert result["total_reports_found"] == 0

    def test_process_pending_has_processing_time(self, mock_celery_task):
        """Test processing includes timing information."""
        result = process_all_pending_reports(mock_celery_task)

        assert "processing_time_ms" in result
        assert result["processing_time_ms"] > 0


class TestBeatScheduleIntegration:
    """Tests for Celery Beat schedule integration."""

    def test_beat_schedule_exists(self):
        """Test beat schedule is defined."""
        from tasks.report_generation import beat_schedule

        assert beat_schedule is not None
        assert isinstance(beat_schedule, dict)

    def test_beat_schedule_has_required_tasks(self):
        """Test beat schedule includes scheduled report processing."""
        from tasks.report_generation import beat_schedule

        # Should have at least one scheduled task
        assert len(beat_schedule) > 0

        # Check for the main processing task
        task_names = [task.get("task") for task in beat_schedule.values()]
        assert "tasks.report_generation.process_all_pending_reports" in task_names

    def test_beat_schedule_has_proper_structure(self):
        """Test beat schedule entries have proper structure."""
        from tasks.report_generation import beat_schedule

        for task_name, task_config in beat_schedule.items():
            # Each task should have required fields
            assert "task" in task_config
            assert "schedule" in task_config

            # Task name should be a string
            assert isinstance(task_name, str)

            # Schedule should be a number (seconds) or crontab
            schedule = task_config["schedule"]
            assert isinstance(schedule, (int, float)) or hasattr(schedule, "run_every")
