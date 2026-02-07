"""
Webhook models for event subscription and delivery tracking
"""
import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, JSON, String, Boolean, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class WebhookEventType(str, enum.Enum):
    """Types of events that can be subscribed to via webhooks"""

    # Candidate events
    CANDIDATE_CREATED = "candidate.created"
    CANDIDATE_UPDATED = "candidate.updated"
    CANDIDATE_DELETED = "candidate.deleted"

    # Ranking events
    RANKING_CREATED = "ranking.created"
    RANKING_UPDATED = "ranking.updated"
    RANKING_DELETED = "ranking.deleted"

    # Status change events
    STATUS_CHANGED = "status.changed"
    STAGE_CHANGED = "stage.changed"

    # Resume events
    RESUME_UPLOADED = "resume.uploaded"
    RESUME_PROCESSED = "resume.processed"
    RESUME_ANALYZED = "resume.analyzed"

    # Vacancy events
    VACANCY_CREATED = "vacancy.created"
    VACANCY_UPDATED = "vacancy.updated"
    VACANCY_FILLED = "vacancy.filled"

    # Match events
    MATCH_CREATED = "match.created"
    MATCH_UPDATED = "match.updated"

    # Feedback events
    FEEDBACK_SUBMITTED = "feedback.submitted"

    # Report events
    REPORT_GENERATED = "report.generated"
    REPORT_EXPORTED = "report.exported"

    # Note events
    NOTE_CREATED = "note.created"
    NOTE_UPDATED = "note.updated"

    # Workflow events
    WORKFLOW_TRIGGERED = "workflow.triggered"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"


class WebhookDeliveryStatus(str, enum.Enum):
    """Status of webhook delivery attempts"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(Base, UUIDMixin, TimestampMixin):
    """
    WebhookSubscription model for managing webhook event subscriptions

    This model enables developers to subscribe to system events and receive
    real-time notifications via HTTP webhooks. Supports event filtering,
    secret-based signature verification, and automatic retry logic.

    Attributes:
        id: UUID primary key
        url: HTTP/HTTPS endpoint URL to receive webhook deliveries
        events: JSON array of event types to subscribe to
        secret: Optional HMAC secret for webhook signature verification
        is_active: Whether the subscription is currently active
        api_key_id: Foreign key to API key that owns this subscription
        last_delivery_at: Timestamp of last successful delivery
        failure_count: Number of consecutive failed deliveries
        created_at: Timestamp when subscription was created (inherited)
        updated_at: Timestamp when subscription was last updated (inherited)
    """

    __tablename__ = "webhook_subscriptions"

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    events: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    api_key_id: Mapped[Optional["UUID"]] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=True, index=True
    )
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<WebhookSubscription(id={self.id}, url={self.url}, active={self.is_active})>"

    def is_subscribed_to(self, event_type: str) -> bool:
        """Check if this subscription is for a specific event type"""
        return event_type in self.events

    def should_disable(self, threshold: int = 10) -> bool:
        """Check if subscription should be disabled due to too many failures"""
        return self.failure_count >= threshold


class WebhookDeliveryLog(Base, UUIDMixin, TimestampMixin):
    """
    WebhookDeliveryLog model for tracking webhook delivery attempts

    This model maintains a detailed log of all webhook delivery attempts,
    including success/failure status, HTTP response codes, and retry timing.
    Enables monitoring and debugging of webhook integrations.

    Attributes:
        id: UUID primary key
        subscription_id: Foreign key to WebhookSubscription
        event_type: Type of event being delivered
        event_data: JSON payload delivered to the webhook endpoint
        status: Current delivery status (pending, success, failed, retrying)
        status_code: HTTP status code received from webhook endpoint
        response_body: Response body received from webhook endpoint
        attempt_count: Number of delivery attempts made
        next_retry_at: Scheduled timestamp for next retry attempt
        error_message: Error message if delivery failed
        created_at: Timestamp when delivery log was created (inherited)
        updated_at: Timestamp when delivery log was last updated (inherited)
    """

    __tablename__ = "webhook_delivery_logs"

    subscription_id: Mapped["UUID"] = mapped_column(
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[WebhookDeliveryStatus] = mapped_column(
        String(50), nullable=False, default=WebhookDeliveryStatus.PENDING, index=True
    )
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<WebhookDeliveryLog(id={self.id}, event={self.event_type}, status={self.status})>"

    def is_successful(self) -> bool:
        """Check if the delivery was successful"""
        return self.status == WebhookDeliveryStatus.SUCCESS

    def should_retry(self, max_attempts: int = 5) -> bool:
        """Check if another retry attempt should be made"""
        return (
            not self.is_successful()
            and self.attempt_count < max_attempts
            and self.status != WebhookDeliveryStatus.PENDING
        )

    def calculate_next_retry(self) -> datetime:
        """Calculate exponential backoff for next retry"""
        import math

        # Exponential backoff: 30s, 60s, 120s, 240s, 480s, etc.
        delay_seconds = 30 * (2 ** min(self.attempt_count, 6))
        from datetime import timedelta

        return datetime.utcnow() + timedelta(seconds=delay_seconds)
