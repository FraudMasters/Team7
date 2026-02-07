"""
Модель webhook подписки для Notification Service.

# Русский комментарий:
Этот модуль определяет модель webhook подписки для отправки
уведомлений на внешние URL.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, JSON, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

logger = logging.getLogger(__name__)


class WebhookSubscription(Base):
    """
    Модель webhook подписки.

    Хранит информацию о webhook подписках для отправки уведомлений
    на внешние URL при определенных событиях.

    Attributes:
        id: Уникальный идентификатор подписки
        name: Название подписки
        url: URL webhook endpoint
        events: Список событий для подписки
        headers: Дополнительные HTTP заголовки
        secret: Секретный ключ для верификации
        is_active: Флаг активности подписки
        organization_id: ID организации (для мультиарендности)
        created_at: Время создания записи
        updated_at: Время последнего обновления записи
    """

    __tablename__ = "webhook_subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Уникальный идентификатор подписки",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Название подписки",
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="URL webhook endpoint",
    )

    events: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Список событий для подписки",
    )

    headers: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Дополнительные HTTP заголовки",
    )

    secret: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Секретный ключ для верификации",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Флаг активности подписки",
    )

    organization_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="ID организации",
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
        """Строковое представление подписки."""
        return f"<WebhookSubscription(id={self.id}, name={self.name}, url={self.url[:30]}...)>"
