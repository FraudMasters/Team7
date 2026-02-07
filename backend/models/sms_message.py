"""
SMSMessage model for SMS-specific communication data
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class SMSDeliveryStatus(str, enum.Enum):
    """Delivery status for SMS messages"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    UNDELIVERED = "undelivered"
    FAILED = "failed"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class SMSMessage(Base, UUIDMixin, TimestampMixin):
    """
    SMSMessage model for SMS-specific communication data

    This model extends the Communication base model with SMS-specific fields.
    It stores detailed SMS metadata including phone numbers, provider information,
    and delivery tracking.

    Attributes:
        id: UUID primary key
        communication_id: Foreign key to Communication base model
        from_number: Sender phone number (in E.164 format)
        to_number: Recipient phone number (in E.164 format)
        provider: SMS service provider (e.g., Twilio, SendGrid, AWS SNS)
        delivery_status: Current delivery status of the SMS
        delivery_error: Optional error message if delivery failed
        provider_message_id: External message ID from the SMS provider
        segment_count: Number of SMS segments used (for long messages)
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "sms_messages"

    communication_id: Mapped[UUID] = mapped_column(
        ForeignKey("communications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    from_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    delivery_status: Mapped[SMSDeliveryStatus] = mapped_column(
        String(50), nullable=False, index=True, default=SMSDeliveryStatus.PENDING
    )
    delivery_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    segment_count: Mapped[Optional[int]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<SMSMessage(id={self.id}, communication_id={self.communication_id}, to_number={self.to_number}, delivery_status={self.delivery_status})>"
