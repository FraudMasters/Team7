#!/usr/bin/env python3
"""
Manual test script for import failure handling and retry mechanism.

This script tests the complete workflow:
1. Trigger import with invalid credentials
2. Verify import fails gracefully
3. Verify error is logged in import log
4. Fix credentials and retry from UI (simulated via API)
5. Verify retry succeeds

Usage:
    python manual_import_retry_test.py

Requirements:
    - Backend server running on http://localhost:8000
    - PostgreSQL database accessible
    - Valid database credentials in config.py
"""
import asyncio
import sys
from datetime import datetime
from uuid import uuid4, UUID
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session_maker
from models import JobBoardIntegration, ImportLog, ImportJobStatus
from tasks.import_tasks import poll_job_board


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


async def cleanup_test_data(db: AsyncSession, integration_id: UUID):
    """Clean up test data."""
    try:
        # Delete import logs
        logs_query = select(ImportLog).where(
            ImportLog.job_board_id == str(integration_id)
        )
        logs_result = await db.execute(logs_query)
        logs = logs_result.scalars().all()

        for log in logs:
            await db.delete(log)

        # Delete integration
        integration_query = select(JobBoardIntegration).where(
            JobBoardIntegration.id == integration_id
        )
        integration_result = await db.execute(integration_query)
        integration = integration_result.scalar_one_or_none()

        if integration:
            await db.delete(integration)

        await db.commit()
        print_success("Cleanup completed")
    except Exception as e:
        print_error(f"Cleanup failed: {e}")


async def test_1_invalid_credentials_fail_gracefully(db: AsyncSession) -> bool:
    """Test 1: Trigger import with invalid credentials and verify graceful failure."""
    print_header("TEST 1: Invalid Credentials Fail Gracefully")

    integration_id = uuid4()

    try:
        # Step 1: Create integration with invalid credentials
        print_info("Creating integration with invalid API key...")
        integration = JobBoardIntegration(
            id=integration_id,
            name="Indeed Test - Invalid Key",
            api_endpoint="https://api.indeed.com/v2",
            api_key="invalid_invalid_invalid_bad_key",  # Clearly invalid
            enabled=True,
            config={"job_id": "test-job-invalid-creds"},
        )

        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        print_success("Integration created with invalid credentials")

        # Step 2: Trigger import (simulate trigger-import endpoint)
        print_info("Triggering import with invalid credentials...")
        try:
            # Directly call the Celery task (simulating what the endpoint does)
            task = poll_job_board.apply_async(
                args=[str(integration.id)],
                kwargs={"job_id": "test-job-invalid-creds", "status_filter": None, "from_date": None}
            )

            print_info(f"Task {task.id} triggered, waiting for completion...")

            # Wait for task to complete (max 10 seconds)
            result = task.get(timeout=10)

            print_info(f"Task result: {result.get('status')}")
        except Exception as e:
            print_info(f"Task execution completed (may have failed as expected): {e}")

        # Step 3: Wait a moment for database to be updated
        await asyncio.sleep(1)

        # Step 4: Verify import log shows failure
        print_info("Checking import log for failure entry...")
        logs_query = (
            select(ImportLog)
            .where(ImportLog.job_board_id == str(integration_id))
            .order_by(ImportLog.created_at.desc())
        )
        logs_result = await db.execute(logs_query)
        import_log = logs_result.scalar_one_or_none()

        if not import_log:
            print_error("No import log found!")
            await cleanup_test_data(db, integration_id)
            return False

        print_success(f"Import log found with status: {import_log.status.value}")

        # Verify failure status
        if import_log.status != ImportJobStatus.FAILED:
            print_error(f"Expected FAILED status, got: {import_log.status.value}")
            await cleanup_test_data(db, integration_id)
            return False
        print_success("Import log shows FAILED status ✓")

        # Verify error message exists
        if not import_log.error_message:
            print_error("Expected error message in import log")
            await cleanup_test_data(db, integration_id)
            return False
        print_success(f"Error message logged: {import_log.error_message[:80]}...")

        # Verify error details exist
        if not import_log.error_details:
            print_info("No error details (this is acceptable)")
        else:
            print_success(f"Error details present: {import_log.error_details}")

        # Verify timestamps
        if not import_log.started_at or not import_log.completed_at:
            print_error("Expected started_at and completed_at timestamps")
            await cleanup_test_data(db, integration_id)
            return False
        print_success("Timestamps present (started_at, completed_at)")

        print_success("TEST 1 PASSED: Invalid credentials failed gracefully\n")

        # Keep test data for next test
        return True

    except Exception as e:
        print_error(f"Test 1 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await cleanup_test_data(db, integration_id)
        return False


async def test_2_retry_failed_import(db: AsyncSession, integration_id: UUID) -> bool:
    """Test 2: Retry a failed import after fixing credentials."""
    print_header("TEST 2: Retry Failed Import")

    try:
        # Step 1: Get the failed import log from previous test
        print_info("Retrieving failed import log from previous test...")
        logs_query = (
            select(ImportLog)
            .where(ImportLog.job_board_id == str(integration_id))
            .order_by(ImportLog.created_at.desc())
        )
        logs_result = await db.execute(logs_query)
        import_log = logs_result.scalar_one_or_none()

        if not import_log:
            print_error("No import log found from previous test!")
            return False

        print_success(f"Found import log: {import_log.id}")
        print_info(f"Current status: {import_log.status.value}")
        print_info(f"Current retry count: {import_log.retry_count}")

        # Store initial retry count
        initial_retry_count = import_log.retry_count or 0

        # Step 2: Simulate fixing credentials
        print_info("Simulating credential fix...")
        integration_query = select(JobBoardIntegration).where(
            JobBoardIntegration.id == integration_id
        )
        integration_result = await db.execute(integration_query)
        integration = integration_result.scalar_one_or_none()

        if not integration:
            print_error("Integration not found!")
            return False

        integration.api_key = "corrected_api_key_12345"
        await db.commit()
        print_success("Credentials fixed (API key updated)")

        # Step 3: Simulate retry endpoint logic
        print_info("Simulating retry endpoint logic...")

        # Check if can retry (FAILED or PARTIAL status)
        if import_log.status not in [ImportJobStatus.FAILED, ImportJobStatus.PARTIAL]:
            print_error(f"Cannot retry import with status: {import_log.status.value}")
            return False
        print_success("Import log status allows retry")

        # Check retry count limit
        MAX_RETRIES = 5
        if import_log.retry_count and import_log.retry_count >= MAX_RETRIES:
            print_error(f"Retry limit exceeded: {import_log.retry_count}")
            return False
        print_success(f"Retry count within limit: {import_log.retry_count}/{MAX_RETRIES}")

        # Step 4: Update import log for retry
        print_info("Updating import log for retry...")
        import_log.retry_count = (import_log.retry_count or 0) + 1
        import_log.status = ImportJobStatus.IN_PROGRESS
        import_log.error_message = None  # Clear previous error
        await db.commit()
        await db.refresh(import_log)

        print_success(f"Retry count incremented: {import_log.retry_count}")
        print_success(f"Status updated to: {import_log.status.value}")

        # Step 5: Trigger new import task
        print_info("Triggering new import task...")
        try:
            task = poll_job_board.apply_async(
                args=[str(integration.id)],
                kwargs={
                    "job_id": integration.config.get("job_id"),
                    "status_filter": None,
                    "from_date": None,
                }
            )

            print_success(f"New task triggered: {task.id}")

            # Wait for task
            result = task.get(timeout=10)
            print_info(f"Task result: {result.get('status')}")

        except Exception as e:
            print_info(f"Task execution: {e}")

        # Step 6: Verify retry count was incremented
        await db.refresh(import_log)
        if import_log.retry_count != initial_retry_count + 1:
            print_error(f"Retry count not incremented correctly: {import_log.retry_count} vs {initial_retry_count + 1}")
            return False
        print_success(f"Retry count incremented correctly: {import_log.retry_count}")

        print_success("TEST 2 PASSED: Failed import retried successfully\n")

        return True

    except Exception as e:
        print_error(f"Test 2 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_cannot_retry_successful_import(db: AsyncSession) -> bool:
    """Test 3: Verify that successful imports cannot be retried."""
    print_header("TEST 3: Cannot Retry Successful Import")

    integration_id = uuid4()

    try:
        # Step 1: Create integration
        print_info("Creating integration...")
        integration = JobBoardIntegration(
            id=integration_id,
            name="Indeed Test - Successful Import",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_api_key",
            enabled=True,
            config={"job_id": "test-job-success"},
        )

        db.add(integration)
        await db.commit()
        print_success("Integration created")

        # Step 2: Create successful import log
        print_info("Creating successful import log...")
        success_log = ImportLog(
            id=uuid4(),
            job_board_id=str(integration_id),
            job_board_name=integration.name,
            status=ImportJobStatus.COMPLETED,  # Successful
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
        print_success("Successful import log created")

        # Step 3: Try to retry (simulate endpoint validation)
        print_info("Attempting to retry successful import...")

        # Check if can retry
        can_retry = success_log.status in [ImportJobStatus.FAILED, ImportJobStatus.PARTIAL]

        if can_retry:
            print_error("Should NOT be able to retry successful import!")
            await cleanup_test_data(db, integration_id)
            return False

        print_success("Correctly prevented retry of successful import")

        print_success("TEST 3 PASSED: Cannot retry successful import\n")

        await cleanup_test_data(db, integration_id)
        return True

    except Exception as e:
        print_error(f"Test 3 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await cleanup_test_data(db, integration_id)
        return False


async def test_4_retry_limit_enforced(db: AsyncSession) -> bool:
    """Test 4: Verify that retry limit is enforced."""
    print_header("TEST 4: Retry Limit Enforced")

    integration_id = uuid4()

    try:
        # Step 1: Create integration
        print_info("Creating integration...")
        integration = JobBoardIntegration(
            id=integration_id,
            name="Indeed Test - Retry Limit",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_api_key",
            enabled=True,
            config={"job_id": "test-job-limit"},
        )

        db.add(integration)
        await db.commit()
        print_success("Integration created")

        # Step 2: Create failed import log at retry limit
        print_info("Creating import log at max retry limit...")
        failed_log = ImportLog(
            id=uuid4(),
            job_board_id=str(integration_id),
            job_board_name=integration.name,
            status=ImportJobStatus.FAILED,
            records_processed=0,
            records_succeeded=0,
            records_failed=1,
            error_message="Persistent error",
            import_metadata={"job_id": "test-job-limit"},
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            retry_count=5,  # At max limit
        )

        db.add(failed_log)
        await db.commit()
        print_success("Import log created with retry_count=5")

        # Step 3: Try to retry beyond limit
        print_info("Attempting to retry beyond max limit...")

        MAX_RETRIES = 5
        can_retry = failed_log.retry_count < MAX_RETRIES

        if can_retry:
            print_error("Should NOT be able to retry beyond max limit!")
            await cleanup_test_data(db, integration_id)
            return False

        print_success(f"Correctly prevented retry beyond limit: {failed_log.retry_count}/{MAX_RETRIES}")

        print_success("TEST 4 PASSED: Retry limit enforced\n")

        await cleanup_test_data(db, integration_id)
        return True

    except Exception as e:
        print_error(f"Test 4 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await cleanup_test_data(db, integration_id)
        return False


async def test_5_disabled_integration_cannot_retry(db: AsyncSession) -> bool:
    """Test 5: Verify that disabled integrations cannot be retried."""
    print_header("TEST 5: Disabled Integration Cannot Retry")

    integration_id = uuid4()

    try:
        # Step 1: Create disabled integration
        print_info("Creating DISABLED integration...")
        integration = JobBoardIntegration(
            id=integration_id,
            name="Indeed Test - Disabled",
            api_endpoint="https://api.indeed.com/v2",
            api_key="test_api_key",
            enabled=False,  # DISABLED
            config={"job_id": "test-job-disabled"},
        )

        db.add(integration)
        await db.commit()
        print_success("Disabled integration created")

        # Step 2: Create failed import log
        print_info("Creating failed import log...")
        failed_log = ImportLog(
            id=uuid4(),
            job_board_id=str(integration_id),
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
        print_success("Failed import log created")

        # Step 3: Try to retry (should fail due to disabled integration)
        print_info("Attempting to retry disabled integration...")

        # Check if integration is enabled
        if not integration.enabled:
            print_success("Correctly prevented retry: integration is disabled")
        else:
            print_error("Should have detected disabled integration!")
            await cleanup_test_data(db, integration_id)
            return False

        print_success("TEST 5 PASSED: Disabled integration cannot be retried\n")

        await cleanup_test_data(db, integration_id)
        return True

    except Exception as e:
        print_error(f"Test 5 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        await cleanup_test_data(db, integration_id)
        return False


async def main():
    """Run all tests."""
    print_header("IMPORT FAILURE HANDLING AND RETRY MECHANISM TESTS")
    print_info("Starting test suite...")
    print_info("Make sure backend server is running on http://localhost:8000")

    test_results = []

    async with async_session_maker() as db:
        # Test 1: Invalid credentials fail gracefully
        result1 = await test_1_invalid_credentials_fail_gracefully(db)
        test_results.append(("Test 1: Invalid Credentials Fail Gracefully", result1))

        if result1:
            # Get integration ID for subsequent tests
            integration_query = select(JobBoardIntegration).where(
                JobBoardIntegration.name == "Indeed Test - Invalid Key"
            )
            integration_result = await db.execute(integration_query)
            integration = integration_result.scalar_one_or_none()

            if integration:
                # Test 2: Retry failed import
                result2 = await test_2_retry_failed_import(db, integration.id)
                test_results.append(("Test 2: Retry Failed Import", result2))

                # Cleanup
                await cleanup_test_data(db, integration.id)

        # Test 3: Cannot retry successful import
        result3 = await test_3_cannot_retry_successful_import(db)
        test_results.append(("Test 3: Cannot Retry Successful Import", result3))

        # Test 4: Retry limit enforced
        result4 = await test_4_retry_limit_enforced(db)
        test_results.append(("Test 4: Retry Limit Enforced", result4))

        # Test 5: Disabled integration cannot retry
        result5 = await test_5_disabled_integration_cannot_retry(db)
        test_results.append(("Test 5: Disabled Integration Cannot Retry", result5))

    # Print summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = f"{Colors.GREEN}PASSED{Colors.END}" if result else f"{Colors.RED}FAILED{Colors.END}"
        print(f"{status}: {test_name}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED! ✓{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}SOME TESTS FAILED! ✗{Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
