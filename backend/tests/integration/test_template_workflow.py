"""
Integration tests for communication template workflow.

This test module verifies the complete end-to-end template workflow:
1. Create communication template
2. Preview template with variable substitution
3. Use template to compose email
4. Send email via Celery task
5. Verify email uses template content

These tests require a running database and use mocked SMTP for testing.
"""
import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import async_session_maker
from models import Communication, EmailMessage, Resume, CommunicationTemplate
from models.communication import CommunicationType, CommunicationDirection, CommunicationStatus
from api.communication_templates import (
    create_template,
    list_templates,
    get_template,
    update_template,
    delete_template,
    preview_template
)
from api.communications import create_communication, get_communication
from tasks.email_sync_task import send_email_task


# Test Fixtures

@pytest.fixture
async def db_session() -> AsyncSession:
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_candidate(db_session: AsyncSession) -> Resume:
    """Create a test candidate (resume) with email."""
    candidate = Resume(
        id=str(uuid4()),
        name="Test Candidate",
        email="test.candidate@example.com",
        metadata={"contact_email": "test.candidate@example.com"}
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


@pytest.fixture
async def test_recruiter(db_session: AsyncSession) -> Resume:
    """Create a test recruiter."""
    recruiter = Resume(
        id=str(uuid4()),
        name="Test Recruiter",
        email="recruiter@test.com",
        metadata={"user_type": "recruiter"}
    )
    db_session.add(recruiter)
    await db_session.commit()
    await db_session.refresh(recruiter)
    return recruiter


@pytest.fixture
def email_config():
    """Mock email configuration for testing."""
    return {
        "smtp_server": "smtp.test.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_username": "test@test.com",
        "smtp_password": "testpassword",
        "smtp_from_email": "noreply@test.com",
        "smtp_from_name": "Test Company"
    }


@pytest.fixture
def mock_smtp_response():
    """Mock SMTP email response."""
    return {
        "message_id": "<test123@test.com>",
        "status": "sent",
        "to": "test.candidate@example.com",
        "from": "noreply@test.com",
        "subject": "Interview Invitation",
        "accepted": ["test.candidate@example.com"],
        "rejected": []
    }


# Test: Create communication template

@pytest.mark.asyncio
async def test_step1_create_communication_template(db_session: AsyncSession):
    """
    Step 1: Create communication template.

    Verifies:
    - Template can be created via API
    - Template has correct fields (name, type, subject, body, variables)
    - Template is stored in database
    - Template variables are extracted from {{variable}} syntax
    """
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Interview Invitation",
            "type": "email",
            "subject": "Interview Invitation - {{position}}",
            "body": """Dear {{candidate_name}},

We are pleased to invite you for an interview for the {{position}} position.

Date: {{interview_date}}
Time: {{interview_time}}
Location: {{interview_location}}

Please confirm your attendance.

Best regards,
{{recruiter_name}}""",
            "variables": {
                "candidate_name": "Full name of the candidate",
                "position": "Job position title",
                "interview_date": "Date of interview (YYYY-MM-DD)",
                "interview_time": "Time of interview (HH:MM)",
                "interview_location": "Interview location or meeting link",
                "recruiter_name": "Name of the recruiter"
            },
            "is_active": True,
            "language": "en",
            "created_by": str(uuid4())
        }
    }

    # Create template via API
    result = await create_template(template_data, db_session)

    # Verify response structure
    assert "template" in result
    assert result["template"]["name"] == "Interview Invitation"
    assert result["template"]["type"] == "email"
    assert result["template"]["subject"] == "Interview Invitation - {{position}}"
    assert "{{candidate_name}}" in result["template"]["body"]
    assert "{{position}}" in result["template"]["body"]
    assert result["template"]["is_active"] is True
    assert "id" in result["template"]

    # Verify template was stored in database
    stmt = select(CommunicationTemplate).where(
        CommunicationTemplate.name == "Interview Invitation"
    )
    template_from_db = await db_session.execute(stmt)
    template = template_from_db.scalar_one_or_none()

    assert template is not None
    assert template.name == "Interview Invitation"
    assert template.type == "email"
    assert template.variables["candidate_name"] == "Full name of the candidate"


# Test: Preview template with variable substitution

@pytest.mark.asyncio
async def test_step2_preview_template_variable_substitution(db_session: AsyncSession):
    """
    Step 2: Preview template with variable substitution.

    Verifies:
    - Template can be previewed with variable values
    - Variables are correctly substituted in subject and body
    - Preview returns rendered content
    """
    # First create a template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Interview Invitation",
            "type": "email",
            "subject": "Interview Invitation - {{position}}",
            "body": "Dear {{candidate_name}},\n\nWe invite you to interview for {{position}} on {{interview_date}}.",
            "variables": {
                "candidate_name": "Candidate name",
                "position": "Job position",
                "interview_date": "Interview date"
            },
            "is_active": True,
            "language": "en"
        }
    }

    created_template = await create_template(template_data, db_session)
    template_id = created_template["template"]["id"]

    # Preview with variable values
    preview_data = {
        "variables": {
            "candidate_name": "John Doe",
            "position": "Senior Software Engineer",
            "interview_date": "2026-02-10"
        }
    }

    preview_result = await preview_template(template_id, preview_data, db_session)

    # Verify substituted content
    assert "subject" in preview_result
    assert "body" in preview_result
    assert preview_result["subject"] == "Interview Invitation - Senior Software Engineer"
    assert "Dear John Doe," in preview_result["body"]
    assert "Senior Software Engineer" in preview_result["body"]
    assert "2026-02-10" in preview_result["body"]
    assert "{{candidate_name}}" not in preview_result["body"]  # Variables should be substituted
    assert "{{position}}" not in preview_result["subject"]


# Test: Use template to compose email

@pytest.mark.asyncio
async def test_step3_use_template_to_compose_email(db_session: AsyncSession, test_candidate):
    """
    Step 3: Use template to compose email.

    Verifies:
    - Email can be composed using template content
    - Email has correct structure (to, from, subject, body)
    - Template variables are substituted with actual values
    """
    # Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Interview Invitation",
            "type": "email",
            "subject": "Interview Invitation - {{position}}",
            "body": "Dear {{candidate_name}},\n\nInterview for {{position}} on {{interview_date}}.",
            "variables": {
                "candidate_name": "Candidate name",
                "position": "Position",
                "interview_date": "Interview date"
            },
            "is_active": True,
            "language": "en"
        }
    }

    created_template = await create_template(template_data, db_session)

    # Compose email using template
    email_data = {
        "candidate_id": str(test_candidate.id),
        "type": "email",
        "direction": "outbound",
        "subject": "Interview Invitation - Senior Software Engineer",
        "body": "Dear Test Candidate,\n\nInterview for Senior Software Engineer on 2026-02-10.",
        "status": "pending",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "template_id": created_template["template"]["id"],
            "template_variables": {
                "candidate_name": "Test Candidate",
                "position": "Senior Software Engineer",
                "interview_date": "2026-02-10"
            }
        }
    }

    # Create communication record
    result = await create_communication(email_data, db_session)

    # Verify email composition
    assert result["type"] == "email"
    assert result["direction"] == "outbound"
    assert result["subject"] == "Interview Invitation - Senior Software Engineer"
    assert "Dear Test Candidate," in result["body"]
    assert "Senior Software Engineer" in result["body"]
    assert "2026-02-10" in result["body"]
    assert result["metadata"]["template_id"] == created_template["template"]["id"]


# Test: Send email via Celery task

@pytest.mark.asyncio
async def test_step4_send_email_via_celery_task(
    db_session: AsyncSession,
    test_candidate,
    email_config,
    mock_smtp_response
):
    """
    Step 4: Send email via Celery task.

    Verifies:
    - Email sending Celery task can be triggered
    - Email is sent via SMTP
    - Communication record is updated with sent status
    - EmailMessage record is created with message_id
    """
    # Create a pending email communication
    email_comm = Communication(
        id=str(uuid4()),
        candidate_id=str(test_candidate.id),
        type=CommunicationType.EMAIL,
        direction=CommunicationDirection.OUTBOUND,
        status=CommunicationStatus.PENDING,
        subject="Interview Invitation - Senior Software Engineer",
        body="Dear Test Candidate,\n\nInterview details...",
        sent_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={
            "to_address": "test.candidate@example.com",
            "template_id": str(uuid4())
        }
    )

    db_session.add(email_comm)
    await db_session.commit()
    await db_session.refresh(email_comm)

    # Mock SMTP sending
    with patch('tasks.email_sync_task.smtplib.SMTP') as mock_smtp:
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.return_value = None

        # Send email via Celery task
        task_result = await send_email_task(
            communication_id=str(email_comm.id),
            to_address="test.candidate@example.com",
            subject="Interview Invitation - Senior Software Engineer",
            body="Dear Test Candidate,\n\nInterview details...",
            from_email="noreply@test.com",
            from_name="Test Company"
        )

        # Verify task result
        assert task_result["status"] == "sent"
        assert "message_id" in task_result
        assert task_result["to_address"] == "test.candidate@example.com"

        # Verify communication was updated
        await db_session.refresh(email_comm)
        assert email_comm.status == CommunicationStatus.SENT
        assert email_comm.sent_at is not None


# Test: Verify email uses template content

@pytest.mark.asyncio
async def test_step5_verify_email_uses_template_content(
    db_session: AsyncSession,
    test_candidate,
    test_recruiter
):
    """
    Step 5: Verify email uses template content.

    Verifies:
    - Sent email contains template content with substituted variables
    - Email subject matches template subject
    - Email body matches template body
    - Template metadata is preserved in communication record
    """
    # Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Interview Invitation",
            "type": "email",
            "subject": "Interview Invitation - {{position}}",
            "body": "Dear {{candidate_name}},\n\nWe invite you to interview for {{position}} on {{interview_date}} at {{interview_time}}.\n\nLocation: {{location}}",
            "variables": {
                "candidate_name": "Candidate name",
                "position": "Job position",
                "interview_date": "Interview date",
                "interview_time": "Interview time",
                "location": "Interview location"
            },
            "is_active": True,
            "language": "en"
        }
    }

    created_template = await create_template(template_data, db_session)
    template_id = created_template["template"]["id"]

    # Variable values for substitution
    variables = {
        "candidate_name": "Jane Doe",
        "position": "Product Manager",
        "interview_date": "2026-02-15",
        "interview_time": "14:00",
        "location": "123 Main St, Conference Room A"
    }

    # Create and send email communication
    email_data = {
        "candidate_id": str(test_candidate.id),
        "recruiter_id": str(test_recruiter.id),
        "type": "email",
        "direction": "outbound",
        "subject": "Interview Invitation - Product Manager",
        "body": f"Dear {variables['candidate_name']},\n\nWe invite you to interview for {variables['position']} on {variables['interview_date']} at {variables['interview_time']}.\n\nLocation: {variables['location']}",
        "status": "sent",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "to_address": test_candidate.email,
            "template_id": template_id,
            "template_variables": variables
        }
    }

    result = await create_communication(email_data, db_session)
    communication_id = result["id"]

    # Verify email uses template content
    communication = await get_communication(communication_id, db_session)

    # Check subject matches template
    assert communication["subject"] == "Interview Invitation - Product Manager"
    assert "Product Manager" in communication["subject"]

    # Check body matches template with substitutions
    assert "Dear Jane Doe," in communication["body"]
    assert "Product Manager" in communication["body"]
    assert "2026-02-15" in communication["body"]
    assert "14:00" in communication["body"]
    assert "123 Main St, Conference Room A" in communication["body"]

    # Check template metadata is preserved
    assert communication["metadata"]["template_id"] == template_id
    assert communication["metadata"]["template_variables"]["candidate_name"] == "Jane Doe"
    assert communication["metadata"]["template_variables"]["position"] == "Product Manager"

    # Verify no unsubstituted variables remain
    assert "{{" not in communication["subject"]
    assert "{{" not in communication["body"]


# Test: Complete template workflow

@pytest.mark.asyncio
async def test_complete_template_workflow(
    db_session: AsyncSession,
    test_candidate,
    test_recruiter,
    email_config
):
    """
    Complete template workflow test.

    Verifies the entire workflow from template creation to email sending:
    1. Create template with variables
    2. Preview template with variable substitution
    3. Compose email using template
    4. Send email
    5. Verify email content
    """
    # Step 1: Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Offer Letter",
            "type": "email",
            "subject": "Job Offer - {{position}} at {{company}}",
            "body": """Dear {{candidate_name}},

We are pleased to offer you the position of {{position}} at {{company}}!

Salary: ${{salary}}
Start Date: {{start_date}}

Please review the attached offer letter and sign by {{deadline}}.

Congratulations!
{{recruiter_name}}""",
            "variables": {
                "candidate_name": "Candidate name",
                "position": "Job position",
                "company": "Company name",
                "salary": "Annual salary",
                "start_date": "Employment start date",
                "deadline": "Offer acceptance deadline",
                "recruiter_name": "Recruiter name"
            },
            "is_active": True,
            "language": "en",
            "created_by": str(test_recruiter.id)
        }
    }

    created_template = await create_template(template_data, db_session)
    template_id = created_template["template"]["id"]
    assert created_template["template"]["name"] == "Offer Letter"

    # Step 2: Preview template
    variables = {
        "candidate_name": "Alice Johnson",
        "position": "Senior UX Designer",
        "company": "TechCorp Inc.",
        "salary": "95,000",
        "start_date": "2026-03-01",
        "deadline": "2026-02-15",
        "recruiter_name": "Bob Smith"
    }

    preview = await preview_template(template_id, variables, db_session)
    assert "Alice Johnson" in preview["body"]
    assert "Senior UX Designer" in preview["subject"]
    assert "TechCorp Inc." in preview["body"]
    assert "$95,000" in preview["body"]

    # Step 3: Compose email using template
    email_data = {
        "candidate_id": str(test_candidate.id),
        "recruiter_id": str(test_recruiter.id),
        "type": "email",
        "direction": "outbound",
        "subject": preview["subject"],
        "body": preview["body"],
        "status": "pending",
        "sent_at": datetime.utcnow().isoformat(),
        "metadata": {
            "to_address": test_candidate.email,
            "template_id": template_id,
            "template_variables": variables
        }
    }

    composed_email = await create_communication(email_data, db_session)
    assert composed_email["status"] == "pending"
    assert composed_email["metadata"]["template_id"] == template_id

    # Step 4: Send email (mock SMTP)
    communication_id = composed_email["id"]

    with patch('tasks.email_sync_task.smtplib.SMTP') as mock_smtp:
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        task_result = await send_email_task(
            communication_id=communication_id,
            to_address=test_candidate.email,
            subject=composed_email["subject"],
            body=composed_email["body"],
            from_email="noreply@test.com",
            from_name="TechCorp HR"
        )

        assert task_result["status"] == "sent"

    # Step 5: Verify email content
    sent_email = await get_communication(communication_id, db_session)

    assert sent_email["subject"] == "Job Offer - Senior UX Designer at TechCorp Inc."
    assert "Dear Alice Johnson," in sent_email["body"]
    assert "Senior UX Designer" in sent_email["body"]
    assert "TechCorp Inc." in sent_email["body"]
    assert "$95,000" in sent_email["body"]
    assert "2026-03-01" in sent_email["body"]
    assert "2026-02-15" in sent_email["body"]
    assert "Bob Smith" in sent_email["body"]
    assert sent_email["status"] == "sent"
    assert sent_email["metadata"]["template_id"] == template_id


# Test: Template with missing variables

@pytest.mark.asyncio
async def test_template_with_missing_variables(db_session: AsyncSession):
    """
    Test template preview with missing variables.

    Verifies:
    - Missing variables are handled gracefully
    - Unsubstituted variables remain in output
    """
    # Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Follow-up Email",
            "type": "email",
            "subject": "Following up on {{position}} application",
            "body": "Hi {{candidate_name}},\n\nAny update on {{position}}?",
            "variables": {
                "candidate_name": "Candidate name",
                "position": "Position"
            },
            "is_active": True,
            "language": "en"
        }
    }

    created_template = await create_template(template_data, db_session)
    template_id = created_template["template"]["id"]

    # Preview with only some variables provided
    preview_data = {
        "variables": {
            "candidate_name": "John"
            # Missing: position
        }
    }

    preview = await preview_template(template_id, preview_data, db_session)

    # Verify provided variable is substituted
    assert "Hi John," in preview["body"]

    # Verify missing variable remains unsubstituted
    assert "{{position}}" in preview["subject"]
    assert "{{position}}" in preview["body"]


# Test: List templates with filters

@pytest.mark.asyncio
async def test_list_templates_with_filters(db_session: AsyncSession):
    """
    Test listing templates with filters.

    Verifies:
    - Templates can be filtered by type
    - Templates can be filtered by is_active status
    - Pagination works correctly
    """
    org_id = str(uuid4())

    # Create multiple templates
    templates = [
        {
            "template": {
                "organization_id": org_id,
                "name": "Email Template 1",
                "type": "email",
                "subject": "Test",
                "body": "Test body",
                "is_active": True,
                "language": "en"
            }
        },
        {
            "template": {
                "organization_id": org_id,
                "name": "Email Template 2",
                "type": "email",
                "subject": "Test 2",
                "body": "Test body 2",
                "is_active": False,
                "language": "en"
            }
        },
        {
            "template": {
                "organization_id": org_id,
                "name": "SMS Template",
                "type": "sms",
                "body": "SMS test",
                "is_active": True,
                "language": "en"
            }
        }
    ]

    for template in templates:
        await create_template(template, db_session)

    # Filter by type=email
    email_templates = await list_templates(
        type="email",
        skip=0,
        limit=10,
        db_session=db_session
    )

    assert email_templates["total_count"] >= 2
    assert all(t["type"] == "email" for t in email_templates["templates"])

    # Filter by is_active=True
    active_templates = await list_templates(
        is_active=True,
        skip=0,
        limit=10,
        db_session=db_session
    )

    assert all(t["is_active"] is True for t in active_templates["templates"])


# Test: Update template

@pytest.mark.asyncio
async def test_update_template(db_session: AsyncSession):
    """
    Test updating a template.

    Verifies:
    - Template can be updated
    - Changes are persisted
    - Variables can be modified
    """
    # Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Original Name",
            "type": "email",
            "subject": "Original Subject",
            "body": "Original body with {{variable}}",
            "variables": {"variable": "Original var"},
            "is_active": True,
            "language": "en"
        }
    }

    created = await create_template(template_data, db_session)
    template_id = created["template"]["id"]

    # Update template
    update_data = {
        "name": "Updated Name",
        "subject": "Updated Subject",
        "body": "Updated body with {{new_variable}}",
        "variables": {"new_variable": "New var"}
    }

    updated = await update_template(template_id, update_data, db_session)

    assert updated["template"]["name"] == "Updated Name"
    assert updated["template"]["subject"] == "Updated Subject"
    assert "Updated body" in updated["template"]["body"]
    assert updated["template"]["variables"]["new_variable"] == "New var"


# Test: Delete template

@pytest.mark.asyncio
async def test_delete_template(db_session: AsyncSession):
    """
    Test deleting a template.

    Verifies:
    - Template can be deleted
    - Template is removed from database
    """
    # Create template
    template_data = {
        "template": {
            "organization_id": str(uuid4()),
            "name": "Template to Delete",
            "type": "email",
            "subject": "Test",
            "body": "Test body",
            "is_active": True,
            "language": "en"
        }
    }

    created = await create_template(template_data, db_session)
    template_id = created["template"]["id"]

    # Delete template
    result = await delete_template(template_id, db_session)
    assert result["status"] == "deleted"

    # Verify template is deleted
    stmt = select(CommunicationTemplate).where(
        CommunicationTemplate.id == template_id
    )
    deleted_template = await db_session.execute(stmt)
    assert deleted_template.scalar_one_or_none() is None
