"""
Tests for Notifications Service.

Tests cover notification creation, sending, status tracking,
email/SMS/webhook notifications, and notification history.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4


class TestNotificationModels:
    """Tests for notification model enums and status."""

    def test_notification_status_values(self):
        """Test NotificationStatus enum values."""
        from models.notification import NotificationStatus

        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.DELIVERED.value == "delivered"

    def test_notification_type_values(self):
        """Test NotificationType enum values."""
        from models.notification import NotificationType

        assert NotificationType.EMAIL.value == "email"
        assert NotificationType.SMS.value == "sms"
        assert NotificationType.WEBHOOK.value == "webhook"
        assert NotificationType.IN_APP.value == "in_app"

    def test_notification_priority_values(self):
        """Test NotificationPriority enum values."""
        from models.notification import NotificationPriority

        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"


class TestSendNotificationRequest:
    """Tests for SendNotificationRequest model."""

    def test_valid_email_request(self):
        """Test valid email notification request."""
        from api.notifications import SendNotificationRequest

        request = SendNotificationRequest(
            type="email",
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body content",
            priority="normal",
        )

        assert request.type == "email"
        assert request.recipient == "test@example.com"
        assert request.subject == "Test Subject"

    def test_valid_sms_request(self):
        """Test valid SMS notification request."""
        from api.notifications import SendNotificationRequest

        request = SendNotificationRequest(
            type="sms",
            recipient="+1234567890",
            body="SMS message content",
            priority="high",
        )

        assert request.type == "sms"
        assert request.recipient == "+1234567890"

    def test_valid_webhook_request(self):
        """Test valid webhook notification request."""
        from api.notifications import SendNotificationRequest

        request = SendNotificationRequest(
            type="webhook",
            recipient="https://example.com/webhook",
            body='{"event": "notification"}',
            metadata={"event_type": "test"},
        )

        assert request.type == "webhook"
        assert "https://" in request.recipient

    def test_request_with_template(self):
        """Test notification request with template."""
        from api.notifications import SendNotificationRequest

        request = SendNotificationRequest(
            type="email",
            recipient="test@example.com",
            template_name="welcome_email",
            template_vars={"name": "John", "company": "ACME"},
        )

        assert request.template_name == "welcome_email"
        assert request.template_vars["name"] == "John"

    def test_request_with_metadata(self):
        """Test notification request with metadata."""
        from api.notifications import SendNotificationRequest

        request = SendNotificationRequest(
            type="email",
            recipient="test@example.com",
            subject="Test",
            body="Body",
            metadata={"campaign_id": "123", "user_id": "456"},
        )

        assert request.metadata["campaign_id"] == "123"


class TestNotificationResponse:
    """Tests for NotificationResponse model."""

    def test_valid_notification_response(self):
        """Test valid notification response."""
        from api.notifications import NotificationResponse

        response = NotificationResponse(
            id=str(uuid4()),
            type="email",
            recipient="test@example.com",
            status="sent",
            priority="high",
            subject="Test Subject",
            sent_at=datetime.utcnow().isoformat(),
            created_at=datetime.utcnow().isoformat(),
        )

        assert response.type == "email"
        assert response.status == "sent"

    def test_response_with_pending_status(self):
        """Test response with pending status (no sent_at)."""
        from api.notifications import NotificationResponse

        response = NotificationResponse(
            id=str(uuid4()),
            type="sms",
            recipient="+1234567890",
            status="pending",
            priority="normal",
            subject=None,
            sent_at=None,
            created_at=datetime.utcnow().isoformat(),
        )

        assert response.status == "pending"
        assert response.sent_at is None


class TestNotificationsListResponse:
    """Tests for NotificationsListResponse model."""

    def test_valid_list_response(self):
        """Test valid notifications list response."""
        from api.notifications import NotificationsListResponse, NotificationResponse

        response = NotificationsListResponse(
            total=100,
            skip=0,
            limit=50,
            notifications=[
                NotificationResponse(
                    id=str(uuid4()),
                    type="email",
                    recipient="test1@example.com",
                    status="sent",
                    priority="normal",
                    subject="Test 1",
                    sent_at=datetime.utcnow().isoformat(),
                    created_at=datetime.utcnow().isoformat(),
                ),
                NotificationResponse(
                    id=str(uuid4()),
                    type="sms",
                    recipient="+1234567890",
                    status="pending",
                    priority="high",
                    subject=None,
                    sent_at=None,
                    created_at=datetime.utcnow().isoformat(),
                ),
            ],
        )

        assert response.total == 100
        assert len(response.notifications) == 2
        assert response.skip == 0
        assert response.limit == 50


class TestCreateNotificationRecord:
    """Tests for notification record creation."""

    @pytest.mark.asyncio
    async def test_create_email_notification_record(self):
        """Test creating email notification record."""
        from api.notifications import create_notification_record
        from models.notification import Notification

        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        notification = await create_notification_record(
            db=mock_db,
            notification_type="email",
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body",
            priority="normal",
            metadata={"key": "value"},
        )

        assert notification.notification_type == "email"
        assert notification.recipient == "test@example.com"
        assert notification.subject == "Test Subject"
        assert notification.status == "pending"

    @pytest.mark.asyncio
    async def test_create_sms_notification_record(self):
        """Test creating SMS notification record."""
        from api.notifications import create_notification_record

        mock_db = AsyncMock()
        mock_db.add = Mock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        notification = await create_notification_record(
            db=mock_db,
            notification_type="sms",
            recipient="+1234567890",
            subject=None,
            body="SMS content",
            priority="high",
            metadata=None,
        )

        assert notification.notification_type == "sms"
        assert notification.subject is None


class TestSendNotificationFunctions:
    """Tests for notification sending functions."""

    @pytest.mark.asyncio
    async def test_send_email_notification(self):
        """Test sending email notification."""
        from api.notifications import send_email_notification

        result = await send_email_notification(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test body content",
            metadata={"key": "value"},
        )

        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_send_sms_notification(self):
        """Test sending SMS notification."""
        from api.notifications import send_sms_notification

        result = await send_sms_notification(
            recipient="+1234567890",
            body="SMS message",
            metadata={"carrier": "test"},
        )

        assert result["success"] is True
        assert "message" in result

    @pytest.mark.asyncio
    async def test_send_webhook_notification(self):
        """Test sending webhook notification."""
        from api.notifications import send_webhook_notification

        result = await send_webhook_notification(
            recipient="https://example.com/webhook",
            subject="Webhook event",
            body='{"data": "test"}',
            metadata={"event_id": "123"},
        )

        assert result["success"] is True
        assert "message" in result


class TestNotificationValidation:
    """Tests for notification validation logic."""

    def test_valid_notification_types(self):
        """Test validation of notification types."""
        from models.notification import NotificationType

        valid_types = [t.value for t in NotificationType]

        assert "email" in valid_types
        assert "sms" in valid_types
        assert "webhook" in valid_types
        assert "in_app" in valid_types

    def test_valid_priorities(self):
        """Test validation of priority values."""
        from models.notification import NotificationPriority

        valid_priorities = [p.value for p in NotificationPriority]

        assert "low" in valid_priorities
        assert "normal" in valid_priorities
        assert "high" in valid_priorities
        assert "urgent" in valid_priorities

    def test_invalid_notification_type_rejected(self):
        """Test that invalid notification type is rejected."""
        from models.notification import NotificationType

        with pytest.raises(ValueError):
            NotificationType("invalid_type")

    def test_email_format_validation(self):
        """Test email format validation concept."""
        from services.email_notification_service import EmailNotificationService

        service = EmailNotificationService()

        # Valid email
        assert service.validate_email_address("test@example.com") is True
        assert service.validate_email_address("user.name+tag@domain.co.uk") is True

        # Invalid email
        assert service.validate_email_address("invalid-email") is False
        assert service.validate_email_address("@example.com") is False
        assert service.validate_email_address("test@") is False


class TestEmailNotificationService:
    """Tests for EmailNotificationService."""

    def test_service_initialization(self):
        """Test EmailNotificationService initialization."""
        from services.email_notification_service import EmailNotificationService

        with patch("services.email_notification_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                smtp_host="smtp.example.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="pass",
                smtp_use_tls=True,
                smtp_default_from="noreply@example.com",
            )

            service = EmailNotificationService()

            assert service.smtp_host == "smtp.example.com"
            assert service.smtp_port == 587

    def test_send_email_placeholder_mode(self):
        """Test email sending in placeholder mode."""
        from services.email_notification_service import EmailNotificationService

        with patch("services.email_notification_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                smtp_username=None,
                smtp_password=None,
                smtp_default_from="noreply@example.com",
                smtp_host="smtp.example.com",
                smtp_port=587,
                smtp_use_tls=True,
            )

            service = EmailNotificationService()
            result = service.send_email(
                to="test@example.com",
                subject="Test",
                body="Body",
            )

            assert result["success"] is True
            assert "placeholder" in result["message"].lower()

    def test_send_email_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        from services.email_notification_service import EmailNotificationService

        with patch("services.email_notification_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                smtp_username=None,
                smtp_password=None,
                smtp_default_from="noreply@example.com",
            )

            service = EmailNotificationService()
            result = service.send_email(
                to=["recipient1@example.com", "recipient2@example.com"],
                subject="Test",
                body="Body",
            )

            assert result["recipients_count"] == 2

    def test_send_html_email(self):
        """Test sending HTML email."""
        from services.email_notification_service import EmailNotificationService

        with patch("services.email_notification_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                smtp_username=None,
                smtp_password=None,
                smtp_default_from="noreply@example.com",
            )

            service = EmailNotificationService()
            result = service.send_html_email(
                to="test@example.com",
                subject="HTML Email",
                html_body="<h1>Hello</h1>",
                text_body="Hello",
            )

            assert result["success"] is True

    def test_email_validation(self):
        """Test email address validation."""
        from services.email_notification_service import EmailNotificationService

        with patch("services.email_notification_service.get_settings") as mock_settings:
            mock_settings.return_value = Mock(
                smtp_host="smtp.example.com",
                smtp_port=587,
                smtp_username="user",
                smtp_password="pass",
                smtp_use_tls=True,
                smtp_default_from="noreply@example.com",
            )

            service = EmailNotificationService()

            assert service.validate_email_address("valid@example.com") is True
            assert service.validate_email_address("invalid") is False

    def test_get_email_service_singleton(self):
        """Test that get_email_service returns singleton instance."""
        from services.email_notification_service import get_email_service

        with patch("services.email_notification_service.get_settings"):
            service1 = get_email_service()
            service2 = get_email_service()

            # Should return same instance
            assert service1 is service2


class TestNotificationStatusUpdates:
    """Tests for notification status updates."""

    @pytest.mark.asyncio
    async def test_status_update_to_sent(self):
        """Test status update from pending to sent."""
        from models.notification import Notification, NotificationStatus

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            status=NotificationStatus.PENDING.value,
            subject="Test",
            body="Body",
        )

        # Simulate successful send
        notification.status = NotificationStatus.SENT.value
        notification.sent_at = datetime.utcnow()

        assert notification.status == "sent"
        assert notification.sent_at is not None

    @pytest.mark.asyncio
    async def test_status_update_to_failed(self):
        """Test status update from pending to failed."""
        from models.notification import Notification, NotificationStatus

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            status=NotificationStatus.PENDING.value,
            subject="Test",
            body="Body",
        )

        # Simulate failed send
        notification.status = NotificationStatus.FAILED.value
        notification.error_message = "SMTP connection failed"

        assert notification.status == "failed"
        assert notification.error_message is not None


class TestNotificationFilters:
    """Tests for notification filtering functionality."""

    def test_filter_by_status(self):
        """Test filtering notifications by status."""
        notifications = [
            Mock(status="sent"),
            Mock(status="pending"),
            Mock(status="failed"),
            Mock(status="sent"),
        ]

        sent_only = [n for n in notifications if n.status == "sent"]

        assert len(sent_only) == 2

    def test_filter_by_type(self):
        """Test filtering notifications by type."""
        notifications = [
            Mock(notification_type="email"),
            Mock(notification_type="sms"),
            Mock(notification_type="email"),
            Mock(notification_type="webhook"),
        ]

        email_only = [n for n in notifications if n.notification_type == "email"]

        assert len(email_only) == 2

    def test_filter_by_recipient(self):
        """Test filtering notifications by recipient."""
        notifications = [
            Mock(recipient="test1@example.com"),
            Mock(recipient="test2@example.com"),
            Mock(recipient="test1@example.com"),
        ]

        test1_emails = [n for n in notifications if "test1" in n.recipient]

        assert len(test1_emails) == 2

    def test_combined_filters(self):
        """Test combining multiple filters."""
        notifications = [
            Mock(status="sent", notification_type="email", recipient="test@example.com"),
            Mock(status="pending", notification_type="email", recipient="test@example.com"),
            Mock(status="sent", notification_type="sms", recipient="+1234567890"),
            Mock(status="sent", notification_type="email", recipient="other@example.com"),
        ]

        # Sent + Email + specific recipient
        filtered = [
            n for n in notifications
            if n.status == "sent"
            and n.notification_type == "email"
            and n.recipient == "test@example.com"
        ]

        assert len(filtered) == 1


class TestNotificationPagination:
    """Tests for notification pagination."""

    def test_pagination_logic(self):
        """Test pagination skip and limit logic."""
        all_notifications = list(range(100))  # 100 notifications

        skip = 10
        limit = 20

        paginated = all_notifications[skip:skip + limit]

        assert len(paginated) == 20
        assert paginated[0] == 10
        assert paginated[-1] == 29

    def test_pagination_beyond_bounds(self):
        """Test pagination when skip exceeds available items."""
        all_notifications = list(range(10))

        skip = 15
        limit = 10

        paginated = all_notifications[skip:skip + limit]

        assert len(paginated) == 0


class TestNotificationPriority:
    """Tests for notification priority handling."""

    def test_priority_ordering(self):
        """Test priority ordering for processing."""
        from models.notification import NotificationPriority

        priority_order = {
            NotificationPriority.URGENT: 0,
            NotificationPriority.HIGH: 1,
            NotificationPriority.NORMAL: 2,
            NotificationPriority.LOW: 3,
        }

        notifications = [
            Mock(priority=NotificationPriority.NORMAL.value),
            Mock(priority=NotificationPriority.URGENT.value),
            Mock(priority=NotificationPriority.LOW.value),
            Mock(priority=NotificationPriority.HIGH.value),
        ]

        sorted_notifications = sorted(
            notifications,
            key=lambda n: priority_order.get(NotificationPriority(n.priority), 99)
        )

        assert sorted_notifications[0].priority == "urgent"
        assert sorted_notifications[-1].priority == "low"


class TestNotificationMetadata:
    """Tests for notification metadata handling."""

    def test_metadata_storage(self):
        """Test storing notification metadata."""
        metadata = {
            "campaign_id": "campaign-123",
            "user_id": "user-456",
            "triggered_by": "system",
            "retry_count": 0,
        }

        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
            metadata=metadata,
        )

        assert notification.metadata["campaign_id"] == "campaign-123"
        assert notification.metadata["retry_count"] == 0

    def test_null_metadata(self):
        """Test notification with null metadata."""
        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
            metadata=None,
        )

        assert notification.metadata is None


class TestNotificationTimestamps:
    """Tests for notification timestamp handling."""

    def test_created_at_timestamp(self):
        """Test that created_at is set on creation."""
        from models.notification import Notification

        before = datetime.utcnow()
        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
        )
        after = datetime.utcnow()

        assert notification.created_at is not None
        assert before <= notification.created_at <= after

    def test_sent_at_timestamp_nullable(self):
        """Test that sent_at is nullable initially."""
        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
            status="pending",
        )

        assert notification.sent_at is None

        # After sending
        notification.sent_at = datetime.utcnow()
        assert notification.sent_at is not None


class TestNotificationErrorHandling:
    """Tests for notification error handling."""

    @pytest.mark.asyncio
    async def test_error_message_storage(self):
        """Test storing error message on failure."""
        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
            status="pending",
        )

        # Simulate error
        notification.status = "failed"
        notification.error_message = "SMTP connection timeout after 30 seconds"

        assert notification.status == "failed"
        assert "timeout" in notification.error_message.lower()

    def test_retry_count_in_metadata(self):
        """Test tracking retry count in metadata."""
        metadata = {"retry_count": 3, "last_error": "Connection failed"}

        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body="Body",
            metadata=metadata,
        )

        assert notification.metadata["retry_count"] == 3


class TestNotificationBatchOperations:
    """Tests for batch notification operations."""

    def test_batch_notification_creation(self):
        """Test creating multiple notifications."""
        recipients = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com",
        ]

        notifications = []
        for recipient in recipients:
            notifications.append({
                "recipient": recipient,
                "subject": "Batch Test",
                "body": "Test body",
            })

        assert len(notifications) == 3
        assert notifications[0]["recipient"] == "user1@example.com"


class TestNotificationEdgeCases:
    """Tests for edge cases in notifications."""

    def test_empty_subject_allowed(self):
        """Test that empty subject is allowed for some types."""
        from models.notification import Notification

        # SMS doesn't need subject
        notification = Notification(
            recipient="+1234567890",
            notification_type="sms",
            subject=None,
            body="SMS message",
        )

        assert notification.subject is None

    def test_empty_body_handling(self):
        """Test handling of empty body."""
        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="in_app",
            subject="Notification",
            body="",
        )

        assert notification.body == ""

    def test_very_long_subject(self):
        """Test handling of very long subject."""
        long_subject = "A" * 500

        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject=long_subject,
            body="Body",
        )

        assert len(notification.subject) == 500

    def test_special_characters_in_body(self):
        """Test handling of special characters in body."""
        special_body = "Test with émojis 🎉 and spëcial çharacters"

        from models.notification import Notification

        notification = Notification(
            recipient="test@example.com",
            notification_type="email",
            subject="Test",
            body=special_body,
        )

        assert "🎉" in notification.body
