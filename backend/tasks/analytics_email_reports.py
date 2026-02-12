"""
Analytics email reports tasks for scheduled analytics report delivery.

This module provides Celery tasks for generating and sending analytics
reports via email on a scheduled basis (daily, weekly). Reports include
key metrics aggregations, quality metrics, and dashboard summaries.

Report Types:
- Daily Summary: Key metrics from the last 24 hours
- Weekly Summary: Comprehensive metrics from the last 7 days

Features:
- Configurable recipient lists via settings or task arguments
- Graceful handling of missing email configuration
- Integration with analytics precomputation for data retrieval
- Support for HTML and plain text email formats
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_analytics_report_config() -> Dict[str, Any]:
    """
    Get analytics email report configuration from settings.

    Returns configuration with defaults for:
    - enabled: Whether analytics email reports are enabled (default: True)
    - daily_hour: Hour for daily reports (default: 8 AM)
    - daily_minute: Minute for daily reports (default: 0)
    - weekly_day: Day of week for weekly reports (default: 1 = Monday)
    - weekly_hour: Hour for weekly reports (default: 9 AM)
    - weekly_minute: Minute for weekly reports (default: 0)
    - default_recipients: List of default email recipients

    Returns:
        Dictionary containing report configuration

    Example:
        >>> config = get_analytics_report_config()
        >>> print(config['daily_hour'])
        8
    """
    return {
        "enabled": getattr(settings, "analytics_email_reports_enabled", True),
        "daily_hour": getattr(settings, "analytics_report_daily_hour", 8),
        "daily_minute": getattr(settings, "analytics_report_daily_minute", 0),
        "weekly_day": getattr(settings, "analytics_report_weekly_day", 1),  # Monday
        "weekly_hour": getattr(settings, "analytics_report_weekly_hour", 9),
        "weekly_minute": getattr(settings, "analytics_report_weekly_minute", 0),
        "default_recipients": getattr(
            settings, "analytics_report_default_recipients", []
        ),
    }


def retrieve_cached_analytics(aggregation_type: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached analytics aggregation from Redis.

    This function retrieves pre-computed analytics data from the Redis cache
    that was stored by the analytics precomputation tasks.

    Args:
        aggregation_type: Type of aggregation (key_metrics, quality_metrics, etc.)

    Returns:
        Cached aggregation data, or None if not found

    Example:
        >>> metrics = retrieve_cached_analytics("key_metrics")
        >>> metrics is not None
        True
    """
    try:
        import redis
        import json

        # Connect to Redis
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_cache_max_connections,
        )

        # Generate cache key
        cache_key = f"{settings.redis_cache_key_prefix}:analytics:{aggregation_type}"

        # Retrieve data
        cached_data = redis_client.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            logger.info(f"Retrieved {aggregation_type} from cache")
            return data
        else:
            logger.info(f"No cached data found for {aggregation_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to retrieve cached analytics: {e}", exc_info=True)
        return None


def format_daily_report_email(
    report_data: Dict[str, Any],
    recipients: List[str],
) -> Dict[str, Any]:
    """
    Format daily analytics report email.

    This function formats the daily analytics report email with key metrics,
    summary statistics, and insights from the last 24 hours.

    Args:
        report_data: Analytics data containing key_metrics, quality_metrics, etc.
        recipients: List of email recipients

    Returns:
        Dictionary containing email details:
        {
            "subject": "Daily Analytics Report - Jan 15, 2024",
            "body": "Plain text email body...",
            "html_body": "<html>...</html>",
            "priority": "normal"
        }

    Example:
        >>> data = {"key_metrics": {"time_to_hire": {"average_days": 32.5}}}
        >>> email = format_daily_report_email(data, ["admin@example.com"])
        >>> "Daily Analytics Report" in email['subject']
        True
    """
    try:
        now = datetime.utcnow()
        date_str = now.strftime("%B %d, %Y")

        # Build subject
        subject = f"Daily Analytics Report - {date_str}"

        # Extract key metrics
        key_metrics = report_data.get("key_metrics", {})
        time_to_hire = key_metrics.get("time_to_hire", {})
        resumes = key_metrics.get("resumes", {})
        match_rates = key_metrics.get("match_rates", {})

        # Build plain text body
        body_lines = [
            f"AgentHR Daily Analytics Report",
            f"Generated: {date_str}",
            f"",
            f"=" * 50,
            f"",
            f"EXECUTIVE SUMMARY",
            f"-" * 40,
            f"",
        ]

        # Time to Hire section
        if time_to_hire:
            body_lines.extend([
                f"Time to Hire Metrics:",
                f"  Average: {time_to_hire.get('average_days', 'N/A')} days",
                f"  Median: {time_to_hire.get('median_days', 'N/A')} days",
                f"  Range: {time_to_hire.get('min_days', 'N/A')} - {time_to_hire.get('max_days', 'N/A')} days",
                f"",
            ])

        # Resume Processing section
        if resumes:
            body_lines.extend([
                f"Resume Processing:",
                f"  Total Processed: {resumes.get('total_processed', 0):,}",
                f"  This Month: {resumes.get('processed_this_month', 0):,}",
                f"  This Week: {resumes.get('processed_this_week', 0):,}",
                f"  Avg Rate: {resumes.get('processing_rate_avg', 0):.1f}/day",
                f"",
            ])

        # Match Rates section
        if match_rates:
            body_lines.extend([
                f"Match Performance:",
                f"  Overall Match Rate: {match_rates.get('overall_match_rate', 0):.1%}",
                f"  High Confidence: {match_rates.get('high_confidence_matches', 0):,}",
                f"  Avg Confidence: {match_rates.get('average_confidence', 0):.1%}",
                f"",
            ])

        # Footer
        body_lines.extend([
            f"=" * 50,
            f"",
            f"This is an automated daily report from AgentHR.",
            f"To unsubscribe or change your preferences, contact your administrator.",
        ])

        body = "\n".join(body_lines)

        # Build HTML body
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }",
            "    .container { max-width: 600px; margin: 0 auto; padding: 20px; }",
            "    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }",
            "    h2 { color: #34495e; margin-top: 20px; }",
            "    .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 15px 0; }",
            "    .metric-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }",
            "    .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }",
            "    .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }",
            "    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #7f8c8d; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <div class='container'>",
            f"    <h1>📊 Daily Analytics Report</h1>",
            f"    <p>Generated: {date_str}</p>",
        ]

        # Time to Hire section (HTML)
        if time_to_hire:
            html_lines.extend([
                "    <h2>⏱️ Time to Hire</h2>",
                "    <div class='metric-grid'>",
                f"      <div class='metric-card'><div class='metric-label'>Average</div><div class='metric-value'>{time_to_hire.get('average_days', 'N/A')} days</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Median</div><div class='metric-value'>{time_to_hire.get('median_days', 'N/A')} days</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Minimum</div><div class='metric-value'>{time_to_hire.get('min_days', 'N/A')} days</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Maximum</div><div class='metric-value'>{time_to_hire.get('max_days', 'N/A')} days</div></div>",
                "    </div>",
            ])

        # Resume Processing section (HTML)
        if resumes:
            html_lines.extend([
                "    <h2>📄 Resume Processing</h2>",
                "    <div class='metric-grid'>",
                f"      <div class='metric-card'><div class='metric-label'>Total Processed</div><div class='metric-value'>{resumes.get('total_processed', 0):,}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>This Month</div><div class='metric-value'>{resumes.get('processed_this_month', 0):,}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>This Week</div><div class='metric-value'>{resumes.get('processed_this_week', 0):,}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Avg Rate</div><div class='metric-value'>{resumes.get('processing_rate_avg', 0):.1f}/day</div></div>",
                "    </div>",
            ])

        # Match Rates section (HTML)
        if match_rates:
            html_lines.extend([
                "    <h2>🎯 Match Performance</h2>",
                "    <div class='metric-grid'>",
                f"      <div class='metric-card'><div class='metric-label'>Match Rate</div><div class='metric-value'>{match_rates.get('overall_match_rate', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>High Confidence</div><div class='metric-value'>{match_rates.get('high_confidence_matches', 0):,}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Avg Confidence</div><div class='metric-value'>{match_rates.get('average_confidence', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Low Confidence</div><div class='metric-value'>{match_rates.get('low_confidence_matches', 0):,}</div></div>",
                "    </div>",
            ])

        # Footer
        html_lines.extend([
            "    <div class='footer'>",
            "      <p>This is an automated daily report from AgentHR.</p>",
            "      <p>To unsubscribe or change your preferences, contact your administrator.</p>",
            "    </div>",
            "  </div>",
            "</body>",
            "</html>",
        ])

        html_body = "\n".join(html_lines)

        return {
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "priority": "normal",
        }

    except Exception as e:
        logger.error(f"Failed to format daily report email: {e}", exc_info=True)
        return {
            "subject": f"Daily Analytics Report - Error",
            "body": f"Error generating report: {str(e)}",
            "html_body": f"<p>Error generating report: {str(e)}</p>",
            "priority": "normal",
        }


def format_weekly_report_email(
    report_data: Dict[str, Any],
    recipients: List[str],
) -> Dict[str, Any]:
    """
    Format weekly analytics report email.

    This function formats a comprehensive weekly analytics report including
    key metrics, quality metrics, ranking accuracy, stage durations, and
    trend analysis from the last 7 days.

    Args:
        report_data: Analytics data containing key_metrics, quality_metrics,
                    ranking_accuracy, stage_duration, and predictive analytics
        recipients: List of email recipients

    Returns:
        Dictionary containing email details:
        {
            "subject": "Weekly Analytics Report - Week of Jan 8, 2024",
            "body": "Plain text email body...",
            "html_body": "<html>...</html>",
            "priority": "normal"
        }

    Example:
        >>> data = {"key_metrics": {...}, "quality_metrics": {...}}
        >>> email = format_weekly_report_email(data, ["admin@example.com"])
        >>> "Weekly Analytics Report" in email['subject']
        True
    """
    try:
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        date_str = f"Week of {week_start.strftime('%B %d, %Y')}"

        # Build subject
        subject = f"Weekly Analytics Report - {date_str}"

        # Extract metrics
        key_metrics = report_data.get("key_metrics", {})
        quality_metrics = report_data.get("quality_metrics", {})
        ranking_accuracy = report_data.get("ranking_accuracy", {})
        stage_duration = report_data.get("stage_duration", {})

        time_to_hire = key_metrics.get("time_to_hire", {})
        resumes = key_metrics.get("resumes", {})
        match_rates = key_metrics.get("match_rates", {})

        # Build plain text body
        body_lines = [
            f"AgentHR Weekly Analytics Report",
            f"{date_str}",
            f"",
            f"=" * 60,
            f"",
            f"EXECUTIVE SUMMARY",
            f"-" * 40,
            f"",
        ]

        # Key Metrics section
        if time_to_hire or resumes or match_rates:
            body_lines.append("KEY PERFORMANCE METRICS")
            body_lines.append("")

            if time_to_hire:
                body_lines.extend([
                    f"Time to Hire:",
                    f"  Average: {time_to_hire.get('average_days', 'N/A')} days",
                    f"  Median: {time_to_hire.get('median_days', 'N/A')} days",
                    f"  25th Percentile: {time_to_hire.get('percentile_25', 'N/A')} days",
                    f"  75th Percentile: {time_to_hire.get('percentile_75', 'N/A')} days",
                    f"",
                ])

            if resumes:
                body_lines.extend([
                    f"Resume Processing:",
                    f"  Total Processed: {resumes.get('total_processed', 0):,}",
                    f"  This Week: {resumes.get('processed_this_week', 0):,}",
                    f"  Daily Average: {resumes.get('processing_rate_avg', 0):.1f}",
                    f"",
                ])

            if match_rates:
                body_lines.extend([
                    f"Match Quality:",
                    f"  Overall Match Rate: {match_rates.get('overall_match_rate', 0):.1%}",
                    f"  High Confidence Matches: {match_rates.get('high_confidence_matches', 0):,}",
                    f"",
                ])

        # Quality Metrics section
        if quality_metrics:
            body_lines.extend([
                f"ML/NLP QUALITY METRICS",
                f"-" * 40,
                f"",
                f"  Text Extraction Success: {quality_metrics.get('text_extraction_success_rate', 0):.1%}",
                f"  NER Accuracy: {quality_metrics.get('ner_accuracy', 0):.1%}",
                f"  Avg Keywords/Resume: {quality_metrics.get('avg_keywords_per_resume', 0):.1f}",
                f"  Matching Precision: {quality_metrics.get('matching_precision', 0):.1%}",
                f"  Matching Recall: {quality_metrics.get('matching_recall', 0):.1%}",
                f"  Error Rate: {quality_metrics.get('error_rate', 0):.2%}",
                f"",
            ])

        # Ranking Accuracy section
        ranking_top_n = ranking_accuracy.get("top_n_performance", {})
        feedback_conv = ranking_accuracy.get("feedback_conversion", {})
        if ranking_top_n or feedback_conv:
            body_lines.extend([
                f"RANKING ACCURACY",
                f"-" * 40,
                f"",
            ])

            if ranking_top_n:
                body_lines.extend([
                    f"  Top-1 Success Rate: {ranking_top_n.get('top_1_success_rate', 0):.1%}",
                    f"  Top-3 Success Rate: {ranking_top_n.get('top_3_success_rate', 0):.1%}",
                    f"  Top-5 Success Rate: {ranking_top_n.get('top_5_success_rate', 0):.1%}",
                    f"  Top-10 Success Rate: {ranking_top_n.get('top_10_success_rate', 0):.1%}",
                    f"",
                ])

            if feedback_conv:
                body_lines.extend([
                    f"  Feedback Rate: {feedback_conv.get('feedback_rate', 0):.1%}",
                    f"  Positive Feedback: {feedback_conv.get('positive_feedback_rate', 0):.1%}",
                    f"",
                ])

        # Stage Duration section
        stages = stage_duration.get("stages", [])
        if stages:
            body_lines.extend([
                f"STAGE DURATION ANALYSIS",
                f"-" * 40,
                f"",
            ])
            for stage in stages[:5]:  # Top 5 stages
                body_lines.extend([
                    f"  {stage.get('stage_name', 'Unknown').title()}:",
                    f"    Average: {stage.get('average_days', 0):.1f} days",
                    f"    Candidates: {stage.get('candidate_count', 0):,}",
                    f"",
                ])

        # Footer
        body_lines.extend([
            f"=" * 60,
            f"",
            f"This is an automated weekly report from AgentHR.",
            f"To unsubscribe or change your preferences, contact your administrator.",
        ])

        body = "\n".join(body_lines)

        # Build HTML body (simplified for weekly)
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <style>",
            "    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }",
            "    .container { max-width: 700px; margin: 0 auto; padding: 20px; }",
            "    h1 { color: #2c3e50; border-bottom: 2px solid #27ae60; padding-bottom: 10px; }",
            "    h2 { color: #34495e; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; }",
            "    .metric-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 15px 0; }",
            "    .metric-card { background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 3px solid #27ae60; }",
            "    .metric-label { font-size: 11px; color: #7f8c8d; text-transform: uppercase; }",
            "    .metric-value { font-size: 20px; font-weight: bold; color: #2c3e50; }",
            "    .section { margin: 20px 0; }",
            "    .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #7f8c8d; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <div class='container'>",
            f"    <h1>📊 Weekly Analytics Report</h1>",
            f"    <p>{date_str}</p>",
        ]

        # Key Metrics (HTML)
        if resumes or time_to_hire or match_rates:
            html_lines.extend([
                "    <h2>📈 Key Performance Metrics</h2>",
                "    <div class='metric-grid'>",
            ])
            if resumes:
                html_lines.append(f"      <div class='metric-card'><div class='metric-label'>Resumes This Week</div><div class='metric-value'>{resumes.get('processed_this_week', 0):,}</div></div>")
            if time_to_hire:
                html_lines.append(f"      <div class='metric-card'><div class='metric-label'>Avg Time to Hire</div><div class='metric-value'>{time_to_hire.get('average_days', 'N/A')} days</div></div>")
            if match_rates:
                html_lines.append(f"      <div class='metric-card'><div class='metric-label'>Match Rate</div><div class='metric-value'>{match_rates.get('overall_match_rate', 0):.1%}</div></div>")
            html_lines.append("    </div>")

        # Quality Metrics (HTML)
        if quality_metrics:
            html_lines.extend([
                "    <h2>🤖 ML/NLP Quality Metrics</h2>",
                "    <div class='metric-grid'>",
                f"      <div class='metric-card'><div class='metric-label'>Extraction Success</div><div class='metric-value'>{quality_metrics.get('text_extraction_success_rate', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>NER Accuracy</div><div class='metric-value'>{quality_metrics.get('ner_accuracy', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Error Rate</div><div class='metric-value'>{quality_metrics.get('error_rate', 0):.2%}</div></div>",
                "    </div>",
            ])

        # Ranking (HTML)
        if ranking_top_n:
            html_lines.extend([
                "    <h2>🎯 Ranking Accuracy</h2>",
                "    <div class='metric-grid'>",
                f"      <div class='metric-card'><div class='metric-label'>Top-5 Success</div><div class='metric-value'>{ranking_top_n.get('top_5_success_rate', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Top-10 Success</div><div class='metric-value'>{ranking_top_n.get('top_10_success_rate', 0):.1%}</div></div>",
                f"      <div class='metric-card'><div class='metric-label'>Total Hires</div><div class='metric-value'>{ranking_top_n.get('total_hires', 0):,}</div></div>",
                "    </div>",
            ])

        # Footer
        html_lines.extend([
            "    <div class='footer'>",
            "      <p>This is an automated weekly report from AgentHR.</p>",
            "      <p>To unsubscribe or change your preferences, contact your administrator.</p>",
            "    </div>",
            "  </div>",
            "</body>",
            "</html>",
        ])

        html_body = "\n".join(html_lines)

        return {
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "priority": "normal",
        }

    except Exception as e:
        logger.error(f"Failed to format weekly report email: {e}", exc_info=True)
        return {
            "subject": f"Weekly Analytics Report - Error",
            "body": f"Error generating report: {str(e)}",
            "html_body": f"<p>Error generating report: {str(e)}</p>",
            "priority": "normal",
        }


def send_analytics_report_email(
    recipients: List[str],
    email_content: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send analytics report email to recipients.

    This function uses the email service to send the formatted analytics
    report email to the specified recipients.

    Args:
        recipients: List of email addresses to send the report to
        email_content: Dictionary containing subject, body, and html_body

    Returns:
        Dictionary containing send results:
        - success: Whether email was sent successfully
        - recipients_count: Number of recipients
        - sent_at: Timestamp when sent
        - error: Error message (if failed)

    Example:
        >>> content = {"subject": "Test", "body": "...", "html_body": "..."}
        >>> result = send_analytics_report_email(["admin@example.com"], content)
        >>> result['success']
        True
    """
    try:
        from services.email_service import get_email_service

        email_service = get_email_service()

        if not email_service.enabled:
            logger.warning("Email service is disabled, skipping analytics report email")
            return {
                "success": False,
                "recipients_count": len(recipients),
                "error": "Email service is disabled",
            }

        subject = email_content.get("subject", "Analytics Report")
        html_body = email_content.get("html_body", email_content.get("body", ""))

        # Send to each recipient
        success_count = 0
        for recipient in recipients:
            try:
                result = email_service.send_email(
                    to=recipient,
                    subject=subject,
                    body=html_body,
                    html=True,
                )
                if result:
                    success_count += 1
                    logger.info(f"Analytics report email sent to {recipient}")
                else:
                    logger.warning(f"Failed to send analytics report email to {recipient}")
            except Exception as e:
                logger.error(f"Error sending to {recipient}: {e}")

        return {
            "success": success_count > 0,
            "recipients_count": len(recipients),
            "successful_sends": success_count,
            "sent_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to send analytics report email: {e}", exc_info=True)
        return {
            "success": False,
            "recipients_count": len(recipients),
            "error": str(e),
        }


def gather_report_data(report_type: str) -> Dict[str, Any]:
    """
    Gather all analytics data for the report.

    This function retrieves cached analytics data from Redis for all
    relevant aggregation types.

    Args:
        report_type: Type of report (daily, weekly)

    Returns:
        Dictionary containing all analytics data

    Example:
        >>> data = gather_report_data("daily")
        >>> "key_metrics" in data
        True
    """
    report_data = {
        "key_metrics": retrieve_cached_analytics("key_metrics"),
        "quality_metrics": retrieve_cached_analytics("quality_metrics"),
        "ranking_accuracy": retrieve_cached_analytics("ranking_accuracy"),
        "stage_duration": retrieve_cached_analytics("stage_duration"),
        "report_type": report_type,
        "generated_at": datetime.utcnow().isoformat(),
    }

    # For weekly reports, also include predictive analytics
    if report_type == "weekly":
        report_data["predictive"] = retrieve_cached_analytics("predictive")

    return report_data


@shared_task(
    name="tasks.analytics_email_reports.send_analytics_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_analytics_report(
    self,
    report_type: str = "daily",
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send analytics report email.

    This Celery task handles the complete workflow of generating and sending
    an analytics report email:
    1. Gather cached analytics data
    2. Format email based on report type
    3. Send email to recipients

    Args:
        self: Celery task instance (bind=True)
        report_type: Type of report (daily, weekly)
        recipients: List of email recipients (defaults to configured recipients)

    Returns:
        Dictionary containing task results:
        - report_type: Type of report sent
        - status: Task status (completed/failed)
        - recipients_count: Number of recipients
        - email_sent: Whether email was sent successfully
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For data gathering or email sending errors

    Example:
        >>> from tasks.analytics_email_reports import send_analytics_report
        >>> task = send_analytics_report.delay("daily", ["admin@example.com"])
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 4
    current_step = 0

    try:
        logger.info(f"Starting {report_type} analytics report email task")

        # Validate report type
        if report_type not in ("daily", "weekly"):
            return {
                "report_type": report_type,
                "status": "failed",
                "error": f"Invalid report type: {report_type}. Must be 'daily' or 'weekly'.",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Get recipients
        config = get_analytics_report_config()
        if recipients is None:
            recipients = config.get("default_recipients", [])

        if not recipients:
            logger.warning(f"No recipients configured for {report_type} analytics report")
            return {
                "report_type": report_type,
                "status": "skipped",
                "reason": "No recipients configured",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Step 1: Gather analytics data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "gathering_data",
            "message": "Gathering analytics data...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Gathering data")

        report_data = gather_report_data(report_type)

        # Step 2: Format email
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "formatting_email",
            "message": "Formatting report email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Formatting email")

        if report_type == "daily":
            email_content = format_daily_report_email(report_data, recipients)
        else:
            email_content = format_weekly_report_email(report_data, recipients)

        # Step 3: Send email
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "sending_email",
            "message": "Sending report email...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Sending email")

        send_result = send_analytics_report_email(recipients, email_content)

        # Step 4: Finalize
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": 100,
            "status": "completed",
            "message": f"{report_type.capitalize()} report sent successfully",
        }
        self.update_state(state="PROGRESS", meta=progress)

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "report_type": report_type,
            "status": "completed" if send_result.get("success") else "partial",
            "recipients_count": len(recipients),
            "successful_sends": send_result.get("successful_sends", 0),
            "email_sent": send_result.get("success", False),
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"{report_type.capitalize()} analytics report email completed: "
            f"recipients={len(recipients)}, "
            f"sent={send_result.get('successful_sends', 0)}, "
            f"time={processing_time_ms}ms"
        )

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "report_type": report_type,
            "status": "failed",
            "error": "Report sending exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in analytics report email task: {e}", exc_info=True)
        return {
            "report_type": report_type,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.analytics_email_reports.send_daily_analytics_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_daily_analytics_report(
    self,
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send daily analytics report email.

    This is a convenience task that wraps send_analytics_report with
    report_type='daily'. It is designed to be scheduled by Celery Beat.

    Args:
        self: Celery task instance (bind=True)
        recipients: Optional list of email recipients

    Returns:
        Dictionary containing task results

    Example:
        >>> from tasks.analytics_email_reports import send_daily_analytics_report
        >>> task = send_daily_analytics_report.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    return send_analytics_report.apply_async(
        kwargs={"report_type": "daily", "recipients": recipients}
    ).get()


@shared_task(
    name="tasks.analytics_email_reports.send_weekly_analytics_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def send_weekly_analytics_report(
    self,
    recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Send weekly analytics report email.

    This is a convenience task that wraps send_analytics_report with
    report_type='weekly'. It is designed to be scheduled by Celery Beat.

    Args:
        self: Celery task instance (bind=True)
        recipients: Optional list of email recipients

    Returns:
        Dictionary containing task results

    Example:
        >>> from tasks.analytics_email_reports import send_weekly_analytics_report
        >>> task = send_weekly_analytics_report.delay()
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    return send_analytics_report.apply_async(
        kwargs={"report_type": "weekly", "recipients": recipients}
    ).get()
