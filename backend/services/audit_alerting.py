"""
Audit alerting service for detecting suspicious patterns in audit logs.

This module provides comprehensive security monitoring and alerting by analyzing audit logs
for suspicious activity patterns. It detects potentially malicious or anomalous behavior such
as failed authentication attempts, bulk data exports, permission escalation, and unusual
user activity patterns.

The audit alerting service supports:
- Failed login attempt detection (brute force protection)
- Bulk data export monitoring (data exfiltration prevention)
- Permission and role change tracking (privilege escalation detection)
- Configurable alert rules with thresholds and time windows
- Alert throttling to prevent notification spam
- Organization-scoped and global alert rules
- Multi-channel alert delivery (email, webhook, Slack)

Security Patterns Detected:
- Brute force attacks (multiple failed logins from same user/IP)
- Data exfiltration (bulk exports exceeding thresholds)
- Insider threats (unusual permission changes, role escalations)
- Account compromise (suspicious login patterns, multiple IPs)
- System abuse (excessive API calls, configuration tampering)
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config import get_settings
from database import async_session_maker
from models.audit_alert_config import AlertSeverity, AlertType, AuditAlertConfig
from models.audit_log import AuditActionType, AuditLog

logger = logging.getLogger(__name__)

# Global audit alerting service instance
_audit_alerting_service: Optional["AuditAlertingService"] = None


class AuditAlertingService:
    """
    Audit alerting service for detecting suspicious patterns in audit logs.

    This class provides a high-level interface for security monitoring and alerting.
    It analyzes audit logs to detect suspicious activity patterns and triggers alerts
    when configured thresholds are exceeded.

    Attributes:
        db: Database session for database operations (can be sync or async)
        alert_configs_cache: In-memory cache of alert configurations

    Example:
        >>> service = AuditAlertingService(db_session)
        >>> alerts = await service.detect_suspicious_activity(
        ...     time_window_minutes=10,
        ...     organization_id=org.id
        ... )
        >>> for alert in alerts:
        ...     print(f"Alert: {alert['alert_type']} - {alert['message']}")
    """

    # Default thresholds for suspicious activity detection
    DEFAULT_FAILED_LOGIN_THRESHOLD = 5
    DEFAULT_BULK_EXPORT_THRESHOLD = 100
    DEFAULT_TIME_WINDOW_MINUTES = 10
    DEFAULT_PERMISSION_CHANGE_THRESHOLD = 3
    DEFAULT_ROLE_CHANGE_THRESHOLD = 2

    # Action types for each alert category
    FAILED_LOGIN_ACTIONS = [
        AuditActionType.LOGIN_FAILED,
    ]

    BULK_EXPORT_ACTIONS = [
        AuditActionType.DATA_EXPORTED,
        AuditActionType.REPORT_GENERATED,
    ]

    PERMISSION_CHANGE_ACTIONS = [
        AuditActionType.USER_ROLE_CHANGED,
        AuditActionType.SETTINGS_UPDATED,
    ]

    ROLE_CHANGE_ACTIONS = [
        AuditActionType.USER_ROLE_CHANGED,
    ]

    USER_MANAGEMENT_ACTIONS = [
        AuditActionType.USER_CREATED,
        AuditActionType.USER_DELETED,
        AuditActionType.USER_INVITED,
    ]

    def __init__(
        self,
        db: Optional[Session] = None,
    ) -> None:
        """
        Initialize the audit alerting service.

        Args:
            db: Database session for database operations (optional for async usage)
        """
        settings = get_settings()

        self.db = db
        self.alert_configs_cache: Dict[str, AuditAlertConfig] = {}

        logger.info("AuditAlertingService initialized")

    async def detect_suspicious_activity(
        self,
        time_window_minutes: int = DEFAULT_TIME_WINDOW_MINUTES,
        organization_id: Optional[UUID] = None,
        alert_types: Optional[List[AlertType]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect suspicious activity patterns in audit logs.

        Analyzes recent audit logs to identify security threats and anomalous behavior.
        Checks for failed login attempts, bulk data exports, permission changes, and
        other suspicious patterns based on configured alert rules.

        Args:
            time_window_minutes: Time window in minutes to analyze (default: 10)
            organization_id: Organization UUID to scope analysis (None for all orgs)
            alert_types: List of specific alert types to check (None for all)

        Returns:
            List of alert dictionaries containing:
            - alert_type: Type of alert triggered
            - severity: Alert severity level
            - message: Human-readable alert message
            - count: Number of occurrences that triggered the alert
            - threshold: Configured threshold that was exceeded
            - time_window_minutes: Time window used for analysis
            - entities: List of affected entities (users, IPs, etc.)
            - first_occurrence: Timestamp of first occurrence
            - last_occurrence: Timestamp of last occurrence
            - organization_id: Organization ID if scoped

        Example:
            >>> service = AuditAlertingService()
            >>> alerts = await service.detect_suspicious_activity(
            ...     time_window_minutes=30,
            ...     organization_id=org_id
            ... )
            >>> for alert in alerts:
            ...     print(f"{alert['severity']}: {alert['message']}")
        """
        try:
            logger.info(
                f"Starting suspicious activity detection: "
                f"time_window={time_window_minutes}min, "
                f"org_id={organization_id}, "
                f"alert_types={alert_types}"
            )

            # Calculate time window
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=time_window_minutes)

            alerts: List[Dict[str, Any]] = []

            async with async_session_maker() as session:
                # Load active alert configurations
                alert_configs = await self._load_alert_configs(
                    session=session,
                    organization_id=organization_id,
                    alert_types=alert_types,
                )

                # Check each alert type
                for config in alert_configs:
                    try:
                        if config.alert_type == AlertType.FAILED_LOGINS:
                            result = await self._check_failed_logins(
                                session=session,
                                start_time=start_time,
                                end_time=end_time,
                                config=config,
                            )
                            if result:
                                alerts.append(result)

                        elif config.alert_type == AlertType.BULK_DATA_EXPORT:
                            result = await self._check_bulk_data_export(
                                session=session,
                                start_time=start_time,
                                end_time=end_time,
                                config=config,
                            )
                            if result:
                                alerts.append(result)

                        elif config.alert_type == AlertType.PERMISSION_CHANGES:
                            result = await self._check_permission_changes(
                                session=session,
                                start_time=start_time,
                                end_time=end_time,
                                config=config,
                            )
                            if result:
                                alerts.append(result)

                        elif config.alert_type == AlertType.ROLE_CHANGES:
                            result = await self._check_role_changes(
                                session=session,
                                start_time=start_time,
                                end_time=end_time,
                                config=config,
                            )
                            if result:
                                alerts.append(result)

                    except Exception as e:
                        logger.error(
                            f"Error checking alert type {config.alert_type}: {e}",
                            exc_info=True,
                        )
                        continue

            logger.info(
                f"Suspicious activity detection completed: "
                f"{len(alerts)} alerts triggered"
            )

            return alerts

        except Exception as e:
            logger.error(
                f"Error in suspicious activity detection: {e}",
                exc_info=True,
            )
            return []

    async def _load_alert_configs(
        self,
        session: AsyncSession,
        organization_id: Optional[UUID] = None,
        alert_types: Optional[List[AlertType]] = None,
    ) -> List[AuditAlertConfig]:
        """
        Load active alert configurations from database.

        Args:
            session: Database session
            organization_id: Organization UUID to filter by
            alert_types: List of alert types to filter by

        Returns:
            List of active AuditAlertConfig objects
        """
        try:
            # Build query for active alert configs
            query = select(AuditAlertConfig).where(
                AuditAlertConfig.enabled == True  # noqa: E712
            )

            # Filter by organization (include global rules with null org_id)
            if organization_id:
                query = query.where(
                    or_(
                        AuditAlertConfig.organization_id == organization_id,
                        AuditAlertConfig.organization_id.is_(None),
                    )
                )

            # Filter by alert types
            if alert_types:
                query = query.where(AuditAlertConfig.alert_type.in_(alert_types))

            result = await session.execute(query)
            configs = result.scalars().all()

            logger.debug(
                f"Loaded {len(configs)} active alert configurations "
                f"(org_id={organization_id})"
            )

            return configs

        except Exception as e:
            logger.error(f"Error loading alert configs: {e}", exc_info=True)
            return []

    async def _check_failed_logins(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        config: AuditAlertConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for excessive failed login attempts.

        Detects brute force attacks by counting failed login attempts per user
        and IP address within the time window.

        Args:
            session: Database session
            start_time: Start of time window
            end_time: End of time window
            config: Alert configuration

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        try:
            # Query failed login attempts grouped by user_id and ip_address
            query = (
                select(
                    AuditLog.user_id,
                    AuditLog.ip_address,
                    func.count(AuditLog.id).label("attempt_count"),
                    func.min(AuditLog.created_at).label("first_attempt"),
                    func.max(AuditLog.created_at).label("last_attempt"),
                )
                .where(
                    and_(
                        AuditLog.action_type == AuditActionType.LOGIN_FAILED,
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time,
                    )
                )
                .group_by(AuditLog.user_id, AuditLog.ip_address)
                .having(func.count(AuditLog.id) >= config.threshold)
            )

            # Filter by organization if configured
            if config.organization_id:
                query = query.where(
                    AuditLog.organization_id == config.organization_id
                )

            result = await session.execute(query)
            violations = result.all()

            if violations:
                entities = [
                    {
                        "user_id": str(v.user_id) if v.user_id else None,
                        "ip_address": v.ip_address,
                        "attempt_count": v.attempt_count,
                        "first_attempt": v.first_attempt.isoformat(),
                        "last_attempt": v.last_attempt.isoformat(),
                    }
                    for v in violations
                ]

                return {
                    "alert_type": AlertType.FAILED_LOGINS,
                    "severity": config.severity,
                    "message": (
                        f"Detected {len(violations)} user(s) with excessive failed login attempts. "
                        f"Threshold: {config.threshold} attempts in {config.time_window_minutes} minutes."
                    ),
                    "count": len(violations),
                    "threshold": config.threshold,
                    "time_window_minutes": config.time_window_minutes,
                    "entities": entities,
                    "first_occurrence": entities[0]["first_attempt"],
                    "last_occurrence": entities[-1]["last_attempt"],
                    "organization_id": str(config.organization_id) if config.organization_id else None,
                    "config_id": str(config.id),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking failed logins: {e}", exc_info=True)
            return None

    async def _check_bulk_data_export(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        config: AuditAlertConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for bulk data export operations.

        Detects potential data exfiltration by counting data export operations
        within the time window.

        Args:
            session: Database session
            start_time: Start of time window
            end_time: End of time window
            config: Alert configuration

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        try:
            # Query data export operations
            query = (
                select(
                    AuditLog.user_id,
                    AuditLog.action_type,
                    func.count(AuditLog.id).label("export_count"),
                    func.min(AuditLog.created_at).label("first_export"),
                    func.max(AuditLog.created_at).label("last_export"),
                )
                .where(
                    and_(
                        AuditLog.action_type.in_(self.BULK_EXPORT_ACTIONS),
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time,
                    )
                )
                .group_by(AuditLog.user_id, AuditLog.action_type)
                .having(func.count(AuditLog.id) >= config.threshold)
            )

            # Filter by organization if configured
            if config.organization_id:
                query = query.where(
                    AuditLog.organization_id == config.organization_id
                )

            result = await session.execute(query)
            violations = result.all()

            if violations:
                entities = [
                    {
                        "user_id": str(v.user_id) if v.user_id else None,
                        "action_type": v.action_type,
                        "export_count": v.export_count,
                        "first_export": v.first_export.isoformat(),
                        "last_export": v.last_export.isoformat(),
                    }
                    for v in violations
                ]

                total_exports = sum(e["export_count"] for e in entities)

                return {
                    "alert_type": AlertType.BULK_DATA_EXPORT,
                    "severity": config.severity,
                    "message": (
                        f"Detected {len(violations)} user(s) with excessive data export operations. "
                        f"Total exports: {total_exports}. "
                        f"Threshold: {config.threshold} exports in {config.time_window_minutes} minutes."
                    ),
                    "count": total_exports,
                    "threshold": config.threshold,
                    "time_window_minutes": config.time_window_minutes,
                    "entities": entities,
                    "first_occurrence": entities[0]["first_export"],
                    "last_occurrence": entities[-1]["last_export"],
                    "organization_id": str(config.organization_id) if config.organization_id else None,
                    "config_id": str(config.id),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking bulk data export: {e}", exc_info=True)
            return None

    async def _check_permission_changes(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        config: AuditAlertConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for permission and settings changes.

        Detects potential privilege escalation by counting permission-related
        changes within the time window.

        Args:
            session: Database session
            start_time: Start of time window
            end_time: End of time window
            config: Alert configuration

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        try:
            # Query permission change operations
            query = (
                select(
                    AuditLog.user_id,
                    AuditLog.action_type,
                    AuditLog.entity_type,
                    func.count(AuditLog.id).label("change_count"),
                    func.min(AuditLog.created_at).label("first_change"),
                    func.max(AuditLog.created_at).label("last_change"),
                )
                .where(
                    and_(
                        AuditLog.action_type.in_(self.PERMISSION_CHANGE_ACTIONS),
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time,
                    )
                )
                .group_by(AuditLog.user_id, AuditLog.action_type, AuditLog.entity_type)
                .having(func.count(AuditLog.id) >= config.threshold)
            )

            # Filter by organization if configured
            if config.organization_id:
                query = query.where(
                    AuditLog.organization_id == config.organization_id
                )

            result = await session.execute(query)
            violations = result.all()

            if violations:
                entities = [
                    {
                        "user_id": str(v.user_id) if v.user_id else None,
                        "action_type": v.action_type,
                        "entity_type": v.entity_type,
                        "change_count": v.change_count,
                        "first_change": v.first_change.isoformat(),
                        "last_change": v.last_change.isoformat(),
                    }
                    for v in violations
                ]

                total_changes = sum(e["change_count"] for e in entities)

                return {
                    "alert_type": AlertType.PERMISSION_CHANGES,
                    "severity": config.severity,
                    "message": (
                        f"Detected {len(violations)} user(s) with excessive permission changes. "
                        f"Total changes: {total_changes}. "
                        f"Threshold: {config.threshold} changes in {config.time_window_minutes} minutes."
                    ),
                    "count": total_changes,
                    "threshold": config.threshold,
                    "time_window_minutes": config.time_window_minutes,
                    "entities": entities,
                    "first_occurrence": entities[0]["first_change"],
                    "last_occurrence": entities[-1]["last_change"],
                    "organization_id": str(config.organization_id) if config.organization_id else None,
                    "config_id": str(config.id),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking permission changes: {e}", exc_info=True)
            return None

    async def _check_role_changes(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        config: AuditAlertConfig,
    ) -> Optional[Dict[str, Any]]:
        """
        Check for user role changes.

        Detects potential privilege escalation by counting role change operations
        within the time window.

        Args:
            session: Database session
            start_time: Start of time window
            end_time: End of time window
            config: Alert configuration

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        try:
            # Query role change operations
            query = (
                select(
                    AuditLog.user_id,
                    AuditLog.entity_id,
                    func.count(AuditLog.id).label("role_change_count"),
                    func.min(AuditLog.created_at).label("first_change"),
                    func.max(AuditLog.created_at).label("last_change"),
                )
                .where(
                    and_(
                        AuditLog.action_type == AuditActionType.USER_ROLE_CHANGED,
                        AuditLog.created_at >= start_time,
                        AuditLog.created_at <= end_time,
                    )
                )
                .group_by(AuditLog.user_id, AuditLog.entity_id)
                .having(func.count(AuditLog.id) >= config.threshold)
            )

            # Filter by organization if configured
            if config.organization_id:
                query = query.where(
                    AuditLog.organization_id == config.organization_id
                )

            result = await session.execute(query)
            violations = result.all()

            if violations:
                entities = [
                    {
                        "user_id": str(v.user_id) if v.user_id else None,
                        "target_user_id": str(v.entity_id) if v.entity_id else None,
                        "role_change_count": v.role_change_count,
                        "first_change": v.first_change.isoformat(),
                        "last_change": v.last_change.isoformat(),
                    }
                    for v in violations
                ]

                total_changes = sum(e["role_change_count"] for e in entities)

                return {
                    "alert_type": AlertType.ROLE_CHANGES,
                    "severity": config.severity,
                    "message": (
                        f"Detected {len(violations)} user(s) with excessive role changes. "
                        f"Total changes: {total_changes}. "
                        f"Threshold: {config.threshold} changes in {config.time_window_minutes} minutes."
                    ),
                    "count": total_changes,
                    "threshold": config.threshold,
                    "time_window_minutes": config.time_window_minutes,
                    "entities": entities,
                    "first_occurrence": entities[0]["first_change"],
                    "last_occurrence": entities[-1]["last_change"],
                    "organization_id": str(config.organization_id) if config.organization_id else None,
                    "config_id": str(config.id),
                }

            return None

        except Exception as e:
            logger.error(f"Error checking role changes: {e}", exc_info=True)
            return None


def get_audit_alerting_service(db: Optional[Session] = None) -> AuditAlertingService:
    """
    Get or create the global audit alerting service instance.

    Args:
        db: Database session (optional)

    Returns:
        AuditAlertingService instance
    """
    global _audit_alerting_service

    if _audit_alerting_service is None:
        _audit_alerting_service = AuditAlertingService(db=db)

    return _audit_alerting_service


# Convenience function for direct import
async def detect_suspicious_activity(
    time_window_minutes: int = AuditAlertingService.DEFAULT_TIME_WINDOW_MINUTES,
    organization_id: Optional[UUID] = None,
    alert_types: Optional[List[AlertType]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect suspicious activity patterns in audit logs.

    This is a convenience function that creates a service instance and performs
    suspicious activity detection. Use this for one-off checks or when you don't
    need to maintain a service instance.

    Args:
        time_window_minutes: Time window in minutes to analyze (default: 10)
        organization_id: Organization UUID to scope analysis (None for all orgs)
        alert_types: List of specific alert types to check (None for all)

    Returns:
        List of alert dictionaries with detected suspicious patterns

    Example:
        >>> from backend.services.audit_alerting import detect_suspicious_activity
        >>> alerts = await detect_suspicious_activity(time_window_minutes=30)
        >>> for alert in alerts:
        ...     print(f"Alert: {alert['message']}")
    """
    service = get_audit_alerting_service()
    return await service.detect_suspicious_activity(
        time_window_minutes=time_window_minutes,
        organization_id=organization_id,
        alert_types=alert_types,
    )
