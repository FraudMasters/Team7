"""
CandidateActivity model for tracking candidate stage changes and notes history.

Модель CandidateActivity для отслеживания изменений этапов кандидата и истории заметок.
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateActivityType(str, enum.Enum):
    """
    Types of candidate activities that can be tracked.

    Типы активностей кандидата, которые можно отслеживать.

    These activity types represent different events in the candidate lifecycle.

    Эти типы активностей представляют различные события в жизненном цикле кандидата.
    """

    STAGE_CHANGED = "stage_changed"          # Hiring stage changed / Изменен этап найма
    NOTE_ADDED = "note_added"                # Note was added / Заметка добавлена
    NOTE_UPDATED = "note_updated"            # Note was updated / Заметка обновлена
    NOTE_DELETED = "note_deleted"            # Note was deleted / Заметка удалена
    TAG_ADDED = "tag_added"                  # Tag was added / Тег добавлен
    TAG_REMOVED = "tag_removed"              # Tag was removed / Тег удален
    RANKING_CHANGED = "ranking_changed"      # Candidate ranking changed / Рейтинг кандидата изменен
    RATING_CHANGED = "rating_changed"        # Candidate rating changed / Оценка кандидата изменена
    CONTACT_ATTEMPT = "contact_attempt"      # Attempted to contact candidate / Попытка связи с кандидатом
    INTERVIEW_SCHEDULED = "interview_scheduled"  # Interview was scheduled / Собеседование запланировано
    FEEDBACK_PROVIDED = "feedback_provided"  # Feedback was provided / Feedback предоставлен
    STATUS_UPDATED = "status_updated"        # Candidate status updated / Статус кандидата обновлен
    EMAIL_SENT = "email_sent"                # Email was sent to candidate / Email отправлен кандидату
    CALLOUT_MADE = "callout_made"            # Phone call was made / Звонок был сделан


class CandidateActivity(Base, UUIDMixin, TimestampMixin):
    """
    CandidateActivity model for tracking candidate stage changes and notes history.

    Модель CandidateActivity для отслеживания изменений этапов кандидата и истории заметок.

    This model maintains a comprehensive audit trail of all candidate-related activities,
    enabling recruiters to track the complete history of a candidate's journey through
    the hiring pipeline. It records stage transitions, notes additions/changes, tag
    modifications, and other significant candidate events.

    Эта модель ведет полную историю всех активностей, связанных с кандидатом,
    позволяя рекрутерам отслеживать полный путь кандидата через воронку найма.
    Она записывает переходы между этапами, добавления/изменения заметок, изменения
    тегов и другие важные события.

    Attributes:
        id: UUID primary key / UUID первичный ключ
        activity_type: Type of activity that occurred / Тип произошедшей активности
        candidate_id: Foreign key to the candidate / Внешний ключ к кандидату
        vacancy_id: Optional foreign key to the related job vacancy / Внешний ключ к вакансии
        from_stage: Previous hiring stage (for stage changes) / Предыдущий этап найма
        to_stage: New hiring stage (for stage changes) / Новый этап найма
        note_id: Optional foreign key to related CandidateNote / Внешний ключ к CandidateNote
        tag_id: Optional foreign key to related CandidateTag / Внешний ключ к CandidateTag
        recruiter_id: Foreign key to Recruiter who performed the action / Внешний ключ к Recruiter
        activity_data: JSON object with activity-specific data / JSON с данными активности
        reason: Optional text explanation for the activity / Текстовое объяснение активности
        created_at: Timestamp when activity was recorded / Время записи активности
        updated_at: Timestamp when activity was last updated / Время последнего обновления активности

    Example:
        >>> activity = CandidateActivity(
        ...     activity_type=CandidateActivityType.STAGE_CHANGED,
        ...     candidate_id=candidate_id,
        ...     from_stage="NEW",
        ...     to_stage="SCREENING",
        ...     recruiter_id=recruiter_id,
        ...     reason="Passed initial resume screen"
        ... )
    """

    __tablename__ = "candidate_activities"

    # Activity type / Тип активности
    activity_type: Mapped[CandidateActivityType] = mapped_column(
        String(50), nullable=False, index=True
    )

    # Related entities / Связанные сущности
    candidate_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Stage change fields / Поля изменения этапа
    from_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    to_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Related objects / Связанные объекты
    note_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("candidate_notes.id", ondelete="SET NULL"), nullable=True
    )
    tag_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("candidate_tags.id", ondelete="SET NULL"), nullable=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Additional data / Дополнительные данные
    activity_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CandidateActivity(id={self.id}, type={self.activity_type}, candidate={self.candidate_id})>"
