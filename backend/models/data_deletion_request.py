"""
DataDeletionRequest model for GDPR right-to-be-forgotten requests
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class DeletionRequestStatus(str, enum.Enum):
    """Status of a data deletion request"""

    PENDING = "pending"  # Request received, awaiting verification
    VERIFIED = "verified"  # Request verified by user, ready for processing
    PROCESSING = "processing"  # Deletion is in progress
    COMPLETED = "completed"  # Data deletion completed successfully
    REJECTED = "rejected"  # Request rejected (e.g., legal obligation to retain data)
    REQUIRES_VERIFICATION = "requires_verification"  # Additional verification needed


class DataDeletionRequest(Base, UUIDMixin, TimestampMixin):
    """
    DataDeletionRequest model for GDPR right-to-be-forgotten requests

    This model implements GDPR Article 17 - Right to Erasure (Right to be Forgotten).
    It tracks data deletion requests from individuals (candidates, recruiters, etc.)
    who want their personal data removed from the system.

    The deletion request workflow:
    1. Request submitted with email (PENDING)
    2. Verification email sent to requester
    3. Requester verifies via token (VERIFIED)
    4. Admin processes the request (PROCESSING)
    5. Data deleted/anonymized (COMPLETED)
    6. Request may be REJECTED if legal obligation to retain data exists

    GDPR Requirements Met:
    - Right to erasure: Individuals can request deletion of their data
    - Verification: Request must be verified to prevent unauthorized deletion
    - Timely response: Request status tracks processing timeline
    - Legal exceptions: Rejection status for legally required data retention
    - Audit trail: Complete history of deletion requests and outcomes

    Attributes:
        id: UUID primary key
        requester_email: Email address of the person requesting deletion
        requester_type: Type of requester (candidate, recruiter, other)
        status: Current status of the deletion request
        verification_token: Token sent to email for verification
        verified_at: Timestamp when request was verified via email token
        processed_at: Timestamp when deletion processing was completed
        rejection_reason: Reason why request was rejected (if applicable)
        notes: Additional notes or context about the request
        created_at: Timestamp when request was created (inherited)
        updated_at: Timestamp when request was last updated (inherited)
    """

    __tablename__ = "data_deletion_requests"

    requester_email: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    requester_type: Mapped[str] = mapped_column(
        String(50), default="candidate", nullable=False, index=True
    )
    status: Mapped[DeletionRequestStatus] = mapped_column(
        String(50), default=DeletionRequestStatus.PENDING, nullable=False, index=True
    )
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DataDeletionRequest(id={self.id}, email={self.requester_email}, status={self.status})>"

    def is_verified(self) -> bool:
        """Check if request has been verified"""
        return self.verified_at is not None

    def is_completed(self) -> bool:
        """Check if request has been completed"""
        return self.status == DeletionRequestStatus.COMPLETED

    def can_be_processed(self) -> bool:
        """Check if request is ready for processing"""
        return self.status == DeletionRequestStatus.VERIFIED
