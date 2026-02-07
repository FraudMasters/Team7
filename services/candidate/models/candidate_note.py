"""
CandidateNote model for collaborative notes and comments on candidates.

Модель CandidateNote для совместных заметок и комментариев к кандидатам.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateNote(Base, UUIDMixin, TimestampMixin):
    """
    CandidateNote model for collaborative notes and comments on candidates.

    Модель CandidateNote для совместных заметок и комментариев к кандидатам.

    This model enables team collaboration by allowing recruiters and hiring managers
    to add notes and comments to candidate profiles. Notes can be private or visible
    to the entire team, supporting coordinated hiring decisions.

    Эта модель обеспечивает командную работу, позволяя рекрутерам и наймерам
    добавлять заметки и комментарии к профилям кандидатов. Заметки могут быть
    приватными или видимыми всей команде, что поддерживает скоординированные
    решения при найме.

    Attributes:
        id: UUID primary key / UUID первичный ключ
        candidate_id: Foreign key to Candidate / Внешний ключ к Candidate
        recruiter_id: Optional foreign key to Recruiter (author of the note) / Внешний ключ к Recruiter (автор заметки)
        content: The note or comment content / Содержимое заметки или комментария
        is_private: Whether the note is private (only visible to author) or team-visible / Приватность заметки
        is_pinned: Whether the note is pinned to the top / Закреплена ли заметка сверху
        created_at: Timestamp when note was created / Время создания заметки
        updated_at: Timestamp when note was last updated / Время последнего обновления заметки

    Example:
        >>> note = CandidateNote(
        ...     candidate_id=candidate_id,
        ...     recruiter_id=recruiter_id,
        ...     content="Strong technical skills, good culture fit",
        ...     is_private=False
        ... )
    """

    __tablename__ = "candidate_notes"

    # Foreign keys / Внешние ключи
    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Note content / Содержимое заметки
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Visibility and display settings / Настройки видимости и отображения
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<CandidateNote(id={self.id}, candidate_id={self.candidate_id}, is_private={self.is_private})>"
