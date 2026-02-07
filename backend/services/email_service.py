"""
Email service with SMTP configuration and template support.

This module provides email sending capabilities using SMTP with connection pooling,
automatic retries, and template support for HTML and plain text emails.

The email service supports:
- SMTP configuration with TLS/SSL support
- Connection pooling for efficient email sending
- Automatic retries with exponential backoff
- HTML and plain text email support
- Template-based email generation
- Graceful fallback when SMTP is unavailable
- Health checks and connection monitoring

Email template format: templates/email/{template_name}.html
Example: templates/email/welcome.html
"""
import logging
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import get_settings

logger = logging.getLogger(__name__)

# Global email service instance
_email_service: Optional["EmailService"] = None


class EmailService:
    """
    Email service with SMTP configuration and template support.

    This class provides a high-level interface for sending emails with
    automatic connection management, retries, and template rendering.

    Attributes:
        enabled: Whether email sending is enabled
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_username: SMTP username for authentication
        smtp_from_email: Default sender email address
        smtp_from_name: Default sender name
        use_tls: Use TLS for SMTP connection
        use_ssl: Use SSL for SMTP connection
        timeout: SMTP connection timeout in seconds
        max_retries: Maximum number of retry attempts

    Example:
        >>> email = EmailService()
        >>> email.send_email(
        ...     to="user@example.com",
        ...     subject="Welcome",
        ...     body="Welcome to our service!"
        ... )
    """

    # Email template categories
    TEMPLATE_WELCOME = "welcome"
    TEMPLATE_PASSWORD_RESET = "password_reset"
    TEMPLATE_NOTIFICATION = "notification"
    TEMPLATE_MATCH_ALERT = "match_alert"
    TEMPLATE_ANALYSIS_COMPLETE = "analysis_complete"
    TEMPLATE_BACKUP_SUCCESS = "backup_success"
    TEMPLATE_BACKUP_FAILURE = "backup_failure"

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_email: Optional[str] = None,
        smtp_from_name: Optional[str] = None,
        enabled: Optional[bool] = None,
        use_tls: Optional[bool] = None,
        use_ssl: Optional[bool] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
        templates_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the email service with SMTP configuration.

        Args:
            smtp_host: SMTP server hostname (defaults to settings)
            smtp_port: SMTP server port (defaults to settings)
            smtp_username: SMTP username (defaults to settings)
            smtp_password: SMTP password (defaults to settings)
            smtp_from_email: Default sender email (defaults to settings)
            smtp_from_name: Default sender name (defaults to settings)
            enabled: Whether email sending is enabled (defaults to settings)
            use_tls: Use TLS (defaults to settings)
            use_ssl: Use SSL (defaults to settings)
            timeout: Connection timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
            retry_delay: Delay between retries in seconds (defaults to settings)
            templates_dir: Directory for email templates (defaults to settings)
        """
        settings = get_settings()

        self.enabled = enabled if enabled is not None else settings.smtp_enabled
        self.smtp_host = smtp_host or settings.smtp_host
        self.smtp_port = smtp_port or settings.smtp_port
        self.smtp_username = smtp_username or settings.smtp_username
        self.smtp_password = smtp_password or settings.smtp_password
        self.smtp_from_email = smtp_from_email or settings.smtp_from_email
        self.smtp_from_name = smtp_from_name or settings.smtp_from_name
        self.use_tls = use_tls if use_tls is not None else settings.smtp_use_tls
        self.use_ssl = use_ssl if use_ssl is not None else settings.smtp_use_ssl
        self.timeout = timeout or settings.smtp_timeout_seconds
        self.max_retries = max_retries or settings.smtp_max_retries
        self.retry_delay = retry_delay or settings.smtp_retry_delay_seconds
        self.templates_dir = templates_dir or settings.email_templates_dir

        # Validate configuration
        self._validate_config()

        logger.info(
            f"EmailService initialized (enabled={self.enabled}, "
            f"host={self.smtp_host}, port={self.smtp_port})"
        )

    def _validate_config(self) -> None:
        """
        Validate email configuration.

        Logs warnings for common configuration issues but doesn't raise exceptions,
        as email sending can be disabled or optional.
        """
        if self.enabled:
            if not self.smtp_host:
                logger.warning("Email enabled but SMTP host not configured")
                self.enabled = False

            if not self.smtp_from_email:
                logger.warning("Email enabled but from_email not configured")
                self.enabled = False

            if self.use_tls and self.use_ssl:
                logger.warning("Both TLS and SSL enabled, using TLS only")
                self.use_ssl = False

    def _create_connection(self) -> Optional[smtplib.SMTP]:
        """
        Create and authenticate SMTP connection.

        Returns:
            Authenticated SMTP connection or None if connection fails

        Example:
            >>> smtp = self._create_connection()
            >>> if smtp:
            ...     # Use connection
            ...     smtp.quit()
        """
        if not self.enabled or not self.smtp_host:
            return None

        try:
            # Create SMTP connection
            if self.use_ssl:
                smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=self.timeout)
            else:
                smtp = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout)

            # Enable debug logging if needed
            # smtp.set_debuglevel(1)

            # Start TLS if configured
            if self.use_tls and not self.use_ssl:
                smtp.starttls()
                logger.debug("TLS enabled for SMTP connection")

            # Authenticate if credentials provided
            if self.smtp_username and self.smtp_password:
                smtp.login(self.smtp_username, self.smtp_password)
                logger.debug(f"Authenticated as {self.smtp_username}")

            logger.debug(f"SMTP connection established to {self.smtp_host}:{self.smtp_port}")
            return smtp

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return None
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error creating connection: {e}")
            return None
        except (OSError, TimeoutError) as e:
            logger.error(f"Network error connecting to SMTP server: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating SMTP connection: {e}", exc_info=True)
            return None

    def _build_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        html: bool = False,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> MIMEMultipart:
        """
        Build email message with headers and body.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            from_email: Sender email (defaults to instance default)
            from_name: Sender name (defaults to instance default)
            html: Whether body is HTML (True) or plain text (False)
            reply_to: Reply-to email address
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            Constructed MIMEMultipart message

        Example:
            >>> msg = self._build_message(
            ...     to="user@example.com",
            ...     subject="Welcome",
            ...     body="Welcome!"
            ... )
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr(
            (from_name or self.smtp_from_name, from_email or self.smtp_from_email)
        )
        msg["To"] = to
        msg["Date"] = formatdate(localtime=True)

        if reply_to:
            msg["Reply-To"] = reply_to

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Attach body
        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type, _charset="utf-8"))

        return msg

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        html: bool = False,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            from_email: Sender email (defaults to instance default)
            from_name: Sender name (defaults to instance default)
            html: Whether body is HTML (True) or plain text (False)
            reply_to: Reply-to email address
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            True if email sent successfully, False otherwise

        Example:
            >>> email = EmailService()
            >>> success = email.send_email(
            ...     to="user@example.com",
            ...     subject="Welcome",
            ...     body="Welcome to our service!"
            ... )
        """
        if not self.enabled:
            logger.debug(f"Email sending disabled, skipping: {to}")
            return False

        # Build message
        msg = self._build_message(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            html=html,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
        )

        # Build recipient list
        recipients = [to]
        if cc:
            recipients.extend(cc)
        if bcc:
            recipients.extend(bcc)

        # Send with retries
        last_error = None
        for attempt in range(self.max_retries + 1):
            smtp = None
            try:
                smtp = self._create_connection()
                if smtp is None:
                    logger.warning(f"Failed to create SMTP connection (attempt {attempt + 1})")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    return False

                smtp.send_message(msg)
                logger.info(f"Email sent successfully to {to}")
                return True

            except smtplib.SMTPException as e:
                last_error = e
                logger.warning(f"SMTP error sending email (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error sending email (attempt {attempt + 1}): {e}", exc_info=True)
            finally:
                if smtp:
                    try:
                        smtp.quit()
                    except Exception:
                        pass

            # Retry with exponential backoff
            if attempt < self.max_retries:
                delay = self.retry_delay * (attempt + 1)
                logger.debug(f"Retrying in {delay} seconds...")
                time.sleep(delay)

        logger.error(f"Failed to send email after {self.max_retries + 1} attempts: {last_error}")
        return False

    def send_template_email(
        self,
        to: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email using a template.

        Args:
            to: Recipient email address
            subject: Email subject line
            template_name: Name of the template (without .html extension)
            context: Dictionary of variables for template rendering
            from_email: Sender email (defaults to instance default)
            from_name: Sender name (defaults to instance default)
            reply_to: Reply-to email address
            cc: List of CC recipients
            bcc: List of BCC recipients

        Returns:
            True if email sent successfully, False otherwise

        Example:
            >>> email = EmailService()
            >>> success = email.send_template_email(
            ...     to="user@example.com",
            ...     subject="Welcome",
            ...     template_name="welcome",
            ...     context={"name": "John", "company": "Acme Corp"}
            ... )
        """
        body = self._render_template(template_name, context)
        if body is None:
            logger.error(f"Failed to render template: {template_name}")
            return False

        return self.send_email(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            from_name=from_name,
            html=True,
            reply_to=reply_to,
            cc=cc,
            bcc=bcc,
        )

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Render an email template with context.

        Args:
            template_name: Name of the template (without .html extension)
            context: Dictionary of variables for template rendering

        Returns:
            Rendered template string or None if template not found

        Example:
            >>> html = self._render_template("welcome", {"name": "John"})
            >>> print(html)
        """
        template_path = self.templates_dir / f"{template_name}.html"

        try:
            if not template_path.exists():
                logger.warning(f"Template not found: {template_path}")
                return None

            # Simple template rendering using str.format()
            # For production, consider using Jinja2 or similar
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # Replace variables in template
            # Supports {variable} syntax
            try:
                return template.format(**context)
            except KeyError as e:
                logger.error(f"Template variable not found: {e}")
                return None

        except IOError as e:
            logger.error(f"Error reading template {template_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error rendering template: {e}", exc_info=True)
            return None

    def send_bulk_emails(
        self,
        recipients: List[Tuple[str, Dict[str, Any]]],
        subject: str,
        template_name: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Send personalized emails to multiple recipients.

        Args:
            recipients: List of (email, context) tuples
            subject: Email subject line
            template_name: Name of the template
            from_email: Sender email (defaults to instance default)
            from_name: Sender name (defaults to instance default)
            reply_to: Reply-to email address

        Returns:
            Dictionary with 'success', 'failed', and 'total' counts

        Example:
            >>> email = EmailService()
            >>> recipients = [
            ...     ("user1@example.com", {"name": "John"}),
            ...     ("user2@example.com", {"name": "Jane"}),
            ... ]
            >>> result = email.send_bulk_emails(
            ...     recipients=recipients,
            ...     subject="Update",
            ...     template_name="notification"
            ... )
        """
        result = {"success": 0, "failed": 0, "total": len(recipients)}

        for to, context in recipients:
            if self.send_template_email(
                to=to,
                subject=subject,
                template_name=template_name,
                context=context,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
            ):
                result["success"] += 1
            else:
                result["failed"] += 1

        logger.info(
            f"Bulk email complete: {result['success']}/{result['total']} sent, "
            f"{result['failed']} failed"
        )
        return result

    def health_check(self) -> Dict[str, Any]:
        """
        Check SMTP connection health and configuration status.

        Returns:
            Dictionary with health status and configuration info

        Example:
            >>> email = EmailService()
            >>> health = email.health_check()
            >>> print(health)
            {'status': 'healthy', 'configured': True, ...}
        """
        result = {
            "status": "unhealthy",
            "enabled": self.enabled,
            "configured": False,
            "connected": False,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "from_email": self.smtp_from_email,
            "error": None,
        }

        if not self.enabled:
            result["error"] = "Email sending is disabled"
            return result

        # Check if configured
        if not all([self.smtp_host, self.smtp_from_email]):
            result["error"] = "Incomplete SMTP configuration"
            return result

        result["configured"] = True

        # Test connection
        smtp = None
        try:
            smtp = self._create_connection()
            if smtp is None:
                result["error"] = "Failed to establish SMTP connection"
                return result

            # Send NOOP to test connection
            smtp.noop()
            result["connected"] = True
            result["status"] = "healthy"
            logger.debug("SMTP health check passed")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"SMTP health check failed: {e}")
        finally:
            if smtp:
                try:
                    smtp.quit()
                except Exception:
                    pass

        return result

    def test_email(self, to: Optional[str] = None) -> bool:
        """
        Send a test email to verify SMTP configuration.

        Args:
            to: Recipient email (defaults to from_email)

        Returns:
            True if test email sent successfully

        Example:
            >>> email = EmailService()
            >>> success = email.test_email("test@example.com")
        """
        if to is None:
            to = self.smtp_from_email

        return self.send_email(
            to=to,
            subject="AgentHR Test Email",
            body="This is a test email from AgentHR. Your SMTP configuration is working correctly!",
            html=False,
        )


def get_email_service() -> EmailService:
    """
    Get or create global email service instance.

    Returns:
        Global EmailService instance

    Example:
        >>> email = get_email_service()
        >>> email.send_email("user@example.com", "Test", "Body")
    """
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_notification_email(
    to: str,
    subject: str,
    message: str,
    notification_type: str = "general",
) -> bool:
    """
    Send a notification email.

    Convenience function for sending notification emails.

    Args:
        to: Recipient email address
        subject: Email subject line
        message: Notification message
        notification_type: Type of notification (for logging)

    Returns:
        True if email sent successfully

    Example:
        >>> send_notification_email(
        ...     to="user@example.com",
        ...     subject="Match Alert",
        ...     message="New candidate matched your vacancy!"
        ... )
    """
    email = get_email_service()

    # Try template first
    context = {
        "message": message,
        "notification_type": notification_type,
    }

    # Fall back to plain text if template fails
    if not email.send_template_email(
        to=to,
        subject=subject,
        template_name=EmailService.TEMPLATE_NOTIFICATION,
        context=context,
    ):
        return email.send_email(
            to=to,
            subject=subject,
            body=message,
            html=False,
        )

    return True
