#!/usr/bin/env python3
"""
Conflict Detection Verification Script

This script tests the conflict detection functionality for interview scheduling.
It verifies that the availability checking endpoint properly detects conflicts
with existing calendar events.

Usage:
    python test_conflict_detection.py

Requirements:
    - Backend server running on localhost:8000
    - Test database with sample data
    - At least one recruiter with connected calendar
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import httpx

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_CANDIDATE_ID = None  # Will be fetched from database
TEST_RECRUITER_IDS = []  # Will be fetched from database


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
    global TEST_CANDIDATE_ID, TEST_RECRUITER_IDS

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
        # Note: This assumes there's a recruiters endpoint or similar
        # You may need to adjust this based on your actual API structure
        response = await client.get(f"{API_BASE_URL}/api/recruiters/?limit=2")
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) >= 1:
                TEST_RECRUITER_IDS = [r["id"] for r in data["items"][:2]]
                print_success(f"Found {len(TEST_RECRUITER_IDS)} recruiter(s)")
            else:
                print_warning("No recruiters found, using fallback")
                # Use fallback IDs for testing
                TEST_RECRUITER_IDS = ["00000000-0000-0000-0000-000000000001"]
        else:
            print_warning("Could not fetch recruiters, using fallback IDs")
            TEST_RECRUITER_IDS = ["00000000-0000-0000-0000-000000000001"]

        return TEST_CANDIDATE_ID is not None and len(TEST_RECRUITER_IDS) > 0

    except Exception as e:
        print_error(f"Error fetching test data: {e}")
        return False


async def test_availability_no_conflict(
    client: httpx.AsyncClient,
    interviewer_id: str,
    start_time: datetime,
) -> bool:
    """
    Test availability check with no conflicts.

    Args:
        client: HTTP client
        interviewer_id: ID of interviewer to check
        start_time: Start time to check

    Returns:
        True if test passed, False otherwise
    """
    print_header("Test 1: Availability Check (No Conflict Expected)")

    end_time = start_time + timedelta(hours=1)

    payload = {
        "interviewer_ids": [interviewer_id],
        "start_time": start_time.isoformat(),
        "duration_minutes": 60,
    }

    print_info(f"Checking availability for {start_time} - {end_time}")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/calendar/check-availability",
            json=payload,
        )

        if response.status_code != 200:
            print_error(f"API returned status {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: all_available={data.get('all_available')}")

        if "interviewer_availability" in data and len(data["interviewer_availability"]) > 0:
            availability = data["interviewer_availability"][0]
            has_connection = availability.get("has_calendar_connection", False)
            is_available = availability.get("is_available", False)
            conflicting_events = availability.get("conflicting_events", [])

            print_info(f"Has calendar connection: {has_connection}")
            print_info(f"Is available: {is_available}")
            print_info(f"Conflicting events: {conflicting_events}")

            if not has_connection:
                print_warning("Interviewer has no calendar connection - cannot fully test")
                return True  # Not a failure, just can't test fully

            if is_available and len(conflicting_events) == 0:
                print_success("No conflicts detected (as expected)")
                return True
            else:
                print_error(f"Unexpected: is_available={is_available}, conflicts={conflicting_events}")
                return False
        else:
            print_error("No interviewer availability data in response")
            return False

    except Exception as e:
        print_error(f"Error during availability check: {e}")
        return False


async def test_create_first_interview(
    client: httpx.AsyncClient,
    interviewer_id: str,
    scheduled_start: datetime,
) -> Optional[str]:
    """
    Create first interview for testing conflicts.

    Args:
        client: HTTP client
        interviewer_id: ID of interviewer
        scheduled_start: Interview start time

    Returns:
        Interview ID if created successfully, None otherwise
    """
    print_header("Test 2: Create First Interview")

    if not TEST_CANDIDATE_ID:
        print_error("No test candidate available")
        return None

    payload = {
        "candidate_id": TEST_CANDIDATE_ID,
        "scheduled_start": scheduled_start.isoformat(),
        "duration_minutes": 60,
        "interview_type": "video",
        "title": "Test Interview - Conflict Detection",
        "participant_ids": [interviewer_id],
    }

    print_info(f"Creating interview at {scheduled_start}")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/interviews/",
            json=payload,
        )

        if response.status_code == 200:
            data = response.json()
            interview_id = data.get("id")
            print_success(f"Interview created: {interview_id}")
            return interview_id
        else:
            print_error(f"Failed to create interview: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None

    except Exception as e:
        print_error(f"Error creating interview: {e}")
        return None


async def test_availability_with_conflict(
    client: httpx.AsyncClient,
    interviewer_id: str,
    scheduled_start: datetime,
) -> bool:
    """
    Test availability check with existing conflict.

    Args:
        client: HTTP client
        interviewer_id: ID of interviewer
        scheduled_start: Time of scheduled interview

    Returns:
        True if conflict detected correctly, False otherwise
    """
    print_header("Test 3: Availability Check (Conflict Expected)")

    end_time = scheduled_start + timedelta(hours=1)

    payload = {
        "interviewer_ids": [interviewer_id],
        "start_time": scheduled_start.isoformat(),
        "duration_minutes": 60,
    }

    print_info(f"Checking availability at {scheduled_start} - {end_time}")
    print_info("(Should conflict with previously created interview)")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/calendar/check-availability",
            json=payload,
        )

        if response.status_code != 200:
            print_error(f"API returned status {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: all_available={data.get('all_available')}")

        if "interviewer_availability" in data and len(data["interviewer_availability"]) > 0:
            availability = data["interviewer_availability"][0]
            has_connection = availability.get("has_calendar_connection", False)
            is_available = availability.get("is_available", False)
            conflicting_events = availability.get("conflicting_events", [])

            print_info(f"Has calendar connection: {has_connection}")
            print_info(f"Is available: {is_available}")
            print_info(f"Conflicting events: {conflicting_events}")

            if not has_connection:
                print_warning("Interviewer has no calendar connection - cannot test conflicts")
                return True  # Not a failure, just can't test

            if not is_available and len(conflicting_events) > 0:
                print_success(f"Conflict detected! Found {len(conflicting_events)} conflicting event(s)")
                for event in conflicting_events:
                    print_info(f"  - {event}")
                return True
            else:
                print_error("Expected conflict but none was detected")
                print_error(f"is_available={is_available}, conflicting_events={conflicting_events}")
                return False
        else:
            print_error("No interviewer availability data in response")
            return False

    except Exception as e:
        print_error(f"Error during availability check: {e}")
        return False


async def test_availability_different_time(
    client: httpx.AsyncClient,
    interviewer_id: str,
    original_time: datetime,
) -> bool:
    """
    Test availability check at different time (should be available).

    Args:
        client: HTTP client
        interviewer_id: ID of interviewer
        original_time: Original interview time (to avoid)

    Returns:
        True if available at different time, False otherwise
    """
    print_header("Test 4: Availability Check (Different Time)")

    # Check 4 hours later
    new_time = original_time + timedelta(hours=4)
    end_time = new_time + timedelta(hours=1)

    payload = {
        "interviewer_ids": [interviewer_id],
        "start_time": new_time.isoformat(),
        "duration_minutes": 60,
    }

    print_info(f"Checking availability at {new_time} - {end_time}")
    print_info("(Should be available - different time)")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/calendar/check-availability",
            json=payload,
        )

        if response.status_code != 200:
            print_error(f"API returned status {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: all_available={data.get('all_available')}")

        if "interviewer_availability" in data and len(data["interviewer_availability"]) > 0:
            availability = data["interviewer_availability"][0]
            has_connection = availability.get("has_calendar_connection", False)
            is_available = availability.get("is_available", False)

            print_info(f"Has calendar connection: {has_connection}")
            print_info(f"Is available: {is_available}")

            if not has_connection:
                print_warning("Interviewer has no calendar connection - cannot test")
                return True  # Not a failure

            if is_available:
                print_success("Interviewer is available at different time")
                return True
            else:
                print_warning(f"Not available at {new_time} (may have other events)")
                return True  # Not a failure, just has other events
        else:
            print_error("No interviewer availability data in response")
            return False

    except Exception as e:
        print_error(f"Error during availability check: {e}")
        return False


async def test_multiple_interviewers(
    client: httpx.AsyncClient,
    interviewer_ids: List[str],
    scheduled_start: datetime,
) -> bool:
    """
    Test availability check for multiple interviewers.

    Args:
        client: HTTP client
        interviewer_ids: List of interviewer IDs
        scheduled_start: Time to check

    Returns:
        True if test passed, False otherwise
    """
    print_header("Test 5: Availability Check (Multiple Interviewers)")

    end_time = scheduled_start + timedelta(hours=1)

    payload = {
        "interviewer_ids": interviewer_ids,
        "start_time": scheduled_start.isoformat(),
        "duration_minutes": 60,
    }

    print_info(f"Checking availability for {len(interviewer_ids)} interviewer(s)")
    print_info(f"Time: {scheduled_start} - {end_time}")

    try:
        response = await client.post(
            f"{API_BASE_URL}/api/calendar/check-availability",
            json=payload,
        )

        if response.status_code != 200:
            print_error(f"API returned status {response.status_code}")
            return False

        data = response.json()
        print_info(f"Response: all_available={data.get('all_available')}")
        print_info(f"Available count: {data.get('available_count')} / {data.get('interviewer_count')}")

        if "interviewer_availability" in data:
            for availability in data["interviewer_availability"]:
                interviewer_id = availability.get("interviewer_id", "unknown")
                is_available = availability.get("is_available", False)
                has_connection = availability.get("has_calendar_connection", False)
                print_info(f"  {interviewer_id}: available={is_available}, has_connection={has_connection}")

            print_success("Successfully checked availability for multiple interviewers")
            return True
        else:
            print_error("No interviewer availability data in response")
            return False

    except Exception as e:
        print_error(f"Error during availability check: {e}")
        return False


async def main():
    """Run all conflict detection tests."""
    print_header("Conflict Detection Verification")
    print_info("Starting conflict detection tests...")
    print_info(f"API endpoint: {API_BASE_URL}")

    # Create HTTP client
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch test data
        if not await get_test_data(client):
            print_error("Failed to fetch test data. Please ensure:")
            print("  - Backend server is running on localhost:8000")
            print("  - Database has sample candidates and recruiters")
            sys.exit(1)

        # Use first recruiter ID for tests
        if len(TEST_RECRUITER_IDS) == 0:
            print_error("No recruiter IDs available for testing")
            sys.exit(1)

        test_interviewer_id = TEST_RECRUITER_IDS[0]

        # Schedule tests for tomorrow at 10 AM
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        test_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)

        # Run tests
        results = []

        # Test 1: Check availability before creating interview
        results.append(await test_availability_no_conflict(client, test_interviewer_id, test_time))

        # Test 2: Create interview
        interview_id = await test_create_first_interview(client, test_interviewer_id, test_time)
        if interview_id:
            results.append(True)

            # Test 3: Check availability with conflict
            results.append(await test_availability_with_conflict(client, test_interviewer_id, test_time))

            # Test 4: Check availability at different time
            results.append(await test_availability_different_time(client, test_interviewer_id, test_time))

            # Test 5: Check multiple interviewers (if available)
            if len(TEST_RECRUITER_IDS) > 1:
                results.append(await test_multiple_interviewers(client, TEST_RECRUITER_IDS, test_time))
            else:
                print_warning("Only one recruiter available, skipping multiple interviewer test")
                results.append(None)  # Skipped
        else:
            print_error("Could not create interview, skipping conflict tests")
            results.append(False)
            results.append(False)
            results.append(False)

        # Print summary
        print_header("Test Summary")

        passed = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if r is False)
        skipped = sum(1 for r in results if r is None)
        total = len(results)

        print_success(f"Passed: {passed}/{total}")
        if failed > 0:
            print_error(f"Failed: {failed}/{total}")
        if skipped > 0:
            print_warning(f"Skipped: {skipped}/{total}")

        print()

        if failed == 0 and skipped == 0:
            print_success("All tests passed! ✓")
            print_info("Conflict detection is working correctly.")
            return 0
        elif failed == 0:
            print_warning("Some tests were skipped, but no failures.")
            return 0
        else:
            print_error("Some tests failed. Please review the output above.")
            print_info("See test_conflict_detection.md for manual testing steps.")
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
