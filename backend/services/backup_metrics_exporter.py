"""
Prometheus metrics exporter for backup system monitoring

This module provides Prometheus metrics for the backup system including:
- Backup operation counters (success, failure, total)
- Backup size gauges by type
- Backup duration metrics
- Last backup timestamps
- S3 sync status metrics
- Disk usage metrics

Metrics are exposed on the /metrics endpoint for Prometheus scraping.
"""
import logging
import time
from datetime import datetime
from typing import Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logger = logging.getLogger(__name__)


class BackupMetricsExporter:
    """
    Prometheus metrics exporter for backup system.

    Tracks backup operations, sizes, durations, and system health.
    Thread-safe singleton instance accessible via get_backup_metrics().

    Example:
        >>> metrics = get_backup_metrics()
        >>> metrics.record_backup_start("database")
        >>> metrics.record_backup_success("database", 1024000, 5.2)
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize backup metrics exporter.

        Args:
            registry: Optional Prometheus registry (uses default if not provided)
        """
        self._registry = registry or CollectorRegistry()

        # Backup operation counters
        self._backup_operations_total = Counter(
            'backup_operations_total',
            'Total number of backup operations',
            ['backup_type', 'status'],
            registry=self._registry,
        )

        self._backup_failures_total = Counter(
            'backup_failures_total',
            'Total number of backup failures',
            ['backup_type', 'error_type'],
            registry=self._registry,
        )

        # Backup size gauges
        self._backup_size_bytes = Gauge(
            'backup_size_bytes',
            'Size of last backup in bytes',
            ['backup_type'],
            registry=self._registry,
        )

        self._backup_duration_seconds = Histogram(
            'backup_duration_seconds',
            'Backup operation duration in seconds',
            ['backup_type'],
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, float('inf')),
            registry=self._registry,
        )

        # Last backup timestamps (as Unix timestamp)
        self._backup_last_success_timestamp = Gauge(
            'backup_last_success_timestamp',
            'Unix timestamp of last successful backup',
            ['backup_type'],
            registry=self._registry,
        )

        self._backup_last_failure_timestamp = Gauge(
            'backup_last_failure_timestamp',
            'Unix timestamp of last failed backup',
            ['backup_type'],
            registry=self._registry,
        )

        # S3 sync metrics
        self._s3_sync_operations_total = Counter(
            's3_sync_operations_total',
            'Total number of S3 sync operations',
            ['status'],
            registry=self._registry,
        )

        self._s3_sync_duration_seconds = Summary(
            's3_sync_duration_seconds',
            'S3 sync operation duration in seconds',
            registry=self._registry,
        )

        self._s3_sync_bytes_uploaded = Gauge(
            's3_sync_bytes_uploaded',
            'Total bytes uploaded to S3 in last sync',
            registry=self._registry,
        )

        # Backup retention metrics
        self._backup_retention_count = Gauge(
            'backup_retention_count',
            'Number of backups currently retained',
            ['backup_type'],
            registry=self._registry,
        )

        self._backup_retention_size_bytes = Gauge(
            'backup_retention_size_bytes',
            'Total size of retained backups in bytes',
            ['backup_type'],
            registry=self._registry,
        )

        # System health metrics
        self._backup_disk_usage_bytes = Gauge(
            'backup_disk_usage_bytes',
            'Disk usage for backup directory in bytes',
            ['type'],  # 'used', 'free', 'total'
            registry=self._registry,
        )

        self._backup_integrity_checks_total = Counter(
            'backup_integrity_checks_total',
            'Total number of backup integrity checks',
            ['result'],
            registry=self._registry,
        )

        # Restore operation metrics
        self._restore_operations_total = Counter(
            'restore_operations_total',
            'Total number of restore operations',
            ['backup_type', 'status'],
            registry=self._registry,
        )

        self._restore_duration_seconds = Histogram(
            'restore_duration_seconds',
            'Restore operation duration in seconds',
            ['backup_type'],
            buckets=(10.0, 60.0, 300.0, 1800.0, 3600.0, float('inf')),
            registry=self._registry,
        )

        logger.info("Backup metrics exporter initialized")

    def record_backup_start(self, backup_type: str) -> None:
        """
        Record the start of a backup operation.

        Args:
            backup_type: Type of backup (database, files, models, full)
        """
        logger.debug(f"Recording backup start: {backup_type}")
        self._backup_operations_total.labels(
            backup_type=backup_type,
            status='started',
        ).inc()

    def record_backup_success(
        self,
        backup_type: str,
        size_bytes: int,
        duration_seconds: float,
    ) -> None:
        """
        Record a successful backup operation.

        Args:
            backup_type: Type of backup (database, files, models, full)
            size_bytes: Size of the backup in bytes
            duration_seconds: Duration of the backup operation
        """
        logger.info(
            f"Recording backup success: {backup_type}, "
            f"size={size_bytes}, duration={duration_seconds:.2f}s"
        )

        self._backup_operations_total.labels(
            backup_type=backup_type,
            status='success',
        ).inc()

        self._backup_size_bytes.labels(backup_type=backup_type).set(size_bytes)
        self._backup_duration_seconds.labels(backup_type=backup_type).observe(duration_seconds)
        self._backup_last_success_timestamp.labels(
            backup_type=backup_type
        ).set(time.time())

    def record_backup_failure(
        self,
        backup_type: str,
        error_type: str,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """
        Record a failed backup operation.

        Args:
            backup_type: Type of backup (database, files, models, full)
            error_type: Type of error (e.g., 'disk_full', 'database_error', 's3_error')
            duration_seconds: Optional duration before failure
        """
        logger.warning(
            f"Recording backup failure: {backup_type}, error={error_type}"
        )

        self._backup_operations_total.labels(
            backup_type=backup_type,
            status='failure',
        ).inc()

        self._backup_failures_total.labels(
            backup_type=backup_type,
            error_type=error_type,
        ).inc()

        self._backup_last_failure_timestamp.labels(
            backup_type=backup_type
        ).set(time.time())

        if duration_seconds is not None:
            self._backup_duration_seconds.labels(
                backup_type=backup_type
            ).observe(duration_seconds)

    def record_s3_sync_start(self) -> None:
        """Record the start of an S3 sync operation."""
        logger.debug("Recording S3 sync start")
        self._s3_sync_operations_total.labels(status='started').inc()

    def record_s3_sync_success(
        self,
        bytes_uploaded: int,
        duration_seconds: float,
    ) -> None:
        """
        Record a successful S3 sync operation.

        Args:
            bytes_uploaded: Total bytes uploaded to S3
            duration_seconds: Duration of the sync operation
        """
        logger.info(
            f"Recording S3 sync success: {bytes_uploaded} bytes, "
            f"{duration_seconds:.2f}s"
        )

        self._s3_sync_operations_total.labels(status='success').inc()
        self._s3_sync_bytes_uploaded.set(bytes_uploaded)
        self._s3_sync_duration_seconds.observe(duration_seconds)

    def record_s3_sync_failure(self, error_type: str) -> None:
        """
        Record a failed S3 sync operation.

        Args:
            error_type: Type of error (e.g., 'auth_error', 'network_error')
        """
        logger.warning(f"Recording S3 sync failure: {error_type}")
        self._s3_sync_operations_total.labels(
            status='failure',
        ).inc()

    def set_backup_retention_metrics(
        self,
        backup_type: str,
        count: int,
        total_size_bytes: int,
    ) -> None:
        """
        Update backup retention metrics.

        Args:
            backup_type: Type of backup (database, files, models, full)
            count: Number of backups retained
            total_size_bytes: Total size of all retained backups
        """
        logger.debug(
            f"Setting retention metrics for {backup_type}: "
            f"{count} backups, {total_size_bytes} bytes"
        )

        self._backup_retention_count.labels(backup_type=backup_type).set(count)
        self._backup_retention_size_bytes.labels(
            backup_type=backup_type
        ).set(total_size_bytes)

    def set_disk_usage_metrics(
        self,
        used_bytes: int,
        free_bytes: int,
        total_bytes: int,
    ) -> None:
        """
        Update disk usage metrics for backup directory.

        Args:
            used_bytes: Used disk space in bytes
            free_bytes: Free disk space in bytes
            total_bytes: Total disk capacity in bytes
        """
        logger.debug(
            f"Setting disk usage: used={used_bytes}, free={free_bytes}, total={total_bytes}"
        )

        self._backup_disk_usage_bytes.labels(type='used').set(used_bytes)
        self._backup_disk_usage_bytes.labels(type='free').set(free_bytes)
        self._backup_disk_usage_bytes.labels(type='total').set(total_bytes)

    def record_integrity_check(
        self,
        result: str,  # 'pass' or 'fail'
    ) -> None:
        """
        Record a backup integrity check result.

        Args:
            result: Result of integrity check ('pass' or 'fail')
        """
        logger.debug(f"Recording integrity check: {result}")
        self._backup_integrity_checks_total.labels(result=result).inc()

    def record_restore_start(self, backup_type: str) -> None:
        """
        Record the start of a restore operation.

        Args:
            backup_type: Type of restore (database, files, models, full)
        """
        logger.debug(f"Recording restore start: {backup_type}")
        self._restore_operations_total.labels(
            backup_type=backup_type,
            status='started',
        ).inc()

    def record_restore_success(
        self,
        backup_type: str,
        duration_seconds: float,
    ) -> None:
        """
        Record a successful restore operation.

        Args:
            backup_type: Type of restore (database, files, models, full)
            duration_seconds: Duration of the restore operation
        """
        logger.info(
            f"Recording restore success: {backup_type}, {duration_seconds:.2f}s"
        )

        self._restore_operations_total.labels(
            backup_type=backup_type,
            status='success',
        ).inc()

        self._restore_duration_seconds.labels(
            backup_type=backup_type
        ).observe(duration_seconds)

    def record_restore_failure(
        self,
        backup_type: str,
        error_type: str,
    ) -> None:
        """
        Record a failed restore operation.

        Args:
            backup_type: Type of restore (database, files, models, full)
            error_type: Type of error
        """
        logger.warning(
            f"Recording restore failure: {backup_type}, error={error_type}"
        )

        self._restore_operations_total.labels(
            backup_type=backup_type,
            status='failure',
        ).inc()

    def generate_metrics(self) -> bytes:
        """
        Generate Prometheus metrics text format.

        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self._registry)

    def get_content_type(self) -> str:
        """
        Get the content type for metrics endpoint.

        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST


# Singleton instance
_backup_metrics_instance: Optional[BackupMetricsExporter] = None


def get_backup_metrics() -> BackupMetricsExporter:
    """
    Get the singleton backup metrics exporter instance.

    Returns:
        BackupMetricsExporter instance
    """
    global _backup_metrics_instance
    if _backup_metrics_instance is None:
        _backup_metrics_instance = BackupMetricsExporter()
    return _backup_metrics_instance


def generate_backup_metrics() -> bytes:
    """
    Generate Prometheus metrics for backup system.

    Convenience function that returns metrics in Prometheus text format.

    Returns:
        Metrics in Prometheus text format
    """
    return get_backup_metrics().generate_metrics()


__all__ = [
    "BackupMetricsExporter",
    "get_backup_metrics",
    "generate_backup_metrics",
]
