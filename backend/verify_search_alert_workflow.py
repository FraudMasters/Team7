#!/usr/bin/env python3
"""
End-to-end verification script for search alert workflow.

This script verifies the complete search alert workflow:
1. Create saved search with filters
2. Upload new resume that matches criteria
3. Trigger Celery task to process
4. Verify SearchAlert record created
5. Verify email notification sent (simulated)
6. Verify alert marked as sent

Usage:
    cd backend
    python verify_search_alert_workflow.py

Requirements:
    - Backend services running (or can use test database)
    - All models and tasks imported successfully
"""
import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db
from models.resume import Resume, ResumeStatus
from models.saved_search import SavedSearch
from models.search_alert import SearchAlert
from tasks.search_alerts_task import (
    check_resume_against_saved_searches,
    send_search_alert_notification,
    process_pending_alerts,
)


# Colors for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(message: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_step(step_num: int, total: int, message: str) -> None:
    """Print step header."""
    print(f"\n{Colors.BOLD}Step {step_num}/{total}: {message}{Colors.END}")
    print("-" * 60)


async def create_test_resume(
    db: AsyncSession,
    filename: str,
    raw_text: str,
    skills: list,
    experience_years: int,
) -> Resume:
    """
    Create a test resume record.

    Args:
        db: Database session
        filename: Resume filename
        raw_text: Raw text content of resume
        skills: List of skills extracted from resume
        experience_years: Years of experience

    Returns:
        Created Resume instance
    """
    resume = Resume(
        filename=filename,
        file_path=f"/test/{filename}",
        content_type="application/pdf",
        status=ResumeStatus.COMPLETED,
        raw_text=raw_text,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    print_success(f"Created test resume: {resume.id}")
    print_info(f"  - Filename: {filename}")
    print_info(f"  - Skills: {', '.join(skills)}")
    print_info(f"  - Experience: {experience_years} years")

    return resume


async def create_saved_search(
    db: AsyncSession,
    name: str,
    query: str,
    filters: dict,
) -> SavedSearch:
    """
    Create a saved search.

    Args:
        db: Database session
        name: Name for the saved search
        query: Search query string
        filters: Filter criteria dict

    Returns:
        Created SavedSearch instance
    """
    saved_search = SavedSearch(
        name=name,
        query=query,
        filters=filters,
    )
    db.add(saved_search)
    await db.commit()
    await db.refresh(saved_search)

    print_success(f"Created saved search: {saved_search.id}")
    print_info(f"  - Name: {name}")
    print_info(f"  - Query: {query}")
    print_info(f"  - Filters: {filters}")

    return saved_search


async def verify_search_alert_created(
    db: AsyncSession,
    saved_search_id: str,
    resume_id: str,
) -> SearchAlert:
    """
    Verify that a SearchAlert record was created.

    Args:
        db: Database session
        saved_search_id: UUID of saved search
        resume_id: UUID of resume

    Returns:
        SearchAlert instance if found

    Raises:
        AssertionError: If alert not found
    """
    stmt = select(SearchAlert).where(
        SearchAlert.saved_search_id == saved_search_id,
        SearchAlert.resume_id == resume_id,
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if alert is None:
        raise AssertionError(
            f"SearchAlert not found for saved_search_id={saved_search_id}, "
            f"resume_id={resume_id}"
        )

    print_success(f"SearchAlert record created: {alert.id}")
    print_info(f"  - is_sent: {alert.is_sent}")
    print_info(f"  - created_at: {alert.created_at}")

    return alert


async def count_pending_alerts(db: AsyncSession) -> int:
    """Count number of pending (unsent) alerts."""
    stmt = select(func.count(SearchAlert.id)).where(SearchAlert.is_sent == False)
    result = await db.execute(stmt)
    count = result.scalar()
    return count


async def main_verification():
    """
    Main verification function that tests the complete search alert workflow.
    """
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Search Alert Workflow - End-to-End Verification")
    print(f"{'='*60}{Colors.END}\n")

    # Use test database
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./verify_search_alerts.db"
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables
    from models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        try:
            # Step 1: Create saved search with filters
            print_step(1, 6, "Create saved search with filters")
            saved_search = await create_saved_search(
                db=db,
                name="Senior Python Developers",
                query="Python AND (Django OR FastAPI)",
                filters={
                    "skills": ["Python", "Django", "FastAPI"],
                    "min_experience_years": 5,
                    "location": "Remote",
                },
            )

            # Step 2: Upload new resume that matches criteria
            print_step(2, 6, "Create/upload matching resume")
            resume = await create_test_resume(
                db=db,
                filename="john_developer.pdf",
                raw_text=(
                    "John Doe - Senior Python Developer\n\n"
                    "Experience:\n"
                    "- 7 years of experience in Python development\n"
                    "- Expert in Django and FastAPI frameworks\n"
                    "- Built RESTful APIs and web applications\n"
                    "- Worked remotely for global teams\n\n"
                    "Skills:\n"
                    "- Python (Expert)\n"
                    "- Django (Advanced)\n"
                    "- FastAPI (Advanced)\n"
                    "- PostgreSQL (Intermediate)\n"
                    "- Docker (Intermediate)\n"
                ),
                skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker"],
                experience_years=7,
            )

            # Step 3: Trigger Celery task to process
            print_step(3, 6, "Trigger check_resume_against_saved_searches task")

            resume_data = {
                "skills": resume.raw_text,  # Using raw_text for skill extraction
                "experience_years": 7,
                "location": "Remote",
                "education": "Bachelor's",
                "raw_text": resume.raw_text,
            }

            # Extract skills from raw_text for better matching
            from analyzers.hf_skill_extractor import extract_resume_skills
            try:
                skills_result = extract_resume_skills(resume.raw_text)
                resume_data["skills"] = skills_result.get("skills", [])
            except Exception as e:
                print_info(f"Skill extraction failed, using default: {e}")
                resume_data["skills"] = ["Python", "Django", "FastAPI"]

            print_info(f"Calling check_resume_against_saved_searches...")
            task_result = check_resume_against_saved_searches(
                resume_id=str(resume.id),
                resume_data=resume_data,
            )

            print_success(f"Task completed: {task_result['status']}")
            print_info(f"  - Total searches checked: {task_result['total_searches_checked']}")
            print_info(f"  - Matches found: {task_result['matches_found']}")
            print_info(f"  - Alerts created: {task_result['alerts_created']}")
            print_info(f"  - Processing time: {task_result.get('processing_time_ms', 'N/A')}ms")

            # Verify task results
            assert task_result["status"] == "completed", "Task should complete successfully"
            assert task_result["matches_found"] >= 1, "Should find at least 1 match"
            assert task_result["alerts_created"] >= 1, "Should create at least 1 alert"

            # Step 4: Verify SearchAlert record created
            print_step(4, 6, "Verify SearchAlert record created in database")
            alert = await verify_search_alert_created(
                db=db,
                saved_search_id=saved_search.id,
                resume_id=resume.id,
            )

            assert alert.is_sent is False, "Alert should not be sent yet"
            assert alert.error_message is None, "Alert should not have errors"

            # Count pending alerts
            pending_count = await count_pending_alerts(db)
            print_info(f"Total pending alerts: {pending_count}")

            # Step 5: Process pending alerts (simulating email notification)
            print_step(5, 6, "Process pending alerts (send notifications)")

            print_info(f"Calling process_pending_alerts...")
            process_result = process_pending_alerts(batch_size=50)

            print_success(f"Processing completed: {process_result['status']}")
            print_info(f"  - Total alerts processed: {process_result['total_alerts_processed']}")
            print_info(f"  - Successful sends: {process_result['successful_sends']}")
            print_info(f"  - Failed sends: {process_result['failed_sends']}")
            print_info(f"  - Remaining pending: {process_result['remaining_pending']}")
            print_info(f"  - Processing time: {process_result.get('processing_time_ms', 'N/A')}ms")

            # Verify processing results
            assert process_result["status"] == "completed", "Processing should complete"
            assert process_result["successful_sends"] >= 1, "Should send at least 1 alert"

            # Step 6: Verify alert marked as sent
            print_step(6, 6, "Verify alert marked as sent")
            await db.refresh(alert)

            print_success(f"Alert status updated:")
            print_info(f"  - is_sent: {alert.is_sent}")
            print_info(f"  - sent_at: {alert.sent_at}")
            print_info(f"  - error_message: {alert.error_message}")

            assert alert.is_sent is True, "Alert should be marked as sent"
            assert alert.sent_at is not None, "Alert should have sent_at timestamp"
            assert alert.error_message is None, "Alert should not have errors"

            # Additional verification: check that notification task was called
            print_step(7, 6, "Additional verification: send_search_alert_notification")

            # Create a new alert to test individual notification sending
            test_resume = await create_test_resume(
                db=db,
                filename="another_developer.pdf",
                raw_text="Another Python developer with Django experience",
                skills=["Python", "Django"],
                experience_years=5,
            )

            test_alert = SearchAlert(
                saved_search_id=saved_search.id,
                resume_id=test_resume.id,
                is_sent=False,
            )
            db.add(test_alert)
            await db.commit()
            await db.refresh(test_alert)

            print_info(f"Testing send_search_alert_notification for alert {test_alert.id}...")
            notification_result = send_search_alert_notification(
                alert_id=str(test_alert.id),
                saved_search_id=str(saved_search.id),
                resume_id=str(test_resume.id),
                recipient_email="test@example.com",
            )

            print_success(f"Notification task completed:")
            print_info(f"  - Status: {notification_result['status']}")
            print_info(f"  - Recipient: {notification_result['recipient']}")
            print_info(f"  - Sent at: {notification_result.get('sent_at', 'N/A')}")
            print_info(f"  - Processing time: {notification_result.get('processing_time_ms', 'N/A')}ms")

            assert notification_result["status"] == "sent", "Notification should be sent"
            assert notification_result["recipient"] == "test@example.com", "Recipient should match"

            # Final summary
            print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}")
            print("✓ All verification steps PASSED!")
            print(f"{'='*60}{Colors.END}\n")

            print(f"{Colors.BOLD}Summary:{Colors.END}")
            print(f"  ✓ Saved search created with filters")
            print(f"  ✓ Resume uploaded and processed")
            print(f"  ✓ Celery task matched resume to saved search")
            print(f"  ✓ SearchAlert record created")
            print(f"  ✓ Pending alerts processed")
            print(f"  ✓ Email notification sent (simulated)")
            print(f"  ✓ Alert marked as sent")
            print(f"  ✓ Individual notification task verified")

            print(f"\n{Colors.GREEN}Search alert workflow is working correctly!{Colors.END}\n")

            return True

        except AssertionError as e:
            print_error(f"Verification failed: {e}")
            return False

        except Exception as e:
            print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_multiple_matches():
    """
    Test scenario where one resume matches multiple saved searches.
    """
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Bonus Test: Multiple Saved Searches Match")
    print(f"{'='*60}{Colors.END}\n")

    async def run_test():
        TEST_DATABASE_URL = "sqlite+aiosqlite:///./verify_search_alerts.db"
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        from models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_maker() as db:
            try:
                # Create multiple saved searches
                search1 = await create_saved_search(
                    db=db,
                    name="Python Developers",
                    query="Python",
                    filters={"skills": ["Python"]},
                )

                search2 = await create_saved_search(
                    db=db,
                    name="FastAPI Developers",
                    query="FastAPI",
                    filters={"skills": ["FastAPI"]},
                )

                # Create resume matching both
                resume = await create_test_resume(
                    db=db,
                    filename="fullstack_dev.pdf",
                    raw_text="Fullstack developer with Python and FastAPI",
                    skills=["Python", "FastAPI", "JavaScript"],
                    experience_years=5,
                )

                # Trigger checking
                resume_data = {
                    "skills": ["Python", "FastAPI", "JavaScript"],
                    "experience_years": 5,
                    "raw_text": resume.raw_text,
                }

                task_result = check_resume_against_saved_searches(
                    resume_id=str(resume.id),
                    resume_data=resume_data,
                )

                print_success(f"Resume matched {task_result['matches_found']} saved searches")
                print_info(f"Alerts created: {task_result['alerts_created']}")

                # Verify both alerts created
                stmt = select(SearchAlert).where(SearchAlert.resume_id == resume.id)
                result = await db.execute(stmt)
                alerts = result.scalars().all()

                assert len(alerts) == 2, f"Should create 2 alerts, got {len(alerts)}"
                print_success(f"✓ Both SearchAlert records created")

                return True

            except Exception as e:
                print_error(f"Test failed: {e}")
                return False

    return asyncio.run(run_test())


def test_no_match_scenario():
    """
    Test scenario where resume doesn't match any saved searches.
    """
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Bonus Test: No Match Scenario")
    print(f"{'='*60}{Colors.END}\n")

    async def run_test():
        TEST_DATABASE_URL = "sqlite+aiosqlite:///./verify_search_alerts.db"
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        from models.base import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_maker() as db:
            try:
                # Create saved search with specific requirements
                search = await create_saved_search(
                    db=db,
                    name="Senior Java Architects",
                    query="Java AND Architect",
                    filters={
                        "skills": ["Java", "Spring", "Kubernetes"],
                        "min_experience_years": 10,
                    },
                )

                # Create resume that doesn't match
                resume = await create_test_resume(
                    db=db,
                    filename="junior_python.pdf",
                    raw_text="Junior Python developer with 1 year of experience",
                    skills=["Python", "Flask"],
                    experience_years=1,
                )

                # Trigger checking
                resume_data = {
                    "skills": ["Python", "Flask"],
                    "experience_years": 1,
                    "raw_text": resume.raw_text,
                }

                task_result = check_resume_against_saved_searches(
                    resume_id=str(resume.id),
                    resume_data=resume_data,
                )

                print_success(f"No matches found (as expected)")
                print_info(f"Matches: {task_result['matches_found']}")
                print_info(f"Alerts created: {task_result['alerts_created']}")

                # Verify no alerts created
                assert task_result["matches_found"] == 0, "Should have 0 matches"
                assert task_result["alerts_created"] == 0, "Should create 0 alerts"

                stmt = select(func.count(SearchAlert.id)).where(
                    SearchAlert.resume_id == resume.id
                )
                result = await db.execute(stmt)
                count = result.scalar()

                assert count == 0, f"Should have 0 alerts, got {count}"
                print_success(f"✓ No SearchAlert records created (correct)")

                return True

            except Exception as e:
                print_error(f"Test failed: {e}")
                return False

    return asyncio.run(run_test())


if __name__ == "__main__":
    # Run main verification
    main_success = asyncio.run(main_verification())

    # Run bonus tests
    multi_success = test_multiple_matches()
    no_match_success = test_no_match_scenario()

    # Exit with appropriate code
    if main_success and multi_success and no_match_success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All tests PASSED! ✓{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests FAILED! ✗{Colors.END}\n")
        sys.exit(1)
