"""
Notification model for real-time user notifications
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class NotificationType(str, enum.Enum):
    """Types of notifications that can be sent to users"""

    # Candidate-related notifications
    CANDIDATE_STAGE_CHANGED = "candidate_stage_changed"
    CANDIDATE_NOTE_ADDED = "candidate_note_added"
    CANDIDATE_TAG_ADDED = "candidate_tag_added"
    CANDIDATE_RANKING_CHANGED = "candidate_ranking_changed"
    NEW_CANDIDATE_MATCH = "new_candidate_match"
    CANDIDATE_REVIEW_REQUIRED = "candidate_review_required"

    # Vacancy-related notifications
    VACANCY_CREATED = "vacancy_created"
    VACANCY_UPDATED = "vacancy_updated"
    VACANCY_STATUS_CHANGED = "vacancy_status_changed"

    # System notifications
    SYSTEM_ANNOUNCEMENT = "system_announcement"
    REPORT_GENERATED = "report_generated"
    BACKUP_COMPLETED = "backup_completed"

    # Digest notifications
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"

    # Alert notifications
    SEARCH_ALERT_MATCH = "search_alert_match"


class Notification(Base, UUIDMixin, TimestampMixin):
    """
    Notification model for real-time user notifications

    This model stores notifications for recruiters and other users, supporting
    in-app notifications, email digests, and real-time WebSocket delivery.
    Notifications can be linked to related entities like candidates, vacancies,
    or other system resources for context navigation.

    Attributes:
        id: UUID primary key
        recipient_id: Foreign key to the Recruiter who should receive this notification
        notification_type: Type of notification (from NotificationType enum)
        title: Short title/heading for the notification
        message: Detailed message content
        data: Optional JSON object with additional notification-specific data
        is_read: Boolean flag indicating if the notification has been read
        read_at: Optional timestamp when the notification was marked as read
        delivered_at: Optional timestamp when the notification was successfully delivered
        delivery_failed: Boolean flag indicating if delivery failed
        delivery_error: Optional error message if delivery failed
        retry_count: Number of delivery retry attempts
        candidate_id: Optional foreign key to related candidate (resume/match result)
        vacancy_id: Optional foreign key to related job vacancy
        action_url: Optional URL for the notification's action link
        created_at: Timestamp when notification was created (inherited)
        updated_at: Timestamp when notification was last updated (inherited)
    """

    __tablename__ = "notifications"

    recipient_id: Mapped[UUID] = mapped_column(
        ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        String(50), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivery_failed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivery_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)
    candidate_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.notification_type}, recipient={self.recipient_id}, read={self.is_read})>"
