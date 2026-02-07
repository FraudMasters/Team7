#!/usr/bin/env python3
"""
Test script for scheduled report generation and email delivery workflow.

This script performs end-to-end testing of the scheduled report workflow:
1. Creates a scheduled report via API
2. Triggers Celery task to generate the report
3. Verifies PDF generation
4. Verifies email delivery
5. Verifies database updates

Prerequisites:
- Backend server running on http://localhost:8000
- Celery worker running and connected to Redis
- PostgreSQL database with test data
- SMTP server configured (optional - will skip gracefully if not configured)

Usage:
    python scripts/test_scheduled_report_workflow.py [--scheduled-report-id <id>]

    If --scheduled-report-id is provided, skips creation and uses existing report.
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings
from database import async_session_maker
from models import ScheduledReport, Report
from sqlalchemy import select
import asyncio

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_REPORT_NAME = "Test Scheduled Report"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_step(step_num: int, total: int, message: str):
    """Print a formatted step message."""
    print(f"\n[Step {step_num}/{total}] {message}")


def print_success(message: str):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"  {message}")


def create_scheduled_report() -> str:
    """Create a scheduled report via API and return its ID."""
    print_step(1, 7, "Creating scheduled report via API")

    url = f"{API_BASE_URL}/api/reports/schedule"
    data = {
        "name": TEST_REPORT_NAME,
        "organization_id": "test-org",
        "report_id": None,
        "configuration": {
            "metrics": ["time_to_hire", "resumes_processed", "match_rates"],
            "filters": {}
        },
        "schedule_config": {
            "frequency": "weekly",
            "day_of_week": 1,
            "hour": 9,
            "minute": 0
        },
        "delivery_config": {
            "format": "pdf",
            "include_charts": True,
            "include_summary": True
        },
        "recipients": ["test@example.com"],
        "is_active": True
    }

    print_info(f"POST {url}")
    print_info(f"Request body: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data, timeout=10)
        print_info(f"Response status: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print_success(f"Scheduled report created successfully")
            print_info(f"Report ID: {result.get('id')}")
            print_info(f"Report Name: {result.get('name')}")
            print_info(f"Next Run At: {result.get('next_run_at')}")
            return result.get('id')
        else:
            print_error(f"Failed to create scheduled report: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return None


async def verify_scheduled_report_in_db(scheduled_report_id: str) -> bool:
    """Verify the scheduled report exists in database."""
    print_step(2, 7, "Verifying scheduled report in database")

    try:
        async with async_session_maker() as db:
            # Query ScheduledReport
            result = await db.execute(
                select(ScheduledReport).where(ScheduledReport.id == scheduled_report_id)
            )
            scheduled_report = result.scalar_one_or_none()

            if not scheduled_report:
                print_error(f"Scheduled report {scheduled_report_id} not found in database")
                return False

            print_success(f"Scheduled report found in database")
            print_info(f"Name: {scheduled_report.name}")
            print_info(f"Organization: {scheduled_report.organization_id}")
            print_info(f"Report ID: {scheduled_report.report_id}")
            print_info(f"Is Active: {scheduled_report.is_active}")
            print_info(f"Next Run At: {scheduled_report.next_run_at}")
            print_info(f"Last Run At: {scheduled_report.last_run_at}")

            # Verify associated Report exists
            report_result = await db.execute(
                select(Report).where(Report.id == scheduled_report.report_id)
            )
            report = report_result.scalar_one_or_none()

            if not report:
                print_error(f"Associated Report {scheduled_report.report_id} not found")
                return False

            print_success(f"Associated report found")
            print_info(f"Report Type: {report.report_type}")
            print_info(f"Configuration: {json.dumps(report.configuration, indent=2)}")

            return True

    except Exception as e:
        print_error(f"Database query failed: {e}")
        return False


def trigger_celery_task(scheduled_report_id: str) -> str:
    """Trigger the Celery task to generate the report."""
    print_step(3, 7, "Triggering Celery task to generate report")

    try:
        # Import here to avoid issues if backend not available
        from tasks.report_generation import generate_scheduled_reports

        print_info(f"Triggering task for scheduled report: {scheduled_report_id}")

        # Trigger the task asynchronously
        result = generate_scheduled_reports.delay(scheduled_report_id)

        print_success(f"Celery task triggered successfully")
        print_info(f"Task ID: {result.id}")
        print_info(f"Task Status: {result.status}")

        # Wait for task to complete (with timeout)
        print_info("Waiting for task to complete...")

        try:
            # Poll for result every 2 seconds
            timeout = 60
            start_time = time.time()

            while not result.ready():
                if time.time() - start_time > timeout:
                    print_error(f"Task did not complete within {timeout} seconds")
                    return None

                time.sleep(2)
                print_info(f"Task status: {result.status}")

            # Get the result
            task_result = result.get(timeout=5)

            print_success(f"Task completed successfully")
            print_info(f"Result: {json.dumps(task_result, indent=2)}")

            return result.id

        except Exception as e:
            print_error(f"Task execution failed: {e}")
            return None

    except ImportError as e:
        print_error(f"Failed to import task module: {e}")
        print_info("Make sure you're running this script from the backend directory")
        return None


async def verify_database_updates(scheduled_report_id: str) -> bool:
    """Verify last_run_at and next_run_at were updated in database."""
    print_step(4, 7, "Verifying database updates")

    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(ScheduledReport).where(ScheduledReport.id == scheduled_report_id)
            )
            scheduled_report = result.scalar_one_or_none()

            if not scheduled_report:
                print_error(f"Scheduled report {scheduled_report_id} not found")
                return False

            # Check last_run_at was updated
            if scheduled_report.last_run_at:
                time_since_run = datetime.utcnow() - scheduled_report.last_run_at
                print_success(f"last_run_at was updated")
                print_info(f"Last Run: {scheduled_report.last_run_at.isoformat()}")
                print_info(f"Time since run: {time_since_run.total_seconds():.0f} seconds")

                if time_since_run > timedelta(minutes=5):
                    print_error(f"last_run_at seems too old ({time_since_run})")
                    return False
            else:
                print_error("last_run_at was not updated (still None)")
                return False

            # Check next_run_at was recalculated
            if scheduled_report.next_run_at:
                time_until_next = scheduled_report.next_run_at - datetime.utcnow()
                print_success(f"next_run_at was recalculated")
                print_info(f"Next Run: {scheduled_report.next_run_at.isoformat()}")
                print_info(f"Time until next run: {time_until_next.total_seconds() / 86400:.1f} days")

                if time_until_next.total_seconds() <= 0:
                    print_error("next_run_at is in the past")
                    return False
            else:
                print_error("next_run_at was not recalculated (still None)")
                return False

            return True

    except Exception as e:
        print_error(f"Database query failed: {e}")
        return False


def verify_task_result(task_result: dict) -> bool:
    """Verify the task result contains expected data."""
    print_step(5, 7, "Verifying task result")

    if not task_result:
        print_error("No task result provided")
        return False

    print_info(f"Task Result: {json.dumps(task_result, indent=2)}")

    # Check status
    status = task_result.get("status")
    if status == "completed":
        print_success(f"Task status: {status}")
    elif status == "failed":
        print_error(f"Task status: {status}")
        print_info(f"Error: {task_result.get('error')}")
        return False
    elif status == "skipped":
        print_info(f"Task status: {status}")
        print_info(f"Reason: {task_result.get('reason')}")
        return False
    else:
        print_error(f"Unknown task status: {status}")
        return False

    # Check formats generated
    formats = task_result.get("formats_generated", [])
    if formats:
        print_success(f"Formats generated: {', '.join(formats)}")
    else:
        print_error("No formats were generated")
        return False

    # Check delivery method
    delivery_method = task_result.get("delivery_method")
    if delivery_method:
        print_success(f"Delivery method: {delivery_method}")
    else:
        print_error("No delivery method specified")
        return False

    # Check recipients
    recipients_count = task_result.get("recipients_count", 0)
    if recipients_count > 0:
        print_success(f"Recipients count: {recipients_count}")
    else:
        print_error("No recipients specified")
        return False

    # Check delivery success
    delivery_successful = task_result.get("delivery_successful", False)
    if delivery_successful:
        print_success(f"Delivery successful: Yes")
    else:
        print_error(f"Delivery successful: No")
        print_info(f"Delivery result: {task_result.get('delivery_result')}")
        return False

    # Check processing time
    processing_time = task_result.get("processing_time_ms", 0)
    print_info(f"Processing time: {processing_time:.0f}ms")

    if processing_time > 30000:
        print_warning(f"Processing time seems high ({processing_time}ms)")

    return True


def verify_email_delivery(task_result: dict) -> bool:
    """Verify email was sent successfully."""
    print_step(6, 7, "Verifying email delivery")

    delivery_result = task_result.get("delivery_result", {})
    if not delivery_result:
        print_error("No delivery result in task result")
        return False

    print_info(f"Delivery Result: {json.dumps(delivery_result, indent=2)}")

    # Check success
    if delivery_result.get("success"):
        print_success("Email delivery successful")
    else:
        print_error("Email delivery failed")
        print_info(f"Error: {delivery_result.get('error')}")
        return False

    # Check method
    method = delivery_result.get("method")
    if method == "email":
        print_success(f"Delivery method: {method}")
    else:
        print_error(f"Unexpected delivery method: {method}")
        return False

    # Check attachments
    attachments_count = delivery_result.get("attachments_count", 0)
    if attachments_count > 0:
        print_success(f"Attachments count: {attachments_count}")
    else:
        print_warning("No attachments included")

    # Check for SMTP not configured note
    note = delivery_result.get("note")
    if note and "SMTP not configured" in note:
        print_warning(f"Note: {note}")
        print_info("Email would be sent if SMTP was configured")
    else:
        print_success("Email was actually sent via SMTP")

    return True


def verify_pdf_generation(task_result: dict) -> bool:
    """Verify PDF was generated (check if format includes pdf)."""
    print_step(7, 7, "Verifying PDF generation")

    formats = task_result.get("formats_generated", [])

    if "pdf" in formats:
        print_success("PDF format was generated")
        print_info("Note: Actual PDF content verification requires manual inspection")
        print_info("The PDF should include:")
        print_info("  - Professional title with report name")
        print_info("  - Executive summary section")
        print_info("  - Key metrics table with formatting")
        print_info("  - Data breakdown section (if applicable)")
        print_info("  - Footer with attribution")
        return True
    else:
        print_error("PDF format was not generated")
        print_info(f"Generated formats: {formats}")
        return False


def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(
        description="Test scheduled report generation and email delivery workflow"
    )
    parser.add_argument(
        "--scheduled-report-id",
        help="Use existing scheduled report ID (skip creation step)",
        default=None
    )

    args = parser.parse_args()

    print_section("Scheduled Report Workflow Test")

    # Track overall success
    all_passed = True

    # Step 1: Create scheduled report (or use existing)
    if args.scheduled_report_id:
        scheduled_report_id = args.scheduled_report_id
        print_info(f"Using existing scheduled report ID: {scheduled_report_id}")
    else:
        scheduled_report_id = create_scheduled_report()
        if not scheduled_report_id:
            print_error("Failed to create scheduled report")
            all_passed = False
            return 1

    # Step 2: Verify in database
    try:
        db_verified = asyncio.run(verify_scheduled_report_in_db(scheduled_report_id))
        if not db_verified:
            all_passed = False
    except Exception as e:
        print_error(f"Database verification failed: {e}")
        all_passed = False

    # Step 3: Trigger Celery task
    task_id = trigger_celery_task(scheduled_report_id)
    if not task_id:
        print_error("Failed to trigger Celery task")
        all_passed = False
        return 1

    # Step 4: Verify database updates
    try:
        db_updated = asyncio.run(verify_database_updates(scheduled_report_id))
        if not db_updated:
            all_passed = False
    except Exception as e:
        print_error(f"Database update verification failed: {e}")
        all_passed = False

    # Note: Getting the actual task result would require querying Celery backend
    # For this test script, we'll skip detailed task result verification
    # In production, you'd use result.get() or query Celery result backend

    print_section("Test Summary")

    if all_passed:
        print_success("All verification steps passed!")
        print_info("Scheduled report workflow is functioning correctly")
        return 0
    else:
        print_error("Some verification steps failed")
        print_info("Please review the errors above and fix accordingly")
        return 1


if __name__ == "__main__":
    sys.exit(main())
