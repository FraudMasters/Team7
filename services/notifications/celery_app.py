"""
Celery application configuration for Notification Service.

Этот модуль настраивает приложение Celery для асинхронной отправки уведомлений,
включая электронную почту, SMS и вебхуки.

This module configures the Celery application for asynchronous notification delivery,
including email, SMS, and webhooks.
"""
import logging
import os
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

# Настройка логирования / Configure logging
logger = logging.getLogger(__name__)

# Загрузка настроек из конфигурации сервиса / Load settings from service config
# Import the service settings
try:
    import sys
    # Добавляем родительскую директорию сервиса в путь для импорта конфигурации
    # Add service parent directory to path for configuration import
    service_dir = Path(__file__).parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from config import get_settings
    settings = get_settings()

    # Celery broker URL (Redis)
    BROKER_URL = settings.celery_broker_url
    RESULT_BACKEND = settings.celery_result_backend

    logger.info(f"Celery configured with broker: {BROKER_URL[:20]}...")

except Exception as e:
    logger.warning(f"Failed to load service configuration, using defaults: {e}")
    # Резервные значения по умолчанию / Fallback default values
    BROKER_URL = os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1"
    )
    RESULT_BACKEND = os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/1"
    )

# Создание приложения Celery / Create Celery application
celery_app = Celery(
    "notifications",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "tasks.email_task",  # Задачи отправки email / Email sending tasks
    ],
)

# Настройка Celery / Celery configuration
celery_app.conf.update(
    # Настройки задачи / Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Имя очереди для этого сервиса / Queue name for this service
    task_default_queue="notifications",
    task_queues={
        "notifications": {
            "exchange": "notifications",
            "routing_key": "notifications",
        },
    },
    # Настройки маршрутизации / Routing settings
    task_default_exchange="notifications",
    task_default_routing_key="notifications",
    # Настройки результата / Result settings
    result_expires=3600,  # Результаты хранятся 1 час / Results stored for 1 hour
    result_extended=True,
    # Настройки повторных попыток / Retry settings
    task_acks_late=True,  # Подтверждение задачи только после успешного выполнения / Ack only after successful completion
    worker_prefetch_multiplier=1,  # Количество задач, предварительно выбираемых одним рабочим / Tasks prefetched per worker
    # Настройки тайм-аута / Timeout settings
    task_soft_time_limit=300,  # Мягкий лимит времени (5 минут) / Soft time limit (5 minutes)
    task_time_limit=600,  # Жесткий лимит времени (10 минут) / Hard time limit (10 minutes)
    # Настройки производительности / Performance settings
    worker_max_tasks_per_child=50,  # Перезагрузка рабочего после 50 задач для предотвращения утечек памяти / Worker restart after 50 tasks to prevent memory leaks
    # Настройки трассировки / Tracing settings
    task_send_sent_event=True,  # Отправлять события о состоянии задачи / Send task state events
    # Настройки форматирования / Formatting settings
    task_includes_parent_id=True,  # Включать ID родительской задачи / Include parent task ID
    # Настройки сжатия / Compression settings
    task_compression="gzip",  # Использовать сжатие gzip для больших payloads / Use gzip compression for large payloads
    # Настройки сообщений / Message settings
    task_publish_retry=False,  # Не повторять попытки публикации задачи / Do not retry task publishing
    task_publish_retry_policy={
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.2,
    },
)

# Расписание периодических задач / Periodic task schedule
# Может быть расширено для регулярной обработки отложенных уведомлений
# Can be extended for regular deferred notification processing
celery_app.conf.beat_schedule = {
    # Пример периодической задачи (закомментирован)
    # Example periodic task (commented out)
    # "retry-failed-notifications": {
    #     "task": "tasks.email_task.retry_failed_notifications",
    #     "schedule": crontab(hour=1, minute=0),  # Ежедневно в 1:00 AM / Daily at 1:00 AM
    # },
}


# Настройка сигналов Celery для мониторинга / Configure Celery signals for monitoring
from celery.signals import worker_ready, worker_shutdown, task_prerun, task_postrun, task_failure


@worker_ready.connect
def on_worker_ready(**kwargs):
    """Обработчик сигнала готовности рабочего / Worker ready signal handler."""
    logger.info("Celery worker ready for Notification Service")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Обработчик сигнала остановки рабочего / Worker shutdown signal handler."""
    logger.info("Celery worker shutting down for Notification Service")


@task_prerun.connect
def on_task_prerun(**kwargs):
    """Обработчик сигнала перед запуском задачи / Task pre-run signal handler."""
    task_id = kwargs.get("task_id", "unknown")
    task_name = kwargs.get("task_name", "unknown")
    logger.debug(f"Starting task {task_name} (ID: {task_id[:8]}...)")


@task_postrun.connect
def on_task_postrun(**kwargs):
    """Обработчик сигнала после выполнения задачи / Task post-run signal handler."""
    task_id = kwargs.get("task_id", "unknown")
    task_name = kwargs.get("task_name", "unknown")
    state = kwargs.get("state", "unknown")
    logger.debug(f"Completed task {task_name} (ID: {task_id[:8]}...) with state: {state}")


@task_failure.connect
def on_task_failure(**kwargs):
    """Обработчик сигнала сбоя задачи / Task failure signal handler."""
    task_id = kwargs.get("task_id", "unknown")
    task_name = kwargs.get("task_name", "unknown")
    exception = kwargs.get("exception", "Unknown exception")
    logger.warning(f"Task {task_name} (ID: {task_id[:8]}...) failed: {exception}")


def get_celery_app() -> Celery:
    """
    Получить экземпляр приложения Celery.

    Get the Celery application instance.

    Returns:
        Celery: Настроенное приложение Celery / Configured Celery application

    Example:
        >>> from celery_app import get_celery_app
        >>> app = get_celery_app()
        >>> app.send_task('tasks.email_task.send_feedback_notification', args=['feedback_id'])
    """
    return celery_app


if __name__ == "__main__":
    # Запуск рабочего Celery напрямую / Start Celery worker directly
    # Использование: python -m celery_app
    # Usage: python -m celery_app
    celery_app.start()
