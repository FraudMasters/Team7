"""
Integration tests for backup system workflow.

This test suite validates end-to-end integration between:
- Backup operation execution
- Prometheus metrics recording
- /metrics endpoint exposure
- Email notification delivery
- Alert rule evaluation triggers
- Dashboard data availability

Test Coverage:
- Backup operation → metrics recording flow
- Metrics → /metrics endpoint → Prometheus format
- Backup failure → notification flow
- Email notification with SMTP mock
- Dashboard queries return correct data
- Alert rules trigger on conditions
- End-to-end backup workflow
"""
import pytest
import os
import time
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

import sys
sys.path.insert(0, str(__file__).parent.parent.parent)

from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from main import app
from services.backup_metrics_exporter import (
    BackupMetricsExporter,
    get_backup_metrics,
)
from services.email_notification_service import (
    EmailNotificationService,
    send_backup_notification,
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def metrics_exporter() -> BackupMetricsExporter:
    """
    Create a fresh metrics exporter for testing.

    Returns:
        BackupMetricsExporter instance with isolated registry
    """
    registry = CollectorRegistry()
    return BackupMetricsExporter(registry=registry)


class TestBackupMetricsFlow:
    """Tests for backup operation to metrics recording flow."""

    def test_backup_start_records_metrics(self, metrics_exporter):
        """Test that backup start operation records metrics."""
        # Record backup start
        metrics_exporter.record_backup_start("database")

        # Generate metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        # Verify metrics recorded
        assert 'backup_operations_total' in metrics
        assert 'backup_type="database"' in metrics
        assert 'status="started"' in metrics

    def test_backup_success_records_all_metrics(self, metrics_exporter):
        """Test that backup success records all related metrics."""
        # Record successful backup
        metrics_exporter.record_backup_success(
            backup_type="files",
            size_bytes=5120000,
            duration_seconds=45.5,
        )

        # Generate metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        # Verify all success metrics
        assert 'backup_operations_total{backup_type="files",status="success"}' in metrics
        assert 'backup_size_bytes{backup_type="files"}' in metrics
        assert 'backup_duration_seconds{backup_type="files"}' in metrics
        assert 'backup_last_success_timestamp{backup_type="files"}' in metrics

    def test_backup_failure_records_failure_metrics(self, metrics_exporter):
        """Test that backup failure records failure metrics."""
        # Record failed backup
        metrics_exporter.record_backup_failure(
            backup_type="models",
            error_type="disk_full",
            duration_seconds=5.5,
        )

        # Generate metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        # Verify failure metrics
        assert 'backup_operations_total{backup_type="models",status="failure"}' in metrics
        assert 'backup_failures_total{backup_type="models",error_type="disk_full"}' in metrics
        assert 'backup_last_failure_timestamp{backup_type="models"}' in metrics

    def test_complete_backup_workflow(self, metrics_exporter):
        """Test complete backup workflow: start → success."""
        # Start backup
        metrics_exporter.record_backup_start("full")
        start_time = time.time()

        # Simulate backup completion
        duration = time.time() - start_time
        metrics_exporter.record_backup_success(
            backup_type="full",
            size_bytes=10240000,
            duration_seconds=duration,
        )

        # Verify all metrics recorded
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        assert 'backup_operations_total' in metrics
        assert 'backup_size_bytes' in metrics
        assert 'backup_duration_seconds' in metrics
        assert 'backup_last_success_timestamp' in metrics


class TestMetricsEndpointIntegration:
    """Tests for /metrics endpoint integration."""

    def test_metrics_endpoint_returns_200(self, client):
        """Test that /metrics endpoint returns 200 status."""
        response = client.get("/metrics")

        assert response.status_code == 200

    def test_metrics_endpoint_content_type(self, client):
        """Test that /metrics endpoint returns correct content type."""
        response = client.get("/metrics")

        # Should return Prometheus content type
        assert 'text/plain' in response.headers.get('content-type', '').lower()

    def test_metrics_endpoint_contains_metric_names(self, client):
        """Test that /metrics endpoint contains backup metric names."""
        # Record some metrics first
        exporter = get_backup_metrics()
        exporter.record_backup_start("database")
        exporter.record_backup_success("database", 1000000, 5.0)

        # Get metrics from endpoint
        response = client.get("/metrics")
        metrics_text = response.text

        # Verify metric names present
        assert 'backup_operations_total' in metrics_text
        assert 'backup_size_bytes' in metrics_text
        assert 'backup_duration_seconds' in metrics_text

    def test_metrics_endpoint_prometheus_format(self, client):
        """Test that /metrics endpoint returns Prometheus text format."""
        # Record metrics
        exporter = get_backup_metrics()
        exporter.record_backup_success("database", 1000000, 5.0)

        response = client.get("/metrics")
        metrics_text = response.text

        # Verify Prometheus format markers
        assert '# TYPE' in metrics_text or 'backup_' in metrics_text

    def test_metrics_endpoint_updates_realtime(self, client):
        """Test that metrics endpoint shows real-time updates."""
        # Get initial metrics
        response1 = client.get("/metrics")
        initial_length = len(response1.text)

        # Record new operation
        exporter = get_backup_metrics()
        exporter.record_backup_start("files")

        # Get updated metrics
        response2 = client.get("/metrics")

        # Metrics should have changed
        assert len(response2.text) >= initial_length


class TestS3SyncMetricsFlow:
    """Tests for S3 sync metrics flow."""

    def test_s3_sync_start_to_success_flow(self, metrics_exporter):
        """Test S3 sync from start to success."""
        # Start sync
        metrics_exporter.record_s3_sync_start()

        # Complete sync
        metrics_exporter.record_s3_sync_success(
            bytes_uploaded=10240000,
            duration_seconds=60.5,
        )

        # Verify metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        assert 's3_sync_operations_total{status="started"}' in metrics
        assert 's3_sync_operations_total{status="success"}' in metrics
        assert 's3_sync_bytes_uploaded' in metrics
        assert 's3_sync_duration_seconds' in metrics

    def test_s3_sync_failure_flow(self, metrics_exporter):
        """Test S3 sync failure flow."""
        # Start and fail sync
        metrics_exporter.record_s3_sync_start()
        metrics_exporter.record_s3_sync_failure(error_type="auth_error")

        # Verify failure metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        assert 's3_sync_operations_total{status="started"}' in metrics
        assert 's3_sync_operations_total{status="failure"}' in metrics


class TestRestoreMetricsFlow:
    """Tests for restore operation metrics flow."""

    def test_restore_success_flow(self, metrics_exporter):
        """Test restore from start to success."""
        # Start restore
        metrics_exporter.record_restore_start("database")

        # Complete restore
        metrics_exporter.record_restore_success(
            backup_type="database",
            duration_seconds=180.5,
        )

        # Verify metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        assert 'restore_operations_total{backup_type="database",status="started"}' in metrics
        assert 'restore_operations_total{backup_type="database",status="success"}' in metrics
        assert 'restore_duration_seconds{backup_type="database"}' in metrics

    def test_restore_failure_flow(self, metrics_exporter):
        """Test restore failure flow."""
        # Start and fail restore
        metrics_exporter.record_restore_start("files")
        metrics_exporter.record_restore_failure(
            backup_type="files",
            error_type="corruption_error",
        )

        # Verify failure metrics
        metrics = metrics_exporter.generate_metrics().decode('utf-8')

        assert 'restore_operations_total{backup_type="files",status="started"}' in metrics
        assert 'restore_operations_total{backup_type="files",status="failure"}' in metrics


class TestEmailNotificationFlow:
    """Tests for email notification flow."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_backup_failure_triggers_email(self, mock_smtp):
        """Test that backup failure triggers email notification."""
        service = EmailNotificationService()

        # Send failure notification
        result = service.send_backup_failure_notification(
            operation='daily_backup',
            error_message='Disk full',
        )

        # Verify email sent
        assert result is True
        mock_smtp.assert_called_once()

        # Verify email content
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]
        message_str = str(message)

        assert 'daily_backup' in message_str
        assert 'Disk full' in message_str

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_backup_success_sends_optional_email(self, mock_smtp):
        """Test that backup success can send email (optional)."""
        service = EmailNotificationService()

        # Send success notification
        result = service.send_backup_success_notification(
            operation='manual_backup',
            backup_type='database',
            size_bytes=1024000,
            duration_seconds=45.5,
        )

        # Verify email sent
        assert result is True

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_warning_notification_flow(self, mock_smtp):
        """Test warning notification flow."""
        service = EmailNotificationService()

        result = service.send_backup_warning_notification(
            warning_type='low_disk_space',
            message='Less than 10% disk space remaining',
            context={
                'current_usage': '90%',
                'threshold': '10%',
            },
        )

        # Verify email sent
        assert result is True


class TestBackupFailureAlertFlow:
    """Tests for backup failure alert evaluation flow."""

    def test_backup_failure_increments_failure_counter(self):
        """Test that backup failure increments failure counter."""
        exporter = BackupMetricsExporter()

        # Simulate multiple failures
        exporter.record_backup_failure("database", "disk_full")
        exporter.record_backup_failure("database", "connection_error")
        exporter.record_backup_failure("files", "io_error")

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Verify failures counted
        assert 'backup_failures_total' in metrics
        assert 'error_type="disk_full"' in metrics
        assert 'error_type="connection_error"' in metrics
        assert 'error_type="io_error"' in metrics

    def test_consecutive_failures_trigger_alert(self):
        """Test that consecutive failures can be detected from metrics."""
        exporter = BackupMetricsExporter()

        # Simulate 3 consecutive failures
        for _ in range(3):
            exporter.record_backup_failure("database", "disk_full")

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Metrics should show 3 failures
        assert 'backup_failures_total{backup_type="database",error_type="disk_full"} 3.0' in metrics


class TestDashboardDataAvailability:
    """Tests for dashboard data queries."""

    def test_dashboard_can_query_backup_operations(self):
        """Test that dashboard can query backup operations metrics."""
        exporter = BackupMetricsExporter()

        # Record various backup operations
        exporter.record_backup_start("database")
        exporter.record_backup_success("database", 1000000, 10.0)
        exporter.record_backup_start("files")
        exporter.record_backup_failure("files", "disk_full", 5.0)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Dashboard should be able to query:
        # 1. Total operations by status
        assert 'backup_operations_total{backup_type="database",status="started"}' in metrics
        assert 'backup_operations_total{backup_type="database",status="success"}' in metrics
        assert 'backup_operations_total{backup_type="files",status="started"}' in metrics
        assert 'backup_operations_total{backup_type="files",status="failure"}' in metrics

    def test_dashboard_can_query_backup_sizes(self):
        """Test that dashboard can query backup size metrics."""
        exporter = BackupMetricsExporter()

        # Record backups with different sizes
        exporter.record_backup_success("database", 1000000, 10.0)
        exporter.record_backup_success("files", 5000000, 30.0)
        exporter.record_backup_success("models", 200000, 5.0)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Dashboard should see sizes for each type
        assert 'backup_size_bytes{backup_type="database"}' in metrics
        assert 'backup_size_bytes{backup_type="files"}' in metrics
        assert 'backup_size_bytes{backup_type="models"}' in metrics

    def test_dashboard_can_query_last_backup_timestamps(self):
        """Test that dashboard can query last backup timestamps."""
        exporter = BackupMetricsExporter()

        # Record successful backup
        exporter.record_backup_success("database", 1000000, 10.0)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Dashboard should see last success timestamp
        assert 'backup_last_success_timestamp{backup_type="database"}' in metrics

    def test_dashboard_can_query_disk_usage(self):
        """Test that dashboard can query disk usage metrics."""
        exporter = BackupMetricsExporter()

        # Set disk usage
        exporter.set_disk_usage_metrics(
            used_bytes=100000000000,
            free_bytes=500000000000,
            total_bytes=600000000000,
        )

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Dashboard should see disk usage
        assert 'backup_disk_usage_bytes{type="used"}' in metrics
        assert 'backup_disk_usage_bytes{type="free"}' in metrics
        assert 'backup_disk_usage_bytes{type="total"}' in metrics


class TestRetentionMetricsFlow:
    """Tests for backup retention metrics flow."""

    def test_retention_metrics_update(self):
        """Test that retention metrics can be updated."""
        exporter = BackupMetricsExporter()

        # Set retention metrics
        exporter.set_backup_retention_metrics(
            backup_type="database",
            count=30,
            total_size_bytes=30000000000,
        )

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Verify retention metrics
        assert 'backup_retention_count{backup_type="database"} 30.0' in metrics
        assert 'backup_retention_size_bytes{backup_type="database"} 3.0e+10' in metrics

    def test_multiple_backup_types_retention(self):
        """Test retention metrics for multiple backup types."""
        exporter = BackupMetricsExporter()

        # Set retention for different types
        exporter.set_backup_retention_metrics("database", 30, 30000000000)
        exporter.set_backup_retention_metrics("files", 15, 15000000000)
        exporter.set_backup_retention_metrics("models", 7, 7000000000)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # All types should be present
        assert 'backup_type="database"' in metrics
        assert 'backup_type="files"' in metrics
        assert 'backup_type="models"' in metrics


class TestIntegrityCheckFlow:
    """Tests for integrity check flow."""

    def test_integrity_check_pass_records_metrics(self):
        """Test that passing integrity check is recorded."""
        exporter = BackupMetricsExporter()

        exporter.record_integrity_check(result="pass")

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Verify check recorded
        assert 'backup_integrity_checks_total{result="pass"} 1.0' in metrics

    def test_integrity_check_fail_records_metrics(self):
        """Test that failing integrity check is recorded."""
        exporter = BackupMetricsExporter()

        exporter.record_integrity_check(result="fail")

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Verify check recorded
        assert 'backup_integrity_checks_total{result="fail"} 1.0' in metrics

    def test_multiple_integrity_checks(self):
        """Test multiple integrity checks over time."""
        exporter = BackupMetricsExporter()

        # Simulate multiple checks
        exporter.record_integrity_check("pass")
        exporter.record_integrity_check("pass")
        exporter.record_integrity_check("fail")
        exporter.record_integrity_check("pass")

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Verify counts
        assert 'backup_integrity_checks_total{result="pass"} 3.0' in metrics
        assert 'backup_integrity_checks_total{result="fail"} 1.0' in metrics


class TestEndToEndBackupWorkflow:
    """Tests for complete end-to-end backup workflows."""

    def test_successful_backup_workflow(self):
        """Test complete successful backup workflow."""
        exporter = BackupMetricsExporter()

        # 1. Start backup
        exporter.record_backup_start("full")

        # 2. Complete backup
        exporter.record_backup_success("full", 10240000, 120.5)

        # 3. Set retention metrics
        exporter.set_backup_retention_metrics("full", 1, 10240000)

        # 4. Record integrity check
        exporter.record_integrity_check("pass")

        # 5. Sync to S3
        exporter.record_s3_sync_start()
        exporter.record_s3_sync_success(10240000, 60.0)

        # Verify all metrics recorded
        metrics = exporter.generate_metrics().decode('utf-8')

        assert 'backup_operations_total' in metrics
        assert 'backup_size_bytes' in metrics
        assert 'backup_retention_count' in metrics
        assert 'backup_integrity_checks_total' in metrics
        assert 's3_sync_operations_total' in metrics

    def test_failed_backup_workflow(self):
        """Test complete failed backup workflow."""
        exporter = BackupMetricsExporter()

        # 1. Start backup
        exporter.record_backup_start("database")

        # 2. Fail backup
        exporter.record_backup_failure("database", "disk_full", 10.5)

        # Verify failure metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        assert 'backup_operations_total{backup_type="database",status="started"}' in metrics
        assert 'backup_operations_total{backup_type="database",status="failure"}' in metrics
        assert 'backup_failures_total{backup_type="database",error_type="disk_full"}' in metrics
        assert 'backup_last_failure_timestamp{backup_type="database"}' in metrics

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_failed_backup_with_notification_workflow(self, mock_smtp):
        """Test failed backup workflow with email notification."""
        # 1. Record metrics
        exporter = BackupMetricsExporter()
        exporter.record_backup_start("files")
        exporter.record_backup_failure("files", "io_error", 15.0)

        # 2. Send notification
        notification_sent = send_backup_notification(
            'failure',
            operation='daily_backup',
            error_message='IO error writing backup',
        )

        # Verify workflow completed
        assert notification_sent is True
        mock_smtp.assert_called_once()


class TestMetricsIsolation:
    """Tests for metrics isolation between operations."""

    def test_different_backup_types_separate_metrics(self):
        """Test that different backup types have separate metrics."""
        exporter = BackupMetricsExporter()

        # Record different backup types
        exporter.record_backup_success("database", 1000000, 10.0)
        exporter.record_backup_success("files", 5000000, 30.0)
        exporter.record_backup_success("models", 200000, 5.0)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Each type should have separate metrics
        assert 'backup_type="database"' in metrics
        assert 'backup_type="files"' in metrics
        assert 'backup_type="models"' in metrics

    def test_operations_and_restores_separate(self):
        """Test that backup and restore operations have separate metrics."""
        exporter = BackupMetricsExporter()

        # Record backup and restore
        exporter.record_backup_success("database", 1000000, 10.0)
        exporter.record_restore_success("database", 60.0)

        # Generate metrics
        metrics = exporter.generate_metrics().decode('utf-8')

        # Should have both backup and restore metrics
        assert 'backup_operations_total' in metrics
        assert 'restore_operations_total' in metrics
