"""
Модель шаблона SMS для Notification Service.

# Русский комментарий:
Этот модуль определяет модель шаблона SMS для переиспользуемых
шаблонов уведомлений с поддержкой подсчета символов и сегментов.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, JSON, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database import Base

logger = logging.getLogger(__name__)


class SMSTemplate(Base):
    """
    Модель шаблона SMS.

    Хранит переиспользуемые шаблоны SMS с переменными для подстановки
    и поддержкой подсчета символов и сегментов.

    Attributes:
        id: Уникальный идентификатор шаблона
        name: Название шаблона
        body: Текст SMS с переменными
        variables: Список переменных для подстановки
        template_blocks: JSON-структура для построителя шаблонов
        category: Категория шаблона
        pipeline_stage: Этап pipeline для шаблона
        is_active: Флаг активности шаблона
        language: Язык шаблона (en, ru)
        created_at: Время создания записи
        updated_at: Время последнего обновления записи
    """

    __tablename__ = "sms_templates"

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

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Текст SMS с переменными",
    )

    variables: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Список переменных для подстановки",
    )

    template_blocks: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="JSON-структура для построителя шаблонов",
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Категория шаблона",
    )

    pipeline_stage: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Этап pipeline для шаблона",
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

    @property
    def character_count(self) -> int:
        """
        Подсчет количества символов в теле SMS.

        Returns:
            Количество символов в body
        """
        return len(self.body) if self.body else 0

    @property
    def segment_count(self) -> int:
        """
        Подсчет количества SMS-сегментов.

        SMS сегментируется по 160 символов для GSM-7 кодировки.
        Для Unicode (если есть не-GSM символы) - 70 символов на сегмент.

        Returns:
            Количество сегментов SMS
        """
        if not self.body:
            return 0

        char_count = self.character_count

        # Проверяем, содержит ли текст не-GSM символы
        # GSM-7 базовый набор: A-Z, a-z, 0-9, и основные символы
        gsm_basic = set(
            "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
            "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
        )

        # Если есть символы вне GSM-7, используем Unicode (70 символов/сегмент)
        is_unicode = any(char not in gsm_basic for char in self.body)

        if is_unicode:
            # Unicode: 70 символов на сегмент
            chars_per_segment = 70
        else:
            # GSM-7: 160 символов на сегмент
            chars_per_segment = 160

        # Вычисляем количество сегментов
        if char_count == 0:
            return 0
        elif char_count <= chars_per_segment:
            return 1
        else:
            # Для многосегментных SMS используем меньший лимит
            # (GSM-7: 153, Unicode: 67) из-за заголовка UDH
            chars_per_multi_segment = 153 if not is_unicode else 67
            return (char_count + chars_per_multi_segment - 1) // chars_per_multi_segment

    def preview(self, context: Optional[dict] = None) -> str:
        """
        Генерирует preview SMS с подстановкой переменных.

        Args:
            context: Словарь с данными для подстановки переменных

        Returns:
            Текст SMS с подставленными значениями
        """
        if not context:
            context = {}

        preview_text = self.body

        # Простая подстановка переменных в формате {variable_name}
        for key, value in context.items():
            preview_text = preview_text.replace(f"{{{key}}}", str(value))

        return preview_text

    def __repr__(self) -> str:
        """Строковое представление шаблона."""
        return f"<SMSTemplate(id={self.id}, name={self.name}, language={self.language})>"
