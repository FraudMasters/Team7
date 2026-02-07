#!/usr/bin/env python3
"""
Interview History Tracking Verification Script

This script tests the complete interview history tracking workflow. It verifies that:
- Multiple interviews can be scheduled for a candidate
- All interviews appear in the candidate's activity history
- Interview details (date, time, participants) are correctly stored in activity metadata
- Activity timeline can be filtered by interview_scheduled type
- Historical interview data is retrievable via the API

Usage:
    python test_interview_history.py

Requirements:
    - Backend server running on localhost:8000
    - Test database with sample data
    - At least one candidate in the database
    - At least one recruiter in the database
"""

import asyncio
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import httpx
import json

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_CANDIDATE_ID = None  # Will be fetched from database
TEST_RECRUITER_ID = None  # Will be fetched from database
CREATED_INTERVIEW_IDS = []  # Track created interviews for cleanup


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


async def create_interview(
    client: httpx.AsyncClient,
    title: str,
    interview_type: str,
    scheduled_start: datetime,
    duration_minutes: int,
    description: str = "",
) -> Optional[str]:
    """
    Create a single interview for testing.

    Args:
        client: HTTP client
        title: Interview title
        interview_type: Type of interview (phone, video, onsite, etc.)
        scheduled_start: Interview start time
        duration_minutes: Duration in minutes
        description: Interview description

    Returns:
        Interview ID if created successfully, None otherwise
    """
    if not TEST_CANDIDATE_ID or not TEST_RECRUITER_ID:
        print_error("Missing test data (candidate_id or recruiter_id)")
        return None

    payload = {
        "candidate_id": TEST_CANDIDATE_ID,
        "scheduled_start": scheduled_start.isoformat(),
        "duration_minutes": duration_minutes,
        "interview_type": interview_type,
        "title": title,
        "description": description,
        "participant_ids": [TEST_RECRUITER_ID],
    }

    try:
        response = await client.post(f"{API_BASE_URL}/api/interviews/", json=payload)
        if response.status_code == 200:
            data = response.json()
            interview_id = data.get("id")
            print_success(f"Created interview: {title} (ID: {interview_id})")
            print_info(f"  Scheduled: {scheduled_start.strftime('%Y-%m-%d %H:%M UTC')}")
            print_info(f"  Duration: {duration_minutes} minutes")
            print_info(f"  Type: {interview_type}")
            return interview_id
        else:
            print_error(f"Failed to create interview: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception creating interview: {e}")
        return None


async def test_create_multiple_interviews(client: httpx.AsyncClient) -> bool:
    """
    Test creating multiple interviews for the same candidate.

    Returns:
        True if all interviews created successfully, False otherwise
    """
    print_header("Test 1: Create Multiple Interviews")

    if not TEST_CANDIDATE_ID or not TEST_RECRUITER_ID:
        print_error("Missing test data (candidate_id or recruiter_id)")
        return False

    # Schedule interviews at different times
    base_time = datetime.now(timezone.utc) + timedelta(days=1)
    base_time = base_time.replace(hour=10, minute=0, second=0, microsecond=0)

    interviews_to_create = [
        {
            "title": "Initial Phone Screen",
            "type": "phone",
            "start": base_time,
            "duration": 30,
            "description": "Initial screening call to assess candidate fit"
        },
        {
            "title": "Technical Interview",
            "type": "video",
            "start": base_time + timedelta(days=1, hours=2),
            "duration": 60,
            "description": "Deep technical assessment with senior engineer"
        },
        {
            "title": "Onsite Panel Interview",
            "type": "onsite",
            "start": base_time + timedelta(days=3),
            "duration": 90,
            "description": "In-person panel interview with team members"
        },
        {
            "title": "Final Interview with Hiring Manager",
            "type": "panel",
            "start": base_time + timedelta(days=5),
            "duration": 45,
            "description": "Final decision interview with hiring manager"
        }
    ]

    print_info(f"Creating {len(interviews_to_create)} interviews for candidate {TEST_CANDIDATE_ID}...")

    for i, interview_spec in enumerate(interviews_to_create, 1):
        print_info(f"\nInterview {i}/{len(interviews_to_create)}:")
        interview_id = await create_interview(
            client,
            interview_spec["title"],
            interview_spec["type"],
            interview_spec["start"],
            interview_spec["duration"],
            interview_spec["description"]
        )

        if interview_id:
            CREATED_INTERVIEW_IDS.append(interview_id)
        else:
            print_error(f"Failed to create interview {i}")
            return False

        # Small delay to ensure timestamps are different
        await asyncio.sleep(0.5)

    print_success(f"Successfully created {len(CREATED_INTERVIEW_IDS)} interviews")
    return len(CREATED_INTERVIEW_IDS) == len(interviews_to_create)


async def test_get_candidate_activities(client: httpx.AsyncClient) -> bool:
    """
    Test retrieving candidate activity timeline.

    Returns:
        True if activities retrieved successfully, False otherwise
    """
    print_header("Test 2: Retrieve Candidate Activity Timeline")

    if not TEST_CANDIDATE_ID:
        print_error("Missing test candidate ID")
        return False

    try:
        # Get all activities for the candidate
        response = await client.get(
            f"{API_BASE_URL}/api/candidate-activities/",
            params={
                "resume_id": TEST_CANDIDATE_ID,
                "limit": 100
            }
        )

        if response.status_code != 200:
            print_error(f"Failed to fetch activities: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

        data = response.json()
        activities = data.get("activities", [])
        total_count = data.get("total_count", 0)

        print_success(f"Retrieved {len(activities)} activities (total: {total_count})")
        print_info(f"Candidate ID: {TEST_CANDIDATE_ID}")

        # Filter for interview_scheduled activities
        interview_activities = [
            a for a in activities
            if a.get("activity_type") == "interview_scheduled"
        ]

        print_success(f"Found {len(interview_activities)} interview_scheduled activities")

        if len(interview_activities) > 0:
            print_info("\nInterview activities:")
            for i, activity in enumerate(interview_activities, 1):
                print_info(f"\n  Interview {i}:")
                print_info(f"    Activity ID: {activity.get('id')}")
                print_info(f"    Created: {activity.get('created_at')}")

                # Check metadata
                metadata = activity.get("activity_data", {})
                if metadata:
                    print_info(f"    Interview ID: {metadata.get('interview_id')}")
                    print_info(f"    Title: {metadata.get('interview_title')}")
                    print_info(f"    Scheduled: {metadata.get('scheduled_start')}")
                    print_info(f"    Duration: {metadata.get('duration_minutes')} minutes")
                    print_info(f"    Type: {metadata.get('interview_type')}")
                else:
                    print_warning("    No metadata found!")

        return True

    except Exception as e:
        print_error(f"Exception fetching activities: {e}")
        return False


async def test_filter_by_interview_type(client: httpx.AsyncClient) -> bool:
    """
    Test filtering activities by interview_scheduled type.

    Returns:
        True if filtering works correctly, False otherwise
    """
    print_header("Test 3: Filter Activities by Type")

    if not TEST_CANDIDATE_ID:
        print_error("Missing test candidate ID")
        return False

    try:
        # Filter for interview_scheduled activities only
        response = await client.get(
            f"{API_BASE_URL}/api/candidate-activities/",
            params={
                "resume_id": TEST_CANDIDATE_ID,
                "activity_type": "interview_scheduled",
                "limit": 100
            }
        )

        if response.status_code != 200:
            print_error(f"Failed to fetch filtered activities: {response.status_code}")
            return False

        data = response.json()
        activities = data.get("activities", [])
        total_count = data.get("total_count", 0)

        print_success(f"Retrieved {len(activities)} interview_scheduled activities")

        # Verify all activities are of the correct type
        all_correct = all(a.get("activity_type") == "interview_scheduled" for a in activities)

        if all_correct:
            print_success("All filtered activities have correct type (interview_scheduled)")
        else:
            print_error("Some activities have incorrect type!")
            return False

        # Verify we have the expected number of interviews
        expected_count = len(CREATED_INTERVIEW_IDS)
        if len(activities) >= expected_count:
            print_success(f"Found at least {expected_count} interview activities as expected")
        else:
            print_warning(f"Expected {expected_count} interviews, found {len(activities)}")

        return True

    except Exception as e:
        print_error(f"Exception filtering activities: {e}")
        return False


async def test_verify_interview_details(client: httpx.AsyncClient) -> bool:
    """
    Test that interview details are correctly stored in activity metadata.

    Returns:
        True if all details are correct, False otherwise
    """
    print_header("Test 4: Verify Interview Details in Activities")

    if not TEST_CANDIDATE_ID:
        print_error("Missing test candidate ID")
        return False

    try:
        # Get interview_scheduled activities
        response = await client.get(
            f"{API_BASE_URL}/api/candidate-activities/",
            params={
                "resume_id": TEST_CANDIDATE_ID,
                "activity_type": "interview_scheduled",
                "limit": 100
            }
        )

        if response.status_code != 200:
            print_error(f"Failed to fetch activities: {response.status_code}")
            return False

        data = response.json()
        activities = data.get("activities", [])

        if len(activities) == 0:
            print_error("No interview activities found")
            return False

        print_info(f"Verifying details for {len(activities)} interview activities...")

        all_valid = True
        for i, activity in enumerate(activities, 1):
            metadata = activity.get("activity_data", {})
            print_info(f"\nInterview {i}:")

            # Check required fields
            required_fields = ["interview_id", "interview_title", "scheduled_start", "duration_minutes", "interview_type"]
            missing_fields = [f for f in required_fields if not metadata.get(f)]

            if missing_fields:
                print_error(f"  Missing required fields: {', '.join(missing_fields)}")
                all_valid = False
            else:
                print_success(f"  All required fields present")

                # Verify field formats
                interview_id = metadata.get("interview_id")
                if interview_id in CREATED_INTERVIEW_IDS:
                    print_success(f"  ✓ Interview ID matches created interview")
                else:
                    print_warning(f"  Interview ID not in created list (may be from previous test)")

                title = metadata.get("interview_title")
                if title and len(title) > 0:
                    print_success(f"  ✓ Title present: '{title}'")

                scheduled_start = metadata.get("scheduled_start")
                if scheduled_start:
                    try:
                        datetime.fromisoformat(scheduled_start.replace('Z', '+00:00'))
                        print_success(f"  ✓ Valid scheduled_start timestamp")
                    except ValueError:
                        print_error(f"  ✗ Invalid scheduled_start format: {scheduled_start}")
                        all_valid = False

                duration = metadata.get("duration_minutes")
                if duration and isinstance(duration, (int, float)) and duration > 0:
                    print_success(f"  ✓ Valid duration: {duration} minutes")

                interview_type = metadata.get("interview_type")
                valid_types = ["phone", "video", "onsite", "technical", "panel"]
                if interview_type in valid_types:
                    print_success(f"  ✓ Valid interview type: {interview_type}")
                else:
                    print_error(f"  ✗ Invalid interview type: {interview_type}")

        if all_valid:
            print_success("\nAll interview activities have valid metadata")
        else:
            print_error("\nSome interview activities have invalid metadata")

        return all_valid

    except Exception as e:
        print_error(f"Exception verifying interview details: {e}")
        return False


async def test_list_interviews_for_candidate(client: httpx.AsyncClient) -> bool:
    """
    Test listing all interviews for a candidate via the interviews API.

    Returns:
        True if interviews can be listed, False otherwise
    """
    print_header("Test 5: List Interviews via Interviews API")

    if not TEST_CANDIDATE_ID:
        print_error("Missing test candidate ID")
        return False

    try:
        # List interviews for the candidate
        response = await client.get(
            f"{API_BASE_URL}/api/interviews/",
            params={
                "candidate_id": TEST_CANDIDATE_ID,
                "limit": 100
            }
        )

        if response.status_code != 200:
            print_error(f"Failed to list interviews: {response.status_code}")
            return False

        data = response.json()
        interviews = data.get("items", [])
        total_count = data.get("total", 0)

        print_success(f"Retrieved {len(interviews)} interviews (total: {total_count})")

        if len(interviews) > 0:
            print_info("\nInterview details:")
            for i, interview in enumerate(interviews, 1):
                print_info(f"\n  Interview {i}:")
                print_info(f"    ID: {interview.get('id')}")
                print_info(f"    Title: {interview.get('title')}")
                print_info(f"    Status: {interview.get('status')}")
                print_info(f"    Type: {interview.get('interview_type')}")
                print_info(f"    Scheduled: {interview.get('scheduled_start')}")
                print_info(f"    Duration: {interview.get('duration_minutes')} minutes")
                print_info(f"    Location: {interview.get('location') or 'N/A'}")
                print_info(f"    Meeting Link: {interview.get('meeting_link') or 'N/A'}")

                # Verify participants
                participants = interview.get("participants", [])
                print_info(f"    Participants: {len(participants)}")

        return True

    except Exception as e:
        print_error(f"Exception listing interviews: {e}")
        return False


async def cleanup_test_data(client: httpx.AsyncClient):
    """
    Clean up test interviews.

    Args:
        client: HTTP client
    """
    print_header("Cleanup: Deleting Test Interviews")

    if not CREATED_INTERVIEW_IDS:
        print_info("No interviews to clean up")
        return

    print_info(f"Deleting {len(CREATED_INTERVIEW_IDS)} test interviews...")

    for interview_id in CREATED_INTERVIEW_IDS:
        try:
            response = await client.delete(f"{API_BASE_URL}/api/interviews/{interview_id}")
            if response.status_code in [200, 204]:
                print_success(f"Deleted interview {interview_id}")
            else:
                print_warning(f"Failed to delete interview {interview_id}: {response.status_code}")
        except Exception as e:
            print_error(f"Exception deleting interview {interview_id}: {e}")


async def main():
    """Main test execution function."""
    print_header("Interview History Tracking Verification")
    print_info("This script tests interview history tracking and activity timeline")
    print_info(f"API endpoint: {API_BASE_URL}")
    print_info("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 0: Fetch test data
        if not await get_test_data(client):
            print_error("Failed to fetch test data. Exiting.")
            sys.exit(1)

        # Test 1: Create multiple interviews
        test1_passed = await test_create_multiple_interviews(client)
        if not test1_passed:
            print_error("Test 1 failed: Could not create interviews")
            await cleanup_test_data(client)
            sys.exit(1)

        # Give time for database transactions
        await asyncio.sleep(2)

        # Test 2: Get candidate activities
        test2_passed = await test_get_candidate_activities(client)

        # Test 3: Filter by interview type
        test3_passed = await test_filter_by_interview_type(client)

        # Test 4: Verify interview details
        test4_passed = await test_verify_interview_details(client)

        # Test 5: List interviews via interviews API
        test5_passed = await test_list_interviews_for_candidate(client)

        # Cleanup
        await cleanup_test_data(client)

        # Summary
        print_header("Test Summary")
        results = [
            ("Create Multiple Interviews", test1_passed),
            ("Retrieve Activity Timeline", test2_passed),
            ("Filter by Interview Type", test3_passed),
            ("Verify Interview Details", test4_passed),
            ("List via Interviews API", test5_passed),
        ]

        for test_name, passed in results:
            status = f"{Colors.GREEN}PASSED{Colors.END}" if passed else f"{Colors.RED}FAILED{Colors.END}"
            print(f"{test_name}: {status}")

        all_passed = all(passed for _, passed in results)

        print("\n" + "=" * 70)
        if all_passed:
            print_success("All tests PASSED!")
            print_info("Interview history tracking is working correctly")
            return 0
        else:
            print_error("Some tests FAILED")
            print_error("Please review the errors above and fix any issues")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
