#!/usr/bin/env python3
"""
Manual test script for import failure handling and retry mechanism.

This script simulates various import failure scenarios to verify that:
1. Invalid credentials cause graceful failures
2. Errors are properly logged in ImportLog
3. Retries after fixing credentials succeed

Usage:
    python manual_import_failure_test.py

Requirements:
    - PostgreSQL database running
    - Backend dependencies installed
    - Test database configured

Exit codes:
    0: All tests passed
    1: One or more tests failed
"""

import sys
import os
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from database import async_session_maker
from models import JobBoardIntegration, ImportLog, ImportJobStatus
from sqlalchemy import select


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_failure(message: str):
    """Print failure message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_test_header(message: str):
    """Print test header in bold."""
    print(f"\n{Colors.BOLD}{message}{Colors.RESET}")
    print("=" * 80)


async def cleanup_test_data(db_session, integration_id: str):
    """Clean up test data."""
    try:
        # Delete import logs
        logs_result = await db_session.execute(
            select(ImportLog).where(ImportLog.job_board_id == integration_id)
        )
        logs = logs_result.scalars().all()
        for log in logs:
            await db_session.delete(log)

        # Delete integration
        integration_result = await db_session.execute(
            select(JobBoardIntegration).where(JobBoardIntegration.id == integration_id)
        )
        integration = integration_result.scalar_one_or_none()
        if integration:
            await db_session.delete(integration)

        await db_session.commit()
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")


async def test_invalid_api_key() -> bool:
    """
    Test 1: Import with invalid API key fails gracefully.

    Creates an integration with an invalid API key and verifies:
    - Import fails without crashing
    - Error is logged in ImportLog
    - Error details are captured
    """
    print_test_header("Test 1: Invalid API Key")

    integration_id = uuid4()

    try:
        async with async_session_maker() as db:
            # Create integration with invalid key
            integration = JobBoardIntegration(
                id=integration_id,
                name="Test Invalid Key",
                api_endpoint="https://api.indeed.com/v1",
                api_key="invalid_key_12345",
                enabled=True,
                config={"job_id": "test_job_1"}
            )
            db.add(integration)
            await db.commit()

            print_info(f"Created integration {integration_id}")

            # Simulate import task with mocked client
            from unittest.mock import Mock, AsyncMock, patch

            with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client:
                mock_instance = AsyncMock()
                mock_instance.fetch_all_applicants.return_value = Mock(
                    applicants=[],
                    total_count=0,
                    page=1,
                    page_size=0,
                    has_more=False,
                    errors=["HTTP error fetching applicants: 401 - Unauthorized"]
                )
                mock_client.return_value = mock_instance

                # Import poll_job_board function
                from tasks.import_tasks import poll_job_board

                # Execute import task
                result = poll_job_board(
                    job_board_integration_id=str(integration_id),
                    job_id="test_job_1"
                )

                # Verify failure
                if result.get("status") != "failed":
                    print_failure(f"Expected status='failed', got '{result.get('status')}'")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Import failed as expected")

                # Verify error logging
                logs_result = await db.execute(
                    select(ImportLog).where(ImportLog.job_board_id == str(integration_id))
                )
                import_log = logs_result.scalar_one_or_none()

                if not import_log:
                    print_failure("No ImportLog entry created")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("ImportLog entry created")

                if import_log.status != ImportJobStatus.FAILED:
                    print_failure(f"Expected log status=FAILED, got '{import_log.status}'")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("ImportLog status is FAILED")

                if not import_log.error_message:
                    print_failure("No error message in ImportLog")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success(f"Error message logged: {import_log.error_message}")

                if not import_log.error_details:
                    print_failure("No error_details in ImportLog")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Error details captured")

            await cleanup_test_data(db, integration_id)
            return True

    except Exception as e:
        print_failure(f"Test failed with exception: {e}")
        return False


async def test_network_error() -> bool:
    """
    Test 2: Import with network error fails gracefully.

    Creates an integration and simulates a network error to verify:
    - Import fails without crashing
    - Network error is properly logged
    """
    print_test_header("Test 2: Network Error")

    integration_id = uuid4()

    try:
        async with async_session_maker() as db:
            # Create integration
            integration = JobBoardIntegration(
                id=integration_id,
                name="Test Network Error",
                api_endpoint="https://api.indeed.com/v1",
                api_key="test_key",
                enabled=True,
                config={"job_id": "test_job_2"}
            )
            db.add(integration)
            await db.commit()

            print_info(f"Created integration {integration_id}")

            # Simulate network error
            from unittest.mock import Mock, AsyncMock, patch

            with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client:
                mock_instance = AsyncMock()
                mock_instance.fetch_all_applicants.return_value = Mock(
                    applicants=[],
                    total_count=0,
                    page=1,
                    page_size=0,
                    has_more=False,
                    errors=["Request error fetching applicants: Connection timeout"]
                )
                mock_client.return_value = mock_instance

                from tasks.import_tasks import poll_job_board

                result = poll_job_board(
                    job_board_integration_id=str(integration_id),
                    job_id="test_job_2"
                )

                if result.get("status") != "failed":
                    print_failure(f"Expected status='failed', got '{result.get('status')}'")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Import failed due to network error")

                # Verify error details
                logs_result = await db.execute(
                    select(ImportLog).where(ImportLog.job_board_id == str(integration_id))
                )
                import_log = logs_result.scalar_one_or_none()

                if not import_log or import_log.status != ImportJobStatus.FAILED:
                    print_failure("Failed to log network error")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Network error properly logged")

                if "Connection timeout" not in import_log.error_message:
                    print_failure(f"Expected 'Connection timeout' in error, got: {import_log.error_message}")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Network error details captured")

            await cleanup_test_data(db, integration_id)
            return True

    except Exception as e:
        print_failure(f"Test failed with exception: {e}")
        return False


async def test_retry_after_fixing_credentials() -> bool:
    """
    Test 3: Retry after fixing credentials succeeds.

    Simulates the complete flow:
    1. Import fails with bad credentials
    2. Fix the credentials
    3. Retry succeeds
    4. Both failures and success are logged
    """
    print_test_header("Test 3: Retry After Fixing Credentials")

    integration_id = uuid4()

    try:
        async with async_session_maker() as db:
            # Create integration with bad credentials
            integration = JobBoardIntegration(
                id=integration_id,
                name="Test Retry Success",
                api_endpoint="https://api.indeed.com/v1",
                api_key="bad_key",
                enabled=True,
                config={"job_id": "test_job_3"}
            )
            db.add(integration)
            await db.commit()

            print_info(f"Created integration {integration_id} with bad credentials")

            # First import attempt (should fail)
            from unittest.mock import Mock, AsyncMock, patch

            with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client:
                mock_instance = AsyncMock()
                mock_instance.fetch_all_applicants.return_value = Mock(
                    applicants=[],
                    total_count=0,
                    page=1,
                    page_size=0,
                    has_more=False,
                    errors=["HTTP error fetching applicants: 401 - Unauthorized"]
                )
                mock_client.return_value = mock_instance

                from tasks.import_tasks import poll_job_board

                result1 = poll_job_board(
                    job_board_integration_id=str(integration_id),
                    job_id="test_job_3"
                )

                if result1.get("status") != "failed":
                    print_failure("First attempt should have failed")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("First import attempt failed as expected")

            # Fix credentials
            integration.api_key = "good_key"
            await db.commit()
            print_info("Updated API key to good credentials")

            # Second import attempt (should succeed)
            with patch('services.job_board_clients.indeed_client.IndeedClient') as mock_client:
                from services.job_board_clients.indeed_client import IndeedApplicant

                mock_applicant = IndeedApplicant(
                    applicant_id="applicant_1",
                    resume_url="https://example.com/resume1.pdf",
                    candidate_name="John Doe",
                    candidate_email="john@example.com",
                    job_title="Software Engineer"
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
                mock_client.return_value = mock_instance

                result2 = poll_job_board(
                    job_board_integration_id=str(integration_id),
                    job_id="test_job_3"
                )

                if result2.get("status") != "completed":
                    print_failure(f"Second attempt should have succeeded, got: {result2.get('status')}")
                    await cleanup_test_data(db, integration_id)
                    return False

                print_success("Second import attempt succeeded")

            # Verify both logs exist
            logs_result = await db.execute(
                select(ImportLog).where(
                    ImportLog.job_board_id == str(integration_id)
                ).order_by(ImportLog.created_at)
            )
            import_logs = logs_result.scalars().all()

            if len(import_logs) < 2:
                print_failure(f"Expected at least 2 logs, got {len(import_logs)}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success(f"Found {len(import_logs)} import log entries")

            # Verify first log is failed
            if import_logs[0].status != ImportJobStatus.FAILED:
                print_failure(f"First log should be FAILED, got {import_logs[0].status}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("First log entry shows FAILED status")

            # Verify latest log is successful
            latest_log = import_logs[-1]
            if latest_log.status != ImportJobStatus.SUCCESS:
                print_failure(f"Latest log should be SUCCESS, got {latest_log.status}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Latest log entry shows SUCCESS status")

            if latest_log.records_succeeded != 1:
                print_failure(f"Expected 1 record succeeded, got {latest_log.records_succeeded}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Latest log shows 1 record succeeded")

            await cleanup_test_data(db, integration_id)
            return True

    except Exception as e:
        print_failure(f"Test failed with exception: {e}")
        return False


async def test_missing_job_id() -> bool:
    """
    Test 4: Import fails when job_id is missing.

    Verifies that missing configuration is caught and logged properly.
    """
    print_test_header("Test 4: Missing Job ID")

    integration_id = uuid4()

    try:
        async with async_session_maker() as db:
            # Create integration without job_id in config
            integration = JobBoardIntegration(
                id=integration_id,
                name="Test Missing Job ID",
                api_endpoint="https://api.indeed.com/v1",
                api_key="test_key",
                enabled=True,
                config={}  # No job_id
            )
            db.add(integration)
            await db.commit()

            print_info(f"Created integration {integration_id} without job_id")

            from tasks.import_tasks import poll_job_board

            result = poll_job_board(
                job_board_integration_id=str(integration_id)
                # No job_id parameter
            )

            if result.get("status") != "failed":
                print_failure(f"Expected status='failed', got '{result.get('status')}'")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Import failed due to missing job_id")

            # Verify error is logged
            logs_result = await db.execute(
                select(ImportLog).where(ImportLog.job_board_id == str(integration_id))
            )
            import_log = logs_result.scalar_one_or_none()

            if not import_log:
                print_failure("No ImportLog entry created")
                await cleanup_test_data(db, integration_id)
                return False

            if "Job ID not provided" not in import_log.error_message:
                print_failure(f"Expected 'Job ID not provided' in error, got: {import_log.error_message}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Missing job_id error properly logged")

            await cleanup_test_data(db, integration_id)
            return True

    except Exception as e:
        print_failure(f"Test failed with exception: {e}")
        return False


async def test_disabled_integration() -> bool:
    """
    Test 5: Import fails for disabled integration.

    Verifies that disabled integrations cannot import.
    """
    print_test_header("Test 5: Disabled Integration")

    integration_id = uuid4()

    try:
        async with async_session_maker() as db:
            # Create disabled integration
            integration = JobBoardIntegration(
                id=integration_id,
                name="Test Disabled Integration",
                api_endpoint="https://api.indeed.com/v1",
                api_key="test_key",
                enabled=False,  # Disabled
                config={"job_id": "test_job_5"}
            )
            db.add(integration)
            await db.commit()

            print_info(f"Created disabled integration {integration_id}")

            from tasks.import_tasks import poll_job_board

            result = poll_job_board(
                job_board_integration_id=str(integration_id),
                job_id="test_job_5"
            )

            if result.get("status") != "failed":
                print_failure(f"Expected status='failed', got '{result.get('status')}'")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Import failed for disabled integration")

            if "disabled" not in result.get("error", "").lower():
                print_failure(f"Expected 'disabled' in error, got: {result.get('error')}")
                await cleanup_test_data(db, integration_id)
                return False

            print_success("Error message mentions disabled integration")

            await cleanup_test_data(db, integration_id)
            return True

    except Exception as e:
        print_failure(f"Test failed with exception: {e}")
        return False


async def main():
    """Run all manual tests."""
    print(f"\n{Colors.BOLD}{'=' * 80}")
    print(f"Import Failure Handling and Retry Mechanism - Manual Tests")
    print(f"{'=' * 80}{Colors.RESET}\n")

    tests = [
        ("Invalid API Key", test_invalid_api_key),
        ("Network Error", test_network_error),
        ("Retry After Fixing Credentials", test_retry_after_fixing_credentials),
        ("Missing Job ID", test_missing_job_id),
        ("Disabled Integration", test_disabled_integration),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_failure(f"Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))

    # Print summary
    print(f"\n{Colors.BOLD}{'=' * 80}")
    print("Test Summary")
    print(f"{'=' * 80}{Colors.RESET}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"{test_name:.<50} {status}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}{total - passed} test(s) failed{Colors.RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
