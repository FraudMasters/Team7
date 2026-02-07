"""
Модель шаблона email для Notification Service.

# Русский комментарий:
Этот модуль определяет модель шаблона email для переиспользуемых
шаблонов уведомлений.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, JSON, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

logger = logging.getLogger(__name__)


class EmailTemplate(Base):
    """
    Модель шаблона email.

    Хранит переиспользуемые шаблоны email с переменными для подстановки.

    Attributes:
        id: Уникальный идентификатор шаблона
        name: Название шаблона
        subject: Тема email с переменными
        body: Тело email с переменными
        variables: Список переменных для подстановки
        is_active: Флаг активности шаблона
        language: Язык шаблона (en, ru)
        created_at: Время создания записи
        updated_at: Время последнего обновления записи
    """

    __tablename__ = "email_templates"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Уникальный идентификатор шаблона",
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="Название шаблона",
    )

    subject: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Тема email с переменными",
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Тело email с переменными",
    )

    variables: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Список переменных для подстановки",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Флаг активности шаблона",
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False,
        comment="Язык шаблона",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Описание шаблона",
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
        """Строковое представление шаблона."""
        return f"<EmailTemplate(id={self.id}, name={self.name}, language={self.language})>"
