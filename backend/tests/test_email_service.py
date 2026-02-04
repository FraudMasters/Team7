"""
Unit tests for EmailNotificationService.

Tests cover SMTP configuration, email message construction,
template rendering, error handling, and notification delivery.

Test Coverage:
- EmailNotificationService initialization and configuration
- SMTP configuration loading from environment
- Email message construction (headers, body, HTML)
- Template rendering for different notification types
- Backup failure notifications
- Backup success notifications
- Backup warning notifications
- Restore operation notifications
- Error handling (SMTP failures, timeouts, authentication)
- Disabled email behavior
- Singleton pattern
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from email.message import EmailMessage

from services.email_notification_service import (
    EmailNotificationService,
    get_email_service,
    send_backup_notification,
)


class TestEmailNotificationServiceInit:
    """Tests for EmailNotificationService initialization."""

    def test_initialization_with_no_recipient(self):
        """Test initialization when no notification email is configured."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            service = EmailNotificationService()

            assert service.is_enabled() is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_HOST': 'smtp.example.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'user@example.com',
        'SMTP_PASSWORD': 'password',
    })
    def test_initialization_with_recipient(self):
        """Test initialization with notification email configured."""
        service = EmailNotificationService()

        assert service.is_enabled() is True
        assert service._notification_email == 'admin@example.com'

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    def test_smtp_default_configuration(self):
        """Test default SMTP configuration values."""
        service = EmailNotificationService()

        assert service._smtp_host == 'localhost'
        assert service._smtp_port == 587
        assert service._smtp_use_tls is True

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_HOST': 'smtp.gmail.com',
        'SMTP_PORT': '465',
        'SMTP_USE_TLS': 'false',
        'SMTP_FROM_EMAIL': 'noreply@test.com',
        'SMTP_FROM_NAME': 'Test Backup System',
    })
    def test_custom_smtp_configuration(self):
        """Test custom SMTP configuration from environment."""
        service = EmailNotificationService()

        assert service._smtp_host == 'smtp.gmail.com'
        assert service._smtp_port == 465
        assert service._smtp_use_tls is False
        assert service._smtp_from_email == 'noreply@test.com'
        assert service._smtp_from_name == 'Test Backup System'


class TestIsEnabled:
    """Tests for is_enabled method."""

    def test_is_enabled_when_no_recipient(self):
        """Test is_enabled returns False when no recipient."""
        with patch.dict(os.environ, {}, clear=True):
            service = EmailNotificationService()

            assert service.is_enabled() is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    def test_is_enabled_when_recipient_configured(self):
        """Test is_enabled returns True when recipient configured."""
        service = EmailNotificationService()

        assert service.is_enabled() is True


class TestSendEmail:
    """Tests for send_email method."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        service = EmailNotificationService()

        result = service.send_email(
            to='admin@example.com',
            subject='Test Subject',
            body='Test body',
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_email_with_html(self, mock_smtp):
        """Test sending email with HTML body."""
        service = EmailNotificationService()

        result = service.send_email(
            to='admin@example.com',
            subject='Test Subject',
            body='Plain text body',
            html_body='<html><body>HTML body</body></html>',
        )

        assert result is True

        # Verify send_message was called
        mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_send_email_when_disabled(self):
        """Test send_email returns False when disabled."""
        service = EmailNotificationService()

        result = service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        assert result is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_HOST': 'smtp.example.com',
        'SMTP_PORT': '587',
    })
    @patch('smtplib.SMTP')
    def test_send_email_with_tls(self, mock_smtp):
        """Test email sending with TLS enabled."""
        service = EmailNotificationService()

        service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        # Verify starttls was called
        server_instance = mock_smtp.return_value.__enter__.return_value
        server_instance.starttls.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_USE_TLS': 'false',
    })
    @patch('smtplib.SMTP')
    def test_send_email_without_tls(self, mock_smtp):
        """Test email sending without TLS."""
        service = EmailNotificationService()

        service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        # Verify starttls was NOT called
        server_instance = mock_smtp.return_value.__enter__.return_value
        server_instance.starttls.assert_not_called()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_USER': 'user@example.com',
        'SMTP_PASSWORD': 'password',
    })
    @patch('smtplib.SMTP')
    def test_send_email_with_authentication(self, mock_smtp):
        """Test email sending with SMTP authentication."""
        service = EmailNotificationService()

        service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        # Verify login was called
        server_instance = mock_smtp.return_value.__enter__.return_value
        server_instance.login.assert_called_once_with('user@example.com', 'password')


class TestSendBackupFailureNotification:
    """Tests for backup failure notifications."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_backup_failure_notification(self, mock_smtp):
        """Test backup failure notification sending."""
        service = EmailNotificationService()

        result = service.send_backup_failure_notification(
            operation='daily_backup',
            error_message='Disk full',
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_backup_failure_with_context(self, mock_smtp):
        """Test backup failure with additional context."""
        service = EmailNotificationService()

        result = service.send_backup_failure_notification(
            operation='s3_sync',
            error_message='Authentication failed',
            context={
                'backup_type': 'files',
                'timestamp': '2026-02-03 12:00:00',
                'retry_count': 3,
            },
        )

        assert result is True

        # Verify message contains context
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]
        message_str = str(message)

        assert 'backup_type' in message_str
        assert 'timestamp' in message_str

    @patch.dict(os.environ, {}, clear=True)
    def test_send_backup_failure_when_disabled(self):
        """Test failure notification when email disabled."""
        service = EmailNotificationService()

        result = service.send_backup_failure_notification(
            operation='daily_backup',
            error_message='Disk full',
        )

        assert result is False


class TestSendBackupSuccessNotification:
    """Tests for backup success notifications."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_backup_success_notification(self, mock_smtp):
        """Test backup success notification sending."""
        service = EmailNotificationService()

        result = service.send_backup_success_notification(
            operation='daily_backup',
            backup_type='database',
            size_bytes=1024000,
            duration_seconds=45.5,
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_backup_success_includes_size_and_duration(self, mock_smtp):
        """Test success notification includes size and duration."""
        service = EmailNotificationService()

        service.send_backup_success_notification(
            operation='manual_backup',
            backup_type='files',
            size_bytes=5120000,
            duration_seconds=120.0,
        )

        # Verify message contains size and duration
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]
        message_str = str(message)

        assert '4.88' in message_str  # MB size
        assert '120.00' in message_str  # duration

    @patch.dict(os.environ, {}, clear=True)
    def test_send_backup_success_when_disabled(self):
        """Test success notification when email disabled."""
        service = EmailNotificationService()

        result = service.send_backup_success_notification(
            operation='daily_backup',
            backup_type='database',
            size_bytes=1024000,
            duration_seconds=45.5,
        )

        assert result is False


class TestSendBackupWarningNotification:
    """Tests for backup warning notifications."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_backup_warning_notification(self, mock_smtp):
        """Test backup warning notification sending."""
        service = EmailNotificationService()

        result = service.send_backup_warning_notification(
            warning_type='low_disk_space',
            message='Less than 10% disk space remaining',
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_warning_notification_with_context(self, mock_smtp):
        """Test warning notification with context."""
        service = EmailNotificationService()

        result = service.send_backup_warning_notification(
            warning_type='missed_backup',
            message='Last backup was 48 hours ago',
            context={
                'expected_time': '2026-02-02 02:00:00',
                'last_backup': '2026-01-31 02:00:00',
            },
        )

        assert result is True


class TestSendRestoreNotification:
    """Tests for restore operation notifications."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_restore_success_notification(self, mock_smtp):
        """Test restore success notification."""
        service = EmailNotificationService()

        result = service.send_restore_notification(
            operation='restore_database',
            status='success',
            backup_type='database',
        )

        assert result is True

        # Verify subject contains success
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]
        assert 'Success' in message['Subject']

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_restore_failure_notification(self, mock_smtp):
        """Test restore failure notification."""
        service = EmailNotificationService()

        result = service.send_restore_notification(
            operation='restore_files',
            status='failure',
            backup_type='files',
        )

        assert result is True

        # Verify subject contains failure indicator
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]
        assert 'Failed' in message['Subject']

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_restore_started_notification(self, mock_smtp):
        """Test restore started notification."""
        service = EmailNotificationService()

        result = service.send_restore_notification(
            operation='restore_models',
            status='started',
            backup_type='models',
        )

        assert result is True


class TestErrorHandling:
    """Tests for error handling."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_smtp_authentication_error(self, mock_smtp):
        """Test handling of SMTP authentication errors."""
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')

        service = EmailNotificationService()
        result = service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        assert result is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_smtp_exception_error(self, mock_smtp):
        """Test handling of SMTP exceptions."""
        import smtplib
        mock_smtp.side_effect = smtplib.SMTPException('Connection error')

        service = EmailNotificationService()
        result = service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        assert result is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_generic_exception_error(self, mock_smtp):
        """Test handling of generic exceptions."""
        mock_smtp.side_effect = Exception('Unexpected error')

        service = EmailNotificationService()
        result = service.send_email(
            to='admin@example.com',
            subject='Test',
            body='Body',
        )

        assert result is False


class TestEmailMessageStructure:
    """Tests for email message structure."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
        'SMTP_FROM_NAME': 'Backup System',
        'SMTP_FROM_EMAIL': 'noreply@backup.local',
    })
    @patch('smtplib.SMTP')
    def test_email_headers_set_correctly(self, mock_smtp):
        """Test email headers are set correctly."""
        service = EmailNotificationService()
        service.send_email(
            to='admin@example.com',
            subject='Test Subject',
            body='Test body',
        )

        # Verify message headers
        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]

        assert message['To'] == 'admin@example.com'
        assert message['Subject'] == 'Test Subject'
        assert 'Backup System' in message['From']

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_failure_notification_has_emoji(self, mock_smtp):
        """Test failure notification subject has warning emoji."""
        service = EmailNotificationService()
        service.send_backup_failure_notification(
            operation='daily_backup',
            error_message='Disk full',
        )

        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]

        assert '🚨' in message['Subject'] or 'Backup Failed' in message['Subject']

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_success_notification_has_emoji(self, mock_smtp):
        """Test success notification subject has success emoji."""
        service = EmailNotificationService()
        service.send_backup_success_notification(
            operation='daily_backup',
            backup_type='database',
            size_bytes=1024000,
            duration_seconds=45.5,
        )

        call_args = mock_smtp.return_value.__enter__.return_value.send_message.call_args
        message = call_args[0][0]

        assert '✅' in message['Subject'] or 'Backup Success' in message['Subject']


class TestSingletonPattern:
    """Tests for singleton pattern."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    def test_get_email_service_returns_singleton(self):
        """Test that get_email_service returns the same instance."""
        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    def test_multiple_creates_different_instances(self):
        """Test that direct instantiation creates different instances."""
        service1 = EmailNotificationService()
        service2 = EmailNotificationService()

        # Different instances
        assert service1 is not service2


class TestSendBackupNotification:
    """Tests for send_backup_notification convenience function."""

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_failure_notification(self, mock_smtp):
        """Test send_backup_notification with failure type."""
        result = send_backup_notification(
            'failure',
            operation='daily_backup',
            error_message='Disk full',
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_success_notification(self, mock_smtp):
        """Test send_backup_notification with success type."""
        result = send_backup_notification(
            'success',
            operation='daily_backup',
            backup_type='database',
            size_bytes=1024000,
            duration_seconds=45.5,
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_warning_notification(self, mock_smtp):
        """Test send_backup_notification with warning type."""
        result = send_backup_notification(
            'warning',
            warning_type='low_disk_space',
            message='Less than 10% disk space remaining',
        )

        assert result is True
        mock_smtp.assert_called_once()

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_send_restore_notification(self, mock_smtp):
        """Test send_backup_notification with restore type."""
        result = send_backup_notification(
            'restore',
            operation='restore_database',
            status='success',
            backup_type='database',
        )

        assert result is True
        mock_smtp.assert_called_once()

    def test_send_unknown_notification_type(self):
        """Test send_backup_notification with unknown type."""
        result = send_backup_notification(
            'unknown_type',
        )

        assert result is False

    @patch.dict(os.environ, {
        'BACKUP_NOTIFICATION_EMAIL': 'admin@example.com',
    })
    @patch('smtplib.SMTP')
    def test_notification_with_context(self, mock_smtp):
        """Test notification with context parameters."""
        result = send_backup_notification(
            'failure',
            operation='daily_backup',
            error_message='Disk full',
            context={
                'backup_type': 'database',
                'timestamp': '2026-02-03 12:00:00',
            },
        )

        assert result is True
