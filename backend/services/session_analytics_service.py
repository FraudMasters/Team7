"""
Session analytics service for tracking session patterns and security metrics.

This module provides session analytics functionality including tracking session
creation patterns, device usage, geographic distribution, security anomalies,
and user behavior patterns. It helps identify suspicious activity, optimize
session management, and provide insights for security monitoring.

The session analytics service supports:
- Session creation and activity metrics
- Device and browser analytics
- Geographic distribution tracking
- Security anomaly detection
- User session behavior patterns
- Time-based session analysis
- Concurrent session tracking
- Session lifetime statistics

Analytics are computed in real-time and can be aggregated over different
time periods (hourly, daily, weekly, monthly).
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker
from models.session import Session as SessionModel
from models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)

# Global session analytics service instance
_session_analytics_service: Optional["SessionAnalyticsService"] = None


class SessionAnalyticsService:
    """
    Session analytics service for tracking session patterns and security metrics.

    This class provides comprehensive analytics capabilities for session monitoring,
    security analysis, and user behavior tracking. It computes metrics in real-time
    and supports various aggregation periods.

    Attributes:
        anomaly_threshold_multiplier: Multiplier for anomaly detection (default: 3.0)
        suspicious_ip_threshold: Max sessions per IP before flagging (default: 10)
        concurrent_session_threshold: Max concurrent sessions before alerting (default: 5)

    Example:
        >>> service = SessionAnalyticsService()
        >>> # Get session metrics
        >>> metrics = await service.get_session_metrics(
        ...     user_id="user-123",
        ...     days=30
        ... )
        >>> # Detect anomalies
        >>> anomalies = await service.detect_anomalies(user_id="user-123")
        >>> # Get device distribution
        >>> devices = await service.get_device_distribution(days=7)
    """

    def __init__(
        self,
        anomaly_threshold_multiplier: Optional[float] = None,
        suspicious_ip_threshold: Optional[int] = None,
        concurrent_session_threshold: Optional[int] = None,
    ) -> None:
        """
        Initialize the session analytics service with configuration.

        Args:
            anomaly_threshold_multiplier: Multiplier for anomaly detection (defaults to 3.0)
            suspicious_ip_threshold: Max sessions per IP before flagging (defaults to 10)
            concurrent_session_threshold: Max concurrent sessions before alerting (defaults to 5)
        """
        self.anomaly_threshold_multiplier = anomaly_threshold_multiplier or 3.0
        self.suspicious_ip_threshold = suspicious_ip_threshold or 10
        self.concurrent_session_threshold = concurrent_session_threshold or 5

        logger.info(
            f"SessionAnalyticsService initialized "
            f"(anomaly_threshold={self.anomaly_threshold_multiplier}x, "
            f"suspicious_ip_threshold={self.suspicious_ip_threshold})"
        )

    async def get_session_metrics(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get comprehensive session metrics for a user or globally.

        Args:
            user_id: Optional user ID to filter metrics (None for global metrics)
            days: Number of days to look back (default: 30)

        Returns:
            Dictionary with session metrics including counts, averages, and distributions

        Example:
            >>> service = SessionAnalyticsService()
            >>> metrics = await service.get_session_metrics(user_id="user-123", days=7)
            >>> print(metrics["total_sessions"])
            >>> print(metrics["average_session_duration_minutes"])
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as db:
            try:
                # Build base query
                base_query = select(SessionModel).where(
                    SessionModel.created_at >= cutoff_time
                )
                if user_id:
                    base_query = base_query.where(SessionModel.user_id == user_id)

                # Get all sessions
                result = await db.execute(base_query)
                sessions = result.scalars().all()

                # Calculate metrics
                metrics = {
                    "period_days": days,
                    "user_id": user_id,
                    "total_sessions": len(sessions),
                    "active_sessions": sum(1 for s in sessions if s.is_active),
                    "revoked_sessions": sum(1 for s in sessions if not s.is_active),
                    "expired_sessions": sum(1 for s in sessions if s.is_expired()),
                    "average_sessions_per_day": len(sessions) / days if days > 0 else 0,
                }

                # Calculate session durations
                durations = []
                for session in sessions:
                    if session.revoked_at:
                        duration = (session.revoked_at - session.created_at).total_seconds() / 60
                        durations.append(duration)
                    elif not session.is_active:
                        continue
                    else:
                        duration = (datetime.utcnow() - session.created_at).total_seconds() / 60
                        durations.append(duration)

                if durations:
                    metrics["average_session_duration_minutes"] = sum(durations) / len(durations)
                    metrics["max_session_duration_minutes"] = max(durations)
                    metrics["min_session_duration_minutes"] = min(durations)
                else:
                    metrics["average_session_duration_minutes"] = 0
                    metrics["max_session_duration_minutes"] = 0
                    metrics["min_session_duration_minutes"] = 0

                # Device type distribution
                device_counts = {}
                for session in sessions:
                    device_type = session.device_type or "unknown"
                    device_counts[device_type] = device_counts.get(device_type, 0) + 1
                metrics["device_distribution"] = device_counts

                # Revocation reasons
                revoke_reasons = {}
                for session in sessions:
                    if session.revoke_reason:
                        revoke_reasons[session.revoke_reason] = revoke_reasons.get(
                            session.revoke_reason, 0
                        ) + 1
                metrics["revocation_reasons"] = revoke_reasons

                logger.debug(f"Computed session metrics for user={user_id}, days={days}")
                return metrics

            except Exception as e:
                logger.error(f"Error computing session metrics: {e}", exc_info=True)
                return {
                    "period_days": days,
                    "user_id": user_id,
                    "error": str(e),
                }

    async def get_device_distribution(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get distribution of device types for sessions.

        Args:
            days: Number of days to look back (default: 7)
            user_id: Optional user ID to filter by

        Returns:
            Dictionary mapping device types to counts

        Example:
            >>> service = SessionAnalyticsService()
            >>> devices = await service.get_device_distribution(days=30)
            >>> print(devices)  # {"desktop": 150, "mobile": 75, "tablet": 20}
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as db:
            try:
                # Build query
                query = (
                    select(
                        SessionModel.device_type,
                        func.count(SessionModel.id).label("count"),
                    )
                    .where(SessionModel.created_at >= cutoff_time)
                    .group_by(SessionModel.device_type)
                )

                if user_id:
                    query = query.where(SessionModel.user_id == user_id)

                result = await db.execute(query)
                rows = result.all()

                distribution = {
                    row.device_type or "unknown": row.count
                    for row in rows
                }

                logger.debug(f"Device distribution: {distribution}")
                return distribution

            except Exception as e:
                logger.error(f"Error computing device distribution: {e}", exc_info=True)
                return {}

    async def get_geographic_distribution(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Get geographic distribution of sessions by location.

        Args:
            days: Number of days to look back (default: 7)
            user_id: Optional user ID to filter by

        Returns:
            Dictionary mapping locations to counts

        Example:
            >>> service = SessionAnalyticsService()
            >>> locations = await service.get_geographic_distribution(days=30)
            >>> print(locations)  # {"San Francisco, CA": 100, "New York, NY": 50}
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as db:
            try:
                # Build query
                query = (
                    select(
                        SessionModel.location,
                        func.count(SessionModel.id).label("count"),
                    )
                    .where(
                        and_(
                            SessionModel.created_at >= cutoff_time,
                            SessionModel.location.isnot(None),
                        )
                    )
                    .group_by(SessionModel.location)
                )

                if user_id:
                    query = query.where(SessionModel.user_id == user_id)

                result = await db.execute(query)
                rows = result.all()

                distribution = {row.location: row.count for row in rows}

                logger.debug(f"Geographic distribution: {distribution}")
                return distribution

            except Exception as e:
                logger.error(f"Error computing geographic distribution: {e}", exc_info=True)
                return {}

    async def detect_anomalies(
        self,
        user_id: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalous session patterns for a user.

        Detects:
        - Unusual number of concurrent sessions
        - Sessions from suspicious IPs
        - Rapid session creation
        - Geographic anomalies (if location tracking is enabled)
        - Device switching patterns

        Args:
            user_id: User ID to analyze
            days: Number of days to analyze (default: 7)

        Returns:
            List of detected anomalies with severity and description

        Example:
            >>> service = SessionAnalyticsService()
            >>> anomalies = await service.detect_anomalies("user-123")
            >>> for anomaly in anomalies:
            ...     print(f"{anomaly['type']}: {anomaly['description']}")
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        anomalies = []

        async with async_session_maker() as db:
            try:
                # Get user's sessions
                result = await db.execute(
                    select(SessionModel)
                    .where(
                        and_(
                            SessionModel.user_id == user_id,
                            SessionModel.created_at >= cutoff_time,
                        )
                    )
                    .order_by(SessionModel.created_at.desc())
                )
                sessions = result.scalars().all()

                if not sessions:
                    return anomalies

                # Check concurrent sessions
                concurrent_sessions = sum(1 for s in sessions if s.is_active)
                if concurrent_sessions > self.concurrent_session_threshold:
                    anomalies.append({
                        "type": "concurrent_sessions",
                        "severity": "high" if concurrent_sessions > self.concurrent_session_threshold * 2 else "medium",
                        "description": f"User has {concurrent_sessions} concurrent sessions (threshold: {self.concurrent_session_threshold})",
                        "count": concurrent_sessions,
                    })

                # Check for suspicious IPs (same IP, many sessions)
                ip_counts = {}
                for session in sessions:
                    if session.ip_address:
                        ip_counts[session.ip_address] = ip_counts.get(session.ip_address, 0) + 1

                for ip, count in ip_counts.items():
                    if count > self.suspicious_ip_threshold:
                        anomalies.append({
                            "type": "suspicious_ip",
                            "severity": "high",
                            "description": f"IP address {ip} has {count} sessions (threshold: {self.suspicious_ip_threshold})",
                            "ip_address": ip,
                            "count": count,
                        })

                # Check for rapid session creation (more than 5 sessions in 1 hour)
                recent_sessions = [
                    s for s in sessions
                    if s.created_at > datetime.utcnow() - timedelta(hours=1)
                ]
                if len(recent_sessions) > 5:
                    anomalies.append({
                        "type": "rapid_session_creation",
                        "severity": "medium",
                        "description": f"{len(recent_sessions)} sessions created in the last hour",
                        "count": len(recent_sessions),
                    })

                # Check for geographic anomalies (sessions from multiple locations)
                locations = set(s.location for s in sessions if s.location)
                if len(locations) > 5:
                    anomalies.append({
                        "type": "geographic_anomaly",
                        "severity": "medium",
                        "description": f"Sessions from {len(locations)} different locations in {days} days",
                        "locations": list(locations),
                    })

                # Check for device switching (more than 3 different device types)
                device_types = set(s.device_type for s in sessions if s.device_type)
                if len(device_types) > 3:
                    anomalies.append({
                        "type": "device_switching",
                        "severity": "low",
                        "description": f"Sessions from {len(device_types)} different device types",
                        "device_types": list(device_types),
                    })

                logger.info(f"Detected {len(anomalies)} anomalies for user {user_id}")
                return anomalies

            except Exception as e:
                logger.error(f"Error detecting anomalies for user {user_id}: {e}", exc_info=True)
                return []

    async def detect_anomaly(
        self,
        user_id: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Detect login anomalies for a user based on login attempt patterns.

        Analyzes login attempts to detect suspicious patterns such as:
        - Rapid failed login attempts (brute force attacks)
        - Logins from unusual locations
        - Logins at unusual times
        - Multiple failed attempts followed by success (credential stuffing)
        - Geographic impossibility (logins from different locations too close together)
        - Unusual IP address patterns

        Args:
            user_id: User ID to analyze
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary with anomaly detection results including:
                - has_anomaly: Boolean indicating if any anomalies were detected
                - anomalies: List of detected anomalies with details
                - risk_score: Overall risk score (0-100)
                - recommendations: List of recommended actions

        Example:
            >>> service = SessionAnalyticsService()
            >>> result = await service.detect_anomaly("user-123")
            >>> if result["has_anomaly"]:
            ...     print(f"Risk score: {result['risk_score']}")
            ...     for anomaly in result["anomalies"]:
            ...         print(f"- {anomaly['type']}: {anomaly['description']}")
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        anomalies = []
        risk_score = 0

        async with async_session_maker() as db:
            try:
                # Get user's login attempts
                result = await db.execute(
                    select(LoginAttempt)
                    .where(
                        and_(
                            LoginAttempt.user_id == user_id,
                            LoginAttempt.created_at >= cutoff_time,
                        )
                    )
                    .order_by(LoginAttempt.created_at.desc())
                )
                login_attempts = result.scalars().all()

                if not login_attempts:
                    return {
                        "has_anomaly": False,
                        "anomalies": [],
                        "risk_score": 0,
                        "recommendations": [],
                    }

                # Separate successful and failed attempts
                failed_attempts = [la for la in login_attempts if not la.success]
                successful_attempts = [la for la in login_attempts if la.success]

                # 1. Check for rapid failed login attempts (brute force)
                if len(failed_attempts) > 0:
                    # Check for failed attempts in the last hour
                    recent_failed = [
                        la for la in failed_attempts
                        if la.created_at > datetime.utcnow() - timedelta(hours=1)
                    ]
                    if len(recent_failed) >= 3:
                        severity = "high" if len(recent_failed) >= 5 else "medium"
                        anomalies.append({
                            "type": "rapid_failed_attempts",
                            "severity": severity,
                            "description": f"{len(recent_failed)} failed login attempts in the last hour",
                            "count": len(recent_failed),
                            "risk_impact": 25 if severity == "high" else 15,
                        })
                        risk_score += 25 if severity == "high" else 15

                # 2. Check for credential stuffing pattern (many fails then success)
                if len(failed_attempts) > 5 and len(successful_attempts) > 0:
                    # Check if there are failed attempts followed by a success
                    sorted_attempts = sorted(login_attempts, key=lambda x: x.created_at)
                    for i, attempt in enumerate(sorted_attempts):
                        if attempt.success and i >= 3:
                            # Check if previous 3+ attempts were failures
                            previous_attempts = sorted_attempts[max(0, i-5):i]
                            if all(not pa.success for pa in previous_attempts):
                                anomalies.append({
                                    "type": "credential_stuffing",
                                    "severity": "high",
                                    "description": f"{len(previous_attempts)} failed attempts followed by successful login",
                                    "count": len(previous_attempts),
                                    "risk_impact": 30,
                                })
                                risk_score += 30
                                break

                # 3. Check for logins from multiple unusual locations
                locations = set(la.location for la in login_attempts if la.location)
                if len(locations) > 3:
                    anomalies.append({
                        "type": "multiple_locations",
                        "severity": "medium",
                        "description": f"Login attempts from {len(locations)} different locations in {days} days",
                        "locations": list(locations),
                        "risk_impact": 15,
                    })
                    risk_score += 15

                # 4. Check for geographic impossibility
                if len(successful_attempts) >= 2:
                    sorted_successful = sorted(successful_attempts, key=lambda x: x.created_at)
                    for i in range(1, len(sorted_successful)):
                        prev_attempt = sorted_successful[i-1]
                        curr_attempt = sorted_successful[i]

                        # If both have locations and they're different
                        if (prev_attempt.location and curr_attempt.location and
                            prev_attempt.location != curr_attempt.location):
                            time_diff = (curr_attempt.created_at - prev_attempt.created_at).total_seconds() / 3600
                            # If logins from different locations within 1 hour
                            if time_diff < 1:
                                anomalies.append({
                                    "type": "geographic_impossibility",
                                    "severity": "high",
                                    "description": (
                                        f"Logins from different locations "
                                        f"({prev_attempt.location} -> {curr_attempt.location}) "
                                        f"within {int(time_diff * 60)} minutes"
                                    ),
                                    "time_diff_hours": time_diff,
                                    "risk_impact": 35,
                                })
                                risk_score += 35
                                break

                # 5. Check for logins from suspicious IPs (many failed attempts from same IP)
                ip_failed_counts = {}
                for attempt in failed_attempts:
                    if attempt.ip_address:
                        ip_failed_counts[attempt.ip_address] = ip_failed_counts.get(
                            attempt.ip_address, 0
                        ) + 1

                for ip, count in ip_failed_counts.items():
                    if count >= 5:
                        anomalies.append({
                            "type": "suspicious_ip",
                            "severity": "high",
                            "description": f"IP address {ip} has {count} failed login attempts",
                            "ip_address": ip,
                            "count": count,
                            "risk_impact": 20,
                        })
                        risk_score += 20

                # 6. Check for unusual login times (late night/early morning)
                unusual_hour_logins = []
                for attempt in successful_attempts:
                    hour = attempt.created_at.hour
                    # Consider 2 AM - 6 AM as unusual hours
                    if 2 <= hour < 6:
                        unusual_hour_logins.append(attempt)

                if len(unusual_hour_logins) >= 2:
                    anomalies.append({
                        "type": "unusual_login_times",
                        "severity": "low",
                        "description": f"{len(unusual_hour_logins)} logins during unusual hours (2 AM - 6 AM)",
                        "count": len(unusual_hour_logins),
                        "risk_impact": 10,
                    })
                    risk_score += 10

                # 7. Check for multiple user agent strings (device switching)
                user_agents = set(la.user_agent for la in login_attempts if la.user_agent)
                if len(user_agents) > 5:
                    anomalies.append({
                        "type": "multiple_user_agents",
                        "severity": "medium",
                        "description": f"Login attempts from {len(user_agents)} different user agents",
                        "count": len(user_agents),
                        "risk_impact": 15,
                    })
                    risk_score += 15

                # Cap risk score at 100
                risk_score = min(risk_score, 100)

                # Generate recommendations based on anomalies
                recommendations = []
                if risk_score >= 70:
                    recommendations.append("Immediately require password change")
                    recommendations.append("Enable two-factor authentication")
                    recommendations.append("Review and revoke all active sessions")
                elif risk_score >= 40:
                    recommendations.append("Consider requiring password change")
                    recommendations.append("Enable two-factor authentication if not already enabled")
                    recommendations.append("Monitor account activity closely")
                elif risk_score >= 20:
                    recommendations.append("Monitor account activity")
                    recommendations.append("Consider enabling two-factor authentication")

                has_anomaly = len(anomalies) > 0

                if has_anomaly:
                    logger.warning(
                        f"Login anomalies detected for user {user_id}: "
                        f"{len(anomalies)} anomalies, risk score {risk_score}"
                    )
                else:
                    logger.debug(f"No login anomalies detected for user {user_id}")

                return {
                    "has_anomaly": has_anomaly,
                    "anomalies": anomalies,
                    "risk_score": risk_score,
                    "recommendations": recommendations,
                    "analysis_period_days": days,
                    "total_login_attempts": len(login_attempts),
                    "failed_attempts": len(failed_attempts),
                    "successful_attempts": len(successful_attempts),
                }

            except Exception as e:
                logger.error(f"Error detecting login anomalies for user {user_id}: {e}", exc_info=True)
                return {
                    "has_anomaly": False,
                    "anomalies": [],
                    "risk_score": 0,
                    "recommendations": [],
                    "error": str(e),
                }

    async def get_peak_usage_times(
        self,
        days: int = 7,
        user_id: Optional[str] = None,
    ) -> Dict[int, int]:
        """
        Get peak usage times by hour of day.

        Args:
            days: Number of days to analyze (default: 7)
            user_id: Optional user ID to filter by

        Returns:
            Dictionary mapping hour (0-23) to session count

        Example:
            >>> service = SessionAnalyticsService()
            >>> usage = await service.get_peak_usage_times(days=30)
            >>> peak_hour = max(usage, key=usage.get)
            >>> print(f"Peak usage at hour {peak_hour}")
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as db:
            try:
                # Build query
                query = select(SessionModel).where(
                    SessionModel.created_at >= cutoff_time
                )
                if user_id:
                    query = query.where(SessionModel.user_id == user_id)

                result = await db.execute(query)
                sessions = result.scalars().all()

                # Count sessions by hour
                hour_counts = {hour: 0 for hour in range(24)}
                for session in sessions:
                    hour = session.created_at.hour
                    hour_counts[hour] += 1

                logger.debug(f"Peak usage times computed for {len(sessions)} sessions")
                return hour_counts

            except Exception as e:
                logger.error(f"Error computing peak usage times: {e}", exc_info=True)
                return {hour: 0 for hour in range(24)}

    async def get_session_lifecycle_stats(
        self,
        days: int = 30,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get session lifecycle statistics.

        Args:
            days: Number of days to analyze (default: 30)
            user_id: Optional user ID to filter by

        Returns:
            Dictionary with lifecycle metrics including creation rate, revocation rate, etc.

        Example:
            >>> service = SessionAnalyticsService()
            >>> stats = await service.get_session_lifecycle_stats(days=30)
            >>> print(stats["daily_creation_rate"])
            >>> print(stats["daily_revocation_rate"])
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as db:
            try:
                # Build base query
                query = select(SessionModel).where(
                    SessionModel.created_at >= cutoff_time
                )
                if user_id:
                    query = query.where(SessionModel.user_id == user_id)

                result = await db.execute(query)
                sessions = result.scalars().all()

                # Calculate lifecycle metrics
                total_sessions = len(sessions)
                revoked_sessions = sum(1 for s in sessions if not s.is_active)
                active_sessions = sum(1 for s in sessions if s.is_active)

                stats = {
                    "period_days": days,
                    "user_id": user_id,
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "revoked_sessions": revoked_sessions,
                    "daily_creation_rate": total_sessions / days if days > 0 else 0,
                    "daily_revocation_rate": revoked_sessions / days if days > 0 else 0,
                    "active_to_total_ratio": active_sessions / total_sessions if total_sessions > 0 else 0,
                    "revocation_rate": revoked_sessions / total_sessions if total_sessions > 0 else 0,
                }

                logger.debug(f"Session lifecycle stats computed: {stats}")
                return stats

            except Exception as e:
                logger.error(f"Error computing session lifecycle stats: {e}", exc_info=True)
                return {
                    "period_days": days,
                    "user_id": user_id,
                    "error": str(e),
                }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check session analytics service health.

        Returns:
            Dictionary with health status

        Example:
            >>> service = SessionAnalyticsService()
            >>> health = await service.health_check()
            >>> print(health["status"])
        """
        result = {
            "status": "unhealthy",
            "error": None,
        }

        try:
            # Try to get basic metrics
            metrics = await self.get_session_metrics(days=1)
            if "error" not in metrics:
                result["status"] = "healthy"
            else:
                result["error"] = metrics["error"]

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Session analytics service health check failed: {e}", exc_info=True)

        return result


def get_session_analytics_service() -> SessionAnalyticsService:
    """
    Get or create global session analytics service instance.

    Returns:
        Global SessionAnalyticsService instance

    Example:
        >>> service = get_session_analytics_service()
        >>> metrics = await service.get_session_metrics(days=30)
    """
    global _session_analytics_service
    if _session_analytics_service is None:
        _session_analytics_service = SessionAnalyticsService()
    return _session_analytics_service
