"""
CandidateTag model for custom candidate tags.

Модель CandidateTag для пользовательских тегов кандидатов.
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateTag(Base, UUIDMixin, TimestampMixin):
    """
    CandidateTag model for custom candidate tags.

    Модель CandidateTag для пользовательских тегов кандидатов.

    This model enables organizations to create custom tags for categorizing
    and prioritizing candidates. Common use cases include priority levels
    (High Priority, Urgent), work preferences (Remote, Hybrid), or sourcing
    channels (Referral, LinkedIn Recruiter, etc.).

    Эта модель позволяет организациям создавать пользовательские теги для
    категоризации и приоритизации кандидатов. Typical use cases include уровни
    приоритета (High Priority, Urgent), предпочтения по работе (Remote, Hybrid)
    или каналы источников (Referral, LinkedIn Recruiter и т.д.).

    Attributes:
        id: UUID primary key / UUID первичный ключ
        organization_id: Organization that owns this tag / Организация-владелец тега
        tag_name: Name of the tag / Имя тега
        tag_order: Order in which this tag appears in the UI / Порядок отображения в UI
        is_default: Whether this is a default tag / Является ли тег стандартным
        is_active: Whether this tag is currently active / Активен ли тег
        color: Optional color code for UI display / Цветовой код для отображения в UI
        description: Optional description of when to use this tag / Описание использования тега
        created_at: Timestamp when record was created / Время создания записи
        updated_at: Timestamp when record was last updated / Время последнего обновления записи

    Example:
        >>> tag = CandidateTag(
        ...     organization_id="org-123",
        ...     tag_name="High Priority",
        ...     color="#EF4444",
        ...     is_active=True
        ... )
    """

    __tablename__ = "candidate_tags"

    # Organization / Организация
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tag details / Детали тега
    tag_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tag_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Display options / Параметры отображения
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code / Hex код цвета
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateTag(id={self.id}, org={self.organization_id}, tag={self.tag_name})>"
