"""
PhoneCall model for phone call-specific communication data
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CallType(str, enum.Enum):
    """Types of phone calls"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    MISSED = "missed"


class PhoneCall(Base, UUIDMixin, TimestampMixin):
    """
    PhoneCall model for phone call-specific communication data

    This model extends the Communication base model with phone call-specific fields.
    It stores detailed call metadata including phone numbers, duration, call type,
    and recording information.

    Attributes:
        id: UUID primary key
        communication_id: Foreign key to Communication base model
        from_number: Caller phone number (in E.164 format)
        to_number: Recipient phone number (in E.164 format)
        duration: Call duration in seconds
        call_type: Type of call (inbound, outbound, missed)
        recording_url: Optional URL to call recording
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "phone_calls"

    communication_id: Mapped[UUID] = mapped_column(
        ForeignKey("communications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    from_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    call_type: Mapped[CallType] = mapped_column(
        String(50), nullable=False, index=True
    )
    recording_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    def __repr__(self) -> str:
        return f"<PhoneCall(id={self.id}, communication_id={self.communication_id}, call_type={self.call_type}, duration={self.duration})>"
