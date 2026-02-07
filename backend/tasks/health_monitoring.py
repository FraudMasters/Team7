"""
Health monitoring tasks for automated system health checks.

This module provides Celery tasks for comprehensive health monitoring of
all system components including database, Redis, Celery workers, ML models,
and external services. These tasks are designed to run periodically via
Celery Beat for automated health monitoring and early issue detection.
"""
import asyncio
import logging
from typing import Dict, Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="tasks.health_check",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def health_check_task(self) -> Dict[str, Any]:
    """
    Comprehensive health check task for Celery worker monitoring.

    This task verifies that the Celery worker is functioning correctly
    and that critical ML models are loaded and ready. It's designed to
    run periodically via Celery Beat for automated health monitoring.

    The task checks:
    - Worker responsiveness and hostname
    - ML model availability (NER, zero-shot classification, LanguageTool)
    - Returns appropriate status based on model availability

    This periodic health check helps detect worker issues early and
    ensures the worker is ready to process analysis tasks.

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing health status information:
        - status: Overall health status (healthy/degraded/unhealthy)
        - worker: Worker hostname
        - task_id: Celery task ID
        - models_status: Dict with status of each model type
        - message: Human-readable status message

    Example:
        >>> from tasks.health_monitoring import health_check_task
        >>> result = health_check_task.delay()
        >>> print(result.get())
        {
            'status': 'healthy',
            'worker': 'celery@hostname',
            'task_id': 'abc-123',
            'models_status': {
                'ner_loaded': True,
                'zero_shot_loaded': True,
                'language_tools_loaded': True
            },
            'message': 'Worker operational and all models loaded'
        }
    """
    logger.info("Periodic health check executed")

    # Check if ML models are loaded by attempting to access them
    models_status = {}
    try:
        from backend.analyzers.hf_skill_extractor import (
            _ner_pipeline,
            _zero_shot_pipeline,
        )
        from backend.analyzers.grammar_checker import _language_tools

        models_status["ner_loaded"] = _ner_pipeline is not None
        models_status["zero_shot_loaded"] = _zero_shot_pipeline is not None
        models_status["language_tools_loaded"] = any(
            tool is not None for tool in _language_tools.values()
        )

        all_models_loaded = all(models_status.values())

        if all_models_loaded:
            overall_status = "healthy"
            message = "Worker operational and all models loaded"
        elif models_status.get("ner_loaded") and models_status.get("zero_shot_loaded"):
            # Core models loaded, but LanguageTool missing - acceptable degradation
            overall_status = "degraded"
            message = "Worker operational with core models (LanguageTool not loaded)"
        else:
            # Critical models missing - unhealthy
            overall_status = "unhealthy"
            message = "Worker operational but critical ML models not loaded"

        return {
            "status": overall_status,
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "models_status": models_status,
            "message": message,
        }

    except Exception as e:
        logger.error(f"Error checking model status during health check: {e}")
        return {
            "status": "unhealthy",
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "models_status": models_status,
            "message": f"Worker operational but model check failed: {str(e)}",
        }


@shared_task(
    name="tasks.monitor_health",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def monitor_health(self) -> Dict[str, Any]:
    """
    Comprehensive automated health monitoring task for all system components.

    This task performs comprehensive health checks across all system components:
    - Database connectivity and query performance
    - Redis availability and response time
    - Celery worker status and queue length
    - ML model loading status (NER, zero-shot, LanguageTool)
    - External service availability (LanguageTool API, S3 backup)

    Designed to run periodically via Celery Beat for automated health monitoring,
    early issue detection, and alerting integration. Returns aggregated status
    that can be consumed by monitoring systems and alerting services.

    The task executes all health checks concurrently using asyncio for efficiency,
    then aggregates results to determine overall system health status.

    Args:
        self: Celery task instance (bind=True)

    Returns:
        Dictionary containing comprehensive health status:
        - overall_status: Overall system health (healthy/degraded/unhealthy)
        - worker: Worker hostname executing the check
        - task_id: Celery task ID
        - timestamp: ISO 8601 timestamp of the check
        - checks: Dict with results from each component check:
            - database: Database health status
            - redis: Redis health status
            - celery_workers: Celery worker status
            - ml_models: ML model loading status
            - languagetool: LanguageTool service status
            - s3: S3 backup service status
        - summary: Summary statistics and status counts

    Example:
        >>> from tasks.health_monitoring import monitor_health
        >>> result = monitor_health.delay()
        >>> print(result.get())
        {
            'overall_status': 'healthy',
            'worker': 'celery@hostname',
            'task_id': 'abc-123',
            'timestamp': '2026-02-03T12:00:00Z',
            'checks': {
                'database': {'status': 'healthy', 'latency_seconds': 0.023},
                'redis': {'status': 'healthy', 'latency_seconds': 0.001},
                'celery_workers': {'status': 'healthy', 'worker_count': 2},
                'ml_models': {'status': 'healthy', 'models_loaded': 3},
                'languagetool': {'status': 'healthy'},
                's3': {'status': 'healthy', 'enabled': True}
            },
            'summary': {
                'total_checks': 6,
                'healthy': 6,
                'degraded': 0,
                'unhealthy': 0
            }
        }
    """
    import time
    from datetime import datetime

    logger.info("Starting comprehensive automated health monitoring...")

    start_time = time.time()
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Import health check utilities
    try:
        from backend.utils.health_checks import (
            check_database,
            check_redis,
            check_celery_workers,
            check_ml_models,
            check_languagetool,
            check_s3,
        )
    except ImportError as e:
        logger.error(f"Failed to import health check utilities: {e}")
        return {
            "overall_status": "unhealthy",
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "timestamp": timestamp,
            "error": f"Health check utilities not available: {str(e)}",
            "checks": {},
            "summary": {},
        }

    # Run all health checks asynchronously
    async def run_all_checks() -> Dict[str, Any]:
        """Run all health checks concurrently."""
        checks = {}

        # Run database check
        try:
            checks["database"] = await check_database()
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            checks["database"] = {"status": "unhealthy", "error": str(e)}

        # Run Redis check
        try:
            checks["redis"] = await check_redis()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            checks["redis"] = {"status": "unhealthy", "error": str(e)}

        # Run Celery workers check
        try:
            checks["celery_workers"] = await check_celery_workers()
        except Exception as e:
            logger.error(f"Celery workers health check failed: {e}")
            checks["celery_workers"] = {"status": "unhealthy", "error": str(e)}

        # Run ML models check
        try:
            checks["ml_models"] = await check_ml_models()
        except Exception as e:
            logger.error(f"ML models health check failed: {e}")
            checks["ml_models"] = {"status": "unhealthy", "error": str(e)}

        # Run LanguageTool check
        try:
            checks["languagetool"] = await check_languagetool()
        except Exception as e:
            logger.error(f"LanguageTool health check failed: {e}")
            checks["languagetool"] = {"status": "unhealthy", "error": str(e)}

        # Run S3 check
        try:
            checks["s3"] = await check_s3()
        except Exception as e:
            logger.error(f"S3 health check failed: {e}")
            checks["s3"] = {"status": "unhealthy", "error": str(e)}

        return checks

    # Execute async health checks
    try:
        checks = asyncio.run(run_all_checks())
    except Exception as e:
        logger.error(f"Failed to execute health checks: {e}")
        return {
            "overall_status": "unhealthy",
            "worker": self.request.hostname,
            "task_id": self.request.id,
            "timestamp": timestamp,
            "error": f"Health check execution failed: {str(e)}",
            "checks": {},
            "summary": {},
        }

    # Calculate summary statistics
    total_checks = len(checks)
    healthy_count = sum(1 for c in checks.values() if c.get("status") == "healthy")
    degraded_count = sum(1 for c in checks.values() if c.get("status") == "degraded")
    unhealthy_count = sum(1 for c in checks.values() if c.get("status") == "unhealthy")

    # Determine overall status based on critical components
    # Critical components: database, celery_workers, ml_models
    critical_checks = ["database", "celery_workers", "ml_models"]
    critical_unhealthy = any(
        checks.get(name, {}).get("status") == "unhealthy"
        for name in critical_checks
    )

    if critical_unhealthy:
        overall_status = "unhealthy"
    elif unhealthy_count > 0 or degraded_count > 0:
        # Non-critical components failed or degraded
        overall_status = "degraded" if degraded_count > 0 else "healthy"
        # If any component is unhealthy (even non-critical), mark as degraded
        if unhealthy_count > 0:
            overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Calculate total execution time
    execution_time = round(time.time() - start_time, 3)

    # Build result
    result = {
        "overall_status": overall_status,
        "worker": self.request.hostname,
        "task_id": self.request.id,
        "timestamp": timestamp,
        "execution_time_seconds": execution_time,
        "checks": checks,
        "summary": {
            "total_checks": total_checks,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
        },
    }

    # Log summary
    logger.info(
        f"Health monitoring completed: {overall_status} "
        f"({healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy) "
        f"in {execution_time}s"
    )

    # Log warnings for unhealthy components
    for component_name, component_status in checks.items():
        if component_status.get("status") == "unhealthy":
            error_msg = component_status.get("error", "Unknown error")
            logger.warning(
                f"Component '{component_name}' is unhealthy: {error_msg}"
            )
        elif component_status.get("status") == "degraded":
            logger.warning(f"Component '{component_name}' is degraded")

    return result


# Export tasks for use by celery_app.py
__all__ = [
    "health_check_task",
    "monitor_health",
]
