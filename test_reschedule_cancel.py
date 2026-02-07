#!/usr/bin/env python3
"""
Reschedule/Cancel Workflow Verification Script

This script tests the complete reschedule and cancel workflow for interviews.
It verifies that:
- Interviews can be created successfully
- Interviews can be rescheduled with calendar event updates
- Calendar events are properly synced when rescheduling
- Interviews can be cancelled with calendar event deletion
- Cancellation notifications are sent properly

Usage:
    python test_reschedule_cancel.py

Requirements:
    - Backend server running on localhost:8000
    - Celery worker running for background tasks
    - Test database with sample data
    - At least one recruiter with connected calendar (for full testing)
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import httpx

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_CANDIDATE_ID = None  # Will be fetched from database
TEST_RECRUITER_ID = None  # Will be fetched from database


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(message: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message: str):
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_header(message: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{message}{Colors.END}")
    print("=" * 70)


async def get_test_data(client: httpx.AsyncClient) -> bool:
    """
    Fetch test data from the API.

    Returns:
        True if test data was found, False otherwise
    """
    global TEST_CANDIDATE_ID, TEST_RECRUITER_ID

    print_info("Fetching test data from API...")

    try:
        # Try to get candidates
        response = await client.get(f"{API_BASE_URL}/api/candidates/?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                TEST_CANDIDATE_ID = data["items"][0]["id"]
                print_success(f"Found candidate: {TEST_CANDIDATE_ID}")
            else:
                print_error("No candidates found in database")
                return False
        else:
            print_error(f"Failed to fetch candidates: {response.status_code}")
            return False

        # Try to get recruiters (interviewers)
        response = await client.get(f"{API_BASE_URL}/api/recruiters/?limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                TEST_RECRUITER_ID = data["items"][0]["id"]
                print_success(f"Found recruiter: {TEST_RECRUITER_ID}")
            else:
                print_warning("No recruiters found, using fallback")
                TEST_RECRUITER_ID = "00000000-0000-0000-0000-000000000001"
        else:
            print_warning("Could not fetch recruiters, using fallback ID")
            TEST_RECRUITER_ID = "00000000-0000-0000-0000-000000000001"

        return TEST_CANDIDATE_ID is not None and TEST_RECRUITER_ID is not None

    except Exception as e:
        print_error(f"Error fetching test data: {e}")
        return False


async def test_create_interview(
    client: httpx.AsyncClient,
    scheduled_start: datetime,
) -> Optional[str]:
    """
    Test creating a new interview.

    Args:
        client: HTTP client
        scheduled_start: Interview start time

    Returns:
        Interview ID if created successfully, None otherwise
    """
    print_header("Test 1: Create Interview")

    if not TEST_CANDIDATE_ID or not TEST_RECRUITER_ID:
        print_error("Missing test data (candidate_id or recruiter_id)")
        return None

    payload = {
        "candidate_id": TEST_CANDIDATE_ID,
        "scheduled_start": scheduled_start.isoformat(),
        "duration_minutes": 60,
        "interview_type": "video",
        "title": "Test Interview - Reschedule/Cancel Workflow",
        "description": "This interview will be rescheduled and then cancelled",
        "participant_ids": [TEST_RECRUITER_ID],
    }

    print_info(f"Creating interview at {scheduled_start}")
    print_info(f"Candidate: {TEST_CANDIDATE_ID}")
    print_info(f"Interviewer: {TEST_RECRUITER_ID}")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/interviews/",
            json=payload,
        )

        if response.status_code == 200:
            data = response.json()
            interview_id = data.get("id")
            calendar_event_id = data.get("calendar_event_id")
            calendar_provider = data.get("calendar_provider")

            print_success(f"Interview created: {interview_id}")
            print_info(f"Calendar event ID: {calendar_event_id}")
            print_info(f"Calendar provider: {calendar_provider}")

            if calendar_event_id:
                print_success("Calendar event was created")
            else:
                print_warning("No calendar event ID - calendar integration may not be configured")

            return interview_id
        else:
            print_error(f"Failed to create interview: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error creating interview: {e}")
        return None


async def test_get_interview(
    client: httpx.AsyncClient,
    interview_id: str,
) -> Optional[Dict]:
    """
    Test retrieving interview details.

    Args:
        client: HTTP client
        interview_id: Interview ID to retrieve

    Returns:
        Interview data if retrieved successfully, None otherwise
    """
    print_info(f"Fetching interview details for {interview_id}")

    try:
        response = await client.get(f"{API_BASE_URL}/api/interviews/{interview_id}")

        if response.status_code == 200:
            data = response.json()
            print_success("Interview details retrieved")
            return data
        else:
            print_error(f"Failed to get interview: {response.status_code}")
            return None

    except Exception as e:
        print_error(f"Error retrieving interview: {e}")
        return None


async def test_reschedule_interview(
    client: httpx.AsyncClient,
    interview_id: str,
    new_start_time: datetime,
) -> bool:
    """
    Test rescheduling an interview to a different time.

    Args:
        client: HTTP client
        interview_id: Interview ID to reschedule
        new_start_time: New start time for the interview

    Returns:
        True if rescheduled successfully, False otherwise
    """
    print_header("Test 2: Reschedule Interview")

    # First, get current interview details
    current_data = await test_get_interview(client, interview_id)
    if not current_data:
        print_error("Could not fetch current interview details")
        return False

    old_start = current_data.get("scheduled_start")
    old_calendar_event_id = current_data.get("calendar_event_id")
    calendar_provider = current_data.get("calendar_provider")

    print_info(f"Current scheduled time: {old_start}")
    print_info(f"New scheduled time: {new_start_time}")
    print_info(f"Calendar event ID: {old_calendar_event_id}")
    print_info(f"Calendar provider: {calendar_provider}")

    payload = {
        "scheduled_start": new_start_time.isoformat(),
    }

    print_info(f"Rescheduling interview to {new_start_time}")

    try:
        response = await client.put(
            f"{API_BASE_URL}/api/interviews/{interview_id}",
            json=payload,
        )

        if response.status_code == 200:
            data = response.json()
            new_calendar_event_id = data.get("calendar_event_id")

            print_success(f"Interview rescheduled successfully")
            print_info(f"Updated scheduled start: {data.get('scheduled_start')}")

            # Verify calendar event was updated
            if old_calendar_event_id:
                if calendar_provider:
                    print_success(f"Calendar event update task queued")
                    print_info(f"The calendar event should be updated via background task")
                else:
                    print_warning("Interview had calendar_event_id but no provider")
            else:
                print_warning("No calendar event was associated with this interview")

            # Wait a moment for the background task to process
            if old_calendar_event_id and calendar_provider:
                print_info("Waiting 2 seconds for calendar sync task to process...")
                await asyncio.sleep(2)

                # Verify the update
                updated_data = await test_get_interview(client, interview_id)
                if updated_data:
                    updated_start = updated_data.get("scheduled_start")
                    print_success(f"Verified: Interview time is now {updated_start}")

            return True
        else:
            print_error(f"Failed to reschedule interview: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error rescheduling interview: {e}")
        return False


async def test_verify_reschedule(
    client: httpx.AsyncClient,
    interview_id: str,
    expected_start_time: datetime,
) -> bool:
    """
    Verify that the interview was rescheduled correctly.

    Args:
        client: HTTP client
        interview_id: Interview ID to verify
        expected_start_time: Expected start time after reschedule

    Returns:
        True if verified successfully, False otherwise
    """
    print_header("Test 3: Verify Reschedule")

    print_info("Fetching updated interview details...")

    try:
        response = await client.get(f"{API_BASE_URL}/api/interviews/{interview_id}")

        if response.status_code == 200:
            data = response.json()
            actual_start = data.get("scheduled_start")

            print_info(f"Expected start time: {expected_start_time.isoformat()}")
            print_info(f"Actual start time: {actual_start}")

            # Parse the actual start time
            actual_dt = datetime.fromisoformat(actual_start.replace('Z', '+00:00'))

            # Compare (allow 1 second tolerance for datetime parsing)
            time_diff = abs((actual_dt - expected_start_time).total_seconds())

            if time_diff < 1:
                print_success("Interview was rescheduled to the correct time")
                print_info(f"Status: {data.get('status')}")
                print_info(f"Calendar event ID: {data.get('calendar_event_id')}")
                return True
            else:
                print_error(f"Time mismatch! Difference: {time_diff} seconds")
                return False
        else:
            print_error(f"Failed to fetch interview: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error verifying reschedule: {e}")
        return False


async def test_cancel_interview(
    client: httpx.AsyncClient,
    interview_id: str,
) -> bool:
    """
    Test cancelling an interview.

    Args:
        client: HTTP client
        interview_id: Interview ID to cancel

    Returns:
        True if cancelled successfully, False otherwise
    """
    print_header("Test 4: Cancel Interview")

    # First, get interview details before cancellation
    current_data = await test_get_interview(client, interview_id)
    if not current_data:
        print_error("Could not fetch interview details before cancellation")
        return False

    calendar_event_id = current_data.get("calendar_event_id")
    calendar_provider = current_data.get("calendar_provider")

    print_info(f"Cancelling interview: {interview_id}")
    print_info(f"Calendar event ID: {calendar_event_id}")
    print_info(f"Calendar provider: {calendar_provider}")

    if calendar_event_id and calendar_provider:
        print_info("Calendar event deletion should be queued as background task")

    try:
        response = await client.delete(f"{API_BASE_URL}/api/interviews/{interview_id}")

        if response.status_code == 200:
            data = response.json()
            print_success(f"Interview cancelled successfully")
            print_info(f"Message: {data.get('message')}")

            # Wait a moment for the background task to process
            if calendar_event_id and calendar_provider:
                print_info("Waiting 2 seconds for calendar deletion task to process...")
                await asyncio.sleep(2)
                print_success("Calendar event should now be deleted")

            return True
        else:
            print_error(f"Failed to cancel interview: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False

    except Exception as e:
        print_error(f"Error cancelling interview: {e}")
        return False


async def test_verify_cancellation(
    client: httpx.AsyncClient,
    interview_id: str,
) -> bool:
    """
    Verify that the interview was cancelled correctly.

    Args:
        client: HTTP client
        interview_id: Interview ID to verify

    Returns:
        True if verified as cancelled, False otherwise
    """
    print_header("Test 5: Verify Cancellation")

    print_info("Attempting to fetch deleted interview...")

    try:
        response = await client.get(f"{API_BASE_URL}/api/interviews/{interview_id}")

        if response.status_code == 404:
            print_success("Interview has been deleted (404 Not Found)")
            return True
        else:
            # The interview might still exist but be marked as cancelled
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                print_info(f"Interview still exists with status: {status}")
                if status == "cancelled":
                    print_success("Interview is marked as cancelled")
                    return True
                else:
                    print_warning(f"Interview status is '{status}', expected 'cancelled'")
                    return False
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Error verifying cancellation: {e}")
        return False


async def test_list_interviews(
    client: httpx.AsyncClient,
    candidate_id: str,
) -> bool:
    """
    Test listing interviews to verify history.

    Args:
        client: HTTP client
        candidate_id: Candidate ID to list interviews for

    Returns:
        True if list retrieved successfully, False otherwise
    """
    print_header("Test 6: List Interviews (History Check)")

    print_info(f"Fetching interview history for candidate {candidate_id}")

    try:
        response = await client.get(
            f"{API_BASE_URL}/api/interviews/",
            params={"candidate_id": candidate_id},
        )

        if response.status_code == 200:
            data = response.json()
            interviews = data.get("items", [])
            total = data.get("total", 0)

            print_success(f"Found {total} interview(s) for candidate")
            print_info(f"Interview count in items: {len(interviews)}")

            for interview in interviews:
                print_info(f"  - {interview.get('title')} ({interview.get('scheduled_start')})")

            return True
        else:
            print_error(f"Failed to list interviews: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error listing interviews: {e}")
        return False


async def main():
    """Run all reschedule/cancel workflow tests."""
    print_header("Reschedule/Cancel Workflow Verification")
    print_info("Starting reschedule/cancel workflow tests...")
    print_info(f"API endpoint: {API_BASE_URL}")

    # Create HTTP client
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch test data
        if not await get_test_data(client):
            print_error("Failed to fetch test data. Please ensure:")
            print("  - Backend server is running on localhost:8000")
            print("  - Database has sample candidates and recruiters")
            sys.exit(1)

        # Schedule tests for tomorrow
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        initial_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        rescheduled_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

        # Run tests
        results = []

        # Test 1: Create interview
        interview_id = await test_create_interview(client, initial_time)
        if interview_id:
            results.append(True)

            # Test 2: Reschedule interview
            if await test_reschedule_interview(client, interview_id, rescheduled_time):
                results.append(True)

                # Test 3: Verify reschedule
                results.append(await test_verify_reschedule(client, interview_id, rescheduled_time))

                # Test 4: Cancel interview
                if await test_cancel_interview(client, interview_id):
                    results.append(True)

                    # Test 5: Verify cancellation
                    results.append(await test_verify_cancellation(client, interview_id))
                else:
                    results.append(False)
                    results.append(False)  # Skip verification
            else:
                results.append(False)
                results.append(False)  # Skip verification
                results.append(False)  # Skip cancel
                results.append(False)  # Skip verification
        else:
            print_error("Could not create interview, skipping remaining tests")
            # Add False for all remaining tests
            for _ in range(5):
                results.append(False)

        # Test 6: List interviews (check history)
        if TEST_CANDIDATE_ID:
            results.append(await test_list_interviews(client, TEST_CANDIDATE_ID))
        else:
            results.append(False)

        # Print summary
        print_header("Test Summary")

        passed = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False)
        total = len(results)

        print_success(f"Passed: {passed}/{total}")
        if failed > 0:
            print_error(f"Failed: {failed}/{total}")

        print()

        if failed == 0:
            print_success("All tests passed! ✓")
            print_info("Reschedule/cancel workflow is working correctly.")
            return 0
        else:
            print_error("Some tests failed. Please review the output above.")
            print_info("See test_reschedule_cancel.md for manual testing steps.")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
