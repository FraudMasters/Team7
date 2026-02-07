"""
CookieConsent model for tracking GDPR cookie preferences
"""
from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDMixin


class CookieConsent(Base, UUIDMixin, TimestampMixin):
    """
    CookieConsent model for tracking user cookie preferences and GDPR compliance

    This model stores user preferences for different cookie categories as required by GDPR
    and ePrivacy Directive. Essential cookies are always enabled, but users can opt-in/out
    of analytical, functional, and marketing cookies through a GDPR-compliant cookie banner.

    GDPR Requirements Met:
    - Prior consent for non-essential cookies
    - Granular control over cookie categories
    - Easy withdrawal of consent
    - Complete audit trail of consent changes
    - Cookie consent tied to session/browser for anonymous users

    Attributes:
        id: UUID primary key
        session_id: Browser session ID for anonymous users (optional)
        user_id: Foreign key to User for logged-in users (optional)
        essential_cookies: Essential cookies (always True, required for site functionality)
        functional_cookies: Functional cookies for preferences and features
        analytics_cookies: Analytics cookies for usage tracking and insights
        marketing_cookies: Marketing/targeting cookies for advertising
        consent_version: Version of the cookie policy shown to user
        ip_address: IP address from which consent was given (for verification)
        created_at: Timestamp when consent was recorded (inherited from TimestampMixin)
        updated_at: Timestamp when consent was last updated (inherited from TimestampMixin)
    """

    __tablename__ = "cookie_consent"

    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    essential_cookies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    functional_cookies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    analytics_cookies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    marketing_cookies: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CookieConsent(id={self.id}, "
            f"essential={self.essential_cookies}, "
            f"analytics={self.analytics_cookies}, "
            f"marketing={self.marketing_cookies})>"
        )

    def has_granted_consent(self, cookie_category: str) -> bool:
        """Check if user has granted consent for a specific cookie category"""
        category_map = {
            "essential": self.essential_cookies,
            "functional": self.functional_cookies,
            "analytics": self.analytics_cookies,
            "marketing": self.marketing_cookies,
        }
        return category_map.get(cookie_category.lower(), False)
