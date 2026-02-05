"""
Модель уведомления для Notification Service.

# Русский комментарий:
Этот модуль определяет модель уведомления для хранения истории отправки
уведомлений через различные каналы (email, SMS, webhook).
"""
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, JSON, DateTime, Boolean, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

logger = logging.getLogger(__name__)


class NotificationStatus(str, Enum):
    """Статусы уведомления."""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationType(str, Enum):
    """Типы уведомлений."""

    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """Приоритеты уведомлений."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """
    Модель уведомления.

    Хранит информацию об отправленных уведомлениях, включая тип получателя,
    статус доставки, содержание и метаданные.

    Attributes:
        id: Уникальный идентификатор уведомления
        notification_type: Тип уведомления (email, SMS, webhook, in_app)
        recipient: Получатель уведомления (email, телефон, URL)
        status: Статус доставки (pending, sending, sent, failed, retrying)
        priority: Приоритет уведомления (low, normal, high, urgent)
        subject: Тема уведомления (для email)
        body: Тело уведомления
        metadata: Дополнительные метаданные в формате JSON
        error_message: Сообщение об ошибке (если отправка не удалась)
        retry_count: Количество попыток отправки
        sent_at: Время успешной отправки
        created_at: Время создания записи
        updated_at: Время последнего обновления записи
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Уникальный идентификатор уведомления",
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Тип уведомления",
    )

    recipient: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="Получатель уведомления",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=NotificationStatus.PENDING.value,
        index=True,
        comment="Статус доставки",
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=NotificationPriority.NORMAL.value,
        comment="Приоритет уведомления",
    )

    subject: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Тема уведомления",
    )

    body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Тело уведомления",
    )

    metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные метаданные",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке",
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Количество попыток отправки",
    )

    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время успешной отправки",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Время создания записи",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Время последнего обновления записи",
    )

    def __repr__(self) -> str:
        """Строковое представление уведомления."""
        return (
            f"<Notification(id={self.id}, type={self.notification_type}, "
            f"recipient={self.recipient[:20]}..., status={self.status})>"
        )
