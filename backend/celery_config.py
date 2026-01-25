"""
Celery configuration for async task processing.

This module provides Celery configuration using settings from the application
config module. It configures the broker, result backend, and task behavior.
"""
import logging
from typing import Dict, Any

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Celery configuration dictionary
# This configuration is used by the Celery application in tasks.py
celery_config: Dict[str, Any] = {
    # Broker settings
    "broker_url": settings.celery_broker_url,
    "result_backend": settings.celery_result_backend,
    "broker_connection_retry_on_startup": True,

    # Task settings
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,

    # Task execution settings
    "task_acks_late": True,  # Acknowledge task after execution (reliability)
    "task_reject_on_worker_lost": True,  # Requeue task if worker dies
    "task_track_started": True,  # Track when tasks start
    "task_time_limit": 3600,  # Hard limit: 1 hour (60 minutes * 60 seconds)
    "task_soft_time_limit": 3300,  # Soft limit: 55 minutes (allows graceful shutdown)

    # Result settings
    "result_expires": 86400,  # Results expire after 24 hours (in seconds)
    "result_compression": "gzip",  # Compress results to save space

    # Worker settings
    "worker_prefetch_multiplier": 1,  # Disable prefetching for long tasks
    "worker_max_tasks_per_child": 100,  # Restart worker after 100 tasks (memory management)

    # Task routing (can be extended for specific queues)
    "task_routes": {
        "tasks.analysis_task.analyze_resume_async": {"queue": "analysis"},
        "tasks.analysis_task.*": {"queue": "analysis"},
        "tasks.learning_tasks.aggregate_feedback_and_generate_synonyms": {"queue": "learning"},
        "tasks.learning_tasks.review_and_activate_synonyms": {"queue": "learning"},
        "tasks.learning_tasks.periodic_feedback_aggregation": {"queue": "learning"},
        "tasks.learning_tasks.*": {"queue": "learning"},
    },

    # Task priority (if needed in future)
    "task_default_priority": 5,
    "worker_disable_rate_limits": False,

    # Monitoring
    "worker_send_task_events": True,  # Enable task events for Flower monitoring
    "task_send_sent_event": True,  # Send task-sent events

    # Error handling
    "task_autoretry_for": (Exception,),  # Auto-retry on exceptions
    "task_retry_kwargs": {"max_retries": 3, "countdown": 60},  # Retry settings

    # Performance optimization
    "broker_connection_retry": True,
    "broker_connection_max_retries": 10,
}


def get_celery_config() -> Dict[str, Any]:
    """
    Get the Celery configuration dictionary.

    This function returns the Celery configuration loaded from application
    settings. It provides a centralized point for accessing Celery configuration.

    Returns:
        Dictionary containing Celery configuration settings

    Example:
        >>> from celery_config import get_celery_config
        >>> config = get_celery_config()
        >>> print(config['broker_url'])
        'redis://localhost:6379/0'
    """
    return celery_config


def update_celery_config(**kwargs: Any) -> None:
    """
    Update Celery configuration at runtime.

    This function allows updating specific Celery configuration values
    at runtime. Useful for testing or dynamic configuration changes.

    Args:
        **kwargs: Configuration key-value pairs to update

    Example:
        >>> update_celery_config(task_time_limit=1800)
        >>> # Updates task_time_limit to 30 minutes
    """
    for key, value in kwargs.items():
        if key in celery_config:
            old_value = celery_config[key]
            celery_config[key] = value
            logger.info(f"Updated Celery config: {key} = {old_value} -> {value}")
        else:
            logger.warning(f"Attempted to update non-existent config key: {key}")


# Log configuration on import
logger.info(f"Celery broker URL: {settings.celery_broker_url}")
logger.info(f"Celery result backend: {settings.celery_result_backend}")
logger.info("Celery configuration loaded successfully")
