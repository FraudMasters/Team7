"""
Базовая конфигурация базы данных и общие миксины.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Базовый класс для всех моделей базы данных."""

    pass


class TimestampMixin:
    """Миксин для добавления временных меток created_at и updated_at."""

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
    """Миксин для добавления первичного ключа UUID."""

    @declared_attr.directive
    def id(cls) -> Mapped[uuid4]:
        return mapped_column(
            UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
        )
