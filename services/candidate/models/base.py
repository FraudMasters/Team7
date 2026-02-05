"""
Base database configuration and common mixins.

Базовая конфигурация базы данных и общие миксины.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Базовый класс для всех моделей базы данных.

    All SQLAlchemy models should inherit from this class to get
    access to the declarative mapping and metadata.

    Все модели SQLAlchemy должны наследоваться от этого класса для
    получения доступа к декларативному маппингу и метаданным.
    """
    pass


class TimestampMixin:
    """
    Mixin for adding created_at and updated_at timestamps.

    Миксин для добавления временных меток created_at и updated_at.

    This mixin automatically tracks when a record is created and updated.

    Этот миксин автоматически отслеживает время создания и обновления записи.

    Attributes:
        created_at: Timestamp when the record was created / Время создания записи
        updated_at: Timestamp when the record was last updated / Время последнего обновления записи
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """
    Mixin for adding UUID primary key.

    Миксин для добавления первичного ключа UUID.

    This mixin automatically generates a UUID primary key for each record.

    Этот миксин автоматически генерирует первичный ключ UUID для каждой записи.

    Attributes:
        id: UUID primary key / Первичный ключ UUID
    """

    @declared_attr.directive
    def id(cls) -> Mapped[uuid4]:
        return mapped_column(
            UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
        )
