"""
Integration tests for duplicate detection in resume import flow.

This test suite validates the duplicate detection service that prevents
importing the same resume multiple times from job boards.

Test Coverage:
- Duplicate detection by external ID and job board
- Duplicate detection by candidate email
- Duplicate detection by candidate name and job title
- Integration with import log entries (SKIPPED status)
- Multiple import attempts of the same resume
"""
import asyncio
from typing import Generator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI application
import sys
from pathlib import Path
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
from services.import_service import ImportService, DuplicateCheckResult


@pytest.fixture
async def sample_job_board(db_session: AsyncSession) -> JobBoardIntegration:
    """
    Create a sample job board integration for testing.

    Args:
        db_session: Database session

    Returns:
        JobBoardIntegration instance
    """
    job_board = JobBoardIntegration(
        name="Indeed Test Integration",
        api_endpoint="https://api.indeed.com/v1",
        api_key="test_key_1234567890",
        enabled=True,
        config={"job_id": "test-job-123"},
    )
    db_session.add(job_board)
    await db_session.commit()
    await db_session.refresh(job_board)

    return job_board


@pytest.fixture
async def sample_resume(db_session: AsyncSession) -> Resume:
    """
    Create a sample resume for testing.

    Args:
        db_session: Database session

    Returns:
        Resume instance
    """
    resume = Resume(
        status=ResumeStatus.PENDING,
        filename="test_resume.pdf",
        raw_text="John Doe\nSoftware Engineer\njohn.doe@example.com\nExperience with Python and FastAPI",
        language="en",
    )
    db_session.add(resume)
    await db_session.commit()
    await db_session.refresh(resume)

    return resume


@pytest.fixture
async def imported_resume_fixture(
    db_session: AsyncSession,
    sample_resume: Resume,
    sample_job_board: JobBoardIntegration,
) -> ImportedResume:
    """
    Create a sample imported resume record for testing.

    Args:
        db_session: Database session
        sample_resume: Resume fixture
        sample_job_board: Job board fixture

    Returns:
        ImportedResume instance
    """
    imported_resume = ImportedResume(
        resume_id=sample_resume.id,
        job_board_id=sample_job_board.id,
        external_id="ext-12345",
        source_url="https://example.com/resume/12345",
        import_status=ImportStatus.COMPLETED,
        candidate_name="John Doe",
        candidate_email="john.doe@example.com",
        candidate_phone="+1-555-0123-4567",
        job_title="Software Engineer",
        metadata={"source": "indeed"},
        is_active=True,
    )
    db_session.add(imported_resume)
    await db_session.commit()
    await db_session.refresh(imported_resume)

    return imported_resume


# Pytest fixtures
@pytest.fixture(scope="module")
def client() -> Generator:
    """
    Create a test client placeholder for consistency.

    Yields:
        None (not used for these service-level tests)
    """
    yield None


@pytest.fixture
async def db_session() -> Generator:
    """
    Create a database session for testing.

    Yields:
        AsyncSession instance
    """
    async with async_session_maker() as session:
        yield session
        # Cleanup: Rollback any changes made during the test
        await session.rollback()


class TestDuplicateDetectionByExternalId:
    """Tests for duplicate detection by external ID and job board."""

    @pytest.mark.asyncio
    async def test_duplicate_detected_by_external_id(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that duplicate is detected by external ID and job board.

        This test validates:
        - ImportService detects duplicates by external_id + job_board_id
        - Returns is_duplicate=True
        - Returns correct duplicate_type (external_id)
        - Returns confidence_score of 1.0 (exact match)
        - Returns existing resume and import IDs
        """
        import_service = ImportService(db_session)

        # Check for duplicate using same external_id and job_board_id
        result = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-12345",
        )

        # Validate duplicate detected
        assert result.is_duplicate is True
        assert result.duplicate_type == "external_id"
        assert result.confidence_score == 1.0
        assert result.existing_resume_id == str(imported_resume_fixture.resume_id)
        assert result.existing_import_id == str(imported_resume_fixture.id)

        # Validate details
        assert result.details is not None
        assert result.details["external_id"] == "ext-12345"
        assert result.details["job_board_id"] == str(sample_job_board.id)

    @pytest.mark.asyncio
    async def test_no_duplicate_with_different_external_id(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that no duplicate is detected with different external ID.

        This test validates:
        - Different external_id does not trigger duplicate detection
        - Returns is_duplicate=False
        """
        import_service = ImportService(db_session)

        # Check with different external_id
        result = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-different-999",
        )

        # Validate no duplicate detected
        assert result.is_duplicate is False
        assert result.duplicate_type is None
        assert result.confidence_score is None

    @pytest.mark.asyncio
    async def test_no_duplicate_with_different_job_board(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that no duplicate is detected with different job board.

        This test validates:
        - Same external_id on different job board is not a duplicate
        - Returns is_duplicate=False
        """
        import_service = ImportService(db_session)

        # Create a different job board
        other_board = JobBoardIntegration(
            name="LinkedIn Integration",
            api_endpoint="https://api.linkedin.com/v1",
            api_key="test_key_9876543210",
            enabled=True,
        )
        db_session.add(other_board)
        await db_session.commit()

        # Check with same external_id but different job board
        result = await import_service.check_duplicate(
            job_board_id=str(other_board.id),
            external_id="ext-12345",  # Same external_id
        )

        # Validate no duplicate detected (different job board)
        assert result.is_duplicate is False
        assert result.duplicate_type is None


class TestDuplicateDetectionByEmail:
    """Tests for duplicate detection by candidate email."""

    @pytest.mark.asyncio
    async def test_duplicate_detected_by_email(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that duplicate is detected by candidate email.

        This test validates:
        - ImportService detects duplicates by candidate_email
        - Email matching is case-insensitive
        - Returns confidence_score of 0.95 (high confidence)
        """
        import_service = ImportService(db_session)

        # Check for duplicate using email
        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),  # Different job board
            candidate_email="JOHN.DOE@EXAMPLE.COM",  # Uppercase email
        )

        # Validate duplicate detected
        assert result.is_duplicate is True
        assert result.duplicate_type == "email"
        assert result.confidence_score == 0.95
        assert result.existing_resume_id == str(imported_resume_fixture.resume_id)

        # Validate details
        assert result.details["email"] == "JOHN.DOE@EXAMPLE.COM"
        assert result.details["candidate_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_email_normalization_works(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that email normalization works correctly.

        This test validates:
        - Leading/trailing whitespace is trimmed
        - Case-insensitive matching works
        - All variations of the same email are detected as duplicates
        """
        import_service = ImportService(db_session)

        # Test with various email formats
        test_emails = [
            "  john.doe@example.com  ",  # Whitespace
            "John.Doe@Example.Com",  # Mixed case
            "JOHN.DOE@EXAMPLE.COM",  # Uppercase
            "john.doe@example.com",  # Exact match
        ]

        for email in test_emails:
            result = await import_service.check_duplicate(
                job_board_id=str(uuid4()),
                candidate_email=email,
            )

            assert result.is_duplicate is True, f"Failed for email: {email}"
            assert result.duplicate_type == "email"

    @pytest.mark.asyncio
    async def test_no_duplicate_with_different_email(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that no duplicate is detected with different email.

        This test validates:
        - Different email does not trigger duplicate detection
        """
        import_service = ImportService(db_session)

        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            candidate_email="different.email@example.com",
        )

        assert result.is_duplicate is False


class TestDuplicateDetectionByNameAndTitle:
    """Tests for duplicate detection by candidate name and job title."""

    @pytest.mark.asyncio
    async def test_duplicate_detected_by_exact_name_and_title(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that duplicate is detected by exact name and title match.

        This test validates:
        - ImportService detects duplicates by candidate_name + job_title
        - Exact match returns confidence_score of 1.0
        """
        import_service = ImportService(db_session)

        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            candidate_name="John Doe",
            job_title="Software Engineer",
        )

        assert result.is_duplicate is True
        assert result.duplicate_type == "name_title"
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_duplicate_detected_by_partial_name_and_title(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that duplicate is detected by partial name match.

        This test validates:
        - Fuzzy matching catches similar names
        - Returns confidence_score >= 0.7 for good matches
        """
        import_service = ImportService(db_session)

        # Test with name that contains the original name
        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            candidate_name="John Michael Doe",  # Extended name
            job_title="Senior Software Engineer",  # Extended title
        )

        assert result.is_duplicate is True
        assert result.duplicate_type == "name_title"
        assert result.confidence_score >= 0.7

    @pytest.mark.asyncio
    async def test_no_duplicate_with_different_name_and_title(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that no duplicate is detected with completely different name and title.

        This test validates:
        - Different names don't trigger false positives
        """
        import_service = ImportService(db_session)

        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            candidate_name="Jane Smith",
            job_title="Product Manager",
        )

        assert result.is_duplicate is False

    @pytest.mark.asyncio
    async def test_name_similarity_calculation(
        self,
        db_session: AsyncSession,
        sample_resume: Resume,
        sample_job_board: JobBoardIntegration,
    ):
        """
        Test the name similarity calculation algorithm.

        This test validates:
        - Exact match returns 1.0
        - Partial match returns >= 0.7
        - No match returns < 0.7
        """
        import_service = ImportService(db_session)

        # Create test data
        imported = ImportedResume(
            resume_id=sample_resume.id,
            job_board_id=sample_job_board.id,
            external_id="test-ext-1",
            candidate_name="Robert Johnson",
            job_title="Data Scientist",
            import_status=ImportStatus.COMPLETED,
            is_active=True,
        )
        db_session.add(imported)
        await db_session.commit()

        # Test similarity calculation
        test_cases = [
            ("Robert Johnson", "Data Scientist", 1.0),  # Exact match
            ("Robert Johnson Jr.", "Data Scientist", 0.85),  # Contains
            ("Bob Johnson", "Senior Data Scientist", 0.5),  # Partial first name
            ("Alice Williams", "Data Scientist", 0.0),  # Completely different
        ]

        for name, title, min_confidence in test_cases:
            result = await import_service.check_duplicate(
                job_board_id=str(uuid4()),
                candidate_name=name,
                job_title=title,
            )

            if min_confidence >= 0.7:
                assert result.is_duplicate is True, f"Failed for {name}"
                assert result.confidence_score >= min_confidence
            else:
                assert result.is_duplicate is False, f"Should not match for {name}"


class TestDuplicateDetectionPriority:
    """Tests for duplicate detection priority order."""

    @pytest.mark.asyncio
    async def test_external_id_has_highest_priority(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that external_id check has highest priority.

        This test validates:
        - Priority 1: external_id + job_board_id
        - When all criteria match, external_id takes precedence
        """
        import_service = ImportService(db_session)

        # Provide all criteria, should detect by external_id
        result = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-12345",
            candidate_email="john.doe@example.com",
            candidate_name="John Doe",
            job_title="Software Engineer",
        )

        assert result.is_duplicate is True
        assert result.duplicate_type == "external_id"  # Highest priority
        assert result.confidence_score == 1.0

    @pytest.mark.asyncio
    async def test_email_has_second_priority(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that email check has second priority.

        This test validates:
        - Priority 2: email (if no external_id match)
        - Email takes precedence over name/title matching
        """
        import_service = ImportService(db_session)

        # Provide email and name/title, should detect by email
        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            external_id=None,  # No external_id
            candidate_email="john.doe@example.com",
            candidate_name="John Doe",
            job_title="Software Engineer",
        )

        assert result.is_duplicate is True
        assert result.duplicate_type == "email"  # Second priority
        assert result.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_name_title_has_lowest_priority(
        self,
        db_session: AsyncSession,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that name/title check has lowest priority.

        This test validates:
        - Priority 3: name + title (if no external_id or email match)
        - Used as fallback when other methods don't apply
        """
        import_service = ImportService(db_session)

        # Provide only name and title
        result = await import_service.check_duplicate(
            job_board_id=str(uuid4()),
            external_id=None,
            candidate_email=None,
            candidate_name="John Doe",
            job_title="Software Engineer",
        )

        assert result.is_duplicate is True
        assert result.duplicate_type == "name_title"  # Lowest priority
        assert result.confidence_score >= 0.7


class TestEndToEndDuplicatePrevention:
    """End-to-end tests for duplicate prevention in import flow."""

    @pytest.mark.asyncio
    async def test_import_log_shows_skipped_duplicate(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that import log shows SKIPPED status for duplicate.

        This test validates:
        - When duplicate is detected, import should be skipped
        - ImportLog should have status=SKIPPED
        - Error message should indicate duplicate
        """
        import_service = ImportService(db_session)

        # Check for duplicate
        duplicate_result = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-12345",
        )

        # Simulate creating import log based on duplicate check
        if duplicate_result.is_duplicate:
            import_log = ImportLog(
                job_board_id=str(sample_job_board.id),
                job_board_name=sample_job_board.name,
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
                    "external_id": "ext-12345",
                    "duplicate_detected": True,
                },
            )
            db_session.add(import_log)
            await db_session.commit()
            await db_session.refresh(import_log)

            # Verify import log
            assert import_log.status == ImportJobStatus.SKIPPED
            assert import_log.error_message == "skipped - duplicate"
            assert import_log.error_details["duplicate_detected"] is True
            assert import_log.error_details["duplicate_type"] == "external_id"

    @pytest.mark.asyncio
    async def test_multiple_import_attempts_create_skipped_logs(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that multiple import attempts create multiple SKIPPED logs.

        This test validates:
        - Attempting to import the same resume 3 times creates 3 SKIPPED logs
        - Each log has correct duplicate information
        """
        import_service = ImportService(db_session)

        # Simulate 3 import attempts
        for attempt in range(1, 4):
            # Check duplicate
            duplicate_result = await import_service.check_duplicate(
                job_board_id=str(sample_job_board.id),
                external_id="ext-12345",
            )

            # Create import log
            import_log = ImportLog(
                job_board_id=str(sample_job_board.id),
                job_board_name=sample_job_board.name,
                status=ImportJobStatus.SKIPPED,
                records_processed=1,
                records_succeeded=0,
                records_failed=0,
                error_message="skipped - duplicate",
                error_details={
                    "duplicate_type": duplicate_result.duplicate_type,
                    "attempt": attempt,
                },
                import_metadata={
                    "external_id": "ext-12345",
                    "retry_attempt": attempt,
                },
            )
            db_session.add(import_log)

        await db_session.commit()

        # Verify all logs were created
        query = select(ImportLog).where(
            ImportLog.job_board_id == str(sample_job_board.id),
            ImportLog.status == ImportJobStatus.SKIPPED,
            ImportLog.error_message == "skipped - duplicate",
        )
        result = await db_session.execute(query)
        skipped_logs = result.scalars().all()

        assert len(skipped_logs) == 3

        # Verify each log has unique retry_attempt
        retry_attempts = [
            log.import_metadata.get("retry_attempt") for log in skipped_logs
        ]
        assert sorted(retry_attempts) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_complete_duplicate_prevention_flow(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        sample_resume: Resume,
    ):
        """
        Test complete duplicate prevention flow.

        This test validates the entire flow:
        1. First import: No duplicate detected → Create ImportedResume
        2. Second import: Duplicate detected → Skip with log
        3. Verify import logs show correct status
        """
        import_service = ImportService(db_session)

        # Step 1: First import - no duplicate
        first_check = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-99999",
            candidate_email="new.candidate@example.com",
        )

        assert first_check.is_duplicate is False

        # Simulate successful import
        imported_resume = ImportedResume(
            resume_id=sample_resume.id,
            job_board_id=sample_job_board.id,
            external_id="ext-99999",
            import_status=ImportStatus.COMPLETED,
            candidate_name="New Candidate",
            candidate_email="new.candidate@example.com",
            is_active=True,
        )
        db_session.add(imported_resume)

        first_log = ImportLog(
            job_board_id=str(sample_job_board.id),
            job_board_name=sample_job_board.name,
            status=ImportJobStatus.SUCCESS,
            records_processed=1,
            records_succeeded=1,
            records_failed=0,
            import_metadata={"external_id": "ext-99999"},
        )
        db_session.add(first_log)
        await db_session.commit()

        # Step 2: Second import - duplicate detected
        second_check = await import_service.check_duplicate(
            job_board_id=str(sample_job_board.id),
            external_id="ext-99999",  # Same external_id
        )

        assert second_check.is_duplicate is True
        assert second_check.duplicate_type == "external_id"

        # Create skipped log
        second_log = ImportLog(
            job_board_id=str(sample_job_board.id),
            job_board_name=sample_job_board.name,
            status=ImportJobStatus.SKIPPED,
            records_processed=1,
            records_succeeded=0,
            records_failed=0,
            error_message="skipped - duplicate",
            error_details={
                "duplicate_type": second_check.duplicate_type,
                "existing_import_id": second_check.existing_import_id,
            },
            import_metadata={"external_id": "ext-99999"},
        )
        db_session.add(second_log)
        await db_session.commit()

        # Step 3: Verify logs
        query = select(ImportLog).where(
            ImportLog.job_board_id == str(sample_job_board.id)
        ).order_by(ImportLog.created_at)
        result = await db_session.execute(query)
        logs = result.scalars().all()

        assert len(logs) == 2
        assert logs[0].status == ImportJobStatus.SUCCESS  # First import
        assert logs[1].status == ImportJobStatus.SKIPPED  # Second import (duplicate)
        assert "duplicate" in logs[1].error_message


class TestImportServiceErrorHandling:
    """Tests for ImportService error handling."""

    @pytest.mark.asyncio
    async def test_invalid_job_board_id_raises_error(
        self,
        db_session: AsyncSession,
    ):
        """
        Test that invalid job_board_id raises ValueError.

        This test validates:
        - Invalid UUID format raises ValueError
        - Error message is descriptive
        """
        import_service = ImportService(db_session)

        with pytest.raises(ValueError) as exc_info:
            await import_service.check_duplicate(
                job_board_id="not-a-valid-uuid",
                external_id="ext-123",
            )

        assert "Invalid job_board_id format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_import_stats_returns_correct_data(
        self,
        db_session: AsyncSession,
        sample_job_board: JobBoardIntegration,
        imported_resume_fixture: ImportedResume,
    ):
        """
        Test that get_import_stats returns correct statistics.

        This test validates:
        - Returns total count of imported resumes
        - Returns breakdown by status
        - Can filter by job_board_id
        """
        import_service = ImportService(db_session)

        # Get stats for specific job board
        stats = await import_service.get_import_stats(
            job_board_id=str(sample_job_board.id)
        )

        assert stats["total_imports"] == 1
        assert stats["by_status"].get("completed") == 1
        assert stats["active_imports"] == 1

        # Get stats for all job boards
        all_stats = await import_service.get_import_stats()
        assert all_stats["total_imports"] >= 1


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """
    Clean up test data after each test.

    This fixture runs automatically after each test to remove
    any test data created during the test.
    """
    yield

    # Cleanup: Remove test job boards, imported resumes, and logs
    from models import ImportedResume, ImportLog, JobBoardIntegration, Resume

    # Remove test import logs
    query = select(ImportLog).where(ImportLog.job_board_name.like("%Test%"))
    result = await db_session.execute(query)
    test_logs = result.scalars().all()

    for log in test_logs:
        await db_session.delete(log)

    # Remove test imported resumes
    query = select(ImportedResume).join(JobBoardIntegration).where(
        JobBoardIntegration.name.like("%Test%")
    )
    result = await db_session.execute(query)
    test_imports = result.scalars().all()

    for imp in test_imports:
        await db_session.delete(imp)

    # Remove test job boards
    query = select(JobBoardIntegration).where(JobBoardIntegration.name.like("%Test%"))
    result = await db_session.execute(query)
    test_boards = result.scalars().all()

    for board in test_boards:
        await db_session.delete(board)

    # Remove test resumes
    query = select(Resume).where(Resume.filename.like("test_%"))
    result = await db_session.execute(query)
    test_resumes = result.scalars().all()

    for resume in test_resumes:
        await db_session.delete(resume)

    await db_session.commit()


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
