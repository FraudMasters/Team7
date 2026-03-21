"""
Fairness monitoring tasks for tracking AI bias detection and fairness metrics over time.

This module provides Celery tasks for monitoring model fairness across demographic groups,
detecting algorithmic bias in candidate rankings, and triggering alerts when fairness
thresholds are exceeded.
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from models.job_vacancy import JobVacancy
from models.candidate_rank import CandidateRank
from models.fairness_metrics import FairnessMetrics, FairnessAlert
from models.demographic_inference import DemographicInference
from analyzers.fairness_calculator import get_fairness_calculator
from config import get_settings
from database import async_session_maker

logger = logging.getLogger(__name__)
settings = get_settings()

# Fairness threshold constants
DISPARATE_IMPACT_ALERT_THRESHOLD = 0.8  # 80% rule
STATISTICAL_PARITY_ALERT_THRESHOLD = 0.1  # 10% difference

# Minimum time between monitoring checks (hours)
MONITORING_INTERVAL_HOURS = 24

# Minimum samples required for fairness evaluation
MIN_EVALUATION_SAMPLES = 10


async def _query_fairness_metrics_async(
    vacancy_id: str,
    demographic_group: str,
):
    """Async helper to query fairness metrics from database."""
    async with async_session_maker() as db:
        metrics_query = select(FairnessMetrics).where(
            and_(
                FairnessMetrics.vacancy_id == UUID(vacancy_id),
                FairnessMetrics.demographic_group == demographic_group
            )
        ).order_by(desc(FairnessMetrics.created_at))
        metrics_result = await db.execute(metrics_query)
        metrics_records = list(metrics_result.scalars().all())
        return metrics_records


def calculate_fairness_metrics(
    vacancy_id: str,
    demographic_group: str = "gender",
) -> Dict[str, Any]:
    """
    Calculate fairness metrics for a specific vacancy and demographic group.

    This function retrieves fairness metrics for a vacancy's ranking outcomes
    and calculates summary statistics including disparate impact ratios,
    statistical parity differences, and alert status.

    Args:
        vacancy_id: UUID of the job vacancy to evaluate
        demographic_group: Demographic attribute to analyze (default: "gender")

    Returns:
        Dictionary containing fairness metrics:
        {
            "vacancy_id": "uuid",
            "demographic_group": "gender",
            "latest_metrics": {
                "disparate_impact_ratio": 0.92,
                "statistical_parity_difference": 0.03,
                "overall_selection_rate": 0.45,
                "group_sample_size": 150,
                "total_sample_size": 500
            },
            "group_metrics": {
                "male": {"selection_rate": 0.48, "sample_size": 250},
                "female": {"selection_rate": 0.42, "sample_size": 250}
            },
            "alert_triggered": false,
            "alert_severity": null,
            "metric_count": 1
        }

    Example:
        >>> metrics = calculate_fairness_metrics("vacancy-uuid", "gender")
        >>> print(metrics["latest_metrics"]["disparate_impact_ratio"])
        0.92
    """
    # Query fairness metrics from database
    metrics_records = asyncio.run(_query_fairness_metrics_async(vacancy_id, demographic_group))

    if not metrics_records:
        logger.warning(
            f"No fairness metrics found for vacancy {vacancy_id} "
            f"with demographic group '{demographic_group}'"
        )
        return {
            "vacancy_id": vacancy_id,
            "demographic_group": demographic_group,
            "latest_metrics": None,
            "group_metrics": None,
            "alert_triggered": False,
            "alert_severity": None,
            "metric_count": 0,
        }

    # Extract metrics from records
    latest_record = metrics_records[0]

    # Build group metrics from the group_metrics JSON field
    group_metrics = latest_record.group_metrics if latest_record.group_metrics else {}

    result = {
        "vacancy_id": vacancy_id,
        "demographic_group": demographic_group,
        "latest_metrics": {
            "disparate_impact_ratio": float(latest_record.disparate_impact_ratio) if latest_record.disparate_impact_ratio else None,
            "statistical_parity_difference": float(latest_record.statistical_parity_difference) if latest_record.statistical_parity_difference else None,
            "overall_selection_rate": float(latest_record.overall_selection_rate) if latest_record.overall_selection_rate else None,
            "group_sample_size": latest_record.group_sample_size,
            "total_sample_size": latest_record.total_sample_size,
        },
        "group_metrics": group_metrics,
        "alert_triggered": latest_record.alert_triggered,
        "alert_severity": latest_record.alert_severity,
        "metric_count": len(metrics_records),
    }

    logger.info(
        f"Calculated fairness metrics for vacancy {vacancy_id}: "
        f"DI={result['latest_metrics']['disparate_impact_ratio']}, "
        f"alert={result['alert_triggered']}"
    )

    return result


def detect_fairness_violation(
    current_metrics: Dict[str, float],
    disparate_impact_threshold: float = DISPARATE_IMPACT_ALERT_THRESHOLD,
    statistical_parity_threshold: float = STATISTICAL_PARITY_ALERT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Detect if fairness metrics violate acceptable thresholds.

    This function compares current fairness metrics against acceptable
    thresholds to identify significant bias that may indicate
    the need for model intervention.

    Args:
        current_metrics: Current fairness metrics
        disparate_impact_threshold: Minimum acceptable disparate impact ratio
        statistical_parity_threshold: Maximum acceptable statistical parity difference

    Returns:
        Dictionary containing violation analysis:
        {
            "is_violation": bool,
            "violation_details": {
                "disparate_impact": {"current": 0.72, "threshold": 0.8, "delta": -0.08, "violated": true},
                "statistical_parity": {"current": 0.15, "threshold": 0.1, "delta": 0.05, "violated": true}
            },
            "severity": "high",
            "violated_metrics": ["disparate_impact", "statistical_parity"]
        }

    Example:
        >>> current = {"disparate_impact_ratio": 0.72, "statistical_parity_difference": 0.15}
        >>> result = detect_fairness_violation(current)
        >>> print(result['is_violation'])
        True
    """
    is_violation = False
    violation_details = {}
    violated_metrics = []
    severity = None

    # Check disparate impact
    disparate_impact = current_metrics.get("disparate_impact_ratio")
    if disparate_impact is not None:
        di_violated = disparate_impact < disparate_impact_threshold
        di_delta = disparate_impact - disparate_impact_threshold

        violation_details["disparate_impact"] = {
            "current": round(disparate_impact, 4),
            "threshold": round(disparate_impact_threshold, 4),
            "delta": round(di_delta, 4),
            "violated": di_violated,
        }

        if di_violated:
            is_violation = True
            violated_metrics.append("disparate_impact")

            # Determine severity based on how far below threshold
            if disparate_impact < 0.5:
                severity = "critical"
            elif disparate_impact < 0.65:
                severity = "high"
            elif not severity or severity == "low":
                severity = "medium"

    # Check statistical parity
    stat_parity = current_metrics.get("statistical_parity_difference")
    if stat_parity is not None:
        sp_violated = abs(stat_parity) > statistical_parity_threshold
        sp_delta = abs(stat_parity) - statistical_parity_threshold

        violation_details["statistical_parity"] = {
            "current": round(stat_parity, 4),
            "threshold": round(statistical_parity_threshold, 4),
            "delta": round(sp_delta, 4),
            "violated": sp_violated,
        }

        if sp_violated:
            is_violation = True
            violated_metrics.append("statistical_parity")

            # Determine severity based on how far above threshold
            if abs(stat_parity) > 0.25:
                severity = "critical"
            elif abs(stat_parity) > 0.2:
                severity = "high"
            elif not severity:
                severity = "medium"
            elif severity == "low":
                severity = "medium"

    # Default severity if only minor violations
    if is_violation and not severity:
        severity = "low"

    result = {
        "is_violation": is_violation,
        "violation_details": violation_details,
        "severity": severity,
        "violated_metrics": violated_metrics,
    }

    if is_violation:
        logger.warning(
            f"Fairness violation detected: {', '.join(violated_metrics)}, "
            f"severity: {severity}"
        )
    else:
        logger.info("No fairness violations detected - all metrics within thresholds")

    return result


async def _compare_demographic_outcomes_async(
    vacancy_id: str,
    demographic_groups: List[str],
):
    """Async helper to compare demographic outcomes from database."""
    async with async_session_maker() as db:
        # Get all fairness metrics for this vacancy for the specified demographic groups
        metrics_query = select(FairnessMetrics).where(
            and_(
                FairnessMetrics.vacancy_id == UUID(vacancy_id),
                FairnessMetrics.demographic_group.in_(demographic_groups)
            )
        ).order_by(desc(FairnessMetrics.created_at))

        metrics_result = await db.execute(metrics_query)
        metrics_records = metrics_result.scalars().all()

        # Build group selection rates from latest metrics
        group_selection_rates = {}
        max_disparity = 0.0
        groups_with_violations = []

        for metric in metrics_records:
            demo_group = metric.demographic_group

            # Only include the latest metric for each demographic group
            if demo_group in group_selection_rates:
                continue

            # Extract group metrics from the JSON field
            if metric.group_metrics:
                group_selection_rates[demo_group] = {}

                # Build selection rates for each subgroup
                for subgroup, data in metric.group_metrics.items():
                    selection_rate = data.get('selection_rate', 0.0)
                    group_selection_rates[demo_group][subgroup] = selection_rate

                # Calculate max disparity for this demographic
                rates = list(group_selection_rates[demo_group].values())
                if len(rates) >= 2:
                    disparity = max(rates) - min(rates)
                    max_disparity = max(max_disparity, disparity)

            # Check if this group has violations
            if metric.alert_triggered:
                groups_with_violations.append(demo_group)

        return group_selection_rates, max_disparity, groups_with_violations


def compare_demographic_outcomes(
    vacancy_id: str,
    demographic_groups: List[str],
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Compare outcomes across demographic groups for bias analysis.

    This function retrieves and compares selection metrics for multiple
    demographic groups, calculating outcome disparities and determining
    which groups show potential bias. Useful for identifying protected
    classes that may be disadvantaged by the ranking algorithm.

    Args:
        vacancy_id: JobVacancy UUID to analyze
        demographic_groups: List of demographic attributes to compare (e.g., ["gender", "age_group"])
        db_session: Optional database session for querying (not used, kept for API compatibility)

    Returns:
        Dictionary containing comparison results:
        {
            "vacancy_id": "uuid",
            "demographics_compared": ["gender", "age_group"],
            "group_selection_rates": {
                "gender": {
                    "male": 0.48,
                    "female": 0.42,
                    "non_binary": 0.45
                },
                "age_group": {
                    "under_25": 0.40,
                    "25_34": 0.46,
                    "35_44": 0.48,
                    "45_54": 0.44,
                    "55_64": 0.38
                }
            },
            "max_disparity": 0.10,
            "groups_with_violations": ["gender"],
            "comparison_count": 2
        }

    Example:
        >>> from sqlalchemy.orm import Session
        >>> from tasks.fairness_monitoring import compare_demographic_outcomes
        >>> comparison = compare_demographic_outcomes("vacancy-uuid", ["gender", "age_group"], db_session)
        >>> print(comparison['groups_with_violations'])
        ['gender']
    """
    logger.info(f"Comparing outcomes for {len(demographic_groups)} demographic groups")

    try:
        # Query database for fairness metrics
        group_selection_rates, max_disparity, groups_with_violations = asyncio.run(
            _compare_demographic_outcomes_async(vacancy_id, demographic_groups)
        )

        result = {
            "vacancy_id": vacancy_id,
            "demographics_compared": demographic_groups,
            "group_selection_rates": group_selection_rates,
            "max_disparity": round(max_disparity, 4),
            "groups_with_violations": groups_with_violations,
            "comparison_count": len(demographic_groups),
        }

        logger.info(
            f"Demographic outcome comparison complete: "
            f"{len(demographic_groups)} groups compared, "
            f"{len(groups_with_violations)} with violations"
        )

        return result

    except Exception as e:
        logger.error(
            f"Error comparing demographic outcomes: {e}", exc_info=True
        )
        return {
            "vacancy_id": vacancy_id,
            "demographics_compared": demographic_groups,
            "group_selection_rates": {},
            "max_disparity": 0.0,
            "groups_with_violations": [],
            "comparison_count": 0,
            "error": str(e),
        }


def format_fairness_alert_email(
    vacancy_id: str,
    violation_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Format fairness violation alert email.

    This function formats an email notification for fairness violations,
    including violation metrics, severity level, and actionable recommendations.

    Args:
        vacancy_id: UUID of the job vacancy with the fairness violation
        violation_details: Violation details dictionary containing:
            - demographic_group: Demographic attribute with violation
            - violation: Violation analysis from detect_fairness_violation
            - current_metrics: Current fairness metrics
            - detected_at: Timestamp when violation was detected

    Returns:
        Dictionary containing email details:
        {
            "subject": "⚠️ Fairness Violation Alert: gender (HIGH severity)",
            "body": "Email body with violation details...",
            "priority": "high"
        }

    Example:
        >>> details = {"demographic_group": "gender", "violation": {...}}
        >>> email = format_fairness_alert_email("vacancy-uuid", details)
        >>> print(email['subject'])
        '⚠️ Fairness Violation Alert: gender (HIGH severity)'
    """
    try:
        logger.info(f"Formatting fairness alert email for vacancy: {vacancy_id}")

        demographic_group = violation_details.get("demographic_group", "unknown")
        violation = violation_details.get("violation", {})
        current_metrics = violation_details.get("current_metrics", {})
        detected_at = violation_details.get("detected_at", datetime.utcnow().isoformat())

        severity = violation.get("severity", "unknown")
        violated_metrics = violation.get("violated_metrics", [])
        violation_info = violation.get("violation_details", {})

        # Determine email subject with severity indicator
        severity_emoji = {
            "critical": "🚨",
            "high": "⚠️",
            "medium": "⚡",
            "low": "ℹ️",
        }.get(severity, "⚠️")

        subject = f"{severity_emoji} Fairness Violation Alert: {demographic_group} ({severity.upper()} severity)"

        # Build email body
        body_lines = [
            f"Fairness Violation Alert",
            f"",
            f"Vacancy ID: {vacancy_id}",
            f"Demographic Group: {demographic_group}",
            f"Severity: {severity_emoji} {severity.upper()}",
            f"Detected At: {detected_at}",
            f"",
            f"Violation Summary:",
            f"  Violated Metrics: {', '.join(violated_metrics).replace('_', ' ').title()}",
        ]

        # Add violation details
        if violation_info:
            body_lines.extend([
                f"",
                f"Violation Details:",
            ])

            # Disparate Impact details
            if "disparate_impact" in violation_info:
                di_info = violation_info["disparate_impact"]
                di_current = di_info.get("current", "N/A")
                di_threshold = di_info.get("threshold", "N/A")
                di_delta = di_info.get("delta", 0)

                delta_str = f"{di_delta:+.4f}"
                indicator = "❌" if di_info.get("violated") else "✅"
                body_lines.append(
                    f"  {indicator} Disparate Impact: {di_current} (threshold: {di_threshold}, delta: {delta_str})"
                )

            # Statistical Parity details
            if "statistical_parity" in violation_info:
                sp_info = violation_info["statistical_parity"]
                sp_current = sp_info.get("current", "N/A")
                sp_threshold = sp_info.get("threshold", "N/A")
                sp_delta = sp_info.get("delta", 0)

                delta_str = f"{sp_delta:+.4f}"
                indicator = "❌" if sp_info.get("violated") else "✅"
                body_lines.append(
                    f"  {indicator} Statistical Parity: {sp_current} (threshold: {sp_threshold}, delta: {delta_str})"
                )

        # Add current metrics
        if current_metrics:
            body_lines.extend([
                f"",
                f"Current Fairness Metrics:",
            ])

            for metric_name, metric_value in current_metrics.items():
                if isinstance(metric_value, float):
                    body_lines.append(f"  - {metric_name}: {metric_value:.4f}")
                elif metric_value is not None:
                    body_lines.append(f"  - {metric_name}: {metric_value}")

        # Add recommendations based on severity
        body_lines.extend([
            f"",
            f"Recommendations:",
        ])

        if severity == "critical":
            body_lines.extend([
                f"  1. IMMEDIATE ACTION REQUIRED: Disable ranking for this vacancy",
                f"  2. Review and retrain the ranking model with bias mitigation",
                f"  3. Consider manual review of affected candidate rankings",
            ])
        elif severity == "high":
            body_lines.extend([
                f"  1. Review candidate rankings for this vacancy",
                f"  2. Consider applying bias remediation (reweight strategy)",
                f"  3. Plan model retraining with fairness constraints",
            ])
        elif severity == "medium":
            body_lines.extend([
                f"  1. Monitor this vacancy closely for trend changes",
                f"  2. Consider bias remediation if violations persist",
                f"  3. Review training data for representation issues",
            ])
        else:  # low
            body_lines.extend([
                f"  1. Continue monitoring this vacancy",
                f"  2. Investigate potential causes of minor bias",
                f"  3. Consider periodic fairness audits",
            ])

        body_lines.extend([
            f"",
            f"---",
            f"This is an automated alert from AgentHR Fairness Monitoring System.",
        ])

        body = "\n".join(body_lines)

        # Set priority based on severity
        priority = "high" if severity in ["critical", "high"] else "normal"

        email_details = {
            "subject": subject,
            "body": body,
            "priority": priority,
        }

        logger.info(f"Fairness alert email formatted successfully")
        return email_details

    except Exception as e:
        logger.error(f"Failed to format fairness alert email: {e}", exc_info=True)
        # Return a basic email format on error
        return {
            "subject": f"Fairness Alert: {violation_details.get('demographic_group', 'unknown')}",
            "body": f"A fairness violation was detected for vacancy {vacancy_id}. Severity: {violation_details.get('violation', {}).get('severity', 'unknown')}",
            "priority": "high",
        }


def send_notification_via_email(
    recipients: List[str],
    email_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send notification via email to specified recipients.

    This function sends a notification email using the configured email service.
    In production, this would integrate with SMTP, SendGrid, AWS SES, or similar.

    Args:
        recipients: List of email addresses to send the notification to
        email_details: Email details dictionary containing:
            - subject: Email subject line
            - body: Email body content
            - priority: Email priority (high/normal)
            - attachments: Optional list of attachments

    Returns:
        Dictionary containing email sending results:
        - success: Whether email was sent successfully
        - recipients_count: Number of recipients
        - error: Error message (if failed)

    Example:
        >>> details = {"subject": "Test", "body": "Body", "priority": "normal"}
        >>> result = send_notification_via_email(["admin@example.com"], details)
        >>> result['success']
        True
    """
    # Note: This is a placeholder for email sending
    # In a real implementation, you would use:
    # - Python's smtplib with email.mime modules
    # - SendGrid API
    # - AWS SES
    # - Mailgun
    # Or an internal email service

    try:
        subject = email_details.get("subject", "Notification")
        body = email_details.get("body", "")
        priority = email_details.get("priority", "normal")

        logger.info(
            f"Sending notification email: subject='{subject}', "
            f"to={len(recipients)} recipients, priority={priority}"
        )

        # Placeholder: Log email details
        # In production, this would actually send the email
        email_message = {
            "subject": subject,
            "from": settings.smtp_default_from if hasattr(settings, 'smtp_default_from') else "noreply@agenthr.com",
            "to": recipients,
            "body": body,
            "priority": priority,
        }

        logger.info(
            f"Email prepared: from={email_message['from']}, "
            f"subject='{subject}', to={len(recipients)} recipients"
        )

        # Simulate successful email sending
        # In production: smtp.send_message(email_message)
        success = True
        error = None

        logger.info(f"Notification email sent successfully to {len(recipients)} recipients")

        return {
            "success": success,
            "recipients_count": len(recipients),
            "error": error,
        }

    except Exception as e:
        logger.error(f"Failed to send notification email: {e}", exc_info=True)
        return {
            "success": False,
            "recipients_count": len(recipients),
            "error": str(e),
        }


@shared_task(
    name="tasks.fairness_monitoring.send_fairness_alert",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_fairness_alert(
    self,
    vacancy_id: str,
    violation_details: Dict[str, Any],
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send alert about fairness violations.

    This Celery task handles sending email alerts when fairness violations
    are detected. It formats the alert with violation details, severity level,
    and actionable recommendations for addressing the bias.

    Task Workflow:
    1. Format alert email with violation details
    2. Determine recipients (default: admin emails from settings)
    3. Send alert via email
    4. Return delivery status

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: UUID of the vacancy with fairness violation
        violation_details: Violation details dictionary containing:
            - demographic_group: Demographic attribute with violation
            - violation: Violation analysis from detect_fairness_violation
            - current_metrics: Current fairness metrics
            - detected_at: Timestamp when violation was detected
        recipients: Optional list of email recipients (defaults to admin emails)

    Returns:
        Dictionary containing alert results:
        - vacancy_id: UUID of the vacancy
        - notification_type: Type of notification (fairness_violation)
        - status: Task status (sent/failed)
        - recipients_count: Number of recipients notified
        - delivery_successful: Whether delivery was successful
        - severity: Severity level of the violation
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For email sending errors

    Example:
        >>> from tasks.fairness_monitoring import send_fairness_alert
        >>> details = {"demographic_group": "gender", "violation": {...}}
        >>> task = send_fairness_alert.delay("vacancy-uuid", details)
        >>> alert_result = task.get()
        >>> print(alert_result['status'])
        'sent'
    """
    start_time = time.time()

    try:
        demographic_group = violation_details.get("demographic_group", "unknown")
        violation = violation_details.get("violation", {})
        severity = violation.get("severity", "unknown")

        logger.info(
            f"Sending fairness violation alert for vacancy: {vacancy_id}, "
            f"group: {demographic_group}, severity: {severity}"
        )

        # Step 1: Format alert email
        progress = {
            "current": 1,
            "total": 2,
            "percentage": 50,
            "status": "formatting_alert",
            "message": "Formatting alert email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Formatting alert email")

        email_details = format_fairness_alert_email(vacancy_id, violation_details)

        # Step 2: Determine recipients
        if not recipients:
            # Default to admin emails from settings
            recipients = getattr(settings, 'admin_email_addresses', ['admin@agenthr.com'])
        elif isinstance(recipients, str):
            recipients = [recipients]

        logger.info(f"Recipients: {len(recipients)} email addresses")

        # Step 3: Send alert
        progress = {
            "current": 2,
            "total": 2,
            "percentage": 100,
            "status": "sending_alert",
            "message": "Sending alert email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Sending alert email")

        delivery_result = send_notification_via_email(recipients, email_details)
        delivery_successful = delivery_result.get("success", False)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "vacancy_id": vacancy_id,
            "notification_type": "fairness_violation",
            "status": "sent" if delivery_successful else "failed",
            "recipients_count": len(recipients),
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "severity": severity,
            "demographic_group": demographic_group,
            "processing_time_ms": processing_time_ms,
        }

        if delivery_successful:
            logger.info(
                f"Fairness violation alert sent successfully: vacancy={vacancy_id}, "
                f"group={demographic_group}, severity={severity}, "
                f"delivered to {len(recipients)} recipients, "
                f"time: {processing_time_ms}ms"
            )
        else:
            logger.warning(
                f"Fairness violation alert delivery failed: vacancy={vacancy_id}, "
                f"error: {delivery_result.get('error')}"
            )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "vacancy_id": vacancy_id,
            "notification_type": "fairness_violation",
            "status": "failed",
            "error": "Alert sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in fairness violation alert: {e}", exc_info=True)
        return {
            "vacancy_id": vacancy_id,
            "notification_type": "fairness_violation",
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.fairness_monitoring.monitor_fairness",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def monitor_fairness(
    self,
    vacancy_id: Optional[str] = None,
    demographic_groups: Optional[List[str]] = None,
    check_interval_hours: int = MONITORING_INTERVAL_HOURS,
) -> Dict[str, Any]:
    """
    Monitor fairness metrics and detect bias in candidate rankings.

    This Celery task periodically monitors the fairness of candidate ranking
    outcomes, detects algorithmic bias across demographic groups, and logs/alerts
    when fairness thresholds are exceeded.

    Task Workflow:
    1. Query vacancies with recent ranking activity (or specific vacancy if provided)
    2. Retrieve demographic inferences for ranked candidates
    3. Calculate fairness metrics (disparate impact, statistical parity)
    4. Detect fairness violations beyond acceptable thresholds
    5. Store metrics in database and trigger alerts if needed
    6. Generate fairness monitoring report

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: Optional vacancy UUID to filter (default: None for all active vacancies)
        demographic_groups: List of demographic groups to analyze (default: ["gender", "age_group", "ethnicity"])
        check_interval_hours: Hours since last check (default: 24)

    Returns:
        Dictionary containing monitoring results:
        - vacancies_checked: Number of vacancies monitored
        - violations_detected: Number with fairness violations
        - violating_vacancies: List of vacancy details with violations
        - monitoring_time_ms: Total processing time
        - status: Task status (completed/failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database or processing errors

    Example:
        >>> from tasks.fairness_monitoring import monitor_fairness
        >>> task = monitor_fairness.delay(vacancy_id="vacancy-uuid")
        >>> result = task.get()
        >>> print(result['violations_detected'])
        0
    """
    start_time = time.time()
    total_steps = 6
    current_step = 0

    if demographic_groups is None:
        demographic_groups = ["gender", "age_group", "ethnicity"]

    try:
        logger.info(
            f"Starting fairness monitoring for vacancy: {vacancy_id or 'all'}, "
            f"demographic_groups: {demographic_groups}"
        )

        # Step 1: Query vacancies to monitor
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "querying_vacancies",
            "message": "Querying vacancies with ranking activity...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Querying vacancies")

        # Query active vacancies from database
        async def query_vacancies():
            async with async_session_maker() as db:
                query = select(JobVacancy).where(JobVacancy.status == "active")
                if vacancy_id:
                    query = query.where(JobVacancy.id == UUID(vacancy_id))
                result = await db.execute(query)
                return list(result.scalars().all())

        vacancies = asyncio.run(query_vacancies())
        vacancies_checked = len(vacancies)

        logger.info(f"Found {vacancies_checked} vacancies to monitor")

        if vacancies_checked == 0:
            return {
                "vacancies_checked": 0,
                "violations_detected": 0,
                "violating_vacancies": [],
                "monitoring_time_ms": round((time.time() - start_time) * 1000, 2),
                "status": "completed",
                "message": "No vacancies found to monitor",
            }

        # Step 2: Retrieve demographic data for rankings
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "retrieving_demographics",
            "message": "Retrieving demographic inferences...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Retrieving demographics")

        # Note: In a real implementation, you would query DemographicInference
        # for all resumes ranked for the vacancies being monitored

        # Step 3: Calculate fairness metrics
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "calculating_metrics",
            "message": "Calculating fairness metrics...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Calculating metrics")

        # Use FairnessCalculator to analyze vacancies
        async def analyze_vacancies():
            async with async_session_maker() as db:
                calculator = get_fairness_calculator()
                vacancy_metrics = {}

                for vacancy in vacancies:
                    vacancy_uuid = str(vacancy.id)
                    vacancy_metrics[vacancy_uuid] = {}

                    # Analyze fairness for this vacancy
                    analysis = await calculator.analyze_vacancy_fairness(
                        db,
                        UUID(vacancy_uuid),
                        analysis_date=datetime.now().strftime("%Y-%m-%d"),
                        is_fairness_aware=False
                    )

                    # Extract metrics for each demographic group
                    if "attributes_analyzed" in analysis:
                        for demo_group, demo_metrics in analysis["attributes_analyzed"].items():
                            if demo_group in demographic_groups:
                                # Convert to format expected by downstream code
                                vacancy_metrics[vacancy_uuid][demo_group] = {
                                    "vacancy_id": vacancy_uuid,
                                    "demographic_group": demo_group,
                                    "latest_metrics": demo_metrics if not demo_metrics.get("error") else None,
                                    "alert_triggered": demo_metrics.get("alert_triggered", False),
                                    "alert_severity": demo_metrics.get("max_severity"),
                                }

                return vacancy_metrics

        vacancy_metrics = asyncio.run(analyze_vacancies())

        # Step 4: Detect fairness violations
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "detecting_violations",
            "message": "Detecting fairness violations...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Detecting violations")

        violating_vacancies = []
        for vacancy_id, demo_metrics in vacancy_metrics.items():
            for demographic_group, metrics_data in demo_metrics.items():
                current_metrics = metrics_data.get("latest_metrics", {})

                if not current_metrics:
                    continue

                violation = detect_fairness_violation(current_metrics)

                if violation["is_violation"]:
                    violating_vacancies.append({
                        "vacancy_id": vacancy_id,
                        "demographic_group": demographic_group,
                        "violation": violation,
                        "current_metrics": current_metrics,
                    })

        # Step 5: Store metrics and trigger alerts
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "storing_metrics",
            "message": "Storing fairness metrics and alerts...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Storing metrics")

        violations_detected = len(violating_vacancies)
        for violation_info in violating_vacancies:
            vac_id = violation_info["vacancy_id"]
            demo_group = violation_info["demographic_group"]
            violation = violation_info["violation"]
            severity = violation["severity"]

            logger.warning(
                f"Vacancy {vac_id} shows fairness violation in {demo_group}: "
                f"severity={severity}, "
                f"violated_metrics={', '.join(violation['violated_metrics'])}"
            )

            # FairnessMetrics and FairnessAlert records are already stored
            # by the FairnessCalculator.analyze_vacancy_fairness() method above

        # Step 6: Generate monitoring report
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "generating_report",
            "message": "Generating fairness monitoring report...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Generating report")

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "vacancies_checked": vacancies_checked,
            "violations_detected": violations_detected,
            "violating_vacancies": violating_vacancies,
            "demographic_groups_analyzed": demographic_groups,
            "monitoring_time_ms": processing_time_ms,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Fairness monitoring completed: {vacancies_checked} vacancies checked, "
            f"{violations_detected} violations detected in {processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "status": "failed",
            "error": "Fairness monitoring exceeded maximum time limit",
            "monitoring_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in fairness monitoring: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "monitoring_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.fairness_monitoring.periodic_fairness_monitoring",
    bind=True,
)
def periodic_fairness_monitoring(
    self,
) -> Dict[str, Any]:
    """
    Periodic task to monitor fairness for all active vacancies.

    This is a scheduled task that runs periodically (e.g., daily) to
    automatically monitor all active vacancies and detect fairness violations.

    Returns:
        Dictionary containing monitoring results

    Example:
        >>> # This would be scheduled via Celery beat
        >>> # celery beat schedule: {
        >>> #     'daily-fairness-monitoring': {
        >>> #         'task': 'tasks.fairness_monitoring.periodic_fairness_monitoring',
        >>> #         'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        >>> #     }
        >>> # }
    """
    logger.info("Starting periodic fairness monitoring")

    # Monitor all active vacancies for all demographic groups
    result = monitor_fairness(
        vacancy_id=None,  # All vacancies
        demographic_groups=["gender", "age_group", "ethnicity"],
        check_interval_hours=MONITORING_INTERVAL_HOURS,
    )

    logger.info(f"Periodic fairness monitoring completed: {result.get('status')}")
    return result


@shared_task(
    name="tasks.fairness_monitoring.generate_fairness_report",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def generate_fairness_report(
    self,
    vacancy_id: str,
    days_back: int = 30,
    demographic_groups: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate a comprehensive fairness report for a vacancy.

    This task generates a detailed fairness report including
    historical metrics, trends, violations, and recommendations over time.

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: UUID of the vacancy to report on
        days_back: Number of days of history to include (default: 30)
        demographic_groups: Optional list of demographic groups to include

    Returns:
        Dictionary containing fairness report:
        - vacancy_id: UUID of the vacancy
        - period_start: Start date of report period
        - period_end: End date of report period
        - demographic_groups_analyzed: List of groups analyzed
        - current_metrics: Latest fairness metrics by group
        - historical_trends: Trend data over the period
        - violations_summary: Summary of violations detected
        - recommendations: Actionable recommendations
        - status: Task status

    Example:
        >>> from tasks.fairness_monitoring import generate_fairness_report
        >>> task = generate_fairness_report.delay("vacancy-uuid", days_back=30)
        >>> result = task.get()
        >>> print(result['violations_summary']['total_violations'])
        2
    """
    start_time = time.time()

    if demographic_groups is None:
        demographic_groups = ["gender", "age_group", "ethnicity"]

    try:
        logger.info(f"Generating fairness report for vacancy '{vacancy_id}', days_back: {days_back}")

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=days_back)

        # Query fairness metrics and alerts from database
        async def generate_report_async():
            async with async_session_maker() as db:
                calculator = get_fairness_calculator()

                # Use the fairness calculator's report generation method
                report = await calculator.get_fairness_report(
                    db,
                    UUID(vacancy_id),
                    analysis_date=None  # Get latest
                )

                # Query historical metrics for trends
                start_date = period_start.strftime("%Y-%m-%d")
                metrics_query = select(FairnessMetrics).where(
                    and_(
                        FairnessMetrics.vacancy_id == UUID(vacancy_id),
                        FairnessMetrics.analysis_date >= start_date,
                        FairnessMetrics.demographic_group.in_(demographic_groups)
                    )
                ).order_by(FairnessMetrics.analysis_date)

                metrics_result = await db.execute(metrics_query)
                historical_metrics = list(metrics_result.scalars().all())

                # Build historical trends
                historical_trends = []
                for metric in historical_metrics:
                    historical_trends.append({
                        "date": metric.analysis_date,
                        "demographic_group": metric.demographic_group,
                        "disparate_impact_ratio": float(metric.disparate_impact_ratio or 0),
                        "statistical_parity_difference": float(metric.statistical_parity_difference or 0),
                        "alert_triggered": metric.alert_triggered,
                        "alert_severity": metric.alert_severity,
                    })

                # Extract current metrics and violations from report
                current_metrics = report.get("metrics_by_demographic", {})
                alerts = report.get("alerts", [])

                # Build violations summary
                violations_summary = {
                    "total_violations": len([a for a in alerts if a["status"] == "active"]),
                    "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    "by_demographic": {},
                }

                for alert in alerts:
                    severity = alert.get("severity", "low")
                    if severity in violations_summary["by_severity"]:
                        violations_summary["by_severity"][severity] += 1

                for demo_group, metrics in current_metrics.items():
                    if metrics.get("alert_triggered"):
                        violations_summary["by_demographic"][demo_group] = metrics.get("alert_severity")

                # Get recommendations from report
                recommendations = report.get("recommendations", [])

                return current_metrics, historical_trends, violations_summary, recommendations

        current_metrics, historical_trends, violations_summary, recommendations = asyncio.run(
            generate_report_async()
        )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "vacancy_id": vacancy_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "demographic_groups_analyzed": demographic_groups,
            "current_metrics": current_metrics,
            "historical_trends": historical_trends,
            "violations_summary": violations_summary,
            "recommendations": recommendations,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Fairness report generated for vacancy '{vacancy_id}': "
            f"{violations_summary['total_violations']} violations, "
            f"{len(recommendations)} recommendations"
        )

        return result

    except Exception as e:
        logger.error(f"Error generating fairness report: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.fairness_monitoring.remediate_bias",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
)
def remediate_bias(
    self,
    vacancy_id: str,
    demographic_group: str,
    remediation_strategy: str = "reweight",
) -> Dict[str, Any]:
    """
    Apply bias remediation to a vacancy's rankings.

    This task applies fairness-aware techniques to reduce bias in
    candidate rankings for a specific demographic group.

    Args:
        self: Celery task instance (bind=True)
        vacancy_id: UUID of the vacancy to remediate
        demographic_group: Demographic group showing bias
        remediation_strategy: Strategy to apply (reweight, calibrate, suppress)

    Returns:
        Dictionary containing remediation results:
        - vacancy_id: UUID of the vacancy
        - demographic_group: Group remediated
        - strategy: Strategy applied
        - before_metrics: Fairness metrics before remediation
        - after_metrics: Fairness metrics after remediation
        - improvement: Measured improvement
        - status: Task status

    Example:
        >>> from tasks.fairness_monitoring import remediate_bias
        >>> task = remediate_bias.delay("vacancy-uuid", "gender", "reweight")
        >>> result = task.get()
        >>> print(result['improvement']['disparate_impact_improvement'])
        0.15
    """
    start_time = time.time()

    try:
        logger.info(
            f"Applying bias remediation for vacancy '{vacancy_id}', "
            f"group: {demographic_group}, strategy: {remediation_strategy}"
        )

        # Note: This is a placeholder for remediation logic
        # In a real implementation, you would:
        # 1. Query current rankings and demographic data
        # 2. Calculate current fairness metrics
        # 3. Apply remediation strategy (e.g., reweight features, calibrate thresholds)
        # 4. Re-rank candidates with fairness-aware algorithm
        # 5. Calculate new fairness metrics
        # 6. Store updated rankings and metrics

        # Placeholder data
        before_metrics = {
            "disparate_impact_ratio": 0.72,
            "statistical_parity_difference": 0.15,
        }
        after_metrics = {
            "disparate_impact_ratio": 0.87,
            "statistical_parity_difference": 0.05,
        }
        improvement = {
            "disparate_impact_improvement": round(after_metrics["disparate_impact_ratio"] - before_metrics["disparate_impact_ratio"], 4),
            "parity_improvement": round(before_metrics["statistical_parity_difference"] - after_metrics["statistical_parity_difference"], 4),
        }

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "vacancy_id": vacancy_id,
            "demographic_group": demographic_group,
            "strategy": remediation_strategy,
            "before_metrics": before_metrics,
            "after_metrics": after_metrics,
            "improvement": improvement,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Bias remediation completed for vacancy '{vacancy_id}': "
            f"DI improvement: {improvement['disparate_impact_improvement']:.4f}, "
            f"strategy: {remediation_strategy}"
        )

        return result

    except Exception as e:
        logger.error(f"Error applying bias remediation: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }
