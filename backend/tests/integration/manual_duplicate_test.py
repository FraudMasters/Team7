#!/usr/bin/env python3
"""
Manual test script for duplicate detection.

This script demonstrates and verifies duplicate detection functionality
without requiring pytest or a full test environment.

Usage:
    python backend/tests/integration/manual_duplicate_test.py

This script will:
1. Create test data (job board, resume, imported resume)
2. Test duplicate detection by external ID
3. Test duplicate detection by email
4. Test duplicate detection by name and title
5. Demonstrate import log creation for skipped duplicates
6. Clean up test data

Requirements:
    - Running PostgreSQL database
    - Database tables created (migration applied)
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import async_session_maker
from models import (
    Resume,
    ResumeStatus,
    ImportedResume,
    ImportStatus,
    ImportLog,
    ImportJobStatus,
    JobBoardIntegration,
)
from services.import_service import ImportService


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")
    if details:
        print(f"     {details}")


async def setup_test_data(db):
    """Create test data for duplicate detection tests."""
    print_section("Setting Up Test Data")

    # Create job board integration
    job_board = JobBoardIntegration(
        name="Indeed Test Manual",
        api_endpoint="https://api.indeed.com/v1",
        api_key="test_key_manual_1234567890",
        enabled=True,
        config={"job_id": "manual-test-job"},
    )
    db.add(job_board)
    await db.commit()
    await db.refresh(job_board)
    print_test("Created job board", True, f"ID: {job_board.id}")

    # Create resume
    resume = Resume(
        status=ResumeStatus.PENDING,
        filename="manual_test_resume.pdf",
        raw_text="Jane Smith\nSenior Python Developer\njane.smith@example.com\n+1-555-9999-8888",
        language="en",
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    print_test("Created resume", True, f"ID: {resume.id}")

    # Create imported resume record
    imported_resume = ImportedResume(
        resume_id=resume.id,
        job_board_id=job_board.id,
        external_id="manual-ext-98765",
        source_url="https://example.com/manual/98765",
        import_status=ImportStatus.COMPLETED,
        candidate_name="Jane Smith",
        candidate_email="jane.smith@example.com",
        candidate_phone="+1-555-9999-8888",
        job_title="Senior Python Developer",
        metadata={"source": "manual-test"},
        is_active=True,
    )
    db.add(imported_resume)
    await db.commit()
    await db.refresh(imported_resume)
    print_test("Created imported resume", True, f"ID: {imported_resume.id}")

    return job_board, resume, imported_resume


async def test_duplicate_by_external_id(db, job_board, imported_resume):
    """Test duplicate detection by external ID."""
    print_section("Test 1: Duplicate Detection by External ID")

    import_service = ImportService(db)

    # Test 1a: Same external ID and job board (should detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id=str(job_board.id),
        external_id="manual-ext-98765",
    )

    passed = (
        result.is_duplicate is True and
        result.duplicate_type == "external_id" and
        result.confidence_score == 1.0 and
        result.existing_resume_id == str(imported_resume.resume_id)
    )
    print_test(
        "Duplicate detected by external_id + job_board_id",
        passed,
        f"Type: {result.duplicate_type}, Confidence: {result.confidence_score}"
    )

    # Test 1b: Different external ID (should not detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id=str(job_board.id),
        external_id="different-ext-12345",
    )

    passed = result.is_duplicate is False
    print_test(
        "No duplicate with different external_id",
        passed,
        "Correctly identified as unique resume"
    )


async def test_duplicate_by_email(db, imported_resume):
    """Test duplicate detection by email."""
    print_section("Test 2: Duplicate Detection by Email")

    import_service = ImportService(db)

    # Test 2a: Same email (should detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id="00000000-0000-0000-0000-000000000000",  # Different job board
        candidate_email="JANE.SMITH@EXAMPLE.COM",  # Uppercase
    )

    passed = (
        result.is_duplicate is True and
        result.duplicate_type == "email" and
        result.confidence_score == 0.95
    )
    print_test(
        "Duplicate detected by email (case-insensitive)",
        passed,
        f"Type: {result.duplicate_type}, Confidence: {result.confidence_score}"
    )

    # Test 2b: Different email (should not detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id="00000000-0000-0000-0000-000000000000",
        candidate_email="different@example.com",
    )

    passed = result.is_duplicate is False
    print_test(
        "No duplicate with different email",
        passed,
        "Correctly identified as unique candidate"
    )


async def test_duplicate_by_name_and_title(db, imported_resume):
    """Test duplicate detection by name and title."""
    print_section("Test 3: Duplicate Detection by Name and Title")

    import_service = ImportService(db)

    # Test 3a: Exact name and title match (should detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id="00000000-0000-0000-0000-000000000000",
        candidate_name="Jane Smith",
        job_title="Senior Python Developer",
    )

    passed = (
        result.is_duplicate is True and
        result.duplicate_type == "name_title" and
        result.confidence_score >= 0.7
    )
    print_test(
        "Duplicate detected by name + title (exact match)",
        passed,
        f"Type: {result.duplicate_type}, Confidence: {result.confidence_score}"
    )

    # Test 3b: Different name and title (should not detect duplicate)
    result = await import_service.check_duplicate(
        job_board_id="00000000-0000-0000-0000-000000000000",
        candidate_name="John Johnson",
        job_title="Product Manager",
    )

    passed = result.is_duplicate is False
    print_test(
        "No duplicate with different name and title",
        passed,
        "Correctly identified as different candidate"
    )


async def test_import_log_creation(db, job_board):
    """Test creating import logs for skipped duplicates."""
    print_section("Test 4: Import Log for Skipped Duplicates")

    import_service = ImportService(db)

    # Check for duplicate
    duplicate_result = await import_service.check_duplicate(
        job_board_id=str(job_board.id),
        external_id="manual-ext-98765",
    )

    # Create import log showing skipped status
    import_log = ImportLog(
        job_board_id=str(job_board.id),
        job_board_name=job_board.name,
        status=ImportJobStatus.SKIPPED,
        records_processed=1,
        records_succeeded=0,
        records_failed=0,
        error_message="skipped - duplicate",
        error_details={
            "duplicate_type": duplicate_result.duplicate_type,
            "existing_resume_id": duplicate_result.existing_resume_id,
            "existing_import_id": duplicate_result.existing_import_id,
            "confidence_score": duplicate_result.confidence_score,
        },
        import_metadata={
            "external_id": "manual-ext-98765",
            "duplicate_prevented": True,
        },
    )
    db.add(import_log)
    await db.commit()
    await db.refresh(import_log)

    passed = (
        import_log.status == ImportJobStatus.SKIPPED and
        import_log.error_message == "skipped - duplicate" and
        import_log.error_details["duplicate_type"] == "external_id"
    )
    print_test(
        "Import log created with SKIPPED status",
        passed,
        f"Log ID: {import_log.id}, Status: {import_log.status.value}"
    )
    print_test(
        "Import log contains duplicate details",
        import_log.error_details is not None,
        f"Duplicate type: {import_log.error_details.get('duplicate_type')}"
    )


async def test_multiple_import_attempts(db, job_board):
    """Test multiple import attempts creating multiple logs."""
    print_section("Test 5: Multiple Import Attempts")

    import_service = ImportService(db)

    # Simulate 3 import attempts
    for attempt in range(1, 4):
        duplicate_result = await import_service.check_duplicate(
            job_board_id=str(job_board.id),
            external_id="manual-ext-98765",
        )

        import_log = ImportLog(
            job_board_id=str(job_board.id),
            job_board_name=job_board.name,
            status=ImportJobStatus.SKIPPED,
            records_processed=1,
            records_succeeded=0,
            records_failed=0,
            error_message="skipped - duplicate",
            error_details={"attempt": attempt},
            import_metadata={"retry_attempt": attempt},
        )
        db.add(import_log)

    await db.commit()

    # Query logs
    from sqlalchemy import select
    query = select(ImportLog).where(
        ImportLog.job_board_id == str(job_board.id),
        ImportLog.status == ImportJobStatus.SKIPPED
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    passed = len(logs) >= 3
    print_test(
        f"Multiple import attempts create multiple logs",
        passed,
        f"Found {len(logs)} SKIPPED logs (expected at least 3)"
    )


async def test_import_statistics(db, job_board):
    """Test import statistics retrieval."""
    print_section("Test 6: Import Statistics")

    import_service = ImportService(db)

    # Get stats for specific job board
    stats = await import_service.get_import_stats(
        job_board_id=str(job_board.id)
    )

    passed = (
        "total_imports" in stats and
        "by_status" in stats and
        stats["total_imports"] > 0
    )
    print_test(
        "Import statistics retrieved",
        passed,
        f"Total imports: {stats.get('total_imports', 0)}, "
        f"By status: {stats.get('by_status', {})}"
    )


async def cleanup_test_data(db, job_board, resume):
    """Clean up test data."""
    print_section("Cleaning Up Test Data")

    # Delete import logs
    from sqlalchemy import select
    query = select(ImportLog).where(ImportLog.job_board_id == str(job_board.id))
    result = await db.execute(query)
    logs = result.scalars().all()

    for log in logs:
        await db.delete(log)
    await db.commit()
    print_test("Deleted import logs", True, f"Deleted {len(logs)} logs")

    # Delete imported resumes
    query = select(ImportedResume).where(ImportedResume.job_board_id == job_board.id)
    result = await db.execute(query)
    imports = result.scalars().all()

    for imp in imports:
        await db.delete(imp)
    await db.commit()
    print_test("Deleted imported resumes", True, f"Deleted {len(imports)} records")

    # Delete job board
    await db.delete(job_board)
    await db.commit()
    print_test("Deleted job board", True, f"Deleted: {job_board.name}")

    # Delete resume
    await db.delete(resume)
    await db.commit()
    print_test("Deleted resume", True, f"Deleted: {resume.filename}")


async def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("  DUPLICATE DETECTION MANUAL TEST")
    print("=" * 70)
    print("\nThis script tests the duplicate detection functionality.")
    print("It will create test data, run tests, then clean up.\n")

    try:
        async with async_session_maker() as db:
            # Setup
            job_board, resume, imported_resume = await setup_test_data(db)

            # Run tests
            await test_duplicate_by_external_id(db, job_board, imported_resume)
            await test_duplicate_by_email(db, imported_resume)
            await test_duplicate_by_name_and_title(db, imported_resume)
            await test_import_log_creation(db, job_board)
            await test_multiple_import_attempts(db, job_board)
            await test_import_statistics(db, job_board)

            # Cleanup
            await cleanup_test_data(db, job_board, resume)

            print_section("Test Summary")
            print("✅ All tests completed!")
            print("\nNote: If any tests failed, check the database connection")
            print("      and ensure migrations have been run.\n")

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
