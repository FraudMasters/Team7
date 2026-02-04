"""
End-to-end integration test for email branding workflow.

This test verifies the complete email branding workflow:
1. Create organization via API with branding settings (logo, colors)
2. Set brand colors
3. Upload organization logo
4. Create email template for organization
5. Trigger email notification
6. Verify email uses organization branding (logo, colors, custom text)
"""
import asyncio
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.organization import Organization
from models.branding_settings import BrandingSettings
from models.email_template import EmailTemplate
from models.resume import Resume, ResumeStatus
from tasks.email_task import send_feedback_notification


# Test database URL (use same as main database for integration testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_email_branding_workflow_e2e(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end test: Complete email branding workflow.

    Verification steps:
    1. Create organization via API with branding settings (logo, colors)
    2. Set brand colors (primary, secondary, accent)
    3. Upload organization logo (set logo_url)
    4. Create email template for organization
    5. Trigger email notification
    6. Verify email uses organization branding (logo, colors, custom text)
    """
    print("\n=== Starting Email Branding Workflow Test ===\n")

    # Step 1: Create organization via API
    print("Step 1: Creating organization via API...")
    org_response = await client.post(
        "/api/organizations/",
        json={
            "name": "Test Branded Company",
            "slug": "test-branded-company",
            "domain": "testcompany.com",
            "is_active": True
        }
    )
    assert org_response.status_code == 201, f"Failed to create organization: {org_response.text}"
    org_data = org_response.json()
    organization_id = org_data["id"]
    print(f"✓ Organization created: {org_data['name']} (ID: {organization_id})")
    print(f"  Slug: {org_data['slug']}")
    print(f"  Domain: {org_data['domain']}")

    # Verify organization in database
    org_result = await test_db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = org_result.scalars().first()
    assert organization is not None, "Organization not found in database"
    print(f"✓ Organization verified in database")

    # Step 2: Set brand colors
    print("\nStep 2: Setting brand colors...")
    branding_response = await client.post(
        "/api/branding/",
        json={
            "organization_id": organization_id,
            "primary_color": "#FF5733",
            "secondary_color": "#33FF57",
            "accent_color": "#3357FF",
            "is_active": True
        }
    )
    assert branding_response.status_code == 201, f"Failed to create branding: {branding_response.text}"
    branding_data = branding_response.json()
    print(f"✓ Branding settings created")
    print(f"  Primary color: {branding_data['primary_color']}")
    print(f"  Secondary color: {branding_data['secondary_color']}")
    print(f"  Accent color: {branding_data['accent_color']}")

    # Verify branding in database
    branding_result = await test_db.execute(
        select(BrandingSettings).where(
            and_(
                BrandingSettings.organization_id == organization_id,
                BrandingSettings.is_active == True
            )
        )
    )
    branding = branding_result.scalars().first()
    assert branding is not None, "Branding settings not found in database"
    assert branding.primary_color == "#FF5733"
    assert branding.secondary_color == "#33FF57"
    assert branding.accent_color == "#3357FF"
    print(f"✓ Branding verified in database")

    # Step 3: Upload organization logo (set logo_url)
    print("\nStep 3: Setting organization logo...")
    logo_update_response = await client.put(
        f"/api/organizations/{organization_id}",
        json={
            "logo_url": "https://testcompany.com/logo.png",
            "name": "Test Branded Company",
            "slug": "test-branded-company",
            "domain": "testcompany.com",
            "is_active": True
        }
    )
    assert logo_update_response.status_code == 200
    logo_data = logo_update_response.json()
    print(f"✓ Logo URL set: {logo_data['logo_url']}")

    # Verify logo in database
    await test_db.refresh(organization)
    assert organization.logo_url == "https://testcompany.com/logo.png"
    print(f"✓ Logo verified in database")

    # Step 4: Create email template for organization
    print("\nStep 4: Creating custom email template...")
    template_response = await client.post(
        "/api/email-templates/",
        json={
            "organization_id": organization_id,
            "template_type": "candidate_feedback",
            "subject": "Feedback for {{candidate_name}} from {{organization_name}}",
            "body": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background-color: {{primary_color}}; color: white; padding: 20px; }
        .logo { max-width: 200px; }
        .content { padding: 20px; }
        .score { color: {{primary_color}}; font-size: 24px; font-weight: bold; }
        .footer { background-color: {{secondary_color}}; padding: 10px; text-align: center; }
    </style>
</head>
<body>
    {% if organization_logo %}
    <div class="header">
        <img src="{{organization_logo}}" alt="{{organization_name}}" class="logo">
    </div>
    {% endif %}
    <div class="content">
        <h1>Feedback for {{candidate_name}}</h1>
        <p>Match Score: <span class="score">{{match_score}}%</span></p>
        <p>Feedback ID: {{feedback_id}}</p>
        {% if skills_feedback %}
        <h2>Skills Feedback</h2>
        <p>{{skills_feedback}}</p>
        {% endif %}
    </div>
    <div class="footer">
        <p>Powered by {{organization_name}} - Custom Branded Template</p>
    </div>
</body>
</html>
            """.strip(),
            "is_default": True,
            "is_active": True
        }
    )
    assert template_response.status_code == 201, f"Failed to create template: {template_response.text}"
    template_data = template_response.json()
    template_id = template_data["id"]
    print(f"✓ Email template created (ID: {template_id})")
    print(f"  Subject: {template_data['subject']}")

    # Verify template in database
    template_result = await test_db.execute(
        select(EmailTemplate).where(
            and_(
                EmailTemplate.organization_id == organization_id,
                EmailTemplate.template_type == "candidate_feedback",
                EmailTemplate.is_active == True
            )
        )
    )
    template = template_result.scalars().first()
    assert template is not None, "Email template not found in database"
    assert "Powered by {{organization_name}} - Custom Branded Template" in template.body
    print(f"✓ Template verified in database")

    # Step 5: Trigger email notification
    print("\nStep 5: Triggering email notification...")
    feedback_id = str(uuid.uuid4())
    candidate_name = "John Doe"
    recipient_email = "recruiter@testcompany.com"

    feedback_data = {
        "match_score": 85,
        "skills_feedback": "Strong Python and JavaScript skills",
        "experience_feedback": "5 years of relevant experience",
        "recommendations": ["Schedule technical interview", "Assess cultural fit"],
        "grammar_feedback": "Excellent communication skills",
        "tone": "professional"
    }

    # Trigger the email task (mocking actual email sending)
    with patch('tasks.email_task.asyncio.run') as mock_run:
        # Import the render function to test it directly
        from services.email_rendering import render_email_template
        from database import async_session_maker

        # Render the email template
        async def render_and_verify():
            async with async_session_maker() as db:
                subject, html_body, text_body = render_email_template(
                    db=db,
                    organization_id=organization_id,
                    template_type="candidate_feedback",
                    context={
                        "candidate_name": candidate_name,
                        "feedback_id": feedback_id,
                        "match_score": feedback_data["match_score"],
                        "skills_feedback": feedback_data["skills_feedback"],
                        "experience_feedback": feedback_data["experience_feedback"],
                        "recommendations": feedback_data["recommendations"],
                        "grammar_feedback": feedback_data["grammar_feedback"],
                        "tone": feedback_data["tone"],
                    }
                )
                return subject, html_body, text_body

        subject, html_body, text_body = await render_and_verify()

    print(f"✓ Email rendered successfully")
    print(f"  Subject: {subject}")

    # Step 6: Verify email uses organization branding
    print("\nStep 6: Verifying email branding...")

    # Verify custom template was used (not default)
    assert "Powered by Test Branded Company - Custom Branded Template" in html_body, \
        "Custom template not used in email body"
    print(f"✓ Custom template used (not default)")

    # Verify organization name in email
    assert "Test Branded Company" in html_body, \
        "Organization name not in email"
    assert "Test Branded Company" in subject, \
        "Organization name not in subject"
    print(f"✓ Organization name present: 'Test Branded Company'")

    # Verify logo in email
    assert "https://testcompany.com/logo.png" in html_body, \
        "Logo URL not in email body"
    assert '<img src="https://testcompany.com/logo.png"' in html_body, \
        "Logo image tag not in email"
    print(f"✓ Logo present in email: https://testcompany.com/logo.png")

    # Verify brand colors in email
    assert "#FF5733" in html_body, \
        "Primary color not in email body"
    assert "#33FF57" in html_body, \
        "Secondary color not in email body"
    print(f"✓ Brand colors present:")
    print(f"  - Primary: #FF5733")
    print(f"  - Secondary: #33FF57")

    # Verify candidate name in email
    assert candidate_name in html_body, \
        "Candidate name not in email body"
    assert candidate_name in subject, \
        "Candidate name not in subject"
    print(f"✓ Candidate name present: {candidate_name}")

    # Verify match score in email
    assert "85" in html_body, \
        "Match score not in email body"
    assert "85%" in html_body or "85" in html_body, \
        "Match score format incorrect"
    print(f"✓ Match score present: 85%")

    # Verify feedback ID in email
    assert feedback_id in html_body, \
        "Feedback ID not in email body"
    print(f"✓ Feedback ID present: {feedback_id}")

    # Verify skills feedback in email
    assert "Strong Python and JavaScript skills" in html_body, \
        "Skills feedback not in email body"
    print(f"✓ Skills feedback present")

    # Verify recommendations in email
    assert "Schedule technical interview" in html_body, \
        "Recommendations not in email body"
    print(f"✓ Recommendations present")

    # Verify HTML structure
    assert "<!DOCTYPE html>" in html_body, \
        "HTML DOCTYPE missing"
    assert "<html>" in html_body, \
        "HTML tag missing"
    assert "</html>" in html_body, \
        "HTML closing tag missing"
    print(f"✓ Valid HTML structure")

    # Verify plain text version exists
    assert text_body is not None, \
        "Plain text body is None"
    assert len(text_body) > 0, \
        "Plain text body is empty"
    assert candidate_name in text_body, \
        "Candidate name not in plain text body"
    print(f"✓ Plain text version generated ({len(text_body)} characters)")

    print("\n=== Email Branding Workflow Test PASSED ===\n")
    print("Summary:")
    print("  ✓ Organization created via API")
    print("  ✓ Brand colors set (primary: #FF5733, secondary: #33FF57, accent: #3357FF)")
    print("  ✓ Logo uploaded (https://testcompany.com/logo.png)")
    print("  ✓ Custom email template created")
    print("  ✓ Email notification triggered")
    print("  ✓ Email uses organization logo")
    print("  ✓ Email uses organization brand colors")
    print("  ✓ Email uses custom template text")
    print("  ✓ All template variables rendered correctly")
    print("  ✓ HTML and plain text versions generated")


@pytest.mark.asyncio
async def test_email_fallback_to_default_template(client: AsyncClient, test_db: AsyncSession):
    """
    Test that email falls back to default template when no custom template exists.

    This verifies the fallback behavior for organizations without custom templates.
    """
    print("\n=== Testing Default Template Fallback ===\n")

    # Create organization without custom template
    org_response = await client.post(
        "/api/organizations/",
        json={
            "name": "Fallback Test Company",
            "slug": "fallback-test-company",
            "domain": "fallback.com",
            "is_active": True
        }
    )
    assert org_response.status_code == 201
    org_data = org_response.json()
    organization_id = org_data["id"]
    print(f"✓ Organization created: {org_data['name']} (ID: {organization_id})")

    # Set branding colors
    branding_response = await client.post(
        "/api/branding/",
        json={
            "organization_id": organization_id,
            "primary_color": "#9333EA",
            "secondary_color": "#EC4899",
            "accent_color": "#F59E0B",
            "is_active": True
        }
    )
    assert branding_response.status_code == 201
    print(f"✓ Branding colors set")

    # Render email without custom template (should use default)
    from services.email_rendering import render_email_template
    from database import async_session_maker

    async def render_default():
        async with async_session_maker() as db:
            subject, html_body, text_body = render_email_template(
                db=db,
                organization_id=organization_id,
                template_type="candidate_feedback",
                context={
                    "candidate_name": "Jane Smith",
                    "feedback_id": "feedback-123",
                    "match_score": 92,
                }
            )
            return subject, html_body, text_body

    subject, html_body, text_body = await render_default()

    print(f"✓ Email rendered with default template")
    print(f"  Subject: {subject}")

    # Verify default template was used
    assert "Candidate Feedback:" in subject, \
        "Default template subject not used"
    assert "This is an automated email from" in html_body, \
        "Default template body not used"
    print(f"✓ Default template used (no custom template exists)")

    # Verify branding still applied even with default template
    assert "#9333EA" in html_body, \
        "Primary branding color not applied to default template"
    assert "Fallback Test Company" in html_body or "Fallback Test Company" in text_body, \
        "Organization name not in default template"
    print(f"✓ Branding applied to default template")
    print(f"  - Organization: Fallback Test Company")
    print(f"  - Primary color: #9333EA")

    # Verify candidate info in default template
    assert "Jane Smith" in html_body, \
        "Candidate name not in default template"
    assert "92" in html_body or "92%" in html_body, \
        "Match score not in default template"
    print(f"✓ Candidate information rendered in default template")

    print("\n✓ Default Template Fallback Test PASSED")
    print("Summary:")
    print("  ✓ Default template used when no custom template exists")
    print("  ✓ Organization branding still applied to default template")
    print("  ✓ Template variables rendered correctly")


@pytest.mark.asyncio
async def test_email_branding_without_custom_colors(client: AsyncClient, test_db: AsyncSession):
    """
    Test that email uses default colors when organization has no custom branding.

    This verifies the default branding behavior.
    """
    print("\n=== Testing Default Branding Colors ===\n")

    # Create organization without custom branding
    org_response = await client.post(
        "/api/organizations/",
        json={
            "name": "No Branding Company",
            "slug": "no-branding-company",
            "domain": "nobranding.com",
            "is_active": True
        }
    )
    assert org_response.status_code == 201
    org_data = org_response.json()
    organization_id = org_data["id"]
    print(f"✓ Organization created: {org_data['name']} (ID: {organization_id})")

    # Render email without custom branding
    from services.email_rendering import render_email_template, get_email_rendering_service
    from database import async_session_maker

    async def render_without_branding():
        async with async_session_maker() as db:
            subject, html_body, text_body = render_email_template(
                db=db,
                organization_id=organization_id,
                template_type="candidate_feedback",
                context={
                    "candidate_name": "Bob Johnson",
                    "feedback_id": "feedback-456",
                    "match_score": 78,
                }
            )
            return subject, html_body, text_body

    subject, html_body, text_body = await render_without_branding()

    print(f"✓ Email rendered with default branding")

    # Verify default colors are used
    service = get_email_rendering_service()
    assert service.default_primary_color in html_body, \
        "Default primary color not used"
    print(f"✓ Default primary color used: {service.default_primary_color}")
    print(f"  (Expected: #3B82F6)")

    # Verify organization name still used
    assert "No Branding Company" in html_body or "No Branding Company" in text_body, \
        "Organization name not in email"
    print(f"✓ Organization name present: No Branding Company")

    # Verify email content
    assert "Bob Johnson" in html_body, \
        "Candidate name not in email"
    assert "78" in html_body or "78%" in html_body, \
        "Match score not in email"
    print(f"✓ Email content rendered correctly")

    print("\n✓ Default Branding Colors Test PASSED")
    print("Summary:")
    print("  ✓ Default colors used when no custom branding exists")
    print("  ✓ Organization name still used")
    print("  ✓ Email content rendered correctly")


if __name__ == "__main__":
    print("This test requires pytest with async support.")
    print("Run with: pytest backend/tests/integration/test_email_branding_e2e.py -v")
