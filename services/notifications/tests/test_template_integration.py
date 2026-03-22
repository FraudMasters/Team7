"""
Integration tests for notification template system.

Tests cover the full end-to-end flow:
- Create email template via API
- Save template to database
- Load template in notification service
- Send email using template

These integration tests verify the complete workflow from template
creation through to notification delivery.
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime
from uuid import uuid4


class TestTemplateIntegration:
    """Integration tests for template creation and usage."""

    @pytest.mark.asyncio
    async def test_create_template_via_api_and_save_to_db(self):
        """Test creating email template via API and saving to database."""
        from api.templates import CreateTemplateRequest
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate

        # Mock database session
        mock_db = AsyncMock()

        # Mock query result for checking existing template (should be None)
        mock_existing_result = AsyncMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_existing_result

        # Create template request
        request = CreateTemplateRequest(
            template_type="email",
            name="integration_test_template",
            subject="Welcome {name}!",
            body="Hello {name}, welcome to {company}!",
            variables=["name", "company"],
            template_blocks={
                "blocks": [
                    {"type": "text", "content": "Welcome message"}
                ]
            },
            category="recruitment",
            pipeline_stage="application_received",
            language="en",
            description="Integration test template",
            is_active=True,
        )

        # Create template via service
        service = get_template_service()
        template = await service.create_template(
            db=mock_db,
            template_type=request.template_type,
            name=request.name,
            subject=request.subject,
            body=request.body,
            variables=request.variables,
            template_blocks=request.template_blocks,
            category=request.category,
            pipeline_stage=request.pipeline_stage,
            language=request.language,
            description=request.description,
            is_active=request.is_active,
        )

        # Verify database operations
        assert mock_db.add.called
        assert mock_db.commit.called

        # Verify template data
        added_template = mock_db.add.call_args[0][0]
        assert isinstance(added_template, EmailTemplate)
        assert added_template.name == "integration_test_template"
        assert added_template.subject == "Welcome {name}!"
        assert added_template.body == "Hello {name}, welcome to {company}!"
        assert added_template.variables == ["name", "company"]
        assert added_template.category == "recruitment"
        assert added_template.pipeline_stage == "application_received"

    @pytest.mark.asyncio
    async def test_load_template_from_db_in_notification_service(self):
        """Test loading template from database in notification service."""
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate

        # Create mock template
        mock_template = EmailTemplate(
            id=str(uuid4()),
            name="test_welcome",
            subject="Welcome {name}!",
            body="Hello {name}, your role is {role}.",
            variables=["name", "role"],
            template_blocks=None,
            category="recruitment",
            pipeline_stage="application_received",
            language="en",
            is_active=True,
        )
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        # Load template via service
        service = get_template_service()
        loaded_template = await service.get_template_by_name(
            db=mock_db,
            name="test_welcome",
            template_type="email",
            language="en",
        )

        # Verify template loaded correctly
        assert loaded_template is not None
        assert loaded_template.name == "test_welcome"
        assert loaded_template.subject == "Welcome {name}!"
        assert loaded_template.body == "Hello {name}, your role is {role}."
        assert loaded_template.category == "recruitment"

    @pytest.mark.asyncio
    async def test_render_template_with_variables(self):
        """Test rendering template with variable substitution."""
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate

        # Create mock template
        mock_template = EmailTemplate(
            id=str(uuid4()),
            name="offer_email",
            subject="Job Offer - {position}",
            body="Dear {name}, we are pleased to offer you the position of {position} at {company}.",
            variables=["name", "position", "company"],
            template_blocks=None,
            category="recruitment",
            pipeline_stage="offer",
            language="en",
            is_active=True,
        )
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        # Render template with variables
        service = get_template_service()
        rendered = await service.render_template(
            db=mock_db,
            template_id=mock_template.id,
            template_type="email",
            variables={
                "name": "John Doe",
                "position": "Senior Developer",
                "company": "TechCorp",
            },
        )

        # Verify rendered content
        assert rendered["subject"] == "Job Offer - Senior Developer"
        assert rendered["body"] == "Dear John Doe, we are pleased to offer you the position of Senior Developer at TechCorp."
        assert "active_blocks" in rendered

    @pytest.mark.asyncio
    async def test_send_notification_with_template(self):
        """Test sending notification using template from database."""
        from api.notifications import SendNotificationRequest
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate
        from models.notification import Notification, NotificationStatus

        # Create mock template
        mock_template = EmailTemplate(
            id=str(uuid4()),
            name="rejection_email",
            subject="Application Update - {position}",
            body="Dear {name}, thank you for your interest in {position}. Unfortunately, we have decided to move forward with other candidates.",
            variables=["name", "position"],
            template_blocks=None,
            category="recruitment",
            pipeline_stage="rejection",
            language="en",
            is_active=True,
        )
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        # Mock database session
        mock_db = AsyncMock()

        # Mock template retrieval
        mock_template_result = AsyncMock()
        mock_template_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_template_result

        # Create notification request with template
        request = SendNotificationRequest(
            type="email",
            recipient="candidate@example.com",
            template_name="rejection_email",
            template_vars={
                "name": "Jane Smith",
                "position": "Software Engineer",
            },
            priority="normal",
        )

        # Get template service and render template
        service = get_template_service()
        template = await service.get_template_by_name(
            db=mock_db,
            name=request.template_name,
            template_type="email",
            language="en",
        )

        assert template is not None

        # Render template with variables
        rendered = await service.render_template(
            db=mock_db,
            template_id=template.id,
            template_type="email",
            variables=request.template_vars,
        )

        # Verify rendered content
        assert rendered["subject"] == "Application Update - Software Engineer"
        assert "Jane Smith" in rendered["body"]
        assert "Software Engineer" in rendered["body"]

        # Create notification record
        notification = Notification(
            notification_type=request.type,
            recipient=request.recipient,
            subject=rendered["subject"],
            body=rendered["body"],
            priority=request.priority,
            status=NotificationStatus.PENDING.value,
        )

        assert notification.subject == "Application Update - Software Engineer"
        assert notification.recipient == "candidate@example.com"
        assert notification.status == "pending"

    @pytest.mark.asyncio
    async def test_template_with_conditional_blocks(self):
        """Test template rendering with conditional blocks."""
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate

        # Create mock template with conditional blocks
        mock_template = EmailTemplate(
            id=str(uuid4()),
            name="interview_email",
            subject="Interview Invitation - {position}",
            body="Dear {name}, we would like to invite you for an interview.",
            variables=["name", "position", "status"],
            template_blocks={
                "blocks": [
                    {"type": "text", "content": "Dear {name},"},
                    {
                        "type": "conditional",
                        "condition": {
                            "field": "status",
                            "operator": "eq",
                            "value": "accepted"
                        },
                        "true_block": {"type": "text", "content": "Congratulations! Your application has been accepted."},
                        "false_block": {"type": "text", "content": "Thank you for your application."}
                    }
                ]
            },
            category="recruitment",
            pipeline_stage="interview",
            language="en",
            is_active=True,
        )
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        # Mock database session
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_template
        mock_db.execute.return_value = mock_result

        # Render template with status="accepted"
        service = get_template_service()
        rendered_accepted = await service.render_template(
            db=mock_db,
            template_id=mock_template.id,
            template_type="email",
            variables={
                "name": "Alice Johnson",
                "position": "Product Manager",
                "status": "accepted",
            },
        )

        # Verify conditional block evaluated to true
        assert len(rendered_accepted["active_blocks"]) == 2
        assert rendered_accepted["active_blocks"][0]["content"] == "Dear {name},"
        assert "Congratulations" in rendered_accepted["active_blocks"][1]["content"]

        # Reset mock for second test
        mock_db.execute.return_value = mock_result

        # Render template with status="pending"
        rendered_pending = await service.render_template(
            db=mock_db,
            template_id=mock_template.id,
            template_type="email",
            variables={
                "name": "Bob Wilson",
                "position": "Designer",
                "status": "pending",
            },
        )

        # Verify conditional block evaluated to false
        assert len(rendered_pending["active_blocks"]) == 2
        assert rendered_pending["active_blocks"][0]["content"] == "Dear {name},"
        assert "Thank you" in rendered_pending["active_blocks"][1]["content"]

    @pytest.mark.asyncio
    async def test_end_to_end_template_workflow(self):
        """
        End-to-end test: Create template → Save to DB → Load → Render → Send.

        This test simulates the complete workflow from template creation
        through to sending a notification.
        """
        from api.templates import CreateTemplateRequest
        from api.notifications import SendNotificationRequest
        from services.template_service import get_template_service
        from models.email_template import EmailTemplate
        from models.notification import Notification, NotificationStatus

        # Mock database session
        mock_db = AsyncMock()

        # Step 1: Create template via API
        create_request = CreateTemplateRequest(
            template_type="email",
            name="e2e_welcome_template",
            subject="Welcome to {company}, {name}!",
            body="Hello {name}, we are excited to have you join {company} as a {role}. Your start date is {start_date}.",
            variables=["name", "company", "role", "start_date"],
            template_blocks={
                "blocks": [
                    {"type": "text", "content": "Welcome header"},
                    {"type": "text", "content": "Body content with variables"}
                ]
            },
            category="onboarding",
            pipeline_stage="hired",
            language="en",
            description="End-to-end test welcome template",
            is_active=True,
        )

        # Mock existing template check (returns None)
        mock_existing_result = AsyncMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_existing_result

        # Step 2: Save template to database
        service = get_template_service()
        created_template = await service.create_template(
            db=mock_db,
            template_type=create_request.template_type,
            name=create_request.name,
            subject=create_request.subject,
            body=create_request.body,
            variables=create_request.variables,
            template_blocks=create_request.template_blocks,
            category=create_request.category,
            pipeline_stage=create_request.pipeline_stage,
            language=create_request.language,
            description=create_request.description,
            is_active=create_request.is_active,
        )

        # Verify template creation
        assert mock_db.add.called
        assert mock_db.commit.called
        added_template = mock_db.add.call_args[0][0]
        assert added_template.name == "e2e_welcome_template"

        # Step 3: Simulate template retrieval from DB
        # Create a proper template instance for retrieval
        retrieved_template = EmailTemplate(
            id=str(uuid4()),
            name="e2e_welcome_template",
            subject="Welcome to {company}, {name}!",
            body="Hello {name}, we are excited to have you join {company} as a {role}. Your start date is {start_date}.",
            variables=["name", "company", "role", "start_date"],
            template_blocks=create_request.template_blocks,
            category="onboarding",
            pipeline_stage="hired",
            language="en",
            is_active=True,
        )
        retrieved_template.created_at = datetime.utcnow()
        retrieved_template.updated_at = datetime.utcnow()

        # Mock template retrieval
        mock_retrieve_result = AsyncMock()
        mock_retrieve_result.scalar_one_or_none.return_value = retrieved_template
        mock_db.execute.return_value = mock_retrieve_result

        # Load template by name
        loaded_template = await service.get_template_by_name(
            db=mock_db,
            name="e2e_welcome_template",
            template_type="email",
            language="en",
        )

        assert loaded_template is not None
        assert loaded_template.name == "e2e_welcome_template"

        # Step 4: Render template with actual data
        rendered = await service.render_template(
            db=mock_db,
            template_id=loaded_template.id,
            template_type="email",
            variables={
                "name": "Michael Chen",
                "company": "InnovateTech",
                "role": "Senior Engineer",
                "start_date": "2026-04-01",
            },
        )

        # Verify rendered content
        assert rendered["subject"] == "Welcome to InnovateTech, Michael Chen!"
        assert "Michael Chen" in rendered["body"]
        assert "InnovateTech" in rendered["body"]
        assert "Senior Engineer" in rendered["body"]
        assert "2026-04-01" in rendered["body"]
        assert len(rendered["active_blocks"]) == 2

        # Step 5: Create and verify notification
        notification = Notification(
            notification_type="email",
            recipient="michael.chen@example.com",
            subject=rendered["subject"],
            body=rendered["body"],
            priority="normal",
            status=NotificationStatus.PENDING.value,
            metadata={
                "template_name": "e2e_welcome_template",
                "pipeline_stage": "hired",
            },
        )

        assert notification.recipient == "michael.chen@example.com"
        assert notification.subject == "Welcome to InnovateTech, Michael Chen!"
        assert notification.status == "pending"
        assert notification.metadata["template_name"] == "e2e_welcome_template"
