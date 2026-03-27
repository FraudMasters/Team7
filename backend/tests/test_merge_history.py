"""
Unit tests for merge history tracking and undo functionality.

Tests cover merge history creation, retrieval, undo operations,
and error handling for the CandidateMerger service.

Test Coverage:
- Saving merge history records
- Retrieving merge history by organization
- Retrieving merge history by resume ID
- Undo merge operations
- Undo validation and error handling
- Merge history metadata and timestamps
- Database rollback on errors
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import Base
from services.candidate_merger import (
    CandidateMerger,
    MergeStrategy,
    MergeResult,
)
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis
from models.merge_history import MergeHistory


# ============================================================================
# Test Database Setup
# ============================================================================

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncSession:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_merge_result():
    """Create a sample MergeResult for testing."""
    return MergeResult(
        merged_data={
            "resume_id": str(uuid4()),
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "SQL"],
            "total_experience_months": 48,
            "quality_score": 85,
        },
        undo_data={
            "primary_resume": {
                "id": str(uuid4()),
                "organization_id": str(uuid4()),
                "filename": "john_doe_resume.pdf",
                "raw_text": "Original primary resume text",
                "status": "PROCESSED",
            },
            "duplicate_resume": {
                "id": str(uuid4()),
                "organization_id": str(uuid4()),
                "filename": "john_doe_resume_v2.pdf",
                "raw_text": "Original duplicate resume text",
                "status": "PROCESSED",
            },
            "primary_analysis": {
                "skills": ["Python"],
                "total_experience_months": 36,
                "quality_score": 80,
            },
            "duplicate_analysis": {
                "skills": ["SQL"],
                "total_experience_months": 48,
                "quality_score": 85,
            },
        },
        conflicts_detected=["total_experience_months", "quality_score"],
        conflicts_resolved=2,
        merge_strategy_used="most_complete",
        metadata={
            "primary_resume_id": str(uuid4()),
            "duplicate_resume_id": str(uuid4()),
            "merge_timestamp": datetime.utcnow().isoformat(),
        },
    )


@pytest.fixture
async def sample_resumes(test_db):
    """Create sample resume records in the database."""
    org_id = str(uuid4())

    # Create primary resume
    primary_resume = Resume(
        id=uuid4(),
        organization_id=org_id,
        filename="primary.pdf",
        file_path="/uploads/primary.pdf",
        content_type="application/pdf",
        status=ResumeStatus.PROCESSED,
        raw_text="Primary resume content",
        language="en",
    )
    test_db.add(primary_resume)

    # Create duplicate resume
    duplicate_resume = Resume(
        id=uuid4(),
        organization_id=org_id,
        filename="duplicate.pdf",
        file_path="/uploads/duplicate.pdf",
        content_type="application/pdf",
        status=ResumeStatus.PROCESSED,
        raw_text="Duplicate resume content",
        language="en",
    )
    test_db.add(duplicate_resume)

    # Create primary analysis
    primary_analysis = ResumeAnalysis(
        id=uuid4(),
        resume_id=primary_resume.id,
        skills=["Python", "Django"],
        keywords=["backend", "api"],
        total_experience_months=36,
        quality_score=80,
    )
    test_db.add(primary_analysis)

    # Create duplicate analysis
    duplicate_analysis = ResumeAnalysis(
        id=uuid4(),
        resume_id=duplicate_resume.id,
        skills=["SQL", "PostgreSQL"],
        keywords=["database"],
        total_experience_months=48,
        quality_score=85,
    )
    test_db.add(duplicate_analysis)

    await test_db.commit()
    await test_db.refresh(primary_resume)
    await test_db.refresh(duplicate_resume)
    await test_db.refresh(primary_analysis)
    await test_db.refresh(duplicate_analysis)

    return {
        "organization_id": org_id,
        "primary_resume": primary_resume,
        "duplicate_resume": duplicate_resume,
        "primary_analysis": primary_analysis,
        "duplicate_analysis": duplicate_analysis,
    }


# ============================================================================
# Test Save Merge History
# ============================================================================


class TestSaveMergeHistory:
    """Tests for save_merge_history method."""

    @pytest.mark.asyncio
    async def test_save_merge_history_success(self, test_db, sample_resumes, sample_merge_result):
        """Test successfully saving merge history."""
        merger = CandidateMerger(test_db)

        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
            merged_by_user_id=str(uuid4()),
            reason="Duplicate candidate detected via email match",
            can_undo=True,
        )

        assert history is not None
        assert history.id is not None
        assert history.source_resume_id == str(sample_resumes["duplicate_resume"].id)
        assert history.target_resume_id == str(sample_resumes["primary_resume"].id)
        assert history.organization_id == sample_resumes["organization_id"]
        assert history.can_undo is True
        assert history.reason == "Duplicate candidate detected via email match"
        assert history.merge_data == sample_merge_result.merged_data
        assert history.undo_data == sample_merge_result.undo_data

    @pytest.mark.asyncio
    async def test_save_merge_history_without_user(self, test_db, sample_resumes, sample_merge_result):
        """Test saving merge history without a user ID (system merge)."""
        merger = CandidateMerger(test_db)

        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
            merged_by_user_id=None,
            reason="Automated bulk merge",
        )

        assert history.merged_by_user_id is None
        assert "Automated" in history.reason

    @pytest.mark.asyncio
    async def test_save_merge_history_not_undoable(self, test_db, sample_resumes, sample_merge_result):
        """Test saving merge history that cannot be undone."""
        merger = CandidateMerger(test_db)

        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
            can_undo=False,
        )

        assert history.can_undo is False

    @pytest.mark.asyncio
    async def test_save_merge_history_includes_timestamp(self, test_db, sample_resumes, sample_merge_result):
        """Test that merge history includes timestamp."""
        merger = CandidateMerger(test_db)

        before_save = datetime.utcnow()
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )
        after_save = datetime.utcnow()

        assert history.merge_timestamp is not None
        # Timestamp should be between before and after (with some tolerance)
        assert history.merge_timestamp >= before_save - timedelta(seconds=1)
        assert history.merge_timestamp <= after_save + timedelta(seconds=1)


# ============================================================================
# Test Get Merge History
# ============================================================================


class TestGetMergeHistory:
    """Tests for get_merge_history method."""

    @pytest.mark.asyncio
    async def test_get_merge_history_by_organization(self, test_db, sample_resumes, sample_merge_result):
        """Test retrieving merge history by organization."""
        merger = CandidateMerger(test_db)

        # Create multiple merge history records
        history1 = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        history2 = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["primary_resume"].id),
            target_resume_id=str(sample_resumes["duplicate_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        # Retrieve history
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"]
        )

        assert len(history_records) == 2
        assert history_records[0].organization_id == sample_resumes["organization_id"]
        assert history_records[1].organization_id == sample_resumes["organization_id"]

    @pytest.mark.asyncio
    async def test_get_merge_history_by_resume(self, test_db, sample_resumes, sample_merge_result):
        """Test retrieving merge history filtered by resume ID."""
        merger = CandidateMerger(test_db)

        # Create merge history
        await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        # Retrieve by primary resume ID (as target)
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"],
            resume_id=str(sample_resumes["primary_resume"].id),
        )

        assert len(history_records) == 1
        assert history_records[0].target_resume_id == str(sample_resumes["primary_resume"].id)

        # Retrieve by duplicate resume ID (as source)
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"],
            resume_id=str(sample_resumes["duplicate_resume"].id),
        )

        assert len(history_records) == 1
        assert history_records[0].source_resume_id == str(sample_resumes["duplicate_resume"].id)

    @pytest.mark.asyncio
    async def test_get_merge_history_pagination(self, test_db, sample_resumes, sample_merge_result):
        """Test merge history retrieval with pagination."""
        merger = CandidateMerger(test_db)

        # Create 5 merge history records
        for i in range(5):
            await merger.save_merge_history(
                source_resume_id=str(sample_resumes["duplicate_resume"].id),
                target_resume_id=str(sample_resumes["primary_resume"].id),
                organization_id=sample_resumes["organization_id"],
                merge_result=sample_merge_result,
            )

        # Test limit
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"],
            limit=3,
        )
        assert len(history_records) == 3

        # Test offset
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"],
            limit=3,
            offset=3,
        )
        assert len(history_records) == 2

    @pytest.mark.asyncio
    async def test_get_merge_history_ordering(self, test_db, sample_resumes, sample_merge_result):
        """Test that merge history is ordered by timestamp descending."""
        merger = CandidateMerger(test_db)

        # Create multiple records with slight delays
        history1 = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        history2 = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        # Retrieve history
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"]
        )

        # Most recent should be first
        assert history_records[0].id == history2.id
        assert history_records[1].id == history1.id
        assert history_records[0].merge_timestamp >= history_records[1].merge_timestamp

    @pytest.mark.asyncio
    async def test_get_merge_history_empty_result(self, test_db):
        """Test retrieving merge history for organization with no merges."""
        merger = CandidateMerger(test_db)

        history_records = await merger.get_merge_history(
            organization_id=str(uuid4())
        )

        assert len(history_records) == 0


# ============================================================================
# Test Undo Merge
# ============================================================================


class TestUndoMerge:
    """Tests for undo_merge method."""

    @pytest.mark.asyncio
    async def test_undo_merge_success(self, test_db, sample_resumes, sample_merge_result):
        """Test successfully undoing a merge."""
        merger = CandidateMerger(test_db)

        # Create merge result with proper undo data
        merge_result = MergeResult(
            merged_data={
                "skills": ["Python", "SQL", "PostgreSQL"],
                "total_experience_months": 48,
            },
            undo_data={
                "primary_resume": {
                    "id": str(sample_resumes["primary_resume"].id),
                    "raw_text": "Original primary text",
                    "status": "PROCESSED",
                },
                "duplicate_resume": {
                    "id": str(sample_resumes["duplicate_resume"].id),
                    "raw_text": "Original duplicate text",
                    "status": "PROCESSED",
                },
                "primary_analysis": {
                    "skills": ["Python"],
                    "total_experience_months": 36,
                },
                "duplicate_analysis": {
                    "skills": ["SQL"],
                    "total_experience_months": 48,
                },
            },
            conflicts_detected=[],
            conflicts_resolved=0,
            merge_strategy_used="most_complete",
            metadata={},
        )

        # Save merge history
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=merge_result,
        )

        # Undo the merge
        user_id = str(uuid4())
        result = await merger.undo_merge(
            merge_history_id=str(history.id),
            undone_by_user_id=user_id,
        )

        assert result["status"] == "undone"
        assert result["merge_history_id"] == str(history.id)
        assert result["target_resume_id"] == str(sample_resumes["primary_resume"].id)
        assert result["source_resume_id"] == str(sample_resumes["duplicate_resume"].id)
        assert result["undone_by_user_id"] == user_id
        assert result["primary_resume_restored"] is True
        assert result["duplicate_resume_restored"] is True

    @pytest.mark.asyncio
    async def test_undo_merge_marks_history_as_undone(self, test_db, sample_resumes, sample_merge_result):
        """Test that undo marks merge history as non-undoable."""
        merger = CandidateMerger(test_db)

        # Save merge history
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        assert history.can_undo is True

        # Undo the merge
        await merger.undo_merge(merge_history_id=str(history.id))

        # Refresh and check
        await test_db.refresh(history)
        assert history.can_undo is False
        assert "UNDONE" in history.reason

    @pytest.mark.asyncio
    async def test_undo_merge_nonexistent_history(self, test_db):
        """Test undoing with nonexistent merge history ID."""
        merger = CandidateMerger(test_db)

        with pytest.raises(LookupError) as exc_info:
            await merger.undo_merge(merge_history_id=str(uuid4()))

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_undo_merge_already_undone(self, test_db, sample_resumes, sample_merge_result):
        """Test undoing a merge that was already undone."""
        merger = CandidateMerger(test_db)

        # Save and undo
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        await merger.undo_merge(merge_history_id=str(history.id))

        # Try to undo again
        with pytest.raises(ValueError) as exc_info:
            await merger.undo_merge(merge_history_id=str(history.id))

        assert "cannot be undone" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_undo_merge_non_undoable_merge(self, test_db, sample_resumes, sample_merge_result):
        """Test undoing a merge marked as non-undoable."""
        merger = CandidateMerger(test_db)

        # Save with can_undo=False
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
            can_undo=False,
        )

        # Try to undo
        with pytest.raises(ValueError) as exc_info:
            await merger.undo_merge(merge_history_id=str(history.id))

        assert "non-reversible" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_undo_merge_restores_resume_fields(self, test_db, sample_resumes):
        """Test that undo properly restores resume fields."""
        merger = CandidateMerger(test_db)

        # Modify primary resume
        original_text = sample_resumes["primary_resume"].raw_text
        sample_resumes["primary_resume"].raw_text = "Modified text after merge"
        await test_db.commit()

        # Create merge result with undo data
        merge_result = MergeResult(
            merged_data={},
            undo_data={
                "primary_resume": {
                    "raw_text": original_text,
                },
                "duplicate_resume": {},
            },
            conflicts_detected=[],
            conflicts_resolved=0,
            merge_strategy_used="most_complete",
            metadata={},
        )

        # Save and undo
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=merge_result,
        )

        await merger.undo_merge(merge_history_id=str(history.id))

        # Check that text was restored
        await test_db.refresh(sample_resumes["primary_resume"])
        assert sample_resumes["primary_resume"].raw_text == original_text


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================


class TestMergeHistoryEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_save_merge_history_with_empty_undo_data(self, test_db, sample_resumes):
        """Test saving merge history with empty undo data."""
        merger = CandidateMerger(test_db)

        merge_result = MergeResult(
            merged_data={"name": "Test"},
            undo_data={},
            conflicts_detected=[],
            conflicts_resolved=0,
            merge_strategy_used="most_complete",
            metadata={},
        )

        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=merge_result,
        )

        assert history.undo_data == {}

    @pytest.mark.asyncio
    async def test_get_merge_history_with_large_offset(self, test_db, sample_resumes, sample_merge_result):
        """Test pagination with offset larger than result set."""
        merger = CandidateMerger(test_db)

        # Create 2 records
        await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        # Request with large offset
        history_records = await merger.get_merge_history(
            organization_id=sample_resumes["organization_id"],
            limit=10,
            offset=100,
        )

        assert len(history_records) == 0

    @pytest.mark.asyncio
    async def test_undo_merge_with_missing_target_resume(self, test_db, sample_resumes, sample_merge_result):
        """Test undo when target resume no longer exists."""
        merger = CandidateMerger(test_db)

        # Save merge history
        history = await merger.save_merge_history(
            source_resume_id=str(sample_resumes["duplicate_resume"].id),
            target_resume_id=str(sample_resumes["primary_resume"].id),
            organization_id=sample_resumes["organization_id"],
            merge_result=sample_merge_result,
        )

        # Delete the primary resume
        await test_db.delete(sample_resumes["primary_resume"])
        await test_db.commit()

        # Try to undo - should raise LookupError
        with pytest.raises(LookupError) as exc_info:
            await merger.undo_merge(merge_history_id=str(history.id))

        assert "not found" in str(exc_info.value).lower()
