"""
ConsentRecord model for tracking user consent and GDPR compliance
"""
import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class ConsentType(str, enum.Enum):
    """Types of consent that can be tracked for GDPR compliance"""

    # Core data processing consents
    DATA_PROCESSING = "data_processing"  # Consent for processing personal data
    DATA_STORAGE = "data_storage"  # Consent for storing data on servers
    PROFILE_CREATION = "profile_creation"  # Consent for creating candidate profiles

    # Analytics and tracking
    ANALYTICS = "analytics"  # Consent for analytics tracking
    PERFORMANCE_MONITORING = "performance_monitoring"  # Consent for app performance monitoring

    # Marketing and communications
    MARKETING_EMAILS = "marketing_emails"  # Consent for marketing emails
    NEWSLETTER = "newsletter"  # Consent for newsletter subscription
    JOB_ALERTS = "job_alerts"  # Consent for job notification alerts

    # Cookies and tracking
    ESSENTIAL_COOKIES = "essential_cookies"  # Essential cookies (can't be disabled)
    FUNCTIONAL_COOKIES = "functional_cookies"  # Functional cookies for preferences
    TARGETING_COOKIES = "targeting_cookies"  # Targeting/advertising cookies

    # Data sharing
    DATA_SHARING_THIRD_PARTY = "data_sharing_third_party"  # Consent for sharing with partners
    DATA_SHARING_RECRUITERS = "data_sharing_recruiters"  # Consent for sharing with recruiters

    # Automated processing
    AUTOMATED_PROCESSING = "automated_processing"  # Consent for automated decision making
    AI_ANALYSIS = "ai_analysis"  # Consent for AI-powered resume analysis


class ConsentRecord(Base, UUIDMixin, TimestampMixin):
    """
    ConsentRecord model for tracking user consent and GDPR compliance

    This model provides a comprehensive audit trail of user consents, enabling GDPR compliance
    through explicit consent tracking, the right to withdraw consent, and complete consent history.
    Each consent record captures what the user agreed to, when they agreed, the legal text they
    accepted, and any subsequent withdrawals or changes.

    GDPR Requirements Met:
    - Lawfulness, fairness, and transparency: Explicit consent tracking
    - Purpose limitation: Consent tied to specific processing purposes
    - Data minimization: Granular consent types for minimal data collection
    - Storage limitation: Consent can be withdrawn, triggering data deletion
    - Integrity and confidentiality: Complete audit trail of consent changes
    - Accountability: Timestamped records with IP and user agent for verification

    Attributes:
        id: UUID primary key
        consent_type: Type of consent granted (e.g., data_processing, analytics)
        granted: Whether consent was granted (True) or withdrawn/rejected (False)
        user_id: Foreign key to User who gave/withdrew consent
        organization_id: Foreign key to Organization where consent was given
        consent_text: The exact legal text shown to and accepted by the user
        consent_version: Version of the privacy policy/consent document
        ip_address: IP address from which consent was given (for verification)
        user_agent: User agent string of the client (for verification)
        withdrawn_at: Timestamp when consent was withdrawn (NULL if active)
        withdrawal_reason: Optional reason provided by user for withdrawal
        created_at: Timestamp when consent was recorded
        updated_at: Timestamp when the record was last updated
    """

    __tablename__ = "consent_records"

    consent_type: Mapped[ConsentType] = mapped_column(
        String(50), nullable=False, index=True
    )
    granted: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    consent_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    withdrawal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        status = "granted" if self.granted and not self.withdrawn_at else "withdrawn"
        return f"<ConsentRecord(id={self.id}, type={self.consent_type}, status={status})>"

    def is_active(self) -> bool:
        """Check if consent is currently active (granted and not withdrawn)"""
        return self.granted and self.withdrawn_at is None
