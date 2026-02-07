"""
Communication base model for tracking all candidate interactions
"""
import enum
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CommunicationType(str, enum.Enum):
    """Types of communication channels"""

    EMAIL = "email"
    SMS = "sms"
    PHONE_CALL = "phone_call"
    IN_SYSTEM = "in_system"


class CommunicationDirection(str, enum.Enum):
    """Direction of communication (inbound or outbound)"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CommunicationStatus(str, enum.Enum):
    """Status of the communication"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    READ = "read"


class Communication(Base, UUIDMixin, TimestampMixin):
    """
    Communication base model for tracking all candidate interactions

    This model provides a unified way to track all communications with candidates,
    including emails, SMS messages, phone calls, and in-system messages. It serves
    as a base class that can be extended by specific communication type models
    (EmailMessage, SMSMessage, PhoneCall) while maintaining common fields and
    relationships in one place.

    Attributes:
        id: UUID primary key
        candidate_id: Foreign key to Resume (candidate)
        vacancy_id: Optional foreign key to JobVacancy
        recruiter_id: Optional foreign key to Recruiter (sender/receiver)
        type: Type of communication (email, sms, phone_call, in_system)
        direction: Direction of communication (inbound, outbound)
        status: Current status of the communication
        subject: Optional subject line (for emails, etc.)
        body: Content of the communication
        sent_at: Optional timestamp when communication was sent
        received_at: Optional timestamp when communication was received
        metadata: JSON field for additional communication-specific data
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "communications"

    candidate_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vacancy_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recruiter_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    type: Mapped[CommunicationType] = mapped_column(
        String(50), nullable=False, index=True
    )
    direction: Mapped[CommunicationDirection] = mapped_column(
        String(50), nullable=False, index=True
    )
    status: Mapped[CommunicationStatus] = mapped_column(
        String(50), nullable=False, index=True, default=CommunicationStatus.PENDING
    )
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    received_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Communication(id={self.id}, type={self.type}, direction={self.direction}, candidate_id={self.candidate_id})>"
