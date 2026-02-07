"""
Celery tasks for automated health monitoring and alerting.

This module provides scheduled and manual health monitoring tasks including:
- Periodic health checks for all system components
- Automated alerting when services become unhealthy
- Alert cooldown management to prevent alert fatigue
- Component-specific health checks
- Health monitoring task scheduling via Celery beat
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from celery import shared_task

from config import get_settings
from services.alerting import Alert, AlertingService, get_alerting_service
from services.health_check import HealthCheckService, get_health_check_service

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.health_monitoring.monitor_health_and_alert",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def monitor_health_and_alert(self) -> Dict[str, Any]:
    """
    Scheduled health monitoring task with automated alerting.

    Runs comprehensive health checks on all system components and sends
    alerts when services become unhealthy or degraded. Configured via
    Celery beat to run at specified intervals (default: every 5 minutes).

    This task:
    1. Checks all registered health checkers (database, Redis, Celery, ML models, external APIs)
    2. Determines overall system health status
    3. Sends alerts for unhealthy or degraded essential components
    4. Respects cooldown periods to prevent alert fatigue
    5. Returns summary of health status and alerts sent

    Returns:
        Dictionary with health check results and alert status

    Example:
        >>> result = monitor_health_and_alert()
        >>> print(result['overall_status'])
        'healthy'
    """
    logger.info("Starting automated health monitoring")

    try:
        # Run health checks in async context
        loop = asyncio.get_event_loop()
        health_result = loop.run_until_complete(_perform_health_checks_and_alerts())

        logger.info(
            f"Health monitoring completed: {health_result['overall_status']} "
            f"({health_result.get('alerts_sent', 0)} alerts sent)"
        )

        return health_result

    except Exception as e:
        logger.error(f"Health monitoring failed: {e}", exc_info=True)

        # Retry with backoff
        try:
            raise self.retry(exc=e, countdown=300)
        except self.MaxRetriesExceededError:
            logger.error("Health monitoring max retries exceeded")
            return {
                "status": "failed",
                "error": str(e),
                "overall_status": "unknown",
            }


@shared_task(
    name="tasks.health_monitoring.check_component",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def check_component_task(
    self,
    component_name: str,
    send_alert_if_unhealthy: bool = True,
) -> Dict[str, Any]:
    """
    Check health of a specific component.

    Args:
        component_name: Name of the component to check
        send_alert_if_unhealthy: Send alert if component is unhealthy

    Returns:
        Dictionary with component health status

    Example:
        >>> result = check_component_task("database")
        >>> print(result['status'])
        'healthy'
    """
    logger.info(f"Checking component: {component_name}")

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            _check_component_and_alert(component_name, send_alert_if_unhealthy)
        )

        logger.info(f"Component check completed: {component_name} - {result.get('status')}")

        return result

    except Exception as e:
        logger.error(f"Component check failed for {component_name}: {e}", exc_info=True)

        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                "status": "failed",
                "error": str(e),
                "component": component_name,
            }


@shared_task(
    name="tasks.health_monitoring.check_essential_services",
    bind=True,
)
def check_essential_services_task(self) -> Dict[str, Any]:
    """
    Check health of essential services only (database, Redis, Celery).

    This is useful for readiness probes and quick health checks where
    we only need to verify critical services are available.

    Returns:
        Dictionary with essential service health status
    """
    logger.info("Checking essential services")

    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(_check_essential_services())

        logger.info(
            f"Essential services check completed: {result['overall_status']}"
        )

        return result

    except Exception as e:
        logger.error(f"Essential services check failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "overall_status": "unknown",
        }


async def _perform_health_checks_and_alerts() -> Dict[str, Any]:
    """
    Perform comprehensive health checks and send alerts if needed.

    Returns:
        Dictionary with health check results and alert status
    """
    # Get health check service
    health_service = get_health_check_service()

    # Run all health checks
    health_result = await health_service.check_all()

    # Get alerting service
    alerting_service = get_alerting_service()

    # Track alerts sent
    alerts_sent: List[Dict[str, Any]] = []
    components_by_status: Dict[str, List[str]] = {
        "unhealthy": [],
        "degraded": [],
        "healthy": [],
    }

    # Categorize components by status
    for component_name, component_result in health_result.get("components", {}).items():
        status = component_result.get("status", "unknown")
        if status in components_by_status:
            components_by_status[status].append(component_name)

    # Send alerts for unhealthy essential components
    for component_name in components_by_status["unhealthy"]:
        is_essential = component_name in health_service.ESSENTIAL_COMPONENTS
        if is_essential:
            component_result = health_result["components"][component_name]
            alert = _create_health_alert(
                component_name=component_name,
                status="unhealthy",
                component_result=component_result,
            )
            await _send_alert_if_needed(alerting_service, alert, alerts_sent)

    # Send alerts for degraded essential components (if warning alerts enabled)
    if alerting_service.alert_on_warning:
        for component_name in components_by_status["degraded"]:
            is_essential = component_name in health_service.ESSENTIAL_COMPONENTS
            if is_essential:
                component_result = health_result["components"][component_name]
                alert = _create_health_alert(
                    component_name=component_name,
                    status="degraded",
                    component_result=component_result,
                )
                await _send_alert_if_needed(alerting_service, alert, alerts_sent)

    # Build response
    return {
        "status": "success",
        "overall_status": health_result.get("overall_status", "unknown"),
        "total_time_ms": health_result.get("summary", {}).get("total_time_ms", 0),
        "components_checked": health_result.get("summary", {}).get("components_checked", 0),
        "components_healthy": health_result.get("summary", {}).get("components_healthy", 0),
        "components_degraded": health_result.get("summary", {}).get("components_degraded", 0),
        "components_unhealthy": health_result.get("summary", {}).get("components_unhealthy", 0),
        "alerts_sent": len(alerts_sent),
        "alert_details": alerts_sent,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _check_component_and_alert(
    component_name: str,
    send_alert_if_unhealthy: bool,
) -> Dict[str, Any]:
    """
    Check a specific component and send alert if needed.

    Args:
        component_name: Name of the component to check
        send_alert_if_unhealthy: Whether to send alert if unhealthy

    Returns:
        Dictionary with component health status
    """
    # Get health check service
    health_service = get_health_check_service()

    # Check component
    try:
        component_result = await health_service.check_component(component_name)
    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
            "component": component_name,
        }

    # Send alert if component is unhealthy and alerting is enabled
    alerts_sent = []
    if send_alert_if_unhealthy and not component_result.is_operational():
        alerting_service = get_alerting_service()
        alert = _create_health_alert(
            component_name=component_name,
            status=component_result.status,
            component_result=component_result.to_dict(),
        )
        await _send_alert_if_needed(alerting_service, alert, alerts_sent)

    return {
        "status": "success",
        "component": component_name,
        "component_status": component_result.status,
        "response_time_ms": component_result.response_time_ms,
        "message": component_result.message,
        "details": component_result.details,
        "alerts_sent": len(alerts_sent),
        "error": component_result.error,
    }


async def _check_essential_services() -> Dict[str, Any]:
    """
    Check health of essential services only.

    Returns:
        Dictionary with essential service health status
    """
    # Get health check service
    health_service = get_health_check_service()

    # Check essential services
    health_result = await health_service.check_essential_only()

    return {
        "status": "success",
        "overall_status": health_result.get("overall_status", "unknown"),
        "total_time_ms": health_result.get("summary", {}).get("total_time_ms", 0),
        "components": health_result.get("components", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _create_health_alert(
    component_name: str,
    status: str,
    component_result: Dict[str, Any],
) -> Alert:
    """
    Create an alert from health check results.

    Args:
        component_name: Name of the component
        status: Health status (unhealthy, degraded, healthy)
        component_result: Component health check result

    Returns:
        Alert object
    """
    # Determine severity based on status
    if status == "unhealthy":
        severity = Alert.SEVERITY_CRITICAL
        title = f"{component_name.title()} Unhealthy"
    elif status == "degraded":
        severity = Alert.SEVERITY_WARNING
        title = f"{component_name.title()} Degraded"
    else:
        # Healthy - for recovery notifications
        severity = Alert.SEVERITY_INFO
        title = f"{component_name.title()} Recovered"

    # Build message
    error = component_result.get("error")
    message = component_result.get("message", "")
    response_time = component_result.get("response_time_ms", 0)

    if error:
        full_message = f"{message} - Error: {error}"
    else:
        full_message = message

    if response_time > 0:
        full_message += f" (Response time: {response_time:.2f}ms)"

    # Create alert
    return Alert(
        title=title,
        message=full_message,
        severity=severity,
        component=component_name,
        status=status,
        details=component_result,
    )


async def _send_alert_if_needed(
    alerting_service: AlertingService,
    alert: Alert,
    alerts_sent: List[Dict[str, Any]],
) -> None:
    """
    Send alert through alerting service and track result.

    Args:
        alerting_service: Alerting service instance
        alert: Alert to send
        alerts_sent: List to track sent alerts
    """
    try:
        results = await alerting_service.send_alert(alert)

        # Record successful sends
        successful_channels = [
            channel for channel, success in results.items() if success
        ]

        if successful_channels:
            alerts_sent.append({
                "alert_id": alert.alert_id,
                "component": alert.component,
                "severity": alert.severity,
                "channels": successful_channels,
                "message": alert.message,
            })

            logger.info(
                f"Alert sent for {alert.component} ({alert.severity}) "
                f"via {len(successful_channels)} channel(s)"
            )
        else:
            logger.warning(f"No channels available for alert: {alert.alert_id}")

    except Exception as e:
        logger.error(f"Failed to send alert: {e}", exc_info=True)


__all__ = [
    "monitor_health_and_alert",
    "check_component_task",
    "check_essential_services_task",
]
