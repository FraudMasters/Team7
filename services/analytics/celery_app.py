"""
Конфигурация приложения Celery для Analytics Service.

# Русский комментарий:
Этот модуль конфигурирует приложение Celery для обработки фоновых задач,
таких как планирование генерации отчетов, агрегация данных и аналитическая обработка.
"""
import logging
from celery import Celery

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create Celery application
celery_app = Celery(
    "analytics_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "tasks.report_generation",
    ],
)

# Configure Celery settings
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    # Task routing (optional - for separate queues)
    task_routes={
        "tasks.report_generation.*": {"queue": "analytics_reports"},
    },
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Configure Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "process-all-pending-reports": {
        "task": "tasks.report_generation.process_all_pending_reports",
        "schedule": 3600.0,  # Run every hour
    },
}

logger.info(
    f"Celery app configured: broker={settings.celery_broker_url}, "
    f"backend={settings.celery_result_backend}"
)
