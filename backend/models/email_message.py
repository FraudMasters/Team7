"""
EmailMessage model for email-specific communication data
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class EmailMessage(Base, UUIDMixin, TimestampMixin):
    """
    EmailMessage model for email-specific communication data

    This model extends the Communication base model with email-specific fields.
    It stores detailed email metadata including addresses, message threading,
    and synchronization information.

    Attributes:
        id: UUID primary key
        communication_id: Foreign key to Communication base model
        from_address: Sender email address
        to_address: Recipient email address(es), comma-separated
        cc_address: CC recipients email address(es), comma-separated
        bcc_address: BCC recipients email address(es), comma-separated
        message_id: Unique message ID from email headers (for deduplication)
        thread_id: Thread ID for email conversation tracking
        in_reply_to: Message ID of the email this is replying to
        synced_at: Timestamp when email was last synced from external server
        created_at: Timestamp when record was created (inherited)
        updated_at: Timestamp when record was last updated (inherited)
    """

    __tablename__ = "email_messages"

    communication_id: Mapped[UUID] = mapped_column(
        ForeignKey("communications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    from_address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    cc_address: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    bcc_address: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    in_reply_to: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    synced_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<EmailMessage(id={self.id}, communication_id={self.communication_id}, from_address={self.from_address})>"
