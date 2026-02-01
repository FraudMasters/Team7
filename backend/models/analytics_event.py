"""
AnalyticsEvent model for tracking time-based analytics events
"""
import enum
from typing import Optional

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class AnalyticsEventType(str, enum.Enum):
    """Types of analytics events that can be tracked"""

    RESUME_UPLOADED = "resume_uploaded"
    RESUME_PROCESSED = "resume_processed"
    STAGE_CHANGED = "stage_changed"
    MATCH_CREATED = "match_created"
    MATCH_VIEWED = "match_viewed"
    VACANCY_CREATED = "vacancy_created"
    VACANCY_FILLED = "vacancy_filled"
    FEEDBACK_SUBMITTED = "feedback_submitted"
    REPORT_GENERATED = "report_generated"
    REPORT_EXPORTED = "report_exported"


class AnalyticsEvent(Base, UUIDMixin, TimestampMixin):
    """
    AnalyticsEvent model for tracking time-based analytics events

    This model enables comprehensive analytics by recording events that occur
    in the system, allowing for time-to-hire metrics, funnel visualization,
    source tracking, skill demand analysis, and recruiter performance metrics.

    Attributes:
        id: UUID primary key
        event_type: Type of analytics event
        entity_type: Type of entity the event relates to (resume, vacancy, match, etc.)
        entity_id: ID of the related entity
        user_id: Optional foreign key to user who triggered the event
        recruiter_id: Optional foreign key to Recruiter
        session_id: Optional session ID for grouping related events
        event_data: JSON object with event-specific data
        created_at: Timestamp when event was recorded (inherited)
        updated_at: Timestamp when event was last updated (inherited)
    """

    __tablename__ = "analytics_events"

    event_type: Mapped[AnalyticsEventType] = mapped_column(
        String(50), nullable=False, index=True
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    entity_id: Mapped[Optional[UUIDMixin]] = mapped_column(nullable=True, index=True)
    user_id: Mapped[Optional[UUIDMixin]] = mapped_column(nullable=True, index=True)
    recruiter_id: Mapped[Optional[UUIDMixin]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    event_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, entity={self.entity_type})>"
