"""
Report generation tasks for scheduled analytics reports.

This module provides Celery tasks for generating scheduled reports,
formatting them for delivery (PDF, CSV, etc.), and sending them via
email or other delivery channels.
"""
import asyncio
import logging
import time
import smtplib
from email.message import EmailMessage
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from io import BytesIO

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import async_session_maker
from models import Report, ScheduledReport
from models.audit_log import AuditLog, AuditActionType

logger = logging.getLogger(__name__)
settings = get_settings()


def get_report_data(
    report_config: Dict[str, Any],
    date_range: Dict[str, datetime],
) -> Dict[str, Any]:
    """
    Generate report data based on configuration.

    This function queries analytics data based on the report configuration,
    including filters, dimensions, and metrics specified in the report config.

    Args:
        report_config: Report configuration dictionary containing:
            - filters: Data filters (date range, job, recruiter, etc.)
            - dimensions: Grouping dimensions (day, week, source, etc.)
            - metrics: Metrics to calculate (time_to_hire, resumes_processed, etc.)
        date_range: Date range for the report:
            - start: Start date
            - end: End date

    Returns:
        Dictionary containing report data:
        {
            "metrics": {"time_to_hire": 15.2, "resumes_processed": 150},
            "dimensions": {"source": {"LinkedIn": 50, "Indeed": 30}},
            "summary": "Key findings and insights...",
            "generated_at": "2024-01-15T10:30:00Z"
        }

    Example:
        >>> config = {"filters": {}, "dimensions": ["source"], "metrics": ["time_to_hire"]}
        >>> date_rng = {"start": datetime(2024, 1, 1), "end": datetime(2024, 1, 31)}
        >>> data = get_report_data(config, date_rng)
        >>> print(data['metrics']['time_to_hire'])
        15.2
    """
    # Note: This is a placeholder for report data generation
    # In a real implementation, you would:
    # 1. Query analytics events, match results, resumes, etc.
    # 2. Apply filters from report_config
    # 3. Group by dimensions
    # 4. Calculate metrics
    # 5. Generate summary insights

    report_type = report_config.get("report_type", "custom")
    metrics = report_config.get("metrics", [])
    dimensions = report_config.get("dimensions", [])

    logger.info(
        f"Generating report data for type '{report_type}', "
        f"metrics: {metrics}, dimensions: {dimensions}"
    )

    # Placeholder data - replace with actual database queries
    data = {
        "metrics": {
            "time_to_hire": 15.2,
            "resumes_processed": 150,
            "match_rate": 0.68,
            "source_effectiveness": {
                "LinkedIn": 0.75,
                "Indeed": 0.62,
                "Referral": 0.85,
            },
        },
        "dimensions": {
            "source": {
                "LinkedIn": 50,
                "Indeed": 30,
                "Referral": 20,
            },
            "recruiter": {
                "john@example.com": 80,
                "jane@example.com": 70,
            },
        },
        "summary": f"Report generated for {report_type} covering period from "
                   f"{date_range['start'].date()} to {date_range['end'].date()}",
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info(f"Report data generated successfully")
    return data


def format_report_as_pdf(
    report_data: Dict[str, Any],
    report_name: str,
) -> Optional[bytes]:
    """
    Format report data as PDF document.

    This function converts report data into a PDF document format
    suitable for email delivery or download using ReportLab.

    Args:
        report_data: Report data dictionary from get_report_data()
        report_name: Name of the report for the PDF title

    Returns:
        PDF document as bytes, or None if generation fails

    Example:
        >>> data = {"metrics": {"time_to_hire": 15.2}, "summary": "..."}
        >>> pdf_bytes = format_report_as_pdf(data, "Weekly Analytics")
        >>> len(pdf_bytes) > 0
        True
    """
    try:
        logger.info(f"Generating PDF for report: {report_name}")

        # Create a BytesIO buffer to hold the PDF
        buffer = BytesIO()

        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Container for the PDF elements
        elements = []

        # Get standard styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=0.2 * inch,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=0.15 * inch,
            spaceBefore=0.25 * inch,
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=0.1 * inch,
        )

        # Add title
        title = Paragraph(report_name, title_style)
        elements.append(title)

        # Add generated timestamp
        generated_at = report_data.get('generated_at', 'N/A')
        try:
            # Try to parse and format the timestamp
            dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            formatted_date = dt.strftime('%B %d, %Y at %I:%M %p')
        except (ValueError, AttributeError):
            formatted_date = generated_at

        timestamp = Paragraph(
            f'<font size="9">Generated: {formatted_date}</font>',
            ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=TA_CENTER,
                spaceAfter=0.3 * inch,
            )
        )
        elements.append(timestamp)

        # Add summary section
        summary_heading = Paragraph('Executive Summary', heading_style)
        elements.append(summary_heading)

        summary_text = report_data.get('summary', 'No summary available.')
        summary_paragraph = Paragraph(summary_text, normal_style)
        elements.append(summary_paragraph)

        # Add metrics section
        metrics_heading = Paragraph('Key Metrics', heading_style)
        elements.append(metrics_heading)

        metrics = report_data.get('metrics', {})

        # Process metrics and build table data
        table_data = [['Metric', 'Value']]
        table_data.append(['', ''])  # Header row

        for metric, value in metrics.items():
            if isinstance(value, dict):
                # For nested dictionaries, add each sub-item
                formatted_key = metric.replace('_', ' ').title()
                table_data.append([
                    Paragraph(f'<b>{formatted_key}</b>', normal_style),
                    ''
                ])

                for sub_key, sub_value in value.items():
                    table_data.append([
                        f'  {sub_key}',
                        f'{sub_value:.2%}' if isinstance(sub_value, float) and sub_value <= 1.0
                        else f'{sub_value:.2f}' if isinstance(sub_value, float)
                        else str(sub_value)
                    ])
            else:
                # For simple values
                formatted_key = metric.replace('_', ' ').title()
                formatted_value = (
                    f'{value:.2%}' if isinstance(value, float) and 0 <= value <= 1.0
                    else f'{value:.2f}' if isinstance(value, float)
                    else str(value)
                )
                table_data.append([formatted_key, formatted_value])

        # Create metrics table
        if len(table_data) > 2:  # More than just headers
            table = Table(table_data, colWidths=[3.5 * inch, 2 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#ecf0f1')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('ROWBACKGROUNDS', (0, 2), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            elements.append(table)

        # Add dimensions section if available
        dimensions = report_data.get('dimensions', {})
        if dimensions:
            elements.append(Spacer(1, 0.2 * inch))

            dimensions_heading = Paragraph('Data Breakdown', heading_style)
            elements.append(dimensions_heading)

            for dim_name, dim_data in dimensions.items():
                dim_title = Paragraph(
                    f'<b>{dim_name.replace("_", " ").title()}</b>',
                    normal_style
                )
                elements.append(dim_title)

                dim_table_data = [['Category', 'Count']]
                for category, count in dim_data.items():
                    dim_table_data.append([category, str(count)])

                dim_table = Table(dim_table_data, colWidths=[3.5 * inch, 2 * inch])
                dim_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ]))
                elements.append(dim_table)
                elements.append(Spacer(1, 0.1 * inch))

        # Add footer
        elements.append(Spacer(1, 0.3 * inch))
        footer = Paragraph(
            '<font size="8"><i>Generated by AgentHR Analytics System</i></font>',
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.gray,
                alignment=TA_CENTER,
            )
        )
        elements.append(footer)

        # Build the PDF
        doc.build(elements)

        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes)")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}", exc_info=True)
        return None


def format_report_as_csv(
    report_data: Dict[str, Any],
) -> Optional[bytes]:
    """
    Format report data as CSV document.

    This function converts report data into CSV format
    suitable for data analysis and spreadsheet import.

    Args:
        report_data: Report data dictionary from get_report_data()

    Returns:
        CSV document as bytes, or None if generation fails

    Example:
        >>> data = {"metrics": {"time_to_hire": 15.2}}
        >>> csv_bytes = format_report_as_csv(data)
        >>> len(csv_bytes) > 0
        True
    """
    # Note: This is a placeholder for CSV generation
    # In a real implementation, you would use Python's csv module
    # or pandas to convert the data to CSV format

    try:
        logger.info("Generating CSV for report")

        # Placeholder: Create a simple CSV representation
        csv_content = "Metric,Value\n"

        for metric, value in report_data.get('metrics', {}).items():
            if isinstance(value, dict):
                for k, v in value.items():
                    csv_content += f"{metric}.{k},{v}\n"
            else:
                csv_content += f"{metric},{value}\n"

        csv_bytes = csv_content.encode('utf-8')

        logger.info(f"CSV generated successfully ({len(csv_bytes)} bytes)")
        return csv_bytes

    except Exception as e:
        logger.error(f"Failed to generate CSV: {e}", exc_info=True)
        return None


def _send_email_with_attachments(
    recipients: List[str],
    subject: str,
    body: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Internal helper function to send email with attachments via SMTP.

    Внутренняя вспомогательная функция для отправки email с вложениями через SMTP.

    Args:
        recipients: Список email адресов получателей / List of recipient email addresses
        subject: Тема письма / Email subject
        body: Текстовое содержимое / Plain text body
        attachments: Список вложений (опционально) / List of attachments (optional):
            [
                {"filename": "report.pdf", "content": b"...", "content_type": "application/pdf"},
                {"filename": "data.csv", "content": b"...", "content_type": "text/csv"}
            ]

    Raises:
        smtplib.SMTPException: Для ошибок SMTP / For SMTP errors
        Exception: Для других ошибок отправки / For other sending errors
    """
    # Check if SMTP is configured
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP not configured, logging email instead of sending")
        logger.info(f"Would send email to: {', '.join(recipients)}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body[:200]}...")
        if attachments:
            logger.info(f"Attachments: {', '.join(a.get('filename', 'unknown') for a in attachments)}")
        return

    # Create email message
    msg = EmailMessage()
    msg["From"] = settings.smtp_default_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.set_content(body)

    # Add attachments if provided
    if attachments:
        for attachment in attachments:
            filename = attachment.get('filename')
            content = attachment.get('content')
            content_type = attachment.get('content_type', 'application/octet-stream')

            if filename and content:
                # Parse content type
                maintype, subtype = content_type.split('/', 1) if '/' in content_type else ('application', 'octet-stream')
                msg.add_attachment(
                    content,
                    maintype=maintype,
                    subtype=subtype,
                    filename=filename
                )
                logger.debug(f"Attached file: {filename} ({len(content)} bytes)")

    # Send via SMTP
    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

        logger.info(f"Email successfully sent to {', '.join(recipients)}")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {', '.join(recipients)}: {e}")
        raise


def send_report_via_email(
    recipients: List[str],
    report_name: str,
    report_data: Dict[str, Any],
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Send report via email to specified recipients.

    This function handles sending generated reports via email with optional
    attachments (PDF, CSV, etc.) using the notification service pattern.

    The email is composed with report summary and key metrics in the body,
    with formatted report files attached.

    Args:
        recipients: List of email addresses to send the report to
        report_name: Name of the report for the email subject
        report_data: Report data dictionary for the email body
        attachments: Optional list of attachments:
            [
                {"filename": "report.pdf", "content": b"...", "content_type": "application/pdf"},
                {"filename": "report.csv", "content": b"...", "content_type": "text/csv"}
            ]

    Returns:
        Dictionary containing email sending results:
        - success: Whether email was sent successfully
        - method: Delivery method used (email)
        - recipients_count: Number of recipients
        - attachments_count: Number of attachments
        - sent_at: Timestamp when sent (Unix timestamp)
        - processing_time_ms: Total processing time in milliseconds
        - error: Error message (if failed)

    Example:
        >>> recipients = ["manager@example.com"]
        >>> result = send_report_via_email(recipients, "Weekly Report", data)
        >>> result['success']
        True
    """
    start_time = time.time()

    logger.info(
        f"Sending report '{report_name}' to {len(recipients)} recipients"
    )

    try:
        # Compose email subject
        subject = f"Report: {report_name}"

        # Compose email body with report summary and key metrics
        body_lines = [
            f"Report: {report_name}",
            f"Generated: {report_data.get('generated_at', 'N/A')}",
            "",
            report_data.get('summary', 'Please see attached files for full report details.'),
            "",
            "KEY METRICS",
            "-" * 40,
        ]

        # Add key metrics to email body
        metrics = report_data.get('metrics', {})
        if metrics:
            for key, value in metrics.items():
                if not isinstance(value, dict):
                    formatted_key = key.replace('_', ' ').title()
                    body_lines.append(f"{formatted_key}: {value}")

        body_lines.append("")
        body_lines.append("---")
        body_lines.append("This is an automated report from AgentHR Analytics System.")

        body = "\n".join(body_lines)

        # Send email using helper function
        _send_email_with_attachments(recipients, subject, body, attachments)

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Report email sent successfully to {len(recipients)} recipients "
            f"in {processing_time}ms"
        )

        return {
            "success": True,
            "method": "email",
            "recipients_count": len(recipients),
            "attachments_count": len(attachments) if attachments else 0,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except smtplib.SMTPException as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"SMTP error sending report email: {e}",
            exc_info=True
        )

        return {
            "success": False,
            "method": "email",
            "recipients_count": len(recipients),
            "attachments_count": len(attachments) if attachments else 0,
            "error": f"SMTP error: {str(e)}",
            "processing_time_ms": processing_time,
        }

    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed to send report email: {e}",
            exc_info=True
        )

        return {
            "success": False,
            "method": "email",
            "recipients_count": len(recipients),
            "attachments_count": len(attachments) if attachments else 0,
            "error": str(e),
            "processing_time_ms": processing_time,
        }


async def _load_report_configurations(
    scheduled_report_id: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
    """
    Load ScheduledReport and Report configurations from database (async).

    Args:
        scheduled_report_id: UUID of the scheduled report

    Returns:
        Tuple of (scheduled_report_dict, report_config_dict, error_message)
        If successful, error_message is None
    """
    async with async_session_maker() as db:
        try:
            # Query ScheduledReport by ID
            scheduled_report_result = await db.execute(
                select(ScheduledReport).where(ScheduledReport.id == scheduled_report_id)
            )
            scheduled_report = scheduled_report_result.scalar_one_or_none()

            if not scheduled_report:
                return None, None, f"Scheduled report {scheduled_report_id} not found"

            # Check if scheduled report is active
            if not scheduled_report.is_active:
                return None, None, f"Scheduled report {scheduled_report_id} is not active"

            # Query Report configuration using report_id from ScheduledReport
            report_result = await db.execute(
                select(Report).where(Report.id == scheduled_report.report_id)
            )
            report = report_result.scalar_one_or_none()

            if not report:
                return None, None, f"Report {scheduled_report.report_id} not found"

            # Convert ScheduledReport to dict for easier access
            scheduled_report_dict = {
                "id": str(scheduled_report.id),
                "organization_id": scheduled_report.organization_id,
                "report_id": str(scheduled_report.report_id),
                "name": scheduled_report.name,
                "schedule_config": scheduled_report.schedule_config,
                "delivery_config": scheduled_report.delivery_config,
                "recipients": scheduled_report.recipients,
                "created_by": scheduled_report.created_by,
                "is_active": scheduled_report.is_active,
                "next_run_at": scheduled_report.next_run_at.isoformat() if scheduled_report.next_run_at else None,
                "last_run_at": scheduled_report.last_run_at.isoformat() if scheduled_report.last_run_at else None,
            }

            # Extract report configuration
            report_config = {
                "report_type": report.report_type,
                "name": report.name,
                "configuration": report.configuration,
            }

            return scheduled_report_dict, report_config, None

        except Exception as e:
            logger.error(f"Database error loading scheduled report: {e}", exc_info=True)
            return None, None, f"Database error: {str(e)}"


async def _update_scheduled_report_timestamps(
    scheduled_report_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    Update last_run_at and calculate next_run_at for a scheduled report (async).

    This function updates the last_run_at timestamp to now and recalculates
    the next_run_at based on the schedule configuration.

    Args:
        scheduled_report_id: UUID of the scheduled report

    Returns:
        Tuple of (success, error_message)
        If successful, error_message is None
    """
    async with async_session_maker() as db:
        try:
            # Query ScheduledReport by ID
            result = await db.execute(
                select(ScheduledReport).where(ScheduledReport.id == scheduled_report_id)
            )
            scheduled_report = result.scalar_one_or_none()

            if not scheduled_report:
                return False, f"Scheduled report {scheduled_report_id} not found"

            # Update last_run_at to now
            scheduled_report.last_run_at = datetime.utcnow()

            # Calculate next_run_at based on schedule_config
            schedule_config = scheduled_report.schedule_config
            frequency = schedule_config.get("frequency", "weekly")
            hour = schedule_config.get("hour", 0)
            minute = schedule_config.get("minute", 0)

            now = datetime.utcnow()

            if frequency == "daily":
                # Next run: tomorrow at specified hour:minute
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                scheduled_report.next_run_at = next_run

            elif frequency == "weekly":
                # Next run: next occurrence of specified day_of_week at hour:minute
                day_of_week = schedule_config.get("day_of_week", 0)
                days_ahead = day_of_week - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                next_run += timedelta(days=days_ahead)
                scheduled_report.next_run_at = next_run

            elif frequency == "monthly":
                # Next run: next month on specified day_of_month at hour:minute
                day_of_month = schedule_config.get("day_of_month", 1)
                next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    # Move to next month
                    if now.month == 12:
                        next_run = next_run.replace(year=now.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=now.month + 1)
                scheduled_report.next_run_at = next_run

            # Commit changes
            await db.commit()

            logger.info(
                f"Updated scheduled report {scheduled_report_id}: "
                f"last_run_at={scheduled_report.last_run_at.isoformat()}, "
                f"next_run_at={scheduled_report.next_run_at.isoformat()}"
            )

            return True, None

        except Exception as e:
            logger.error(f"Database error updating scheduled report: {e}", exc_info=True)
            await db.rollback()
            return False, f"Database error: {str(e)}"


async def _create_audit_log_entry(
    scheduled_report_id: str,
    action_data: Dict[str, Any],
    organization_id: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Create an audit log entry for report generation (async).

    This function creates an audit log entry to track when a scheduled report
    was generated and delivered, including details about formats, recipients,
    and delivery status.

    Args:
        scheduled_report_id: UUID of the scheduled report
        action_data: Dictionary containing report generation details:
            - formats_generated: List of formats (pdf, csv)
            - delivery_method: Delivery method used (email)
            - recipients_count: Number of recipients
            - delivery_successful: Whether delivery was successful
            - processing_time_ms: Processing time in milliseconds
        organization_id: Optional UUID of the organization (if available)

    Returns:
        Tuple of (success, error_message)
        If successful, error_message is None
    """
    async with async_session_maker() as db:
        try:
            # Create audit log entry
            audit_log = AuditLog(
                action_type=AuditActionType.REPORT_GENERATED,
                entity_type="scheduled_report",
                entity_id=scheduled_report_id,
                organization_id=organization_id,
                action_data=action_data,
            )

            db.add(audit_log)
            await db.commit()

            logger.info(
                f"Audit log created for scheduled report {scheduled_report_id}: "
                f"formats={action_data.get('formats_generated')}, "
                f"recipients={action_data.get('recipients_count')}, "
                f"delivery_successful={action_data.get('delivery_successful')}"
            )

            return True, None

        except Exception as e:
            logger.error(f"Database error creating audit log: {e}", exc_info=True)
            await db.rollback()
            return False, f"Database error: {str(e)}"


@shared_task(
    name="tasks.report_generation.generate_scheduled_report",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def generate_scheduled_report(
    self,
    scheduled_report_id: str,
) -> Dict[str, Any]:
    """
    Generate and deliver a scheduled report.

    This Celery task handles the complete workflow of generating a scheduled report:
    1. Retrieve scheduled report configuration
    2. Generate report data based on configuration
    3. Format report in requested formats (PDF, CSV, etc.)
    4. Deliver report via configured channels (email, etc.)
    5. Update last_run timestamp

    Task Workflow:
    1. Query ScheduledReport configuration from database
    2. Calculate date range based on schedule config
    3. Query Report configuration for filters and metrics
    4. Generate report data with get_report_data()
    5. Format report based on delivery config (PDF, CSV)
    6. Send report via configured delivery method
    7. Update ScheduledReport.last_run_at timestamp

    Args:
        self: Celery task instance (bind=True)
        scheduled_report_id: UUID of the scheduled report to generate

    Returns:
        Dictionary containing generation results:
        - scheduled_report_id: ID of the scheduled report
        - status: Task status (completed/failed)
        - formats_generated: List of formats generated (pdf, csv)
        - delivery_method: Delivery method used (email)
        - recipients_count: Number of recipients
        - delivery_successful: Whether delivery was successful
        - processing_time_ms: Total processing time
        - error: Error message (if failed)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
        Exception: For database, generation, or delivery errors

    Example:
        >>> from tasks.report_generation import generate_scheduled_report
        >>> task = generate_scheduled_report.delay("abc-123-def")
        >>> result = task.get()
        >>> print(result['status'])
        'completed'
    """
    start_time = time.time()
    total_steps = 6
    current_step = 0

    try:
        logger.info(
            f"Starting scheduled report generation for ID: {scheduled_report_id}"
        )

        # Step 1: Retrieve scheduled report configuration
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "loading_configuration",
            "message": "Loading scheduled report configuration...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Loading configuration")

        # Query ScheduledReport and Report from database using async helper
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                scheduled_report, report_config, error = loop.run_until_complete(
                    _load_report_configurations(scheduled_report_id)
                )
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}", exc_info=True)
            return {
                "scheduled_report_id": scheduled_report_id,
                "status": "failed",
                "error": f"Failed to load configurations: {str(e)}",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        # Handle errors from database query
        if error:
            if "not found" in error and "not active" not in error:
                logger.error(error)
                return {
                    "scheduled_report_id": scheduled_report_id,
                    "status": "failed",
                    "error": error,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }
            elif "not active" in error:
                logger.warning(error)
                return {
                    "scheduled_report_id": scheduled_report_id,
                    "status": "skipped",
                    "reason": error,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                }

        if not scheduled_report or not report_config:
            logger.error("Failed to load scheduled report or report configuration")
            return {
                "scheduled_report_id": scheduled_report_id,
                "status": "failed",
                "error": "Failed to load required configurations",
                "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            }

        logger.info(f"Loaded scheduled report: {scheduled_report['name']}")

        # Step 2: Calculate date range
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "calculating_date_range",
            "message": "Calculating report date range...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Calculating date range")

        # Calculate date range based on schedule config
        frequency = scheduled_report['schedule_config'].get("frequency", "weekly")
        now = datetime.utcnow()

        if frequency == "daily":
            start_date = now - timedelta(days=1)
        elif frequency == "weekly":
            start_date = now - timedelta(weeks=1)
        elif frequency == "monthly":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)

        date_range = {
            "start": start_date,
            "end": now,
        }

        logger.info(f"Date range: {start_date.date()} to {now.date()}")

        # Step 3: Generate report data
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "generating_data",
            "message": "Generating report data...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Generating data")

        report_config_full = report_config["configuration"]
        report_data = get_report_data(report_config_full, date_range)

        logger.info("Report data generated successfully")

        # Step 4: Format report
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "formatting_report",
            "message": "Formatting report document...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Formatting report")

        delivery_config = scheduled_report['delivery_config']
        # Get format from delivery_config and convert to list
        # API uses "format" (singular), can be "pdf", "csv", or "both"
        format_type = delivery_config.get("format", "pdf")
        if format_type == "both":
            formats = ["pdf", "csv"]
        else:
            formats = [format_type] if format_type else ["pdf"]
        attachments = []

        for format_type in formats:
            if format_type == "pdf":
                pdf_bytes = format_report_as_pdf(report_data, scheduled_report['name'])
                if pdf_bytes:
                    attachments.append({
                        "filename": f"{scheduled_report['name']}.pdf",
                        "content": pdf_bytes,
                        "content_type": "application/pdf",
                    })
                    logger.info("PDF format generated successfully")
            elif format_type == "csv":
                csv_bytes = format_report_as_csv(report_data)
                if csv_bytes:
                    attachments.append({
                        "filename": f"{scheduled_report['name']}.csv",
                        "content": csv_bytes,
                        "content_type": "text/csv",
                    })
                    logger.info("CSV format generated successfully")

        # Step 5: Deliver report
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "delivering_report",
            "message": "Delivering report to recipients...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Delivering report")

        delivery_method = delivery_config.get("method", "email")
        recipients = scheduled_report['recipients']

        delivery_result = None
        delivery_successful = False

        if delivery_method == "email":
            delivery_result = send_report_via_email(
                recipients=recipients,
                report_name=scheduled_report['name'],
                report_data=report_data,
                attachments=attachments if attachments else None,
            )
            delivery_successful = delivery_result.get("success", False)

        logger.info(
            f"Report delivery completed: method={delivery_method}, "
            f"successful={delivery_successful}"
        )

        # Step 6: Update last_run timestamp and calculate next_run
        current_step += 1
        progress = {
            "current": current_step,
            "total": total_steps,
            "percentage": int(current_step / total_steps * 100),
            "status": "updating_timestamp",
            "message": "Updating last run timestamp and calculating next run...",
        }
        self.update_state(state="PROGRESS", meta=progress)
        logger.info(f"Task {self.request.id}: Step {current_step}/{total_steps} - Updating timestamps")

        # Update database with last_run_at and next_run_at
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                update_success, update_error = loop.run_until_complete(
                    _update_scheduled_report_timestamps(scheduled_report_id)
                )
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to update scheduled report timestamps: {e}", exc_info=True)
            update_success = False
            update_error = str(e)

        if not update_success:
            logger.warning(f"Failed to update timestamps in database: {update_error}")
            # Continue anyway - the report was still generated and delivered
            # This failure should be tracked but not cause the task to fail

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "scheduled_report_id": scheduled_report_id,
            "status": "completed",
            "formats_generated": [a["filename"].split(".")[-1] for a in attachments],
            "delivery_method": delivery_method,
            "recipients_count": len(recipients),
            "delivery_successful": delivery_successful,
            "delivery_result": delivery_result,
            "processing_time_ms": processing_time_ms,
        }

        logger.info(
            f"Scheduled report generation completed: {scheduled_report['name']}, "
            f"formats: {result['formats_generated']}, "
            f"delivered to {len(recipients)} recipients, "
            f"time: {processing_time_ms}ms"
        )

        # Create audit log entry for report generation
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Extract organization_id from scheduled_report if available
                organization_id = scheduled_report.get("organization_id")

                # Prepare audit log action data
                audit_action_data = {
                    "report_name": scheduled_report['name'],
                    "formats_generated": result['formats_generated'],
                    "delivery_method": delivery_method,
                    "recipients_count": len(recipients),
                    "delivery_successful": delivery_successful,
                    "processing_time_ms": processing_time_ms,
                }

                audit_success, audit_error = loop.run_until_complete(
                    _create_audit_log_entry(
                        scheduled_report_id,
                        audit_action_data,
                        organization_id,
                    )
                )
            finally:
                loop.close()

            if not audit_success:
                logger.warning(f"Failed to create audit log: {audit_error}")
                # Continue anyway - the report was still generated successfully

        except Exception as e:
            logger.error(f"Error creating audit log: {e}", exc_info=True)
            # Continue anyway - don't let audit log failure prevent task completion

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        return {
            "scheduled_report_id": scheduled_report_id,
            "status": "failed",
            "error": "Report generation exceeded maximum time limit",
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }

    except Exception as e:
        logger.error(f"Error in scheduled report generation: {e}", exc_info=True)
        return {
            "scheduled_report_id": scheduled_report_id,
            "status": "failed",
            "error": str(e),
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
        }


@shared_task(
    name="tasks.report_generation.process_all_pending_reports",
    bind=True,
)
def process_all_pending_reports(
    self,
) -> Dict[str, Any]:
    """
    Process all pending scheduled reports.

    This is a scheduled task (typically run every hour by Celery Beat) that
    checks for scheduled reports whose next_run_at timestamp has passed and
    triggers their generation.

    Task Workflow:
    1. Query all active scheduled reports where next_run_at <= now
    2. For each pending report, trigger generate_scheduled_report task
    3. Update next_run_at based on schedule config
    4. Return summary of processed reports

    Returns:
        Dictionary containing processing results:
        - total_reports_found: Total number of pending reports found
        - reports_triggered: Number of report generation tasks triggered
        - reports_skipped: Number of reports skipped (inactive, errors)
        - processing_time_ms: Total processing time
        - status: Task status

    Example:
        >>> from tasks.report_generation import process_all_pending_reports
        >>> task = process_all_pending_reports.delay()
        >>> result = task.get()
        >>> print(result['reports_triggered'])
        5
    """
    start_time = time.time()

    try:
        logger.info("Processing all pending scheduled reports")

        # Note: This is a placeholder for database query
        # In a real implementation, you would query:
        # scheduled_reports = await db_session.execute(
        #     select(ScheduledReport).where(
        #         and_(
        #             ScheduledReport.is_active == True,
        #             ScheduledReport.next_run_at <= datetime.utcnow()
        #         )
        #     )
        # )

        # Placeholder: Simulate finding pending reports
        pending_reports = []  # List of scheduled report IDs

        reports_triggered = 0
        reports_skipped = 0

        for report_id in pending_reports:
            try:
                # Trigger report generation task
                generate_scheduled_report.delay(report_id)
                reports_triggered += 1
                logger.info(f"Triggered report generation for: {report_id}")

            except Exception as e:
                logger.error(f"Failed to trigger report {report_id}: {e}")
                reports_skipped += 1

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        result = {
            "total_reports_found": len(pending_reports),
            "reports_triggered": reports_triggered,
            "reports_skipped": reports_skipped,
            "processing_time_ms": processing_time_ms,
            "status": "completed",
        }

        logger.info(
            f"Pending reports processing completed: "
            f"{reports_triggered} triggered, {reports_skipped} skipped"
        )

        return result

    except Exception as e:
        logger.error(f"Error in pending reports processing: {e}", exc_info=True)
        return {
            "total_reports_found": 0,
            "reports_triggered": 0,
            "reports_skipped": 0,
            "processing_time_ms": round((time.time() - start_time) * 1000, 2),
            "status": "failed",
            "error": str(e),
        }
