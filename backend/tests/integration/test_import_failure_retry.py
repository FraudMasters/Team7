"""
Integration tests for import failure handling and retry mechanism.

Tests the following scenarios:
1. Import fails gracefully with invalid credentials
2. Errors are properly logged in import logs
3. Retry mechanism works correctly
4. Multiple retry attempts are tracked
5. Cannot retry successful imports
"""
import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient
from httpx import AsyncClient


class TestImportFailureHandling:
    """Test import failure scenarios."""

    @pytest.mark.asyncio
    async def test_import_with_invalid_credentials_fails_gracefully(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that import with invalid API key fails gracefully and logs error."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration with invalid credentials
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Test Integration",
            api_endpoint="https://api.indeed.com/v2",
            api_key="invalid_invalid_invalid_invalid_key",  # Invalid API key
            enabled=True,
            config={"job_id": "test-job-123"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Trigger import manually
            response = await client.post(
                f"/api/integrations/{integration.id}/trigger-import"
            )

            # Should accept the request (202)
            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data

            # Wait a moment for task to process
            import asyncio
            await asyncio.sleep(2)

            # Check import log for failure
            log_query = (
                select(ImportLog)
                .where(ImportLog.job_board_id == str(integration.id))
                .order_by(ImportLog.created_at.desc())
            )
            log_result = await db.execute(log_query)
            import_log = log_result.scalar_one_or_none()

            assert import_log is not None
            assert import_log.status == ImportJobStatus.FAILED
            assert import_log.error_message is not None
            assert "invalid" in import_log.error_message.lower() or "auth" in import_log.error_message.lower() or "key" in import_log.error_message.lower()
            assert import_log.records_failed is not None

            # Cleanup
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_import_error_is_logged_with_details(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that import errors are logged with detailed information."""
        from models import JobBoardIntegration, ImportLog
        from database import async_session_maker

        # Create integration that will fail (missing job_id in config)
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Missing Config",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_12345",
            enabled=True,
            config={},  # Missing job_id
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Trigger import
            response = await client.post(
                f"/api/integrations/{integration.id}/trigger-import"
            )

            assert response.status_code == 202

            # Wait for task processing
            import asyncio
            await asyncio.sleep(2)

            # Check import log
            log_query = select(ImportLog).where(
                ImportLog.job_board_id == str(integration.id)
            )
            log_result = await db.execute(log_query)
            import_log = log_result.scalar_one_or_none()

            assert import_log is not None
            assert import_log.error_message is not None
            assert import_log.started_at is not None
            assert import_log.completed_at is not None
            assert import_log.import_metadata is not None
            assert import_log.retry_count == 0

            # Verify error_details contain useful information
            if import_log.error_details:
                assert isinstance(import_log.error_details, dict)

            # Cleanup
            await db.delete(integration)
            await db.commit()


class TestImportRetryMechanism:
    """Test the retry mechanism for failed imports."""

    @pytest.mark.asyncio
    async def test_retry_failed_import_successfully(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that a failed import can be retried successfully."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Retry Test",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_for_retry",
            enabled=True,
            config={"job_id": "test-job-retry"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create a failed import log
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="Authentication failed: Invalid API key",
                error_details={"error_code": "AUTH_001", "error": "invalid_credentials"},
                import_metadata={"job_id": "test-job-retry", "status_filter": None, "from_date": None},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            # Retry the import
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            # Should accept the retry request
            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
            assert data["retry_count"] == 1
            assert "attempt" in data["message"].lower()

            # Verify import log was updated
            await db.refresh(failed_log)
            assert failed_log.retry_count == 1
            assert failed_log.status == ImportJobStatus.IN_PROGRESS

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_retry_partial_import(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that partial imports can also be retried."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Partial Retry",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_partial",
            enabled=True,
            config={"job_id": "test-job-partial"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create a partial import log
            partial_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.PARTIAL,
                records_processed=10,
                records_succeeded=7,
                records_failed=3,
                error_message="Some applicants failed to import",
                error_details={"failed_applicants": ["app1", "app2", "app3"]},
                import_metadata={"job_id": "test-job-partial"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(partial_log)
            await db.commit()
            await db.refresh(partial_log)

            # Retry the partial import
            response = await client.post(
                f"/api/integrations/logs/{partial_log.id}/retry"
            )

            assert response.status_code == 202
            data = response.json()
            assert data["retry_count"] == 1

            # Cleanup
            await db.delete(partial_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_cannot_retry_successful_import(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that successful imports cannot be retried."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Success",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_success",
            enabled=True,
            config={"job_id": "test-job-success"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create a successful import log
            success_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.COMPLETED,
                records_processed=5,
                records_succeeded=5,
                records_failed=0,
                error_message=None,
                import_metadata={"job_id": "test-job-success"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(success_log)
            await db.commit()
            await db.refresh(success_log)

            # Try to retry successful import
            response = await client.post(
                f"/api/integrations/logs/{success_log.id}/retry"
            )

            # Should fail with 400
            assert response.status_code == 400
            data = response.json()
            assert "cannot retry" in data["detail"].lower() or "only failed" in data["detail"].lower()

            # Cleanup
            await db.delete(success_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_cannot_retry_nonexistent_log(
        self, client: AsyncClient
    ):
        """Test that retrying a non-existent log returns 404."""
        fake_log_id = uuid4()

        response = await client.post(
            f"/api/integrations/logs/{fake_log_id}/retry"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_updates_import_log_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that retry updates the import log status to IN_PROGRESS."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Status Update",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_status",
            enabled=True,
            config={"job_id": "test-job-status"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create failed log
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="Network error",
                import_metadata={"job_id": "test-job-status"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(failed_log)
            await db.commit()

            # Get status before retry
            old_status = failed_log.status
            old_error = failed_log.error_message

            # Retry
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            assert response.status_code == 202

            # Refresh and check updates
            await db.refresh(failed_log)
            assert failed_log.status == ImportJobStatus.IN_PROGRESS
            assert failed_log.status != old_status
            # Error message should be cleared for retry
            assert failed_log.error_message != old_error or failed_log.error_message is None

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_multiple_retries_increment_count(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that multiple retries increment the retry count correctly."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Multiple Retries",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_multi",
            enabled=True,
            config={"job_id": "test-job-multi"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create failed log with 2 previous retries
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="API rate limit exceeded",
                import_metadata={"job_id": "test-job-multi"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=2,
            )

            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            initial_count = failed_log.retry_count

            # Retry again
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            assert response.status_code == 202
            data = response.json()
            assert data["retry_count"] == initial_count + 1

            # Verify increment in database
            await db.refresh(failed_log)
            assert failed_log.retry_count == initial_count + 1

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_retry_respects_max_retry_limit(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that retries are limited after maximum attempts."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Max Retries",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_max",
            enabled=True,
            config={"job_id": "test-job-max"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create failed log with 5 retries (at max limit)
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="Persistent error",
                import_metadata={"job_id": "test-job-max"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=5,  # At max limit
            )

            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            # Try to retry beyond max limit
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            # Should fail with 400
            assert response.status_code == 400
            data = response.json()
            assert "maximum" in data["detail"].lower() or "exceeded" in data["detail"].lower()

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_retry_disabled_integration_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that retrying a disabled integration fails gracefully."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create disabled integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - Disabled",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_key_disabled",
            enabled=False,  # Disabled
            config={"job_id": "test-job-disabled"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Create failed log
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="Previous failure",
                import_metadata={"job_id": "test-job-disabled"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            # Try to retry with disabled integration
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            # Should fail with 400
            assert response.status_code == 400
            data = response.json()
            assert "disabled" in data["detail"].lower()

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()

    @pytest.mark.asyncio
    async def test_retry_with_deleted_integration_fails(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that retrying an import when integration is deleted fails gracefully."""
        from models import ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create failed log without integration (simulating deleted integration)
        fake_integration_id = uuid4()
        failed_log = ImportLog(
            id=uuid4(),
            job_board_id=str(fake_integration_id),
            job_board_name="Deleted Integration",
            status=ImportJobStatus.FAILED,
            records_processed=0,
            records_succeeded=0,
            records_failed=1,
            error_message="Previous failure",
            import_metadata={"job_id": "test-job-deleted"},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            retry_count=0,
        )

        async with async_session_maker() as db:
            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            # Try to retry
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            # Should fail with 404
            assert response.status_code == 404

            # Cleanup
            await db.delete(failed_log)
            await db.commit()


class TestRetryEndToEnd:
    """End-to-end tests for retry workflow."""

    @pytest.mark.asyncio
    async def test_complete_retry_workflow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test the complete workflow: failure -> log -> retry -> success."""
        from models import JobBoardIntegration, ImportLog, ImportJobStatus
        from database import async_session_maker

        # Create integration
        integration = JobBoardIntegration(
            id=uuid4(),
            name="Indeed Integration - E2E Retry",
            api_endpoint="https://api.indeed.com/v2",
            api_key="bad_key_initially",
            enabled=True,
            config={"job_id": "test-job-e2e"},
        )

        async with async_session_maker() as db:
            db.add(integration)
            await db.commit()
            await db.refresh(integration)

            # Step 1: Create initial failed import log
            failed_log = ImportLog(
                id=uuid4(),
                job_board_id=str(integration.id),
                job_board_name=integration.name,
                status=ImportJobStatus.FAILED,
                records_processed=0,
                records_succeeded=0,
                records_failed=1,
                error_message="Invalid API key",
                error_details={"code": "AUTH_ERROR"},
                import_metadata={"job_id": "test-job-e2e"},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                retry_count=0,
            )

            db.add(failed_log)
            await db.commit()
            await db.refresh(failed_log)

            # Step 2: Verify failure is logged
            assert failed_log.status == ImportJobStatus.FAILED
            assert failed_log.error_message is not None
            assert failed_log.retry_count == 0

            # Step 3: Simulate fixing credentials and retrying
            integration.api_key = "corrected_key_12345"
            await db.commit()

            # Step 4: Retry the import
            response = await client.post(
                f"/api/integrations/logs/{failed_log.id}/retry"
            )

            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
            assert data["retry_count"] == 1

            # Step 5: Verify log was updated
            await db.refresh(failed_log)
            assert failed_log.retry_count == 1
            assert failed_log.status == ImportJobStatus.IN_PROGRESS

            # Cleanup
            await db.delete(failed_log)
            await db.delete(integration)
            await db.commit()
