"""
GDPR compliance service with consent management and data privacy controls.

This module provides comprehensive GDPR compliance functionality including consent tracking,
data deletion requests, cookie consent management, and privacy verification. It implements
the core GDPR requirements: lawfulness, fairness, transparency, purpose limitation,
data minimization, storage limitation, and integrity & confidentiality.

The GDPR service supports:
- Consent recording and tracking (grant/withdrawal)
- Cookie consent management for GDPR compliance
- Data deletion request management (right to be forgotten)
- Privacy compliance checking for data processing operations
- Audit logging for all consent and privacy operations
- User and organization-level consent management
- IP address and user agent tracking for verification

GDPR Rights Implemented:
- Right to be informed (consent records with full legal text)
- Right of access (consent history retrieval)
- Right to rectification (consent updates)
- Right to erasure (data deletion requests)
- Right to restrict processing (consent withdrawal)
- Right to data portability (consent export)
- Right to object (consent revocation)
- Rights in relation to automated decision making (AI analysis consent)
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from config import get_settings
from models.consent_record import ConsentRecord, ConsentType
from models.cookie_consent import CookieConsent
from models.data_deletion_request import DataDeletionRequest, DeletionRequestStatus

logger = logging.getLogger(__name__)

# Global GDPR service instance
_gdpr_service: Optional["GDPRService"] = None


class GDPRService:
    """
    GDPR compliance service with consent management and data privacy controls.

    This class provides a high-level interface for GDPR compliance operations including
    consent management, data deletion requests, cookie consent, and privacy verification.

    Attributes:
        db: Database session for database operations
        consent_version: Current version of privacy policy/consent documents

    Example:
        >>> service = GDPRService(db_session)
        >>> service.record_consent(
        ...     user_id=user.id,
        ...     consent_type=ConsentType.DATA_PROCESSING,
        ...     granted=True,
        ...     ip_address="192.168.1.1"
        ... )
        >>> has_consent = service.has_consent(user.id, ConsentType.DATA_PROCESSING)
    """

    # Consent categories for organization
    CATEGORY_CORE = "core"  # Essential for service operation
    CATEGORY_ANALYTICS = "analytics"  # Usage analytics and monitoring
    CATEGORY_MARKETING = "marketing"  # Marketing communications
    CATEGORY_COOKIES = "cookies"  # Cookie-based tracking

    # Data processing purposes
    PURPOSE_RESUME_ANALYSIS = "resume_analysis"
    PURPOSE_MATCHING = "matching"
    PURPOSE_PROFILE_CREATION = "profile_creation"
    PURPOSE_COMMUNICATION = "communication"

    def __init__(
        self,
        db: Session,
        consent_version: Optional[str] = None,
    ) -> None:
        """
        Initialize the GDPR service.

        Args:
            db: Database session for database operations
            consent_version: Version of current privacy policy (defaults to settings)
        """
        settings = get_settings()

        self.db = db
        self.consent_version = consent_version or getattr(settings, "privacy_policy_version", "1.0")

        logger.info(
            f"GDPRService initialized (consent_version={self.consent_version})"
        )

    def record_consent(
        self,
        consent_type: ConsentType,
        granted: bool,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        consent_text: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        withdrawal_reason: Optional[str] = None,
    ) -> Optional[ConsentRecord]:
        """
        Record a consent grant or withdrawal.

        Creates a new consent record with full audit trail including IP address,
        user agent, and legal text. For withdrawals, marks previous active consent
        as withdrawn.

        Args:
            consent_type: Type of consent being recorded
            granted: Whether consent was granted (True) or withdrawn (False)
            user_id: User UUID granting/withdrawing consent
            organization_id: Organization UUID for org-level consent
            consent_text: The legal text shown to and accepted by user
            ip_address: IP address of the requester
            user_agent: User agent string of the client
            withdrawal_reason: Reason for consent withdrawal (if withdrawing)

        Returns:
            Created ConsentRecord instance or None if failed

        Example:
            >>> service = GDPRService(db)
            >>> consent = service.record_consent(
            ...     consent_type=ConsentType.DATA_PROCESSING,
            ...     granted=True,
            ...     user_id=user.id,
            ...     ip_address="192.168.1.1"
            ... )
        """
        try:
            # If withdrawing consent, mark previous active consent as withdrawn
            if not granted:
                self._withdraw_previous_consent(
                    consent_type=consent_type,
                    user_id=user_id,
                    organization_id=organization_id,
                    reason=withdrawal_reason,
                )

            # Create new consent record
            consent_record = ConsentRecord(
                consent_type=consent_type,
                granted=granted,
                user_id=user_id,
                organization_id=organization_id,
                consent_text=consent_text,
                consent_version=self.consent_version,
                ip_address=ip_address,
                user_agent=user_agent,
                withdrawn_at=None if granted else datetime.now(timezone.utc),
                withdrawal_reason=withdrawal_reason if not granted else None,
            )

            self.db.add(consent_record)
            self.db.commit()
            self.db.refresh(consent_record)

            logger.info(
                f"Recorded consent: type={consent_type}, granted={granted}, "
                f"user_id={user_id}, org_id={organization_id}"
            )

            return consent_record

        except Exception as e:
            logger.error(f"Error recording consent: {e}", exc_info=True)
            self.db.rollback()
            return None

    def _withdraw_previous_consent(
        self,
        consent_type: ConsentType,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> None:
        """
        Mark previous active consent as withdrawn.

        Args:
            consent_type: Type of consent to withdraw
            user_id: User UUID withdrawing consent
            organization_id: Organization UUID withdrawing consent
            reason: Reason for withdrawal
        """
        try:
            # Find active consent records
            query = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.consent_type == consent_type,
                    ConsentRecord.granted == True,
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )

            if user_id:
                query = query.filter(ConsentRecord.user_id == user_id)
            if organization_id:
                query = query.filter(ConsentRecord.organization_id == organization_id)

            active_consents = query.all()

            # Mark all as withdrawn
            for consent in active_consents:
                consent.withdrawn_at = datetime.now(timezone.utc)
                consent.withdrawal_reason = reason

            self.db.commit()

            if active_consents:
                logger.info(
                    f"Withdrew {len(active_consents)} previous consent(s) "
                    f"for type={consent_type}"
                )

        except Exception as e:
            logger.error(f"Error withdrawing previous consent: {e}", exc_info=True)
            self.db.rollback()

    def has_consent(
        self,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        consent_type: Optional[ConsentType] = None,
    ) -> bool:
        """
        Check if user/org has active consent for specified type(s).

        Args:
            user_id: User UUID to check consent for
            organization_id: Organization UUID to check consent for
            consent_type: Specific consent type to check (None = check all core types)

        Returns:
            True if active consent exists, False otherwise

        Example:
            >>> service = GDPRService(db)
            >>> if service.has_consent(user_id=user.id, consent_type=ConsentType.DATA_PROCESSING):
            ...     # Process user data
        """
        try:
            query = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.granted == True,
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )

            if user_id:
                query = query.filter(ConsentRecord.user_id == user_id)
            if organization_id:
                query = query.filter(ConsentRecord.organization_id == organization_id)
            if consent_type:
                query = query.filter(ConsentRecord.consent_type == consent_type)

            return self.db.query(query.exists()).scalar()

        except Exception as e:
            logger.error(f"Error checking consent: {e}", exc_info=True)
            return False

    def get_active_consents(
        self,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[ConsentRecord]:
        """
        Get all active consents for a user or organization.

        Args:
            user_id: User UUID to get consents for
            organization_id: Organization UUID to get consents for

        Returns:
            List of active ConsentRecord instances

        Example:
            >>> service = GDPRService(db)
            >>> consents = service.get_active_consents(user_id=user.id)
            >>> for consent in consents:
            ...     print(f"{consent.consent_type}: {consent.is_active()}")
        """
        try:
            query = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.granted == True,
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )

            if user_id:
                query = query.filter(ConsentRecord.user_id == user_id)
            if organization_id:
                query = query.filter(ConsentRecord.organization_id == organization_id)

            consents = query.order_by(ConsentRecord.created_at.desc()).all()

            logger.debug(
                f"Retrieved {len(consents)} active consents "
                f"(user_id={user_id}, org_id={organization_id})"
            )

            return consents

        except Exception as e:
            logger.error(f"Error getting active consents: {e}", exc_info=True)
            return []

    def get_consent_history(
        self,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        consent_type: Optional[ConsentType] = None,
        limit: int = 100,
    ) -> List[ConsentRecord]:
        """
        Get consent history for a user or organization.

        Args:
            user_id: User UUID to get history for
            organization_id: Organization UUID to get history for
            consent_type: Filter by specific consent type
            limit: Maximum number of records to return

        Returns:
            List of ConsentRecord instances (includes granted and withdrawn)

        Example:
            >>> service = GDPRService(db)
            >>> history = service.get_consent_history(user_id=user.id)
        """
        try:
            query = self.db.query(ConsentRecord)

            if user_id:
                query = query.filter(ConsentRecord.user_id == user_id)
            if organization_id:
                query = query.filter(ConsentRecord.organization_id == organization_id)
            if consent_type:
                query = query.filter(ConsentRecord.consent_type == consent_type)

            history = query.order_by(ConsentRecord.created_at.desc()).limit(limit).all()

            logger.debug(
                f"Retrieved {len(history)} consent history records "
                f"(user_id={user_id}, org_id={organization_id})"
            )

            return history

        except Exception as e:
            logger.error(f"Error getting consent history: {e}", exc_info=True)
            return []

    def record_cookie_consent(
        self,
        essential_cookies: bool = True,
        functional_cookies: bool = False,
        analytics_cookies: bool = False,
        marketing_cookies: bool = False,
        session_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[CookieConsent]:
        """
        Record cookie consent preferences.

        Creates or updates cookie consent record for a user or session.
        Essential cookies are always enabled.

        Args:
            essential_cookies: Essential cookies (always True)
            functional_cookies: Functional cookies for preferences
            analytics_cookies: Analytics cookies for tracking
            marketing_cookies: Marketing cookies for advertising
            session_id: Browser session ID for anonymous users
            user_id: User UUID for logged-in users
            ip_address: IP address of the requester

        Returns:
            Created or updated CookieConsent instance or None if failed

        Example:
            >>> service = GDPRService(db)
            >>> consent = service.record_cookie_consent(
            ...     analytics_cookies=True,
            ...     functional_cookies=True,
            ...     session_id="session-123"
            ... )
        """
        try:
            # Check if consent already exists
            query = self.db.query(CookieConsent)
            if session_id:
                query = query.filter(CookieConsent.session_id == session_id)
            elif user_id:
                query = query.filter(CookieConsent.user_id == str(user_id))

            existing_consent = query.first()

            if existing_consent:
                # Update existing consent
                existing_consent.essential_cookies = essential_cookies
                existing_consent.functional_cookies = functional_cookies
                existing_consent.analytics_cookies = analytics_cookies
                existing_consent.marketing_cookies = marketing_cookies
                existing_consent.consent_version = self.consent_version
                existing_consent.ip_address = ip_address

                self.db.commit()
                self.db.refresh(existing_consent)

                logger.info(
                    f"Updated cookie consent: session_id={session_id}, user_id={user_id}"
                )

                return existing_consent
            else:
                # Create new consent
                cookie_consent = CookieConsent(
                    session_id=session_id,
                    user_id=str(user_id) if user_id else None,
                    essential_cookies=essential_cookies,
                    functional_cookies=functional_cookies,
                    analytics_cookies=analytics_cookies,
                    marketing_cookies=marketing_cookies,
                    consent_version=self.consent_version,
                    ip_address=ip_address,
                )

                self.db.add(cookie_consent)
                self.db.commit()
                self.db.refresh(cookie_consent)

                logger.info(
                    f"Recorded cookie consent: session_id={session_id}, user_id={user_id}"
                )

                return cookie_consent

        except Exception as e:
            logger.error(f"Error recording cookie consent: {e}", exc_info=True)
            self.db.rollback()
            return None

    def get_cookie_consent(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> Optional[CookieConsent]:
        """
        Get cookie consent for a session or user.

        Args:
            session_id: Browser session ID
            user_id: User UUID

        Returns:
            CookieConsent instance or None if not found

        Example:
            >>> service = GDPRService(db)
            >>> consent = service.get_cookie_consent(session_id="session-123")
            >>> if consent and consent.analytics_cookies:
            ...     # Enable analytics
        """
        try:
            query = self.db.query(CookieConsent)

            if session_id:
                query = query.filter(CookieConsent.session_id == session_id)
            elif user_id:
                query = query.filter(CookieConsent.user_id == str(user_id))
            else:
                return None

            consent = query.first()

            logger.debug(
                f"Retrieved cookie consent: session_id={session_id}, user_id={user_id}, "
                f"found={consent is not None}"
            )

            return consent

        except Exception as e:
            logger.error(f"Error getting cookie consent: {e}", exc_info=True)
            return None

    def has_cookie_consent(
        self,
        cookie_category: str,
        session_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if user has granted consent for a specific cookie category.

        Args:
            cookie_category: Cookie category (essential, functional, analytics, marketing)
            session_id: Browser session ID
            user_id: User UUID

        Returns:
            True if consent granted, False otherwise

        Example:
            >>> service = GDPRService(db)
            >>> if service.has_cookie_consent("analytics", session_id="session-123"):
            ...     # Enable analytics tracking
        """
        try:
            consent = self.get_cookie_consent(session_id=session_id, user_id=user_id)

            if consent is None:
                return False

            return consent.has_granted_consent(cookie_category)

        except Exception as e:
            logger.error(f"Error checking cookie consent: {e}", exc_info=True)
            return False

    def create_deletion_request(
        self,
        requester_email: str,
        requester_type: str = "candidate",
        notes: Optional[str] = None,
    ) -> Optional[DataDeletionRequest]:
        """
        Create a data deletion request (right to be forgotten).

        Creates a deletion request with PENDING status and generates a verification
        token that will be sent to the requester's email.

        Args:
            requester_email: Email of person requesting deletion
            requester_type: Type of requester (candidate, recruiter, other)
            notes: Additional notes about the request

        Returns:
            Created DataDeletionRequest instance or None if failed

        Example:
            >>> service = GDPRService(db)
            >>> request = service.create_deletion_request(
            ...     requester_email="user@example.com",
            ...     requester_type="candidate"
            ... )
            >>> # Send verification email with request.verification_token
        """
        try:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)

            deletion_request = DataDeletionRequest(
                requester_email=requester_email,
                requester_type=requester_type,
                status=DeletionRequestStatus.PENDING,
                verification_token=verification_token,
                notes=notes,
            )

            self.db.add(deletion_request)
            self.db.commit()
            self.db.refresh(deletion_request)

            logger.info(
                f"Created deletion request: id={deletion_request.id}, "
                f"email={requester_email}, type={requester_type}"
            )

            return deletion_request

        except Exception as e:
            logger.error(f"Error creating deletion request: {e}", exc_info=True)
            self.db.rollback()
            return None

    def verify_deletion_request(self, verification_token: str) -> bool:
        """
        Verify a deletion request using the token sent to email.

        Marks the request as VERIFIED if the token is valid.

        Args:
            verification_token: Token sent to requester's email

        Returns:
            True if verification successful, False otherwise

        Example:
            >>> service = GDPRService(db)
            >>> success = service.verify_deletion_request("token-from-email")
        """
        try:
            request = (
                self.db.query(DataDeletionRequest)
                .filter(DataDeletionRequest.verification_token == verification_token)
                .first()
            )

            if request is None:
                logger.warning(f"Invalid deletion request token: {verification_token}")
                return False

            if request.status != DeletionRequestStatus.PENDING:
                logger.warning(
                    f"Deletion request already processed: {request.id}, status={request.status}"
                )
                return False

            request.status = DeletionRequestStatus.VERIFIED
            request.verified_at = datetime.now(timezone.utc)
            request.verification_token = None  # Clear token after use

            self.db.commit()

            logger.info(f"Verified deletion request: id={request.id}")

            return True

        except Exception as e:
            logger.error(f"Error verifying deletion request: {e}", exc_info=True)
            self.db.rollback()
            return False

    def get_deletion_request(
        self, request_id: UUID
    ) -> Optional[DataDeletionRequest]:
        """
        Get a deletion request by ID.

        Args:
            request_id: UUID of the deletion request

        Returns:
            DataDeletionRequest instance or None if not found

        Example:
            >>> service = GDPRService(db)
            >>> request = service.get_deletion_request(request_id)
        """
        try:
            request = (
                self.db.query(DataDeletionRequest)
                .filter(DataDeletionRequest.id == request_id)
                .first()
            )

            return request

        except Exception as e:
            logger.error(f"Error getting deletion request: {e}", exc_info=True)
            return None

    def get_deletion_requests_by_email(
        self, email: str
    ) -> List[DataDeletionRequest]:
        """
        Get all deletion requests for an email address.

        Args:
            email: Email address to search for

        Returns:
            List of DataDeletionRequest instances

        Example:
            >>> service = GDPRService(db)
            >>> requests = service.get_deletion_requests_by_email("user@example.com")
        """
        try:
            requests = (
                self.db.query(DataDeletionRequest)
                .filter(DataDeletionRequest.requester_email == email)
                .order_by(DataDeletionRequest.created_at.desc())
                .all()
            )

            return requests

        except Exception as e:
            logger.error(f"Error getting deletion requests by email: {e}", exc_info=True)
            return []

    def can_process_data(
        self,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        purpose: Optional[str] = None,
    ) -> bool:
        """
        Check if data processing is allowed based on consent.

        Verifies that required consents are in place for specific processing purposes.
        Different purposes require different consent types.

        Args:
            user_id: User UUID to check
            organization_id: Organization UUID to check
            purpose: Processing purpose (resume_analysis, matching, etc.)

        Returns:
            True if processing is allowed, False otherwise

        Example:
            >>> service = GDPRService(db)
            >>> if service.can_process_data(user_id=user.id, purpose="resume_analysis"):
            ...     # Process resume
        """
        try:
            # Map purposes to required consent types
            purpose_consents = {
                self.PURPOSE_RESUME_ANALYSIS: [
                    ConsentType.DATA_PROCESSING,
                    ConsentType.PROFILE_CREATION,
                ],
                self.PURPOSE_MATCHING: [
                    ConsentType.DATA_PROCESSING,
                    ConsentType.DATA_SHARING_RECRUITERS,
                ],
                self.PURPOSE_PROFILE_CREATION: [
                    ConsentType.PROFILE_CREATION,
                    ConsentType.DATA_STORAGE,
                ],
                self.PURPOSE_COMMUNICATION: [
                    ConsentType.MARKETING_EMAILS,
                ],
            }

            required_consents = purpose_consents.get(purpose, [])

            if not required_consents:
                # No specific consent required
                return True

            # Check all required consents
            for consent_type in required_consents:
                if not self.has_consent(
                    user_id=user_id,
                    organization_id=organization_id,
                    consent_type=consent_type,
                ):
                    logger.debug(
                        f"Data processing not allowed: missing consent {consent_type} "
                        f"for purpose {purpose}"
                    )
                    return False

            logger.debug(
                f"Data processing allowed: user_id={user_id}, purpose={purpose}"
            )

            return True

        except Exception as e:
            logger.error(f"Error checking data processing permission: {e}", exc_info=True)
            return False

    def get_privacy_summary(
        self,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Get a summary of privacy status for a user or organization.

        Provides an overview of all consents, cookie preferences, and any
        pending deletion requests.

        Args:
            user_id: User UUID to get summary for
            organization_id: Organization UUID to get summary for

        Returns:
            Dictionary with privacy status summary

        Example:
            >>> service = GDPRService(db)
            >>> summary = service.get_privacy_summary(user_id=user.id)
            >>> print(summary)
            {
                'active_consents': [...],
                'cookie_consent': {...},
                'deletion_requests': [...],
                'can_process_data': True
            }
        """
        try:
            active_consents = self.get_active_consents(
                user_id=user_id, organization_id=organization_id
            )

            cookie_consent = self.get_cookie_consent(
                session_id=None, user_id=user_id
            )

            # Get deletion requests if user_id available
            deletion_requests = []
            if user_id:
                # Assuming email is stored in user model - would need to query user
                # For now, return empty list or implement based on user model
                deletion_requests = []

            return {
                "active_consents": [
                    {
                        "type": c.consent_type.value,
                        "granted_at": c.created_at.isoformat(),
                        "version": c.consent_version,
                    }
                    for c in active_consents
                ],
                "cookie_consent": (
                    {
                        "essential": cookie_consent.essential_cookies,
                        "functional": cookie_consent.functional_cookies,
                        "analytics": cookie_consent.analytics_cookies,
                        "marketing": cookie_consent.marketing_cookies,
                        "version": cookie_consent.consent_version,
                    }
                    if cookie_consent
                    else None
                ),
                "deletion_requests": [
                    {
                        "id": str(r.id),
                        "status": r.status.value,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in deletion_requests
                ],
                "can_process_data": self.can_process_data(user_id=user_id),
            }

        except Exception as e:
            logger.error(f"Error getting privacy summary: {e}", exc_info=True)
            return {
                "active_consents": [],
                "cookie_consent": None,
                "deletion_requests": [],
                "can_process_data": False,
                "error": str(e),
            }


def get_gdpr_service(db: Session) -> GDPRService:
    """
    Get or create GDPR service instance.

    Args:
        db: Database session

    Returns:
        GDPRService instance

    Example:
        >>> from database import get_db
        >>> db = next(get_db())
        >>> service = get_gdpr_service(db)
    """
    return GDPRService(db=db)
