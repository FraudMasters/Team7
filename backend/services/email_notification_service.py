"""
Email notification service for backup system alerts

This module provides email notification capabilities for backup operations including:
- Backup failure notifications
- Backup success notifications
- Backup warning notifications (low disk space, missed backups)
- S3 sync failure notifications
- Restore operation notifications

Supports both synchronous SMTP sending and asynchronous Celery task execution.
"""
import logging
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional, Dict, Any

from config import get_settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """
    Email notification service for backup system alerts.

    Provides SMTP-based email notifications with template support.
    Singleton instance accessible via get_email_service().

    Example:
        >>> email_service = get_email_service()
        >>> email_service.send_backup_failure_notification(
        ...     operation="daily_backup",
        ...     error_message="Disk full"
        ... )
    """

    def __init__(self):
        """Initialize email notification service with settings."""
        self._settings = get_settings()

        # SMTP configuration
        self._smtp_host = os.getenv("SMTP_HOST", "localhost")
        self._smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self._smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self._smtp_user = os.getenv("SMTP_USER")
        self._smtp_password = os.getenv("SMTP_PASSWORD")
        self._smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@backup.local")
        self._smtp_from_name = os.getenv("SMTP_FROM_NAME", "Backup System")

        # Recipient configuration
        self._notification_email = getattr(
            self._settings,
            "backup_notification_email",
            None
        ) or os.getenv("BACKUP_NOTIFICATION_EMAIL")

        # Check if email is enabled
        self._enabled = bool(self._notification_email)

        if not self._enabled:
            logger.warning("Email notifications disabled: No recipient email configured")
        else:
            logger.info(
                f"Email notification service initialized "
                f"(recipient: {self._notification_email})"
            )

    def is_enabled(self) -> bool:
        """
        Check if email notifications are enabled.

        Returns:
            True if email notifications are configured and enabled
        """
        return self._enabled

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self._enabled:
            logger.debug("Email notifications disabled, skipping send")
            return False

        try:
            # Create email message
            msg = EmailMessage()
            msg["To"] = to
            msg["From"] = formataddr((self._smtp_from_name, self._smtp_from_email))
            msg["Subject"] = subject

            # Set plain text body
            msg.set_content(body)

            # Add HTML body if provided
            if html_body:
                msg.add_alternative(html_body, subtype="html")

            # Send via SMTP
            if self._smtp_use_tls:
                with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                    server.starttls()
                    if self._smtp_user and self._smtp_password:
                        server.login(self._smtp_user, self._smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                    if self._smtp_user and self._smtp_password:
                        server.login(self._smtp_user, self._smtp_password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {to}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False

        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending email: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return False

    def send_backup_failure_notification(
        self,
        operation: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification for backup failure.

        Args:
            operation: Name of the failed operation (e.g., "daily_backup", "s3_sync")
            error_message: Error message or exception details
            context: Optional additional context (backup_type, timestamp, etc.)

        Returns:
            True if notification was sent successfully
        """
        if not self._enabled:
            logger.warning(
                f"Backup failure notification for {operation}: {error_message} "
                f"(email not configured)"
            )
            return False

        # Build plain text email
        body_lines = [
            f"Backup Operation Failed: {operation}",
            "",
            f"Error: {error_message}",
            "",
        ]

        # Add context if provided
        if context:
            body_lines.append("Additional Information:")
            for key, value in context.items():
                body_lines.append(f"  {key}: {value}")
            body_lines.append("")

        body_lines.extend([
            "Please investigate this failure as soon as possible.",
            "",
            "---",
            "This is an automated message from the Backup System",
        ])

        body = "\n".join(body_lines)

        # Build HTML version
        html_body = f"""
        <html>
        <body>
            <h2 style="color: #d32f2f;">⚠️ Backup Operation Failed</h2>
            <p><strong>Operation:</strong> {operation}</p>
            <p><strong>Error:</strong> {error_message}</p>
        """

        if context:
            html_body += "<h3>Additional Information:</h3><ul>"
            for key, value in context.items():
                html_body += f"<li><strong>{key}:</strong> {value}</li>"
            html_body += "</ul>"

        html_body += """
            <p><strong>Please investigate this failure as soon as possible.</strong></p>
            <hr>
            <p><em>This is an automated message from the Backup System</em></p>
        </body>
        </html>
        """

        subject = f"🚨 Backup Failed: {operation}"

        return self.send_email(
            to=self._notification_email,
            subject=subject,
            body=body,
            html_body=html_body,
        )

    def send_backup_success_notification(
        self,
        operation: str,
        backup_type: str,
        size_bytes: int,
        duration_seconds: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification for successful backup (optional, usually not needed).

        Args:
            operation: Name of the successful operation
            backup_type: Type of backup (database, files, models, full)
            size_bytes: Size of the backup in bytes
            duration_seconds: Duration of the backup operation
            context: Optional additional context

        Returns:
            True if notification was sent successfully
        """
        if not self._enabled:
            return False

        # Convert bytes to human-readable format
        size_mb = size_bytes / (1024 * 1024)

        body = f"""Backup Operation Completed Successfully

Operation: {operation}
Backup Type: {backup_type}
Size: {size_mb:.2f} MB
Duration: {duration_seconds:.2f} seconds

"""

        if context:
            body += "Additional Information:\n"
            for key, value in context.items():
                body += f"  {key}: {value}\n"
            body += "\n"

        body += "---\nThis is an automated message from the Backup System\n"

        subject = f"✅ Backup Success: {operation}"

        return self.send_email(
            to=self._notification_email,
            subject=subject,
            body=body,
        )

    def send_backup_warning_notification(
        self,
        warning_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification for backup warning (low disk space, missed backup, etc.).

        Args:
            warning_type: Type of warning (e.g., "low_disk_space", "missed_backup")
            message: Warning message
            context: Optional additional context

        Returns:
            True if notification was sent successfully
        """
        if not self._enabled:
            return False

        body_lines = [
            f"Backup System Warning: {warning_type}",
            "",
            f"Warning: {message}",
            "",
        ]

        if context:
            body_lines.append("Additional Information:")
            for key, value in context.items():
                body_lines.append(f"  {key}: {value}")
            body_lines.append("")

        body_lines.extend([
            "Please review this warning to prevent potential failures.",
            "",
            "---",
            "This is an automated message from the Backup System",
        ])

        body = "\n".join(body_lines)

        subject = f"⚠️ Backup Warning: {warning_type}"

        return self.send_email(
            to=self._notification_email,
            subject=subject,
            body=body,
        )

    def send_restore_notification(
        self,
        operation: str,
        status: str,
        backup_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification for restore operation.

        Args:
            operation: Name of the restore operation
            status: Status of the restore (success, failure, started)
            backup_type: Type of restore (database, files, models, full)
            context: Optional additional context

        Returns:
            True if notification was sent successfully
        """
        if not self._enabled:
            return False

        if status == "success":
            subject = f"✅ Restore Success: {operation}"
            emoji = "✅"
        elif status == "failure":
            subject = f"🚨 Restore Failed: {operation}"
            emoji = "🚨"
        else:
            subject = f"ℹ️ Restore {status.title()}: {operation}"
            emoji = "ℹ️"

        body = f"""Restore Operation {status.title()}

Operation: {operation}
Backup Type: {backup_type}
Status: {status}
"""

        if context:
            body += "\nAdditional Information:\n"
            for key, value in context.items():
                body += f"  {key}: {value}\n"

        body += "\n---\nThis is an automated message from the Backup System\n"

        return self.send_email(
            to=self._notification_email,
            subject=subject,
            body=body,
        )


# Singleton instance
_email_service_instance: Optional[EmailNotificationService] = None


def get_email_service() -> EmailNotificationService:
    """
    Get the singleton email notification service instance.

    Returns:
        EmailNotificationService instance
    """
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailNotificationService()
    return _email_service_instance


def send_backup_notification(
    notification_type: str,
    **kwargs
) -> bool:
    """
    Send a backup notification email.

    Convenience function that routes to the appropriate notification method.

    Args:
        notification_type: Type of notification
            - 'failure': Backup failure notification
            - 'success': Backup success notification
            - 'warning': Backup warning notification
            - 'restore': Restore operation notification
        **kwargs: Additional arguments passed to the specific notification method

    Returns:
        True if notification was sent successfully

    Example:
        >>> send_backup_notification(
        ...     'failure',
        ...     operation='daily_backup',
        ...     error_message='Disk full'
        ... )
    """
    service = get_email_service()

    if notification_type == "failure":
        return service.send_backup_failure_notification(
            operation=kwargs.get("operation", "unknown"),
            error_message=kwargs.get("error_message", "No error details"),
            context=kwargs.get("context"),
        )

    elif notification_type == "success":
        return service.send_backup_success_notification(
            operation=kwargs.get("operation", "unknown"),
            backup_type=kwargs.get("backup_type", "unknown"),
            size_bytes=kwargs.get("size_bytes", 0),
            duration_seconds=kwargs.get("duration_seconds", 0.0),
            context=kwargs.get("context"),
        )

    elif notification_type == "warning":
        return service.send_backup_warning_notification(
            warning_type=kwargs.get("warning_type", "unknown"),
            message=kwargs.get("message", "No warning details"),
            context=kwargs.get("context"),
        )

    elif notification_type == "restore":
        return service.send_restore_notification(
            operation=kwargs.get("operation", "unknown"),
            status=kwargs.get("status", "unknown"),
            backup_type=kwargs.get("backup_type", "unknown"),
            context=kwargs.get("context"),
        )

    else:
        logger.error(f"Unknown notification type: {notification_type}")
        return False


__all__ = [
    "EmailNotificationService",
    "get_email_service",
    "send_backup_notification",
]
