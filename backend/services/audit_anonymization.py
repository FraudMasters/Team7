"""
Audit anonymization service for GDPR compliance.

This module provides comprehensive audit log anonymization functionality to support GDPR
compliance, particularly the "right to be forgotten" (Article 17). It anonymizes personally
identifiable information (PII) in audit logs while preserving action patterns, timestamps,
and organizational context for compliance and security analysis.

The audit anonymization service supports:
- User-level log anonymization (right to be forgotten)
- Organization-level bulk anonymization
- Selective field anonymization (user_id, IP address, user agent)
- Pseudonymization with cryptographic hashing for traceability
- Action pattern preservation for compliance auditing
- Anonymization audit trail for verification
- Reversibility protection (one-way pseudonymization)
- Configurable anonymization strategies

GDPR Rights Implemented:
- Right to erasure (Article 17) - anonymize personal data in audit logs
- Right to restriction of processing (Article 18) - mark logs as anonymized
- Data minimization (Article 5) - remove unnecessary PII while retaining compliance data

Anonymization Strategies:
- PSEUDONYMIZE: Replace PII with cryptographic hash (default, maintains patterns)
- GENERIC: Replace PII with generic placeholder values
- NULL: Remove PII entirely (set to NULL)
- HASH_WITH_SALT: Salted hash with organization-specific salt

Fields Anonymized:
- user_id: Replaced with pseudonymized UUID or generic value
- ip_address: Replaced with "anonymized" or hashed value
- user_agent: Replaced with "anonymized" or NULL

Fields Preserved:
- action_type: Action patterns for compliance analysis
- entity_type/entity_id: Resource relationships for audit trails
- organization_id: Organizational context for compliance
- created_at/updated_at: Timestamps for retention policies
- action_data: Depends on strategy (may be sanitized)
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid5, NAMESPACE_DNS

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from config import get_settings
from models.audit_log import AuditActionType, AuditLog

logger = logging.getLogger(__name__)

# Global audit anonymization service instance
_audit_anonymization_service: Optional["AuditAnonymizationService"] = None

# Anonymization constants
ANONYMIZED_IP = "anonymized"
ANONYMIZED_USER_AGENT = "anonymized"
ANONYMIZED_UUID_NAMESPACE = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")  # Custom namespace for audit log anonymization


class AnonymizationStrategy:
    """
    Anonymization strategy enumeration.

    Defines different approaches to anonymizing PII in audit logs,
    balancing privacy protection with analytical value.
    """

    PSEUDONYMIZE = "pseudonymize"  # Replace with cryptographic hash (maintains patterns)
    GENERIC = "generic"  # Replace with generic placeholder values
    NULL = "null"  # Remove entirely (set to NULL)
    HASH_WITH_SALT = "hash_with_salt"  # Salted hash with org-specific salt


class AuditAnonymizationService:
    """
    Audit anonymization service for GDPR compliance.

    This class provides a high-level interface for anonymizing audit logs to support
    GDPR compliance requirements, particularly the right to erasure (right to be forgotten).

    Attributes:
        db: Database session for database operations
        strategy: Anonymization strategy to use (default: PSEUDONYMIZE)
        create_audit_trail: Whether to create audit log for anonymization action

    Example:
        >>> service = AuditAnonymizationService(db_session)
        >>> result = service.anonymize_user_logs(
        ...     user_id=user.id,
        ...     reason="GDPR right to erasure request"
        ... )
        >>> print(f"Anonymized {result['count']} audit log records")
    """

    def __init__(
        self,
        db: Session,
        strategy: str = AnonymizationStrategy.PSEUDONYMIZE,
        create_audit_trail: bool = True,
    ) -> None:
        """
        Initialize the audit anonymization service.

        Args:
            db: Database session for database operations
            strategy: Anonymization strategy to use
            create_audit_trail: Whether to create audit log for anonymization action
        """
        self.db = db
        self.strategy = strategy
        self.create_audit_trail = create_audit_trail

        logger.info(
            f"AuditAnonymizationService initialized (strategy={self.strategy}, "
            f"audit_trail={self.create_audit_trail})"
        )

    def anonymize_user_logs(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
        reason: Optional[str] = None,
        anonymize_action_data: bool = False,
    ) -> Dict[str, Any]:
        """
        Anonymize all audit logs for a specific user (GDPR right to be forgotten).

        Replaces personally identifiable information (user_id, IP address, user agent)
        with anonymized values while preserving action patterns, timestamps, and
        organizational context for compliance analysis.

        Args:
            user_id: User UUID whose logs should be anonymized
            organization_id: Optional organization filter (anonymize only within this org)
            reason: Reason for anonymization (e.g., "GDPR erasure request")
            anonymize_action_data: Whether to also anonymize action_data field (default: False)

        Returns:
            Dictionary with anonymization results:
            {
                "success": bool,
                "user_id": UUID,
                "count": int,  # Number of records anonymized
                "strategy": str,
                "anonymized_at": datetime,
                "reason": str,
                "error": Optional[str]
            }

        Example:
            >>> service = AuditAnonymizationService(db)
            >>> result = service.anonymize_user_logs(
            ...     user_id=user.id,
            ...     reason="User requested account deletion"
            ... )
            >>> print(f"Anonymized {result['count']} records")
        """
        try:
            # Build query filter
            filters = [AuditLog.user_id == user_id]
            if organization_id:
                filters.append(AuditLog.organization_id == organization_id)

            # Count logs to be anonymized
            count_query = self.db.query(AuditLog).filter(and_(*filters))
            total_count = count_query.count()

            if total_count == 0:
                logger.info(f"No audit logs found for user_id={user_id}")
                return {
                    "success": True,
                    "user_id": str(user_id),
                    "count": 0,
                    "strategy": self.strategy,
                    "anonymized_at": datetime.now(timezone.utc),
                    "reason": reason,
                    "error": None,
                }

            # Generate anonymized values based on strategy
            anonymized_values = self._generate_anonymized_values(
                user_id=user_id,
                organization_id=organization_id,
            )

            # Update audit logs with anonymized values
            update_data = {
                "user_id": anonymized_values["user_id"],
                "ip_address": anonymized_values["ip_address"],
                "user_agent": anonymized_values["user_agent"],
                "updated_at": datetime.now(timezone.utc),
            }

            # Optionally anonymize action_data (remove PII from JSON field)
            if anonymize_action_data:
                # Note: This is a simple approach - in production, you might want
                # to selectively sanitize specific fields within action_data
                update_data["action_data"] = None

            # Execute bulk update
            update_stmt = (
                update(AuditLog)
                .where(and_(*filters))
                .values(**update_data)
            )
            result = self.db.execute(update_stmt)
            self.db.commit()

            anonymized_count = result.rowcount

            logger.info(
                f"Anonymized {anonymized_count} audit log records for user_id={user_id} "
                f"(strategy={self.strategy})"
            )

            # Create audit trail for the anonymization action
            if self.create_audit_trail:
                self._create_anonymization_audit_log(
                    user_id=user_id,
                    organization_id=organization_id,
                    count=anonymized_count,
                    reason=reason,
                )

            return {
                "success": True,
                "user_id": str(user_id),
                "count": anonymized_count,
                "strategy": self.strategy,
                "anonymized_at": datetime.now(timezone.utc),
                "reason": reason,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Error anonymizing audit logs for user_id={user_id}: {e}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "user_id": str(user_id),
                "count": 0,
                "strategy": self.strategy,
                "anonymized_at": datetime.now(timezone.utc),
                "reason": reason,
                "error": str(e),
            }

    def anonymize_organization_logs(
        self,
        organization_id: UUID,
        older_than_days: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Anonymize audit logs for an entire organization (bulk anonymization).

        Useful for data minimization policies or when an organization requests
        bulk data deletion.

        Args:
            organization_id: Organization UUID whose logs should be anonymized
            older_than_days: Optional filter to only anonymize logs older than N days
            reason: Reason for anonymization

        Returns:
            Dictionary with anonymization results

        Example:
            >>> service = AuditAnonymizationService(db)
            >>> result = service.anonymize_organization_logs(
            ...     organization_id=org.id,
            ...     older_than_days=365,
            ...     reason="Data minimization policy"
            ... )
        """
        try:
            # Build query filter
            filters = [AuditLog.organization_id == organization_id]

            # Add time filter if specified
            if older_than_days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
                filters.append(AuditLog.created_at < cutoff_date)

            # Count logs to be anonymized
            count_query = self.db.query(AuditLog).filter(and_(*filters))
            total_count = count_query.count()

            if total_count == 0:
                logger.info(f"No audit logs found for organization_id={organization_id}")
                return {
                    "success": True,
                    "organization_id": str(organization_id),
                    "count": 0,
                    "strategy": self.strategy,
                    "anonymized_at": datetime.now(timezone.utc),
                    "reason": reason,
                    "error": None,
                }

            # For organization-wide anonymization, use generic values
            update_data = {
                "user_id": None,  # NULL out user_id for org-wide anonymization
                "ip_address": ANONYMIZED_IP,
                "user_agent": ANONYMIZED_USER_AGENT,
                "updated_at": datetime.now(timezone.utc),
            }

            # Execute bulk update
            update_stmt = (
                update(AuditLog)
                .where(and_(*filters))
                .values(**update_data)
            )
            result = self.db.execute(update_stmt)
            self.db.commit()

            anonymized_count = result.rowcount

            logger.info(
                f"Anonymized {anonymized_count} audit log records for "
                f"organization_id={organization_id} (strategy={self.strategy})"
            )

            # Create audit trail
            if self.create_audit_trail:
                self._create_anonymization_audit_log(
                    user_id=None,
                    organization_id=organization_id,
                    count=anonymized_count,
                    reason=reason,
                )

            return {
                "success": True,
                "organization_id": str(organization_id),
                "count": anonymized_count,
                "strategy": self.strategy,
                "anonymized_at": datetime.now(timezone.utc),
                "reason": reason,
                "error": None,
            }

        except Exception as e:
            logger.error(
                f"Error anonymizing audit logs for organization_id={organization_id}: {e}",
                exc_info=True,
            )
            self.db.rollback()
            return {
                "success": False,
                "organization_id": str(organization_id),
                "count": 0,
                "strategy": self.strategy,
                "anonymized_at": datetime.now(timezone.utc),
                "reason": reason,
                "error": str(e),
            }

    def _generate_anonymized_values(
        self,
        user_id: UUID,
        organization_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Generate anonymized values based on the configured strategy.

        Args:
            user_id: Original user UUID
            organization_id: Optional organization UUID for org-specific salting

        Returns:
            Dictionary with anonymized values for user_id, ip_address, user_agent
        """
        if self.strategy == AnonymizationStrategy.PSEUDONYMIZE:
            # Pseudonymize user_id using UUID5 (deterministic, one-way)
            # This allows pattern analysis while protecting identity
            pseudonymized_user_id = uuid5(ANONYMIZED_UUID_NAMESPACE, str(user_id))

            return {
                "user_id": pseudonymized_user_id,
                "ip_address": ANONYMIZED_IP,
                "user_agent": ANONYMIZED_USER_AGENT,
            }

        elif self.strategy == AnonymizationStrategy.HASH_WITH_SALT:
            # Hash user_id with organization-specific salt
            salt = str(organization_id) if organization_id else "global_salt"
            hashed_user_id_str = hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()
            # Convert hash to UUID (take first 32 hex chars)
            hashed_user_id = UUID(hashed_user_id_str[:32])

            return {
                "user_id": hashed_user_id,
                "ip_address": ANONYMIZED_IP,
                "user_agent": ANONYMIZED_USER_AGENT,
            }

        elif self.strategy == AnonymizationStrategy.NULL:
            # Remove PII entirely
            return {
                "user_id": None,
                "ip_address": None,
                "user_agent": None,
            }

        else:  # GENERIC or default
            # Use generic placeholder values
            # Use a fixed UUID for all anonymized users to indicate "anonymized user"
            generic_user_id = UUID("00000000-0000-0000-0000-000000000000")

            return {
                "user_id": generic_user_id,
                "ip_address": ANONYMIZED_IP,
                "user_agent": ANONYMIZED_USER_AGENT,
            }

    def _create_anonymization_audit_log(
        self,
        user_id: Optional[UUID],
        organization_id: Optional[UUID],
        count: int,
        reason: Optional[str],
    ) -> None:
        """
        Create an audit log entry for the anonymization action itself.

        This provides a complete audit trail showing when and why logs were anonymized,
        supporting compliance verification.

        Args:
            user_id: User UUID whose logs were anonymized (or None for org-wide)
            organization_id: Organization UUID
            count: Number of records anonymized
            reason: Reason for anonymization
        """
        try:
            # Note: We intentionally do NOT anonymize the anonymization audit log itself,
            # as this is the compliance record showing the erasure was performed
            audit_log = AuditLog(
                action_type=AuditActionType.USER_DELETED,  # Reuse existing action type
                entity_type="audit_logs",
                entity_id=user_id,
                user_id=None,  # System action, no specific user
                organization_id=organization_id,
                ip_address=None,
                user_agent=None,
                action_data={
                    "anonymization": True,
                    "records_anonymized": count,
                    "strategy": self.strategy,
                    "target_user_id": str(user_id) if user_id else None,
                },
                reason=reason or "GDPR audit log anonymization",
            )

            self.db.add(audit_log)
            self.db.commit()

            logger.info(f"Created anonymization audit log (count={count})")

        except Exception as e:
            logger.error(f"Error creating anonymization audit log: {e}", exc_info=True)
            # Don't raise - this is a non-critical operation
            self.db.rollback()

    def is_anonymized(self, audit_log: AuditLog) -> bool:
        """
        Check if an audit log has been anonymized.

        Args:
            audit_log: AuditLog instance to check

        Returns:
            True if the log appears to be anonymized, False otherwise

        Example:
            >>> log = db.query(AuditLog).first()
            >>> if service.is_anonymized(log):
            ...     print("This log has been anonymized")
        """
        # Check for anonymization indicators
        is_ip_anonymized = (
            audit_log.ip_address is None or audit_log.ip_address == ANONYMIZED_IP
        )
        is_ua_anonymized = (
            audit_log.user_agent is None or audit_log.user_agent == ANONYMIZED_USER_AGENT
        )
        is_user_anonymized = (
            audit_log.user_id is None
            or audit_log.user_id == UUID("00000000-0000-0000-0000-000000000000")
        )

        # Consider anonymized if at least 2 of 3 fields are anonymized
        anonymized_count = sum([is_ip_anonymized, is_ua_anonymized, is_user_anonymized])
        return anonymized_count >= 2


# Module-level convenience function
def anonymize_user_logs(
    db: Session,
    user_id: UUID,
    organization_id: Optional[UUID] = None,
    strategy: str = AnonymizationStrategy.PSEUDONYMIZE,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience function to anonymize audit logs for a user.

    This is a module-level wrapper around AuditAnonymizationService.anonymize_user_logs()
    for easier importing and usage.

    Args:
        db: Database session
        user_id: User UUID whose logs should be anonymized
        organization_id: Optional organization filter
        strategy: Anonymization strategy (default: PSEUDONYMIZE)
        reason: Reason for anonymization

    Returns:
        Dictionary with anonymization results

    Example:
        >>> from backend.services.audit_anonymization import anonymize_user_logs
        >>> result = anonymize_user_logs(db, user_id=user.id, reason="GDPR request")
        >>> print(f"Anonymized {result['count']} records")
    """
    service = AuditAnonymizationService(db=db, strategy=strategy)
    return service.anonymize_user_logs(
        user_id=user_id,
        organization_id=organization_id,
        reason=reason,
    )


def get_audit_anonymization_service(
    db: Session,
    strategy: str = AnonymizationStrategy.PSEUDONYMIZE,
) -> AuditAnonymizationService:
    """
    Get or create the global audit anonymization service instance.

    Args:
        db: Database session
        strategy: Anonymization strategy to use

    Returns:
        AuditAnonymizationService instance

    Example:
        >>> service = get_audit_anonymization_service(db)
        >>> result = service.anonymize_user_logs(user_id=user.id)
    """
    global _audit_anonymization_service

    # For simplicity, we create a new instance each time rather than caching
    # (since db session lifecycle management can be complex)
    _audit_anonymization_service = AuditAnonymizationService(db=db, strategy=strategy)
    return _audit_anonymization_service
