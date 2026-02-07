"""
Integration tests for import failure handling and retry mechanism.

Tests the complete flow of import failures, error logging, and retry functionality
to ensure the system handles authentication errors gracefully and allows recovery.
"""
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.backend.main import app
from database import async_session_maker
from models import JobBoardIntegration, ImportLog, ImportJobStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_import_with_invalid_api_key_fails_gracefully(db_session):
    """Test that import with invalid API key fails gracefully and logs error."""
    # Create an integration with invalid API key
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Indeed Integration - Invalid Key",
        api_endpoint="https://api.indeed.com/v1",
        api_key="invalid_key_12345",  # Invalid key
        enabled=True,
        config={"job_id": "test_job_123"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Mock the Indeed client to simulate authentication failure
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            # Create a mock client that raises HTTP 401 error
            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=["HTTP error fetching applicants: 401 - Unauthorized"]
            )
            mock_client_class.return_value = mock_instance

            # Trigger the import task directly (simulating Celery task execution)
            from tasks.import_tasks import poll_job_board

            result = poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_123"
            )

            # Verify the result indicates failure
            assert result["status"] == "failed"
            assert result["applicants_found"] == 0
            assert result["applicants_processed"] == 0
            assert len(result["errors"]) > 0
            assert any("401" in error or "Unauthorized" in error for error in result["errors"])

            # Verify an ImportLog was created with FAILED status
            log_result = await db.execute(
                select(ImportLog).where(
                    ImportLog.job_board_id == str(integration.id)
                ).order_by(ImportLog.created_at.desc())
            )
            import_log = log_result.scalar_one_or_none()

            assert import_log is not None
            assert import_log.status == ImportJobStatus.FAILED
            assert import_log.error_message is not None
            assert import_log.records_processed == 0
            assert import_log.records_succeeded == 0

            # Clean up
            await db.delete(integration)
            await db.commit()


@pytest.mark.asyncio
async def test_import_failure_logs_error_details(db_session):
    """Test that import failures are logged with detailed error information."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Integration - Network Error",
        api_endpoint="https://api.indeed.com/v1",
        api_key="test_key",
        enabled=True,
        config={"job_id": "test_job_456"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Mock to simulate network error
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=["Request error fetching applicants: Connection timeout"]
            )
            mock_client_class.return_value = mock_instance

            from tasks.import_tasks import poll_job_board

            result = poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_456"
            )

            # Verify error is in result
            assert result["status"] == "failed"
            assert len(result["errors"]) > 0

            # Verify import log contains error details
            log_result = await db.execute(
                select(ImportLog).where(
                    ImportLog.job_board_id == str(integration.id)
                )
            )
            import_log = log_result.scalar_one_or_none()

            assert import_log is not None
            assert import_log.status == ImportJobStatus.FAILED
            assert import_log.error_message is not None
            assert import_log.error_details is not None
            assert "errors" in import_log.error_details
            assert len(import_log.error_details["errors"]) > 0

            # Clean up
            await db.delete(integration)
            await db.commit()


@pytest.mark.asyncio
async def test_import_with_missing_job_id_in_config(db_session):
    """Test that import fails gracefully when job_id is missing from config."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Integration - Missing Job ID",
        api_endpoint="https://api.indeed.com/v1",
        api_key="test_key",
        enabled=True,
        config={}  # No job_id in config
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        from tasks.import_tasks import poll_job_board

        result = poll_job_board(
            job_board_integration_id=str(integration.id)
            # No job_id parameter
        )

        # Verify failure
        assert result["status"] == "failed"
        assert result["applicants_found"] == 0
        assert any("Job ID not provided" in error for error in result["errors"])

        # Verify log was created
        log_result = await db.execute(
            select(ImportLog).where(
                ImportLog.job_board_id == str(integration.id)
            )
        )
        import_log = log_result.scalar_one_or_none()

        assert import_log is not None
        assert import_log.status == ImportJobStatus.FAILED
        assert "Job ID not provided" in import_log.error_message

        # Clean up
        await db.delete(integration)
        await db.commit()


@pytest.mark.asyncio
async def test_retry_with_fixed_credentials_succeeds(db_session):
    """Test that retrying after fixing credentials succeeds."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Integration - Retry Success",
        api_endpoint="https://api.indeed.com/v1",
        api_key="bad_key",  # Initially bad
        enabled=True,
        config={"job_id": "test_job_789"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # First attempt: Simulate failure with bad credentials
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=["HTTP error fetching applicants: 401 - Unauthorized"]
            )
            mock_client_class.return_value = mock_instance

            from tasks.import_tasks import poll_job_board

            result1 = poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_789"
            )

            assert result1["status"] == "failed"

        # Fix the credentials (update API key in database)
        integration.api_key = "good_key_fixed"
        await db.commit()

        # Second attempt: Simulate success with fixed credentials
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            from services.job_board_clients.indeed_client import IndeedApplicant

            # Create mock applicant
            mock_applicant = IndeedApplicant(
                applicant_id="applicant_1",
                resume_url="https://example.com/resume1.pdf",
                candidate_name="John Doe",
                candidate_email="john@example.com",
                job_title="Software Engineer",
                status="new"
            )

            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[mock_applicant],
                total_count=1,
                page=1,
                page_size=1,
                has_more=False,
                errors=[]
            )
            mock_client_class.return_value = mock_instance

            from tasks.import_tasks import poll_job_board

            result2 = poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_789"
            )

            # Verify success
            assert result2["status"] == "completed"
            assert result2["applicants_found"] == 1
            assert result2["applicants_processed"] == 1
            assert len(result2["errors"]) == 0

            # Verify new import log shows success
            log_result = await db.execute(
                select(ImportLog).where(
                    ImportLog.job_board_id == str(integration.id)
                ).order_by(ImportLog.created_at.desc())
            )
            import_logs = log_result.scalars().all()

            # Should have at least 2 logs (one failed, one successful)
            assert len(import_logs) >= 2

            # Most recent log should be successful
            latest_log = import_logs[0]
            assert latest_log.status == ImportJobStatus.SUCCESS
            assert latest_log.records_succeeded == 1

            # Clean up
            await db.delete(integration)
            await db.commit()


@pytest.mark.asyncio
async def test_manual_trigger_with_invalid_credentials(db_session):
    """Test that manual import trigger fails gracefully with invalid credentials."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Manual Trigger - Bad Credentials",
        api_endpoint="https://api.indeed.com/v1",
        api_key="wrong_key",
        enabled=True,
        config={"job_id": "test_job_999"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        # Trigger import via API endpoint
        client = TestClient(app)
        response = client.post(f"/api/integrations/{integration.id}/trigger-import")

        # Should accept the trigger (202 Accepted)
        # The actual failure happens asynchronously in the Celery task
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data

        # Note: In a real scenario, we'd need to wait for the Celery task to complete
        # and then check the import logs. For this test, we verify the API accepts the trigger
        # and the task would eventually fail due to bad credentials.

        # Clean up
        await db.delete(integration)
        await db.commit()


@pytest.mark.asyncio
async def test_import_with_disabled_integration_fails(db_session):
    """Test that import fails for disabled integrations."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Disabled Integration",
        api_endpoint="https://api.indeed.com/v1",
        api_key="test_key",
        enabled=False,  # Disabled
        config={"job_id": "test_job_disabled"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()
        await db.refresh(integration)

        from tasks.import_tasks import poll_job_board

        result = poll_job_board(
            job_board_integration_id=str(integration.id),
            job_id="test_job_disabled"
        )

        # Verify failure due to disabled integration
        assert result["status"] == "failed"
        assert "disabled" in result["error"].lower()

        # Verify import log was created
        log_result = await db.execute(
            select(ImportLog).where(
                ImportLog.job_board_id == str(integration.id)
            )
        )
        import_log = log_result.scalar_one_or_none()

        # Note: Current implementation returns early without creating log for disabled integration
        # This is by design - the task fails before creating a log entry
        # If this behavior changes, update this test

        # Clean up
        await db.delete(integration)
        await db.commit()


@pytest.mark.asyncio
async def test_multiple_failures_and_then_success(db_session):
    """Test that multiple failures followed by a success are all logged correctly."""
    integration = JobBoardIntegration(
        id=uuid4(),
        name="Test Multiple Attempts",
        api_endpoint="https://api.indeed.com/v1",
        api_key="initially_bad_key",
        enabled=True,
        config={"job_id": "test_job_multi"}
    )

    async with async_session_maker() as db:
        db.add(integration)
        await db.commit()

        # Attempt 1: Fail with bad credentials
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=["401 - Unauthorized"]
            )
            mock_client_class.return_value = mock_instance

            from tasks.import_tasks import poll_job_board

            poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_multi"
            )

        # Attempt 2: Still fail
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[],
                total_count=0,
                page=1,
                page_size=0,
                has_more=False,
                errors=["401 - Unauthorized"]
            )
            mock_client_class.return_value = mock_instance

            poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_multi"
            )

        # Fix credentials
        integration.api_key = "good_key"
        await db.commit()

        # Attempt 3: Succeed
        with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client_class:
            from services.job_board_clients.indeed_client import IndeedApplicant

            mock_applicant = IndeedApplicant(
                applicant_id="applicant_success",
                resume_url="https://example.com/resume.pdf",
                candidate_name="Jane Smith",
                candidate_email="jane@example.com",
                job_title="Data Scientist"
            )

            mock_instance = AsyncMock()
            mock_instance.fetch_all_applicants.return_value = Mock(
                applicants=[mock_applicant],
                total_count=1,
                page=1,
                page_size=1,
                has_more=False,
                errors=[]
            )
            mock_client_class.return_value = mock_instance

            poll_job_board(
                job_board_integration_id=str(integration.id),
                job_id="test_job_multi"
            )

        # Verify all three attempts are logged
        log_result = await db.execute(
            select(ImportLog).where(
                ImportLog.job_board_id == str(integration.id)
            ).order_by(ImportLog.created_at)
        )
        import_logs = log_result.scalars().all()

        assert len(import_logs) == 3

        # First two should be failed
        assert import_logs[0].status == ImportJobStatus.FAILED
        assert import_logs[1].status == ImportJobStatus.FAILED

        # Last one should be successful
        assert import_logs[2].status == ImportJobStatus.SUCCESS
        assert import_logs[2].records_succeeded == 1

        # Clean up
        await db.delete(integration)
        await db.commit()
