"""
Candidate model for managing candidate profiles and hiring pipeline status.

Модель кандидата для управления профилями кандидатов и статусом найма.
"""
import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CandidateStatus(str, enum.Enum):
    """
    Status of candidate in the hiring pipeline.

    Статус кандидата в процессе найма.

    Each candidate moves through these stages during the recruitment process.

    Каждый кандидат проходит эти этапы в процессе найма.
    """

    # Pipeline stages / Этапы воронки
    NEW = "NEW"                      # New candidate / Новый кандидат
    CONTACTED = "CONTACTED"          # Candidate contacted / Кандидат contacted
    SCREENING = "SCREENING"          # Initial screening / Первичный отбор
    INTERVIEW = "INTERVIEW"          # Interview stage / Этап собеседования
    TECHNICAL = "TECHNICAL"          # Technical interview / Техническое собеседование
    OFFER = "OFFER"                  # Offer extended / Выставлено предложение
    HIRED = "HIRED"                  # Candidate hired / Кандидат нанят
    REJECTED = "REJECTED"            # Candidate rejected / Кандидат отклонен
    WITHDRAWN = "WITHDRAWN"          # Candidate withdrew / Кандидат отказался
    ON_HOLD = "ON_HOLD"              # On hold / На удержании


class Candidate(Base, UUIDMixin, TimestampMixin):
    """
    Candidate model for managing candidate profiles and hiring pipeline status.

    Модель кандидата для управления профилями и статусом найма.

    This model represents a candidate in the hiring system. Candidates are
    typically created from resumes and progress through the hiring pipeline.

    Эта модель представляет кандидата в системе найма. Кандидаты обычно
    создаются на основе резюме и проходят через воронку найма.

    Attributes:
        id: UUID primary key / UUID первичный ключ
        resume_id: Foreign key to Resume (in Resume Processing Service) / Внешний ключ к Resume
        full_name: Full name of the candidate / Полное имя кандидата
        email: Email address / Email адрес
        phone: Phone number / Номер телефона
        current_position: Current job position / Текущая должность
        current_company: Current company / Текущая компания
        years_of_experience: Total years of experience / Общий стаж работы в годах
        expected_salary: Expected salary range / Ожидаемая зарплата
        location: Candidate location / Местоположение кандидата
        linkedin_url: LinkedIn profile URL / Ссылка на профиль LinkedIn
        portfolio_url: Portfolio website URL / Ссылка на портфолио
        status: Current hiring pipeline status / Текущий статус воронки найма
        source: Candidate source (LinkedIn, referral, etc.) / Источник кандидата
        tags: List of tag IDs associated with candidate / Список ID тегов кандидата
        rating: Candidate rating (1-5) / Рейтинг кандидата (1-5)
        is_active: Whether candidate profile is active / Активен ли профиль кандидата
        notes_count: Cached count of notes / Кэшированное количество заметок
        extra_metadata: Additional metadata in JSON format / Дополнительные метаданные в JSON
        created_at: Timestamp when candidate was created / Время создания кандидата
        updated_at: Timestamp when candidate was last updated / Время последнего обновления

    Example:
        >>> candidate = Candidate(
        ...     resume_id=uuid4(),
        ...     full_name="Ivan Ivanov",
        ...     email="ivan@example.com",
        ...     status=CandidateStatus.NEW
        ... )
    """

    __tablename__ = "candidates"

    # Foreign key to Resume (stored in Resume Processing Service)
    # Внешний ключ к Resume (хранится в Resume Processing Service)
    resume_id: Mapped[str] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Basic information / Основная информация
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Professional information / Профессиональная информация
    current_position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_salary: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # External links / Внешние ссылки
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Hiring pipeline status / Статус воронки найма
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), default=CandidateStatus.NEW, nullable=False, index=True
    )

    # Source information / Информация об источнике
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Tags and ratings / Теги и рейтинги
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # List of tag IDs / Список ID тегов
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 rating / Рейтинг 1-5

    # Status flags / Флаги статуса
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Cached counts / Кэшированные счетчики
    notes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Additional metadata / Дополнительные метаданные
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.full_name}, status={self.status.value})>"
