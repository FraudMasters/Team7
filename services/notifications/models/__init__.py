"""
Модели базы данных Notification Service.

# Русский комментарий:
Этот пакет содержит модели SQLAlchemy для уведомлений, коммуникаций,
шаблонов email и webhook подписок.
"""

from .sms_template import SMSTemplate

__all__ = ["SMSTemplate"]
