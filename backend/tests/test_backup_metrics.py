"""
Unit tests for BackupMetricsExporter.

Tests cover Prometheus metrics initialization, metric recording,
singleton pattern, and metrics generation for backup system monitoring.

Test Coverage:
- BackupMetricsExporter initialization and singleton pattern
- All 15 Prometheus metrics (counters, gauges, histograms, summaries)
- Metric recording functions for backup operations
- S3 sync metrics recording
- Restore operation metrics
- Disk usage and retention metrics
- Integrity check metrics
- Metrics generation in Prometheus format
"""
import pytest
import time
from unittest.mock import Mock, patch
from prometheus_client import CollectorRegistry

from services.backup_metrics_exporter import (
    BackupMetricsExporter,
    get_backup_metrics,
    generate_backup_metrics,
)


class TestBackupMetricsExporterInit:
    """Tests for BackupMetricsExporter initialization."""

    def test_default_initialization(self):
        """Test initialization with default registry."""
        exporter = BackupMetricsExporter()

        assert exporter is not None
        assert exporter._registry is not None

    def test_custom_registry(self):
        """Test initialization with custom registry."""
        custom_registry = CollectorRegistry()
        exporter = BackupMetricsExporter(registry=custom_registry)

        assert exporter._registry is custom_registry

    def test_all_metrics_registered(self):
        """Verify all 15 Prometheus metrics are registered."""
        exporter = BackupMetricsExporter()

        # Check all metric attributes exist
        assert hasattr(exporter, '_backup_operations_total')
        assert hasattr(exporter, '_backup_failures_total')
        assert hasattr(exporter, '_backup_size_bytes')
        assert hasattr(exporter, '_backup_duration_seconds')
        assert hasattr(exporter, '_backup_last_success_timestamp')
        assert hasattr(exporter, '_backup_last_failure_timestamp')
        assert hasattr(exporter, '_s3_sync_operations_total')
        assert hasattr(exporter, '_s3_sync_duration_seconds')
        assert hasattr(exporter, '_s3_sync_bytes_uploaded')
        assert hasattr(exporter, '_backup_retention_count')
        assert hasattr(exporter, '_backup_retention_size_bytes')
        assert hasattr(exporter, '_backup_disk_usage_bytes')
        assert hasattr(exporter, '_backup_integrity_checks_total')
        assert hasattr(exporter, '_restore_operations_total')
        assert hasattr(exporter, '_restore_duration_seconds')


class TestSingletonPattern:
    """Tests for singleton pattern implementation."""

    def test_get_backup_metrics_returns_singleton(self):
        """Test that get_backup_metrics returns the same instance."""
        exporter1 = get_backup_metrics()
        exporter2 = get_backup_metrics()

        assert exporter1 is exporter2

    def test_multiple_creates_return_different_instances(self):
        """Test that direct instantiation creates different instances."""
        exporter1 = BackupMetricsExporter()
        exporter2 = BackupMetricsExporter()

        # Different instances (not singleton when created directly)
        assert exporter1 is not exporter2

    def test_get_backup_metrics_same_type(self):
        """Test that get_backup_metrics returns correct type."""
        exporter = get_backup_metrics()

        assert isinstance(exporter, BackupMetricsExporter)


class TestBackupOperationMetrics:
    """Tests for backup operation metrics recording."""

    def test_record_backup_start_increments_counter(self):
        """Test that record_backup_start increments operations counter."""
        exporter = BackupMetricsExporter()

        # Record backup start
        exporter.record_backup_start("database")

        # Generate metrics and check
        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'backup_operations_total' in metrics_output
        assert 'backup_type="database"' in metrics_output
        assert 'status="started"' in metrics_output

    def test_record_backup_success_sets_metrics(self):
        """Test that record_backup_success sets all success metrics."""
        exporter = BackupMetricsExporter()

        # Record successful backup
        exporter.record_backup_success(
            backup_type="files",
            size_bytes=1024000,
            duration_seconds=5.5,
        )

        # Generate metrics and check
        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check operations counter
        assert 'backup_operations_total' in metrics_output
        assert 'backup_type="files"' in metrics_output
        assert 'status="success"' in metrics_output

        # Check size gauge
        assert 'backup_size_bytes' in metrics_output
        assert 'backup_type="files"' in metrics_output

        # Check duration histogram
        assert 'backup_duration_seconds' in metrics_output
        assert 'backup_type="files"' in metrics_output

        # Check timestamp gauge
        assert 'backup_last_success_timestamp' in metrics_output

    def test_record_backup_failure_sets_metrics(self):
        """Test that record_backup_failure sets failure metrics."""
        exporter = BackupMetricsExporter()

        # Record failed backup
        exporter.record_backup_failure(
            backup_type="models",
            error_type="disk_full",
            duration_seconds=2.5,
        )

        # Generate metrics and check
        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check operations counter
        assert 'backup_operations_total' in metrics_output
        assert 'backup_type="models"' in metrics_output
        assert 'status="failure"' in metrics_output

        # Check failures counter
        assert 'backup_failures_total' in metrics_output
        assert 'backup_type="models"' in metrics_output
        assert 'error_type="disk_full"' in metrics_output

        # Check timestamp gauge
        assert 'backup_last_failure_timestamp' in metrics_output

    def test_record_backup_failure_without_duration(self):
        """Test record_backup_failure with no duration."""
        exporter = BackupMetricsExporter()

        # Record failed backup without duration
        exporter.record_backup_failure(
            backup_type="database",
            error_type="connection_error",
        )

        # Should still record failure metrics
        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'backup_failures_total' in metrics_output

    def test_multiple_backup_operations(self):
        """Test recording multiple backup operations."""
        exporter = BackupMetricsExporter()

        # Record multiple operations
        exporter.record_backup_start("database")
        exporter.record_backup_success("database", 1000000, 10.0)
        exporter.record_backup_start("files")
        exporter.record_backup_failure("files", "disk_full", 5.0)

        # All should be in metrics
        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'backup_operations_total' in metrics_output


class TestS3SyncMetrics:
    """Tests for S3 sync operation metrics."""

    def test_record_s3_sync_start(self):
        """Test recording S3 sync start."""
        exporter = BackupMetricsExporter()

        exporter.record_s3_sync_start()

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 's3_sync_operations_total' in metrics_output
        assert 'status="started"' in metrics_output

    def test_record_s3_sync_success(self):
        """Test recording successful S3 sync."""
        exporter = BackupMetricsExporter()

        exporter.record_s3_sync_success(
            bytes_uploaded=5120000,
            duration_seconds=45.5,
        )

        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check operations counter
        assert 's3_sync_operations_total' in metrics_output
        assert 'status="success"' in metrics_output

        # Check bytes uploaded gauge
        assert 's3_sync_bytes_uploaded' in metrics_output

        # Check duration summary
        assert 's3_sync_duration_seconds' in metrics_output

    def test_record_s3_sync_failure(self):
        """Test recording failed S3 sync."""
        exporter = BackupMetricsExporter()

        exporter.record_s3_sync_failure(error_type="auth_error")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 's3_sync_operations_total' in metrics_output
        assert 'status="failure"' in metrics_output


class TestRetentionMetrics:
    """Tests for backup retention metrics."""

    def test_set_backup_retention_metrics(self):
        """Test setting backup retention metrics."""
        exporter = BackupMetricsExporter()

        exporter.set_backup_retention_metrics(
            backup_type="database",
            count=30,
            total_size_bytes=51200000000,
        )

        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check count gauge
        assert 'backup_retention_count' in metrics_output
        assert 'backup_type="database"' in metrics_output

        # Check size gauge
        assert 'backup_retention_size_bytes' in metrics_output

    def test_set_disk_usage_metrics(self):
        """Test setting disk usage metrics."""
        exporter = BackupMetricsExporter()

        exporter.set_disk_usage_metrics(
            used_bytes=100000000000,
            free_bytes=500000000000,
            total_bytes=600000000000,
        )

        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check all three disk usage gauges
        assert 'backup_disk_usage_bytes' in metrics_output
        assert 'type="used"' in metrics_output
        assert 'type="free"' in metrics_output
        assert 'type="total"' in metrics_output


class TestIntegrityCheckMetrics:
    """Tests for backup integrity check metrics."""

    def test_record_integrity_check_pass(self):
        """Test recording passing integrity check."""
        exporter = BackupMetricsExporter()

        exporter.record_integrity_check(result="pass")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'backup_integrity_checks_total' in metrics_output
        assert 'result="pass"' in metrics_output

    def test_record_integrity_check_fail(self):
        """Test recording failing integrity check."""
        exporter = BackupMetricsExporter()

        exporter.record_integrity_check(result="fail")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'backup_integrity_checks_total' in metrics_output
        assert 'result="fail"' in metrics_output


class TestRestoreOperationMetrics:
    """Tests for restore operation metrics."""

    def test_record_restore_start(self):
        """Test recording restore start."""
        exporter = BackupMetricsExporter()

        exporter.record_restore_start(backup_type="database")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'restore_operations_total' in metrics_output
        assert 'backup_type="database"' in metrics_output
        assert 'status="started"' in metrics_output

    def test_record_restore_success(self):
        """Test recording successful restore."""
        exporter = BackupMetricsExporter()

        exporter.record_restore_success(
            backup_type="files",
            duration_seconds=120.5,
        )

        metrics_output = exporter.generate_metrics().decode('utf-8')

        # Check operations counter
        assert 'restore_operations_total' in metrics_output
        assert 'backup_type="files"' in metrics_output
        assert 'status="success"' in metrics_output

        # Check duration histogram
        assert 'restore_duration_seconds' in metrics_output

    def test_record_restore_failure(self):
        """Test recording failed restore."""
        exporter = BackupMetricsExporter()

        exporter.record_restore_failure(
            backup_type="models",
            error_type="corruption_error",
        )

        metrics_output = exporter.generate_metrics().decode('utf-8')
        assert 'restore_operations_total' in metrics_output
        assert 'backup_type="models"' in metrics_output
        assert 'status="failure"' in metrics_output


class TestMetricsGeneration:
    """Tests for metrics generation and formatting."""

    def test_generate_metrics_returns_bytes(self):
        """Test that generate_metrics returns bytes."""
        exporter = BackupMetricsExporter()

        metrics = exporter.generate_metrics()

        assert isinstance(metrics, bytes)
        assert len(metrics) > 0

    def test_generate_metrics_contains_metric_names(self):
        """Test that generated metrics contain expected metric names."""
        exporter = BackupMetricsExporter()

        # Record some operations
        exporter.record_backup_start("database")
        exporter.record_backup_success("database", 1000000, 5.0)

        metrics = exporter.generate_metrics().decode('utf-8')

        # Check for key metric names
        assert 'backup_operations_total' in metrics
        assert 'backup_size_bytes' in metrics
        assert 'backup_duration_seconds' in metrics

    def test_get_content_type(self):
        """Test get_content_type returns correct content type."""
        exporter = BackupMetricsExporter()

        content_type = exporter.get_content_type()

        # Should return Prometheus content type
        assert content_type is not None
        assert 'text/plain' in content_type or 'prometheus' in content_type.lower()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_backup_metrics_returns_bytes(self):
        """Test generate_backup_metrics convenience function."""
        metrics = generate_backup_metrics()

        assert isinstance(metrics, bytes)
        assert len(metrics) > 0

    def test_generate_backup_metrics_uses_singleton(self):
        """Test that generate_backup_metrics uses singleton instance."""
        # Get singleton first
        exporter1 = get_backup_metrics()
        exporter1.record_backup_success("database", 1000000, 5.0)

        # Generate metrics
        metrics = generate_backup_metrics().decode('utf-8')

        # Should contain the recorded operation
        assert 'backup_operations_total' in metrics


class TestMetricsLabelsAndTypes:
    """Tests for metric labels and types."""

    def test_backup_operations_counter_labels(self):
        """Test backup_operations_total has correct labels."""
        exporter = BackupMetricsExporter()

        exporter.record_backup_start("full")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        # Check labels exist
        assert 'backup_type=' in metrics_output
        assert 'status=' in metrics_output

    def test_backup_failures_counter_labels(self):
        """Test backup_failures_total has correct labels."""
        exporter = BackupMetricsExporter()

        exporter.record_backup_failure("database", "disk_full")

        metrics_output = exporter.generate_metrics().decode('utf-8')
        # Check labels exist
        assert 'backup_type=' in metrics_output
        assert 'error_type=' in metrics_output

    def test_all_backup_types_supported(self):
        """Test that all backup types are supported."""
        exporter = BackupMetricsExporter()

        backup_types = ["database", "files", "models", "full"]

        for backup_type in backup_types:
            exporter.record_backup_start(backup_type)
            exporter.record_backup_success(backup_type, 1000000, 10.0)

        metrics_output = exporter.generate_metrics().decode('utf-8')

        # All backup types should be in metrics
        for backup_type in backup_types:
            assert f'backup_type="{backup_type}"' in metrics_output


class TestMetricsResetBetweenTests:
    """Tests to ensure metrics don't leak between test instances."""

    def test_separate_exporters_have_separate_metrics(self):
        """Test that separate exporter instances have separate metrics."""
        registry1 = CollectorRegistry()
        registry2 = CollectorRegistry()

        exporter1 = BackupMetricsExporter(registry=registry1)
        exporter2 = BackupMetricsExporter(registry=registry2)

        exporter1.record_backup_start("database")
        exporter2.record_backup_start("files")

        metrics1 = exporter1.generate_metrics().decode('utf-8')
        metrics2 = exporter2.generate_metrics().decode('utf-8')

        # exporter1 should have database, not files
        assert 'backup_type="database"' in metrics1
        assert 'backup_type="files"' not in metrics1

        # exporter2 should have files, not database
        assert 'backup_type="files"' in metrics2
        assert 'backup_type="database"' not in metrics2
