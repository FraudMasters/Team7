"""
Backup service for automated database, files, and models backup

This module provides comprehensive backup functionality including:
- PostgreSQL database dumps using pg_dump
- File system backups (resumes, models)
- Incremental backups using rsync
- Checksum calculation for integrity verification
- S3-compatible off-site storage
- Restore functionality
- Retention policy management
- Prometheus metrics export for monitoring
- Email notifications for failures and warnings
"""
import asyncio
import bz2
import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Import monitoring and notification services
try:
    from services.backup_metrics_exporter import get_backup_metrics
    METRICS_AVAILABLE = True
except ImportError:
    logger.warning("BackupMetricsExporter not available, metrics will be disabled")
    METRICS_AVAILABLE = False

try:
    from services.email_notification_service import send_backup_notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    logger.warning("Email notification service not available, notifications will be disabled")
    NOTIFICATIONS_AVAILABLE = False


# Backup directory structure
BACKUP_BASE_DIR = Path("./data/backups")
DATABASE_BACKUP_DIR = BACKUP_BASE_DIR / "database"
FILES_BACKUP_DIR = BACKUP_BASE_DIR / "files"
MODELS_BACKUP_DIR = BACKUP_BASE_DIR / "models"
FULL_BACKUP_DIR = BACKUP_BASE_DIR / "full"
TEMP_BACKUP_DIR = BACKUP_BASE_DIR / "temp"

# Source directories
UPLOADS_SOURCE_DIR = Path("./data/uploads")
MODELS_SOURCE_DIR = settings.models_cache_path


def ensure_backup_dirs() -> None:
    """Ensure all backup directories exist"""
    for directory in [
        BACKUP_BASE_DIR,
        DATABASE_BACKUP_DIR,
        FILES_BACKUP_DIR,
        MODELS_BACKUP_DIR,
        FULL_BACKUP_DIR,
        TEMP_BACKUP_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured backup directory exists: {directory}")


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate checksum of a file for integrity verification.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def calculate_directory_checksum(directory: Path) -> str:
    """
    Calculate checksum of all files in a directory.

    Args:
        directory: Path to the directory

    Returns:
        Combined checksum of all files
    """
    hash_func = hashlib.sha256()
    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file():
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_func.update(chunk)
    return hash_func.hexdigest()


def format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def parse_database_url(db_url: str) -> Dict[str, str]:
    """
    Parse PostgreSQL database URL into components.

    Args:
        db_url: Database connection URL

    Returns:
        Dictionary with connection components
    """
    # Remove protocol prefix
    url = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")

    # Split user:password@host:port/database
    if "@" in url:
        auth_part, rest = url.split("@", 1)
        user_password = auth_part.split(":")
        user = user_password[0]
        password = user_password[1] if len(user_password) > 1 else ""

        # Split host:port/database
        if "/" in rest:
            host_port, database = rest.split("/", 1)
            host_port_parts = host_port.split(":")
            host = host_port_parts[0]
            port = host_port_parts[1] if len(host_port_parts) > 1 else "5432"
        else:
            host = rest
            port = "5432"
            database = "postgres"
    else:
        # Fallback to settings for database connection
        parsed = urlparse(settings.database_url)
        user = parsed.username or "postgres"
        password = parsed.password or ""
        host = parsed.hostname or ""
        port = str(parsed.port) if parsed.port else "5432"
        database = url.split("/")[-1] if "/" in url else "postgres"

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }


class BackupService:
    """
    Service for managing backup and restore operations.

    This service handles creating backups of the database, uploaded files,
    and ML model cache, with support for incremental backups, integrity
    verification, and S3 off-site storage.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        backup_dir: Optional[Path] = None,
        s3_config: Optional[Dict[str, Any]] = None,
        enable_notifications: bool = True,
        enable_metrics: bool = True,
    ):
        """
        Initialize the backup service.

        Args:
            db_url: Database connection URL (uses settings if not provided)
            backup_dir: Base backup directory (uses default if not provided)
            s3_config: S3 configuration dict with keys: enabled, bucket, endpoint,
                       access_key, secret_key, region
            enable_notifications: Enable email notifications for failures/warnings
            enable_metrics: Enable Prometheus metrics recording
        """
        self.db_url = db_url or settings.database_url
        self.backup_dir = backup_dir or BACKUP_BASE_DIR
        self.s3_config = s3_config or {}
        self.db_params = parse_database_url(self.db_url)
        self.enable_notifications = enable_notifications
        self.enable_metrics = enable_metrics

        ensure_backup_dirs()

        # Set PGPASSWORD for pg_dump
        if self.db_params.get("password"):
            os.environ["PGPASSWORD"] = self.db_params["password"]

        # Initialize metrics exporter if available and enabled
        self.metrics = None
        if METRICS_AVAILABLE and self.enable_metrics:
            try:
                self.metrics = get_backup_metrics()
                logger.info("Backup metrics exporter initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize metrics exporter: {e}")

        # Get notification email from settings
        self.notification_email = getattr(settings, 'backup_notification_email', None)

    def _record_metric_start(self, backup_type: str) -> None:
        """Record backup operation start metric."""
        if self.metrics:
            try:
                self.metrics.record_backup_start(backup_type)
            except Exception as e:
                logger.warning(f"Failed to record start metric for {backup_type}: {e}")

    def _record_metric_success(
        self,
        backup_type: str,
        size_bytes: int,
        duration_seconds: float
    ) -> None:
        """Record successful backup metric."""
        if self.metrics:
            try:
                self.metrics.record_backup_success(backup_type, size_bytes, duration_seconds)
            except Exception as e:
                logger.warning(f"Failed to record success metric for {backup_type}: {e}")

    def _record_metric_failure(
        self,
        backup_type: str,
        error_type: str,
        duration_seconds: Optional[float] = None
    ) -> None:
        """Record failed backup metric."""
        if self.metrics:
            try:
                self.metrics.record_backup_failure(backup_type, error_type, duration_seconds)
            except Exception as e:
                logger.warning(f"Failed to record failure metric for {backup_type}: {e}")

    def _send_failure_notification(
        self,
        operation: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send failure notification email."""
        if not self.enable_notifications or not self.notification_email:
            return

        if NOTIFICATIONS_AVAILABLE:
            try:
                send_backup_notification(
                    notification_type='failure',
                    operation=operation,
                    error_message=error_message,
                    context=context or {},
                )
                logger.info(f"Failure notification sent for {operation}")
            except Exception as e:
                logger.warning(f"Failed to send failure notification: {e}")

    def _send_warning_notification(
        self,
        warning_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send warning notification email."""
        if not self.enable_notifications or not self.notification_email:
            return

        if NOTIFICATIONS_AVAILABLE:
            try:
                send_backup_notification(
                    notification_type='warning',
                    warning_type=warning_type,
                    message=message,
                    context=context or {},
                )
                logger.info(f"Warning notification sent: {warning_type}")
            except Exception as e:
                logger.warning(f"Failed to send warning notification: {e}")

    def create_database_backup(
        self,
        name: Optional[str] = None,
        compression: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a PostgreSQL database backup using pg_dump.

        Args:
            name: Name for the backup (auto-generated if not provided)
            compression: Whether to compress the output

        Returns:
            Dictionary with backup details: path, size, checksum, tables_count
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"database_{timestamp}"

        ensure_backup_dirs()

        # Create temporary file for dump
        temp_file = TEMP_BACKUP_DIR / f"{backup_name}.sql"
        output_file = DATABASE_BACKUP_DIR / f"{backup_name}.sql"

        if compression:
            temp_file = TEMP_BACKUP_DIR / f"{backup_name}.sql.gz"
            output_file = DATABASE_BACKUP_DIR / f"{backup_name}.sql.gz"

        # Record backup start
        self._record_metric_start("database")

        start_time = time.time()
        try:
            logger.info(f"Starting database backup: {backup_name}")

            # Build pg_dump command
            pg_dump_cmd = [
                "pg_dump",
                "-h", self.db_params["host"],
                "-p", self.db_params["port"],
                "-U", self.db_params["user"],
                "-d", self.db_params["database"],
                "--no-owner",
                "--no-acl",
                "--verbose",
            ]

            # Execute pg_dump
            if compression:
                # Use gzip compression
                with open(temp_file, "wb") as f_out:
                    process = subprocess.Popen(
                        pg_dump_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    gzip_process = subprocess.Popen(
                        ["gzip"],
                        stdin=process.stdout,
                        stdout=f_out,
                        stderr=subprocess.PIPE,
                    )
                    process.stdout.close()

                    _, stderr = gzip_process.communicate()
                    if gzip_process.returncode != 0:
                        raise subprocess.CalledProcessError(
                            gzip_process.returncode, pg_dump_cmd, stderr
                        )
            else:
                with open(temp_file, "w") as f_out:
                    subprocess.run(
                        pg_dump_cmd,
                        stdout=f_out,
                        check=True,
                        capture_output=True,
                    )

            elapsed = time.time() - start_time

            # Move to final location
            shutil.move(str(temp_file), str(output_file))

            # Get file info
            size_bytes = output_file.stat().st_size
            checksum = calculate_checksum(output_file)

            # Count tables (grep through the compressed file)
            tables_count = 0
            try:
                if compression:
                    result = subprocess.run(
                        ["zgrep", "-c", "^CREATE TABLE", str(output_file)],
                        capture_output=True,
                        text=True,
                    )
                else:
                    result = subprocess.run(
                        ["grep", "-c", "^CREATE TABLE", str(output_file)],
                        capture_output=True,
                        text=True,
                    )
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    tables_count = int(result.stdout.strip())
            except Exception as e:
                logger.warning(f"Could not count tables: {e}")

            logger.info(
                f"Database backup completed: {backup_name} "
                f"({format_size(size_bytes)}, {tables_count} tables, {elapsed:.1f}s)"
            )

            # Record success metrics
            self._record_metric_success("database", size_bytes, elapsed)

            return {
                "path": str(output_file),
                "size_bytes": size_bytes,
                "checksum": checksum,
                "tables_count": tables_count,
                "elapsed_seconds": elapsed,
            }

        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"pg_dump failed: {error_msg}")

            # Record failure metrics and send notification
            self._record_metric_failure("database", "database_error", elapsed)
            self._send_failure_notification(
                operation="create_database_backup",
                error_message=error_msg,
                context={"backup_name": backup_name}
            )
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Database backup failed: {error_msg}")

            # Record failure metrics and send notification
            self._record_metric_failure("database", "unknown_error", elapsed)
            self._send_failure_notification(
                operation="create_database_backup",
                error_message=error_msg,
                context={"backup_name": backup_name}
            )
            raise

    def create_files_backup(
        self,
        name: Optional[str] = None,
        compression: bool = True,
        incremental: bool = False,
        parent_backup_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a backup of uploaded files.

        Args:
            name: Name for the backup
            compression: Whether to compress the archive
            incremental: Use rsync for incremental backup
            parent_backup_path: Path to parent backup for incremental

        Returns:
            Dictionary with backup details
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"files_{timestamp}"

        ensure_backup_dirs()

        # Record backup start
        self._record_metric_start("files")

        source_dir = UPLOADS_SOURCE_DIR
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            source_dir.mkdir(parents=True, exist_ok=True)

        start_time = time.time()

        if incremental and parent_backup_path:
            # Incremental backup using rsync
            backup_path = FILES_BACKUP_DIR / f"{backup_name}"
            backup_path.mkdir(parents=True, exist_ok=True)

            try:
                rsync_cmd = [
                    "rsync",
                    "-av",
                    "--delete",
                    "--link-dest=" + str(parent_backup_path),
                    str(source_dir) + "/",
                    str(backup_path) + "/",
                ]

                result = subprocess.run(
                    rsync_cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Count files
                files_count = sum(1 for _ in backup_path.rglob("*") if _.is_file())

                # Create tar archive for storage
                tar_path = FILES_BACKUP_DIR / f"{backup_name}.tar.gz"
                with tarfile.open(tar_path, "w:gz") as tar:
                    tar.add(backup_path, arcname=backup_name)

                # Remove the uncompressed directory
                shutil.rmtree(backup_path)

                size_bytes = tar_path.stat().st_size
                checksum = calculate_checksum(tar_path)
                elapsed = time.time() - start_time

                logger.info(
                    f"Files backup completed (incremental): {backup_name} "
                    f"({format_size(size_bytes)}, {files_count} files, {elapsed:.1f}s)"
                )

                # Record success metrics
                self._record_metric_success("files", size_bytes, elapsed)

                return {
                    "path": str(tar_path),
                    "size_bytes": size_bytes,
                    "checksum": checksum,
                    "files_count": files_count,
                    "elapsed_seconds": elapsed,
                    "is_incremental": True,
                }

            except subprocess.CalledProcessError as e:
                elapsed = time.time() - start_time
                error_msg = e.stderr if e.stderr else str(e)
                logger.error(f"rsync failed: {error_msg}")

                # Record failure metrics and send notification
                self._record_metric_failure("files", "rsync_error", elapsed)
                self._send_failure_notification(
                    operation="create_files_backup",
                    error_message=error_msg,
                    context={"backup_name": backup_name, "type": "incremental"}
                )
                raise
            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)
                logger.error(f"Files backup failed: {error_msg}")

                # Record failure metrics and send notification
                self._record_metric_failure("files", "unknown_error", elapsed)
                self._send_failure_notification(
                    operation="create_files_backup",
                    error_message=error_msg,
                    context={"backup_name": backup_name, "type": "incremental"}
                )
                raise
        else:
            # Full backup
            tar_path = FILES_BACKUP_DIR / f"{backup_name}.tar"
            if compression:
                tar_path = FILES_BACKUP_DIR / f"{backup_name}.tar.gz"

            try:
                # Count files before archiving
                files_count = sum(1 for _ in source_dir.rglob("*") if _.is_file())

                mode = "w:gz" if compression else "w"
                with tarfile.open(tar_path, mode) as tar:
                    tar.add(source_dir, arcname="uploads")

                size_bytes = tar_path.stat().st_size
                checksum = calculate_checksum(tar_path)
                elapsed = time.time() - start_time

                logger.info(
                    f"Files backup completed: {backup_name} "
                    f"({format_size(size_bytes)}, {files_count} files, {elapsed:.1f}s)"
                )

                # Record success metrics
                self._record_metric_success("files", size_bytes, elapsed)

                return {
                    "path": str(tar_path),
                    "size_bytes": size_bytes,
                    "checksum": checksum,
                    "files_count": files_count,
                    "elapsed_seconds": elapsed,
                    "is_incremental": False,
                }

            except Exception as e:
                elapsed = time.time() - start_time
                error_msg = str(e)
                logger.error(f"Files backup failed: {error_msg}")

                # Record failure metrics and send notification
                self._record_metric_failure("files", "archive_error", elapsed)
                self._send_failure_notification(
                    operation="create_files_backup",
                    error_message=error_msg,
                    context={"backup_name": backup_name, "type": "full"}
                )
                raise

    def create_models_backup(
        self,
        name: Optional[str] = None,
        compression: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a backup of ML models cache.

        Args:
            name: Name for the backup
            compression: Whether to compress the archive

        Returns:
            Dictionary with backup details
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"models_{timestamp}"

        ensure_backup_dirs()

        # Record backup start
        self._record_metric_start("models")

        source_dir = MODELS_SOURCE_DIR
        if not source_dir.exists():
            logger.warning(f"Models cache directory does not exist: {source_dir}")
            source_dir.mkdir(parents=True, exist_ok=True)

        tar_path = MODELS_BACKUP_DIR / f"{backup_name}.tar"
        if compression:
            tar_path = MODELS_BACKUP_DIR / f"{backup_name}.tar.gz"

        start_time = time.time()

        try:
            # Count files
            files_count = sum(1 for _ in source_dir.rglob("*") if _.is_file())

            mode = "w:gz" if compression else "w"
            with tarfile.open(tar_path, mode) as tar:
                tar.add(source_dir, arcname="models_cache")

            size_bytes = tar_path.stat().st_size
            checksum = calculate_checksum(tar_path)
            elapsed = time.time() - start_time

            logger.info(
                f"Models backup completed: {backup_name} "
                f"({format_size(size_bytes)}, {files_count} files, {elapsed:.1f}s)"
            )

            # Record success metrics
            self._record_metric_success("models", size_bytes, elapsed)

            return {
                "path": str(tar_path),
                "size_bytes": size_bytes,
                "checksum": checksum,
                "files_count": files_count,
                "elapsed_seconds": elapsed,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Models backup failed: {error_msg}")

            # Record failure metrics and send notification
            self._record_metric_failure("models", "archive_error", elapsed)
            self._send_failure_notification(
                operation="create_models_backup",
                error_message=error_msg,
                context={"backup_name": backup_name}
            )
            raise

    def create_full_backup(
        self,
        name: Optional[str] = None,
        compression: bool = True,
        incremental: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a full backup including database, files, and models.

        Args:
            name: Name for the backup
            compression: Whether to compress archives
            incremental: Use incremental for file backup

        Returns:
            Dictionary with combined backup details
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"full_{timestamp}"

        logger.info(f"Starting full backup: {backup_name}")

        start_time = time.time()

        # Create individual backups
        db_result = self.create_database_backup(
            name=f"{backup_name}_db",
            compression=compression,
        )

        files_result = self.create_files_backup(
            name=f"{backup_name}_files",
            compression=compression,
            incremental=incremental,
        )

        models_result = self.create_models_backup(
            name=f"{backup_name}_models",
            compression=compression,
        )

        # Create metadata file first
        metadata = {
            "name": backup_name,
            "created_at": datetime.utcnow().isoformat(),
            "type": "full",
            "components": {
                "database": {
                    "path": db_result["path"],
                    "size_bytes": db_result["size_bytes"],
                    "checksum": db_result["checksum"],
                },
                "files": {
                    "path": files_result["path"],
                    "size_bytes": files_result["size_bytes"],
                    "checksum": files_result["checksum"],
                },
                "models": {
                    "path": models_result["path"],
                    "size_bytes": models_result["size_bytes"],
                    "checksum": models_result["checksum"],
                },
            },
        }

        metadata_path = TEMP_BACKUP_DIR / f"{backup_name}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Create combined archive
        combined_tar = FULL_BACKUP_DIR / f"{backup_name}.tar"
        if compression:
            combined_tar = FULL_BACKUP_DIR / f"{backup_name}.tar.gz"

        with tarfile.open(combined_tar, "w:gz" if compression else "w") as tar:
            # Add all components
            for result in [db_result, files_result, models_result]:
                tar.add(result["path"], arcname=Path(result["path"]).name)
            # Add metadata to archive
            tar.add(metadata_path, arcname="metadata.json")

        # Clean up individual component backups and temp metadata
        for result in [db_result, files_result, models_result]:
            Path(result["path"]).unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)

        size_bytes = combined_tar.stat().st_size
        checksum = calculate_checksum(combined_tar)
        elapsed = time.time() - start_time

        # Count total files and tables
        files_count = (
            db_result.get("tables_count", 0) +
            files_result.get("files_count", 0) +
            models_result.get("files_count", 0)
        )

        logger.info(
            f"Full backup completed: {backup_name} "
            f"({format_size(size_bytes)}, {elapsed:.1f}s)"
        )

        return {
            "path": str(combined_tar),
            "size_bytes": size_bytes,
            "checksum": checksum,
            "files_count": files_count,
            "tables_count": db_result.get("tables_count", 0),
            "elapsed_seconds": elapsed,
        }

    def restore_database_backup(
        self,
        backup_path: str,
    ) -> Dict[str, Any]:
        """
        Restore database from a backup file.

        Args:
            backup_path: Path to the backup file (.sql or .sql.gz)

        Returns:
            Dictionary with restore details
        """
        logger.info(f"Starting database restore from: {backup_path}")

        start_time = time.time()
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Verify checksum if available
        # (This would be checked against the stored checksum in the database)

        # Build psql command
        psql_cmd = [
            "psql",
            "-h", self.db_params["host"],
            "-p", self.db_params["port"],
            "-U", self.db_params["user"],
            "-d", self.db_params["database"],
        ]

        try:
            if str(backup_file).endswith(".gz"):
                # Decompress and restore
                with open(backup_file, "rb") as f_in:
                    gunzip_proc = subprocess.Popen(
                        ["gunzip"],
                        stdin=f_in,
                        stdout=subprocess.PIPE,
                    )
                    subprocess.run(
                        psql_cmd,
                        stdin=gunzip_proc.stdout,
                        check=True,
                    )
                    gunzip_proc.wait()
            else:
                # Direct restore
                with open(backup_file, "r") as f_in:
                    subprocess.run(
                        psql_cmd,
                        stdin=f_in,
                        check=True,
                    )

            elapsed = time.time() - start_time
            logger.info(f"Database restore completed in {elapsed:.1f}s")

            return {
                "success": True,
                "elapsed_seconds": elapsed,
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore failed: {e}")
            raise

    def restore_files_backup(
        self,
        backup_path: str,
        target_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Restore files from a backup archive.

        Args:
            backup_path: Path to the backup archive
            target_dir: Target directory (default: UPLOADS_SOURCE_DIR)

        Returns:
            Dictionary with restore details
        """
        logger.info(f"Starting files restore from: {backup_path}")

        start_time = time.time()
        backup_file = Path(backup_path)
        target = target_dir or UPLOADS_SOURCE_DIR

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create target directory if needed
        target.mkdir(parents=True, exist_ok=True)

        # Extract archive
        with tarfile.open(backup_path, "r:*") as tar:
            tar.extractall(path=target)

        elapsed = time.time() - start_time
        logger.info(f"Files restore completed in {elapsed:.1f}s")

        return {
            "success": True,
            "elapsed_seconds": elapsed,
            "target": str(target),
        }

    def restore_models_backup(
        self,
        backup_path: str,
        target_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Restore ML models from a backup archive.

        Args:
            backup_path: Path to the backup archive
            target_dir: Target directory (default: MODELS_SOURCE_DIR)

        Returns:
            Dictionary with restore details
        """
        logger.info(f"Starting models restore from: {backup_path}")

        start_time = time.time()
        backup_file = Path(backup_path)
        target = target_dir or MODELS_SOURCE_DIR

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create target directory if needed
        target.mkdir(parents=True, exist_ok=True)

        # Extract archive
        with tarfile.open(backup_path, "r:*") as tar:
            tar.extractall(path=target.parent)

        elapsed = time.time() - start_time
        logger.info(f"Models restore completed in {elapsed:.1f}s")

        return {
            "success": True,
            "elapsed_seconds": elapsed,
            "target": str(target),
        }

    def restore_full_backup(
        self,
        backup_path: str,
    ) -> Dict[str, Any]:
        """
        Restore from a full backup archive.

        Args:
            backup_path: Path to the full backup archive

        Returns:
            Dictionary with restore details
        """
        logger.info(f"Starting full restore from: {backup_path}")

        start_time = time.time()
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Extract to temp directory first
        temp_extract = TEMP_BACKUP_DIR / f"restore_{int(time.time())}"
        temp_extract.mkdir(parents=True, exist_ok=True)

        try:
            # Extract the full archive
            with tarfile.open(backup_path, "r:*") as tar:
                tar.extractall(path=temp_extract)

            results = {}

            # Find and restore each component
            for component in ["database", "files", "models"]:
                pattern = f"*_{component}*.sql*"
                if component == "database":
                    pattern = f"*_db*.sql*"
                elif component == "files":
                    pattern = f"*_files*.tar*"
                elif component == "models":
                    pattern = f"*_models*.tar*"

                matches = list(temp_extract.glob(pattern))
                if matches:
                    component_path = matches[0]
                    if component == "database":
                        results["database"] = self.restore_database_backup(
                            str(component_path)
                        )
                    elif component == "files":
                        results["files"] = self.restore_files_backup(
                            str(component_path)
                        )
                    elif component == "models":
                        results["models"] = self.restore_models_backup(
                            str(component_path)
                        )

            elapsed = time.time() - start_time
            logger.info(f"Full restore completed in {elapsed:.1f}s")

            return {
                "success": True,
                "elapsed_seconds": elapsed,
                "components": results,
            }

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_extract, ignore_errors=True)

    def verify_backup_integrity(
        self,
        backup_path: str,
        expected_checksum: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify backup integrity using checksum.

        Args:
            backup_path: Path to the backup file
            expected_checksum: Expected SHA256 checksum

        Returns:
            Dictionary with verification results
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            # Record integrity check failure
            if self.metrics:
                self.metrics.record_integrity_check(result="fail")

            return {
                "valid": False,
                "error": "Backup file not found",
            }

        try:
            # Calculate checksum
            actual_checksum = calculate_checksum(backup_file)

            # Verify file is readable
            with tarfile.open(backup_path, "r:*") as tar:
                members = tar.getmembers()

            checksum_match = True
            if expected_checksum:
                checksum_match = actual_checksum == expected_checksum

            # Record integrity check result
            if self.metrics:
                if checksum_match:
                    self.metrics.record_integrity_check(result="pass")
                else:
                    self.metrics.record_integrity_check(result="fail")

            # Send warning if checksum doesn't match
            if not checksum_match:
                self._send_warning_notification(
                    warning_type="integrity_check_failed",
                    message=f"Backup integrity check failed: checksum mismatch for {backup_file.name}",
                    context={"backup_path": backup_path}
                )

            return {
                "valid": True,
                "checksum_match": checksum_match,
                "actual_checksum": actual_checksum,
                "expected_checksum": expected_checksum,
                "files_count": len(members),
                "size_bytes": backup_file.stat().st_size,
            }

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")

            # Record integrity check failure
            if self.metrics:
                self.metrics.record_integrity_check(result="fail")

            return {
                "valid": False,
                "error": str(e),
            }

    def delete_backup(self, backup_path: str) -> bool:
        """
        Delete a backup file.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if deleted successfully
        """
        backup_file = Path(backup_path)
        try:
            if backup_file.exists():
                backup_file.unlink()
                logger.info(f"Deleted backup: {backup_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_path}: {e}")
            return False

    def get_backups_list(
        self,
        backup_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all backups with metadata.

        Args:
            backup_type: Filter by type (database, files, models, full)

        Returns:
            List of backup information dictionaries
        """
        backups = []

        # Map type to directory
        type_dirs = {
            "database": DATABASE_BACKUP_DIR,
            "files": FILES_BACKUP_DIR,
            "models": MODELS_BACKUP_DIR,
            "full": FULL_BACKUP_DIR,
        }

        search_dirs = (
            [type_dirs[backup_type]] if backup_type and backup_type in type_dirs
            else type_dirs.values()
        )

        for directory in search_dirs:
            for file_path in directory.glob("*"):
                if file_path.is_file() and not file_path.name.endswith(".json"):
                    stat = file_path.stat()
                    backups.append({
                        "path": str(file_path),
                        "name": file_path.stem,
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "type": self._infer_backup_type(file_path, directory),
                    })

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    def _infer_backup_type(
        self,
        file_path: Path,
        directory: Path,
    ) -> str:
        """Infer backup type from file path and name"""
        dir_name = directory.name
        if dir_name in ["database", "files", "models", "full"]:
            return dir_name

        # Try to infer from filename
        name = file_path.name.lower()
        if "database" in name or "db" in name or file_path.suffix == ".sql":
            return "database"
        elif "files" in name or "uploads" in name:
            return "files"
        elif "models" in name:
            return "models"
        return "full"

    def get_disk_usage(self) -> Dict[str, Any]:
        """
        Get disk usage statistics for backup directory.

        Returns:
            Dictionary with usage statistics
        """
        total_bytes = 0
        file_count = 0

        for file_path in self.backup_dir.rglob("*"):
            if file_path.is_file():
                total_bytes += file_path.stat().st_size
                file_count += 1

        # Get system disk usage
        try:
            stat = os.statvfs(str(self.backup_dir))
            free_bytes = stat.f_bavail * stat.f_frsize
            total_disk_bytes = stat.f_blocks * stat.f_frsize
            used_disk_bytes = (stat.f_blocks - stat.f_bfree) * stat.f_frsize

            # Record disk usage metrics
            if self.metrics:
                self.metrics.set_disk_usage_metrics(
                    used_bytes=used_disk_bytes,
                    free_bytes=free_bytes,
                    total_bytes=total_disk_bytes
                )

            # Check for low disk space (warn if less than 10% free)
            free_percentage = (free_bytes / total_disk_bytes * 100) if total_disk_bytes > 0 else 0
            if free_percentage < 10:
                self._send_warning_notification(
                    warning_type="low_disk_space",
                    message=f"Low disk space: {free_percentage:.1f}% free ({format_size(free_bytes)} available)",
                    context={
                        "free_bytes": free_bytes,
                        "total_bytes": total_disk_bytes,
                        "free_percentage": free_percentage
                    }
                )

            return {
                "total_bytes": total_bytes,
                "total_human": format_size(total_bytes),
                "file_count": file_count,
                "disk_free_bytes": free_bytes,
                "disk_total_bytes": total_disk_bytes,
                "disk_free_percentage": free_percentage,
            }
        except Exception as e:
            logger.warning(f"Failed to get disk usage: {e}")
            return {
                "total_bytes": total_bytes,
                "total_human": format_size(total_bytes),
                "file_count": file_count,
            }

    def upload_to_s3(
        self,
        backup_path: str,
        s3_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload backup to S3-compatible storage.

        Args:
            backup_path: Path to the backup file
            s3_key: S3 object key (auto-generated if not provided)

        Returns:
            Dictionary with upload details
        """
        if not self.s3_config.get("enabled"):
            raise ValueError("S3 backup is not enabled")

        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Generate S3 key if not provided
        if s3_key is None:
            timestamp = datetime.utcnow().strftime("%Y/%m/%d")
            s3_key = f"backups/{timestamp}/{backup_file.name}"

        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=self.s3_config.get("endpoint"),
            aws_access_key_id=self.s3_config.get("access_key"),
            aws_secret_access_key=self.s3_config.get("secret_key"),
            region_name=self.s3_config.get("region", "us-east-1"),
        )

        # Record S3 sync start
        if self.metrics:
            self.metrics.record_s3_sync_start()

        start_time = time.time()
        try:
            logger.info(f"Uploading {backup_file.name} to S3: {s3_key}")

            # Upload with multipart upload for large files
            s3_client.upload_file(
                str(backup_file),
                self.s3_config["bucket"],
                s3_key,
                ExtraArgs={"ContentType": "application/octet-stream"},
            )

            elapsed = time.time() - start_time
            size_bytes = backup_file.stat().st_size

            logger.info(f"S3 upload completed in {elapsed:.1f}s")

            # Record S3 sync success
            if self.metrics:
                self.metrics.record_s3_sync_success(size_bytes, elapsed)

            return {
                "success": True,
                "s3_key": s3_key,
                "bucket": self.s3_config["bucket"],
                "size_bytes": size_bytes,
                "elapsed_seconds": elapsed,
            }

        except (ClientError, BotoCoreError) as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            logger.error(f"S3 upload failed: {error_msg}")

            # Record S3 sync failure
            if self.metrics:
                self.metrics.record_s3_sync_failure(error_type="s3_error")

            # Send failure notification
            self._send_failure_notification(
                operation="upload_to_s3",
                error_message=error_msg,
                context={
                    "backup_path": str(backup_file),
                    "s3_key": s3_key,
                    "bucket": self.s3_config.get("bucket")
                }
            )
            raise

    def download_from_s3(
        self,
        s3_key: str,
        local_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download backup from S3-compatible storage.

        Args:
            s3_key: S3 object key
            local_path: Local file path (auto-generated if not provided)

        Returns:
            Dictionary with download details
        """
        if not self.s3_config.get("enabled"):
            raise ValueError("S3 backup is not enabled")

        # Generate local path if not provided
        if local_path is None:
            filename = Path(s3_key).name
            local_path = str(FULL_BACKUP_DIR / filename)

        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=self.s3_config.get("endpoint"),
            aws_access_key_id=self.s3_config.get("access_key"),
            aws_secret_access_key=self.s3_config.get("secret_key"),
            region_name=self.s3_config.get("region", "us-east-1"),
        )

        try:
            logger.info(f"Downloading from S3: {s3_key}")

            start_time = time.time()

            s3_client.download_file(
                self.s3_config["bucket"],
                s3_key,
                local_path,
            )

            elapsed = time.time() - start_time
            size_bytes = Path(local_path).stat().st_size

            logger.info(f"S3 download completed in {elapsed:.1f}s")

            return {
                "success": True,
                "local_path": local_path,
                "s3_key": s3_key,
                "size_bytes": size_bytes,
                "elapsed_seconds": elapsed,
            }

        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 download failed: {e}")
            raise

    def list_s3_backups(self, prefix: str = "backups/") -> List[Dict[str, Any]]:
        """
        List backups in S3 storage.

        Args:
            prefix: S3 key prefix to filter

        Returns:
            List of S3 object information
        """
        if not self.s3_config.get("enabled"):
            return []

        s3_client = boto3.client(
            "s3",
            endpoint_url=self.s3_config.get("endpoint"),
            aws_access_key_id=self.s3_config.get("access_key"),
            aws_secret_access_key=self.s3_config.get("secret_key"),
            region_name=self.s3_config.get("region", "us-east-1"),
        )

        try:
            response = s3_client.list_objects_v2(
                Bucket=self.s3_config["bucket"],
                Prefix=prefix,
            )

            backups = []
            for obj in response.get("Contents", []):
                backups.append({
                    "s3_key": obj["Key"],
                    "size_bytes": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "etag": obj["ETag"].strip('"'),
                })

            return backups

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to list S3 backups: {e}")
            return []

    def cleanup_old_backups(
        self,
        retention_days: int = 30,
        backup_type: Optional[str] = None,
    ) -> List[str]:
        """
        Delete backups older than retention period.

        Args:
            retention_days: Days to retain backups
            backup_type: Filter by type (None for all)

        Returns:
            List of deleted backup paths
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted = []

        backups = self.get_backups_list(backup_type=backup_type)

        for backup in backups:
            created_at = datetime.fromisoformat(backup["created_at"])
            if created_at < cutoff_date:
                if self.delete_backup(backup["path"]):
                    deleted.append(backup["path"])

        logger.info(f"Cleaned up {len(deleted)} old backups older than {retention_days} days")

        # Update retention metrics
        self._update_retention_metrics()

        return deleted

    def _update_retention_metrics(self) -> None:
        """Update retention metrics for all backup types."""
        if not self.metrics:
            return

        backup_types = ["database", "files", "models", "full"]
        for backup_type in backup_types:
            try:
                backups = self.get_backups_list(backup_type=backup_type)
                count = len(backups)
                total_size = sum(b["size_bytes"] for b in backups)

                self.metrics.set_backup_retention_metrics(
                    backup_type=backup_type,
                    count=count,
                    total_size_bytes=total_size
                )
            except Exception as e:
                logger.warning(f"Failed to update retention metrics for {backup_type}: {e}")

    def find_parent_backup(
        self,
        backup_type: str = "full",
        max_age_hours: int = 48,
    ) -> Optional[str]:
        """
        Find a suitable parent backup for incremental backup.

        Args:
            backup_type: Type of backup
            max_age_hours: Maximum age of parent backup

        Returns:
            Path to parent backup or None
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        backups = self.get_backups_list(backup_type=backup_type)

        for backup in backups:
            created_at = datetime.fromisoformat(backup["created_at"])
            if created_at > cutoff_time:
                return backup["path"]

        return None


# Singleton instance
_backup_service: Optional[BackupService] = None


def get_backup_service(
    s3_config: Optional[Dict[str, Any]] = None,
) -> BackupService:
    """
    Get or create the singleton backup service instance.

    Args:
        s3_config: Optional S3 configuration

    Returns:
        BackupService instance
    """
    global _backup_service
    if _backup_service is None or s3_config is not None:
        _backup_service = BackupService(s3_config=s3_config)
    return _backup_service
