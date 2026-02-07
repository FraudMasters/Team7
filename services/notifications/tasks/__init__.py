"""
Celery tasks for Notification Service.

Задачи Celery для Notification Service.

Этот модуль предоставляет задачи для асинхронной отправки уведомлений,
включая электронную почту, SMS и вебхуки.

This module provides tasks for asynchronous notification delivery,
including email, SMS, and webhooks.
"""
from .email_task import (
    send_feedback_notification,
    send_batch_notification,
    send_email_notification,
)

__all__ = [
    "send_feedback_notification",
    "send_batch_notification",
    "send_email_notification",
]
