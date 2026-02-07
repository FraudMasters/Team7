"""
Email notification tasks for sending various types of emails.

Этот модуль предоставляет задачи Celery для отправки email-уведомлений,
включая обратную связь по кандидатам, доставку отчетов, системные оповещения
и другие email-коммуникации.

This module provides Celery tasks for sending email notifications including
candidate feedback, report delivery, system alerts, and other email communications.
"""
import logging
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Any, List, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# Добавляем родительскую директорию для импорта конфигурации
# Add parent directory for configuration import
service_dir = Path(__file__).parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(
    name="tasks.email_task.send_feedback_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_feedback_notification(
    self,
    feedback_id: str,
    recipient_email: str,
    candidate_name: str,
    feedback_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send candidate feedback via email.

    Отправить отзыв о кандидате по электронной почте.

    This Celery task handles sending candidate feedback to recruiters or hiring managers.
    It includes the feedback summary, scores, and detailed analysis.

    Task Workflow:
    1. Format feedback content for email
    2. Compose email with appropriate template
    3. Send email via configured SMTP/service
    4. Return delivery status

    Args:
        self: Экземпляр задачи Celery (bind=True) / Celery task instance (bind=True)
        feedback_id: UUID отзыва кандидата / UUID of the candidate feedback
        recipient_email: Email адрес получателя / Email address of the recipient
        candidate_name: Имя кандидата / Name of the candidate
        feedback_data: Словарь с деталями отзыва / Dictionary containing feedback details:
            - grammar_feedback: Отзыв о грамматике и языке / Grammar and language feedback
            - skills_feedback: Оценка навыков / Skills assessment feedback
            - experience_feedback: Отзыв о опыте работы / Work experience feedback
            - recommendations: Список рекомендаций / List of recommendations
            - match_score: Общий счет совпадения / Overall match score
            - tone: Тон отзыва / Feedback tone

    Returns:
        Словарь с результатами отправки / Dictionary containing sending results:
        - feedback_id: ID отзыва / ID of the feedback
        - status: Статус задачи (sent/failed/pending) / Task status (sent/failed/pending)
        - recipient: Email адрес получателя / Email address of recipient
        - sent_at: Время отправки (timestamp) / Timestamp when sent (ISO format)
        - error: Сообщение об ошибке (при неудаче) / Error message (if failed)
        - processing_time_ms: Общее время обработки / Total processing time

    Raises:
        SoftTimeLimitExceeded: Если задача превышает мягкий лимит времени / If task exceeds soft time limit
        Exception: Для ошибок отправки email / For email sending failures

    Example:
        >>> result = send_feedback_notification.delay(
        ...     feedback_id="123-456",
        ...     recipient_email="recruiter@example.com",
        ...     candidate_name="John Doe",
        ...     feedback_data={"match_score": 85, "recommendations": ["..."]}
        ... )
        >>> print(result.get())
        {'feedback_id': '123-456', 'status': 'sent', 'recipient': 'recruiter@example.com'}
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending feedback notification for feedback_id={feedback_id} "
        f"to {recipient_email}"
    )

    try:
        # Compose email subject
        subject = f"Candidate Feedback: {candidate_name}"

        # Compose email body
        body = f"""
Feedback for Candidate: {candidate_name}
Feedback ID: {feedback_id}

Match Score: {feedback_data.get('match_score', 'N/A')}%

Skills Feedback:
{feedback_data.get('skills_feedback', {})}

Experience Feedback:
{feedback_data.get('experience_feedback', {})}

Recommendations:
{chr(10).join(f'- {rec}' for rec in feedback_data.get('recommendations', []))}

---
This is an automated email from AgentHR Resume Analysis System.
        """.strip()

        # Send email
        _send_email(recipient_email, subject, body)

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Feedback notification sent successfully to {recipient_email} "
            f"in {processing_time}ms"
        )

        return {
            "feedback_id": feedback_id,
            "status": "sent",
            "recipient": recipient_email,
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"Feedback notification task timed out for feedback_id={feedback_id}")
        return {
            "feedback_id": feedback_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": "Task timed out",
        }

    except Exception as e:
        logger.error(
            f"Failed to send feedback notification for feedback_id={feedback_id}: {e}",
            exc_info=True,
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "feedback_id": feedback_id,
            "status": "failed",
            "recipient": recipient_email,
            "error": str(e),
        }


@shared_task(
    name="tasks.email_task.send_batch_notification",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def send_batch_notification(
    self,
    batch_type: str,
    recipient_emails: List[str],
    notification_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send batch notifications to multiple recipients.

    Отправить пакетные уведомления нескольким получателям.

    This Celery task handles sending notifications to multiple recipients
    for batch operations like batch resume analysis completion, system alerts,
    or scheduled reports.

    Args:
        self: Экземпляр задачи Celery (bind=True) / Celery task instance (bind=True)
        batch_type: Тип пакетного уведомления / Type of batch notification (batch_analysis, system_alert, etc.)
        recipient_emails: Список email адресов / List of email addresses to send to
        notification_data: Словарь с деталями уведомления / Dictionary containing notification details:
            - title: Заголовок уведомления / Notification title
            - message: Основное сообщение уведомления / Main notification message
            - details: Дополнительные детали / Additional details dictionary
            - metadata: Любые дополнительные метаданные / Any additional metadata

    Returns:
        Словарь с результатами пакетной отправки / Dictionary containing batch sending results:
        - batch_type: Тип уведомления / Type of notification
        - status: Статус задачи (sent/failed/partial) / Task status (sent/failed/partial)
        - total_recipients: Количество получателей / Number of recipients
        - successful_sends: Количество успешных отправок / Number of successful sends
        - failed_sends: Количество неудачных отправок / Number of failed sends
        - errors: Список ошибок (если есть) / List of errors (if any)
        - processing_time_ms: Общее время обработки / Total processing time
    """
    import time
    start_time = time.time()

    logger.info(
        f"Sending batch notification (type={batch_type}) to {len(recipient_emails)} recipients"
    )

    successful_sends = 0
    failed_sends = 0
    errors = []

    for recipient_email in recipient_emails:
        try:
            subject = notification_data.get("title", f"Batch Notification: {batch_type}")
            body = notification_data.get("message", "")

            if "details" in notification_data:
                body += f"\n\nDetails:\n{notification_data['details']}"

            _send_email(recipient_email, subject, body)
            successful_sends += 1
            logger.info(f"Batch notification sent to {recipient_email}")

        except Exception as e:
            failed_sends += 1
            error_msg = f"Failed to send to {recipient_email}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    processing_time = int((time.time() - start_time) * 1000)

    # Determine overall status
    if failed_sends == 0:
        status = "sent"
    elif successful_sends == 0:
        status = "failed"
    else:
        status = "partial"

    return {
        "batch_type": batch_type,
        "status": status,
        "total_recipients": len(recipient_emails),
        "successful_sends": successful_sends,
        "failed_sends": failed_sends,
        "errors": errors,
        "processing_time_ms": processing_time,
    }


@shared_task(
    name="tasks.email_task.send_email_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email_notification(
    self,
    recipient_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send a generic email notification.

    Отправить общее email-уведомление.

    This Celery task handles sending generic email notifications with optional
    HTML content. Useful for custom notifications, alerts, and system messages.

    Args:
        self: Экземпляр задачи Celery (bind=True) / Celery task instance (bind=True)
        recipient_email: Email адрес получателя / Email address of the recipient
        subject: Тема письма / Email subject
        body: Текстовое содержимое письма / Plain text email body
        html_body: HTML содержимое (опционально) / HTML body content (optional)

    Returns:
        Словарь с результатами отправки / Dictionary containing sending results:
        - recipient: Email адрес получателя / Email address of recipient
        - status: Статус (sent/failed) / Status (sent/failed)
        - sent_at: Время отправки / Timestamp when sent
        - error: Ошибка (при неудаче) / Error message (if failed)

    Raises:
        Exception: Для ошибок отправки email / For email sending failures

    Example:
        >>> result = send_email_notification.delay(
        ...     recipient_email="user@example.com",
        ...     subject="Welcome!",
        ...     body="Thank you for signing up."
        ... )
    """
    import time
    start_time = time.time()

    logger.info(f"Sending email to {recipient_email} with subject: {subject}")

    try:
        _send_email(recipient_email, subject, body, html_body)

        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Email sent successfully to {recipient_email} in {processing_time}ms")

        return {
            "recipient": recipient_email,
            "status": "sent",
            "sent_at": time.time(),
            "processing_time_ms": processing_time,
        }

    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

        return {
            "recipient": recipient_email,
            "status": "failed",
            "error": str(e),
        }


def _send_email(
    recipient_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> None:
    """
    Internal helper function to send email via SMTP.

    Внутренняя вспомогательная функция для отправки email через SMTP.

    Args:
        recipient_email: Email адрес получателя / Email address of the recipient
        subject: Тема письма / Email subject
        body: Текстовое содержимое / Plain text body
        html_body: HTML содержимое (опционально) / HTML body (optional)

    Raises:
        smtplib.SMTPException: Для ошибок SMTP / For SMTP errors
        Exception: Для других ошибок отправки / For other sending errors
    """
    # Check if SMTP is configured
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP not configured, logging email instead of sending")
        logger.info(f"Would send email to: {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body[:200]}...")
        return

    # Create email message
    msg = EmailMessage()
    msg["From"] = settings.smtp_default_from
    msg["To"] = recipient_email
    msg["Subject"] = subject

    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

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

        logger.info(f"Email successfully sent to {recipient_email}")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {recipient_email}: {e}")
        raise
