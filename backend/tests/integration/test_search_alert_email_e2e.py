"""
End-to-end verification of search alert email flow.

This test suite verifies the complete flow:
1. Create saved search with recruiter_id
2. Upload matching resume
3. Verify search alert is created
4. Verify email notification task is triggered
5. Verify email is sent successfully
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

from main import app
from database import get_db
from models.resume import Resume, ResumeStatus
from models.saved_search import SavedSearch
from models.search_alert import SearchAlert
from models.recruiter import Recruiter
from models.resume_analysis import ResumeAnalysis
from tasks.search_alerts_task import (
    check_resume_against_saved_searches,
    send_search_alert_notification,
    process_pending_alerts,
)


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_search_alerts_email_e2e.db"


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
async def test_e2e_search_alert_email_flow_with_recruiter(client: AsyncClient, test_db: AsyncSession):
    """
    End-to-end verification of search alert email flow.

    Steps:
    1. Create a recruiter with is_active=True
    2. Create saved search with recruiter_id
    3. Upload matching resume (create in DB)
    4. Trigger check_resume_against_saved_searches
    5. Verify search alert is created
    6. Verify email notification task gets recruiter email
    7. Verify email is sent successfully
    """
    # Step 1: Create a recruiter
    recruiter = Recruiter(
        name="Test Recruiter",
        email="test-recruiter@example.com",
        department="Engineering",
        is_active=True,
    )
    test_db.add(recruiter)
    await test_db.commit()
    await test_db.refresh(recruiter)

    assert recruiter.id is not None
    assert recruiter.email == "test-recruiter@example.com"
    assert recruiter.is_active is True

    # Step 2: Create saved search with recruiter_id
    saved_search = SavedSearch(
        name="Senior Python Developers",
        query="Python AND Django",
        filters={
            "skills": ["Python", "Django", "FastAPI"],
            "min_experience_years": 5,
            "location": "Remote",
        },
        recruiter_id=recruiter.id,
    )
    test_db.add(saved_search)
    await test_db.commit()
    await test_db.refresh(saved_search)

    assert saved_search.recruiter_id == recruiter.id

    # Step 3: Create matching resume with analysis
    resume = Resume(
        filename="john_developer.pdf",
        file_path="/test/john.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Experienced Python developer with 5 years of experience in FastAPI and Django",
    )
    test_db.add(resume)

    # Create resume analysis with skills
    resume_analysis = ResumeAnalysis(
        resume_id=resume.id,
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker"],
        entities={
            "persons": ["John Developer"],
            "emails": ["john@example.com"],
        },
        experience_years=5,
        language="en",
    )
    test_db.add(resume_analysis)
    await test_db.commit()
    await test_db.refresh(resume)

    # Step 4: Trigger search alert checking
    resume_data = {
        "skills": ["Python", "Django", "FastAPI"],
        "experience_years": 5,
        "location": "Remote",
        "education": "Bachelor's",
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    # Step 5: Verify search alert is created
    assert result["status"] == "completed"
    assert result["matches_found"] == 1
    assert result["alerts_created"] == 1

    # Verify alert in database
    stmt = select(SearchAlert).where(
        SearchAlert.saved_search_id == saved_search.id,
        SearchAlert.resume_id == resume.id
    )
    alert_result = await test_db.execute(stmt)
    alert = alert_result.scalar_one_or_none()

    assert alert is not None
    assert alert.is_sent is False
    assert alert.saved_search_id == saved_search.id
    assert alert.resume_id == resume.id

    # Step 6: Send notification and verify email is triggered with recruiter email
    # Mock the email task to capture the call
    with patch('tasks.search_alerts_task.send_search_alert_email_task') as mock_email_task:
        mock_email_task.delay = Mock(return_value=Mock(id="task-123"))

        notification_result = send_search_alert_notification(
            alert_id=str(alert.id),
        )

        # Verify the email task was called with recruiter email
        mock_email_task.delay.assert_called_once()
        call_kwargs = mock_email_task.delay.call_args[1]

        assert call_kwargs["recipient_email"] == "test-recruiter@example.com"
        assert call_kwargs["candidate_name"] == "John Developer"
        assert "Python" in call_kwargs["matched_skills"]
        assert call_kwargs["saved_search_name"] == "Senior Python Developers"
        assert call_kwargs["match_score"] > 50

    # Step 7: Verify alert is marked as sent
    await test_db.refresh(alert)
    assert alert.is_sent is True
    assert alert.sent_at is not None
    assert alert.error_message is None


@pytest.mark.asyncio
async def test_e2e_search_alert_flow_inactive_recruiter(client: AsyncClient, test_db: AsyncSession):
    """
    Verify that inactive recruiters don't receive alerts.
    """
    # Create an INACTIVE recruiter
    recruiter = Recruiter(
        name="Inactive Recruiter",
        email="inactive@example.com",
        department="Engineering",
        is_active=False,  # Inactive!
    )
    test_db.add(recruiter)
    await test_db.commit()
    await test_db.refresh(recruiter)

    # Create saved search with inactive recruiter
    saved_search = SavedSearch(
        name="Java Developers",
        query="Java",
        filters={"skills": ["Java"]},
        recruiter_id=recruiter.id,
    )
    test_db.add(saved_search)
    await test_db.commit()

    # Create matching resume
    resume = Resume(
        filename="java_dev.pdf",
        file_path="/test/java.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Java developer",
    )
    test_db.add(resume)
    await test_db.commit()

    # Trigger alert checking
    resume_data = {
        "skills": ["Java"],
        "experience_years": 3,
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    # Verify alert is created
    assert result["alerts_created"] == 1

    stmt = select(SearchAlert).where(SearchAlert.resume_id == resume.id)
    alert_result = await test_db.execute(stmt)
    alert = alert_result.scalar_one_or_none()

    # Try to send notification - should fail for inactive recruiter
    with patch('tasks.search_alerts_task.send_search_alert_email_task') as mock_email_task:
        notification_result = send_search_alert_notification(
            alert_id=str(alert.id),
        )

        # Email task should NOT be called for inactive recruiter
        mock_email_task.delay.assert_not_called()
        assert notification_result["status"] == "failed"
        assert "not active" in notification_result["error"]


@pytest.mark.asyncio
async def test_e2e_search_alert_flow_no_recruiter_id(client: AsyncClient, test_db: AsyncSession):
    """
    Verify that saved searches without recruiter_id don't send emails.
    """
    # Create saved search WITHOUT recruiter_id
    saved_search = SavedSearch(
        name="Go Developers",
        query="Go",
        filters={"skills": ["Go"]},
        recruiter_id=None,  # No recruiter!
    )
    test_db.add(saved_search)
    await test_db.commit()

    # Create matching resume
    resume = Resume(
        filename="go_dev.pdf",
        file_path="/test/go.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Go developer",
    )
    test_db.add(resume)
    await test_db.commit()

    # Trigger alert checking
    resume_data = {
        "skills": ["Go"],
        "experience_years": 2,
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    # Verify alert is created
    assert result["alerts_created"] == 1

    stmt = select(SearchAlert).where(SearchAlert.resume_id == resume.id)
    alert_result = await test_db.execute(stmt)
    alert = alert_result.scalar_one_or_none()

    # Try to send notification - should fail for missing recruiter_id
    with patch('tasks.search_alerts_task.send_search_alert_email_task') as mock_email_task:
        notification_result = send_search_alert_notification(
            alert_id=str(alert.id),
        )

        # Email task should NOT be called when no recruiter_id
        mock_email_task.delay.assert_not_called()
        assert notification_result["status"] == "failed"
        assert "no recruiter_id" in notification_result["error"]


@pytest.mark.asyncio
async def test_e2e_process_pending_alerts_with_recruiter(client: AsyncClient, test_db: AsyncSession):
    """
    Verify processing pending alerts includes recruiter lookup.
    """
    # Create recruiter
    recruiter = Recruiter(
        name="Test Recruiter 2",
        email="recruiter2@example.com",
        department="Engineering",
        is_active=True,
    )
    test_db.add(recruiter)
    await test_db.commit()
    await test_db.refresh(recruiter)

    # Create saved search
    saved_search = SavedSearch(
        name="React Developers",
        query="React",
        filters={"skills": ["React", "TypeScript"]},
        recruiter_id=recruiter.id,
    )
    test_db.add(saved_search)
    await test_db.commit()

    # Create resume
    resume = Resume(
        filename="react_dev.pdf",
        file_path="/test/react.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="React developer",
    )
    test_db.add(resume)
    await test_db.commit()

    # Create pending alert manually (is_sent=False)
    alert = SearchAlert(
        saved_search_id=saved_search.id,
        resume_id=resume.id,
        is_sent=False,
    )
    test_db.add(alert)
    await test_db.commit()

    # Process pending alerts with mocked notification task
    with patch('tasks.search_alerts_task.send_search_alert_notification') as mock_notify:
        mock_notify.delay = Mock(return_value=Mock(id="task-456"))

        result = process_pending_alerts(batch_size=50)

        # Verify notification task was triggered
        mock_notify.delay.assert_called_once()
        call_args = mock_notify.delay.call_args[0]

        # Should be called with alert_id
        assert str(alert.id) in call_args


@pytest.mark.asyncio
async def test_e2e_multiple_recruiters_different_matches(client: AsyncClient, test_db: AsyncSession):
    """
    Verify that different recruiters get alerts for their respective saved searches.
    """
    # Create two recruiters
    recruiter1 = Recruiter(
        name="Alice Recruiter",
        email="alice@example.com",
        department="Engineering",
        is_active=True,
    )
    recruiter2 = Recruiter(
        name="Bob Recruiter",
        email="bob@example.com",
        department="Engineering",
        is_active=True,
    )
    test_db.add(recruiter1)
    test_db.add(recruiter2)
    await test_db.commit()
    await test_db.refresh(recruiter1)
    await test_db.refresh(recruiter2)

    # Create saved searches for each recruiter
    saved_search1 = SavedSearch(
        name="Python Developers",
        query="Python",
        filters={"skills": ["Python"]},
        recruiter_id=recruiter1.id,
    )
    saved_search2 = SavedSearch(
        name="Java Developers",
        query="Java",
        filters={"skills": ["Java"]},
        recruiter_id=recruiter2.id,
    )
    test_db.add(saved_search1)
    test_db.add(saved_search2)
    await test_db.commit()

    # Create resume matching both searches (full-stack dev)
    resume = Resume(
        filename="fullstack.pdf",
        file_path="/test/fullstack.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Full-stack developer with Python and Java",
    )
    test_db.add(resume)
    await test_db.commit()

    # Trigger alert checking
    resume_data = {
        "skills": ["Python", "Java"],
        "experience_years": 5,
        "raw_text": resume.raw_text,
    }

    result = check_resume_against_saved_searches(
        resume_id=str(resume.id),
        resume_data=resume_data,
    )

    # Verify 2 alerts created (one for each recruiter)
    assert result["alerts_created"] == 2

    # Get all alerts for this resume
    stmt = select(SearchAlert, SavedSearch, Recruiter).join(
        SavedSearch, SearchAlert.saved_search_id == SavedSearch.id
    ).join(
        Recruiter, SavedSearch.recruiter_id == Recruiter.id
    ).where(SearchAlert.resume_id == resume.id)

    alert_result = await test_db.execute(stmt)
    alerts = alert_result.all()

    # Verify we have 2 alerts for 2 different recruiters
    assert len(alerts) == 2
    recruiter_emails = {alert[2].email for alert in alerts}
    assert "alice@example.com" in recruiter_emails
    assert "bob@example.com" in recruiter_emails


@pytest.mark.asyncio
async def test_e2e_search_alert_email_template_data(client: AsyncClient, test_db: AsyncSession):
    """
    Verify that the email template receives all required data.
    """
    # Create recruiter
    recruiter = Recruiter(
        name="Template Test Recruiter",
        email="template@example.com",
        department="Engineering",
        is_active=True,
    )
    test_db.add(recruiter)
    await test_db.commit()
    await test_db.refresh(recruiter)

    # Create saved search
    saved_search = SavedSearch(
        name="Data Scientists",
        query="Python AND ML",
        filters={
            "skills": ["Python", "Machine Learning", "TensorFlow"],
            "min_experience_years": 3,
        },
        recruiter_id=recruiter.id,
    )
    test_db.add(saved_search)
    await test_db.commit()

    # Create resume with detailed analysis
    resume = Resume(
        filename="data_scientist.pdf",
        file_path="/test/ds.pdf",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text="Data scientist with Python and ML experience",
    )
    test_db.add(resume)

    resume_analysis = ResumeAnalysis(
        resume_id=resume.id,
        skills=["Python", "Machine Learning", "TensorFlow", "Pandas", "NumPy"],
        entities={
            "persons": ["Jane Data Scientist"],
        },
        experience_years=4,
        language="en",
    )
    test_db.add(resume_analysis)
    await test_db.commit()
    await test_db.refresh(resume)

    # Create alert
    alert = SearchAlert(
        saved_search_id=saved_search.id,
        resume_id=resume.id,
        is_sent=False,
    )
    test_db.add(alert)
    await test_db.commit()
    await test_db.refresh(alert)

    # Send notification and capture email task parameters
    with patch('tasks.search_alerts_task.send_search_alert_email_task') as mock_email_task:
        mock_email_task.delay = Mock(return_value=Mock(id="task-789"))

        notification_result = send_search_alert_notification(
            alert_id=str(alert.id),
        )

        # Verify email task was called with all required parameters
        call_kwargs = mock_email_task.delay.call_args[1]

        # Required parameters for email template
        assert "alert_id" in call_kwargs
        assert "saved_search_id" in call_kwargs
        assert "resume_id" in call_kwargs
        assert "recipient_email" in call_kwargs
        assert call_kwargs["recipient_email"] == "template@example.com"
        assert "candidate_name" in call_kwargs
        assert call_kwargs["candidate_name"] == "Jane Data Scientist"
        assert "match_score" in call_kwargs
        assert 0 <= call_kwargs["match_score"] <= 100
        assert "matched_skills" in call_kwargs
        assert len(call_kwargs["matched_skills"]) > 0
        assert "Python" in call_kwargs["matched_skills"]
        assert "saved_search_name" in call_kwargs
        assert call_kwargs["saved_search_name"] == "Data Scientists"
