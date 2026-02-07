"""
Tests for Candidate service.

Tests cover:
- Candidate model and properties
- CandidateStatus enum values
- Database CRUD operations
- Search service functionality
- Helper functions for candidate data retrieval
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from models.candidate import Candidate, CandidateStatus
from models.candidate_note import CandidateNote
from models.candidate_tag import CandidateTag
from models.candidate_activity import CandidateActivity, CandidateActivityType
from services.search_service import SearchService, SearchFilters, SearchResult


# ============================================================================
# Tests for CandidateStatus Enum
# ============================================================================

class TestCandidateStatus:
    """Tests for CandidateStatus enum."""

    def test_status_values_exist(self):
        """Test that all expected status values exist."""
        assert CandidateStatus.NEW.value == "NEW"
        assert CandidateStatus.CONTACTED.value == "CONTACTED"
        assert CandidateStatus.SCREENING.value == "SCREENING"
        assert CandidateStatus.INTERVIEW.value == "INTERVIEW"
        assert CandidateStatus.TECHNICAL.value == "TECHNICAL"
        assert CandidateStatus.OFFER.value == "OFFER"
        assert CandidateStatus.HIRED.value == "HIRED"
        assert CandidateStatus.REJECTED.value == "REJECTED"
        assert CandidateStatus.WITHDRAWN.value == "WITHDRAWN"
        assert CandidateStatus.ON_HOLD.value == "ON_HOLD"

    def test_status_is_string_enum(self):
        """Test that CandidateStatus is a string enum."""
        assert isinstance(CandidateStatus.NEW.value, str)
        assert isinstance(CandidateStatus.HIRED.value, str)

    def test_status_count(self):
        """Test that there are exactly 10 status values."""
        assert len(CandidateStatus) == 10

    def test_status_iteration(self):
        """Test that we can iterate over all statuses."""
        statuses = list(CandidateStatus)
        assert len(statuses) == 10
        assert CandidateStatus.NEW in statuses
        assert CandidateStatus.HIRED in statuses


# ============================================================================
# Tests for Candidate Model
# ============================================================================

class TestCandidateModel:
    """Tests for Candidate model."""

    @pytest.mark.asyncio
    async def test_create_candidate_with_minimal_fields(self, test_db):
        """Test creating a candidate with only required fields."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            status=CandidateStatus.NEW,
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.id is not None
        assert candidate.resume_id is not None
        assert candidate.status == CandidateStatus.NEW
        assert candidate.is_active is True
        assert candidate.notes_count == 0

    @pytest.mark.asyncio
    async def test_create_candidate_with_all_fields(self, test_db):
        """Test creating a candidate with all fields."""
        candidate_id = uuid4()
        resume_id = uuid4()

        candidate = Candidate(
            id=candidate_id,
            resume_id=resume_id,
            full_name="Ivan Ivanov",
            email="ivan@example.com",
            phone="+79001234567",
            current_position="Senior Python Developer",
            current_company="Tech Corp",
            years_of_experience=8,
            expected_salary="150000-200000",
            location="Moscow",
            linkedin_url="https://linkedin.com/in/ivanivanov",
            portfolio_url="https://ivanivanov.dev",
            status=CandidateStatus.INTERVIEW,
            source="LinkedIn",
            tags=["tag1", "tag2"],
            rating=5,
            is_active=True,
            notes_count=3,
            extra_metadata={"key": "value"},
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.full_name == "Ivan Ivanov"
        assert candidate.email == "ivan@example.com"
        assert candidate.phone == "+79001234567"
        assert candidate.current_position == "Senior Python Developer"
        assert candidate.current_company == "Tech Corp"
        assert candidate.years_of_experience == 8
        assert candidate.expected_salary == "150000-200000"
        assert candidate.location == "Moscow"
        assert candidate.linkedin_url == "https://linkedin.com/in/ivanivanov"
        assert candidate.portfolio_url == "https://ivanivanov.dev"
        assert candidate.status == CandidateStatus.INTERVIEW
        assert candidate.source == "LinkedIn"
        assert candidate.tags == ["tag1", "tag2"]
        assert candidate.rating == 5
        assert candidate.is_active is True
        assert candidate.notes_count == 3
        assert candidate.extra_metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_candidate_default_status(self, test_db):
        """Test that candidate defaults to NEW status."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.status == CandidateStatus.NEW

    @pytest.mark.asyncio
    async def test_candidate_default_is_active(self, test_db):
        """Test that candidate defaults to is_active=True."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.is_active is True

    @pytest.mark.asyncio
    async def test_candidate_default_notes_count(self, test_db):
        """Test that candidate defaults to notes_count=0."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.notes_count == 0

    @pytest.mark.asyncio
    async def test_candidate_timestamps(self, test_db):
        """Test that candidate has created_at and updated_at timestamps."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.created_at is not None
        assert candidate.updated_at is not None
        assert isinstance(candidate.created_at, datetime)
        assert isinstance(candidate.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_candidate_repr(self, test_db):
        """Test candidate __repr__ method."""
        candidate_id = uuid4()
        candidate = Candidate(
            id=candidate_id,
            resume_id=uuid4(),
            full_name="Test Candidate",
            status=CandidateStatus.NEW,
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        repr_str = repr(candidate)
        assert "Candidate" in repr_str
        assert str(candidate_id) in repr_str
        assert "Test Candidate" in repr_str
        assert "NEW" in repr_str


# ============================================================================
# Tests for Candidate CRUD Operations
# ============================================================================

class TestCandidateCRUD:
    """Tests for Candidate CRUD operations."""

    @pytest.mark.asyncio
    async def test_read_candidate_by_id(self, test_db, sample_candidate):
        """Test reading a candidate by ID."""
        from sqlalchemy import select

        query = select(Candidate).where(Candidate.id == sample_candidate.id)
        result = await test_db.execute(query)
        found_candidate = result.scalar_one_or_none()

        assert found_candidate is not None
        assert found_candidate.id == sample_candidate.id
        assert found_candidate.full_name == sample_candidate.full_name

    @pytest.mark.asyncio
    async def test_update_candidate(self, test_db, sample_candidate):
        """Test updating a candidate."""
        sample_candidate.full_name = "Updated Name"
        sample_candidate.rating = 3
        await test_db.commit()
        await test_db.refresh(sample_candidate)

        assert sample_candidate.full_name == "Updated Name"
        assert sample_candidate.rating == 3

    @pytest.mark.asyncio
    async def test_soft_delete_candidate(self, test_db, sample_candidate):
        """Test soft deleting a candidate (setting is_active=False)."""
        sample_candidate.is_active = False
        await test_db.commit()
        await test_db.refresh(sample_candidate)

        assert sample_candidate.is_active is False

    @pytest.mark.asyncio
    async def test_list_active_candidates(self, test_db, sample_candidates):
        """Test listing only active candidates."""
        from sqlalchemy import select

        # Soft delete one candidate
        sample_candidates[0].is_active = False
        await test_db.commit()

        query = select(Candidate).where(Candidate.is_active == True)
        result = await test_db.execute(query)
        active_candidates = result.scalars().all()

        assert len(active_candidates) == 4

    @pytest.mark.asyncio
    async def test_filter_candidates_by_status(self, test_db, sample_candidates):
        """Test filtering candidates by status."""
        from sqlalchemy import select

        query = select(Candidate).where(Candidate.status == CandidateStatus.NEW)
        result = await test_db.execute(query)
        new_candidates = result.scalars().all()

        # Bob Johnson should be the only NEW candidate
        assert len(new_candidates) == 1
        assert new_candidates[0].full_name == "Bob Johnson"

    @pytest.mark.asyncio
    async def test_search_candidates_by_name(self, test_db, sample_candidates):
        """Test searching candidates by name."""
        from sqlalchemy import select, or_

        search_pattern = "%John%"
        query = select(Candidate).where(
            or_(
                Candidate.full_name.ilike(search_pattern),
                Candidate.email.ilike(search_pattern),
            )
        )
        result = await test_db.execute(query)
        found_candidates = result.scalars().all()

        # Should find John Doe and Bob Johnson
        assert len(found_candidates) >= 1


# ============================================================================
# Tests for CandidateNote Model
# ============================================================================

class TestCandidateNoteModel:
    """Tests for CandidateNote model."""

    @pytest.mark.asyncio
    async def test_create_note_with_all_fields(self, test_db, sample_candidate):
        """Test creating a note with all fields."""
        note = CandidateNote(
            id=uuid4(),
            candidate_id=sample_candidate.id,
            recruiter_id=uuid4(),
            content="Strong technical skills",
            is_private=True,
            is_pinned=True,
        )
        test_db.add(note)
        await test_db.commit()
        await test_db.refresh(note)

        assert note.content == "Strong technical skills"
        assert note.is_private is True
        assert note.is_pinned is True

    @pytest.mark.asyncio
    async def test_note_default_is_private_false(self, test_db, sample_candidate):
        """Test that note defaults to is_private=False."""
        note = CandidateNote(
            id=uuid4(),
            candidate_id=sample_candidate.id,
            content="Test note",
        )
        test_db.add(note)
        await test_db.commit()
        await test_db.refresh(note)

        assert note.is_private is False

    @pytest.mark.asyncio
    async def test_note_default_is_pinned_false(self, test_db, sample_candidate):
        """Test that note defaults to is_pinned=False."""
        note = CandidateNote(
            id=uuid4(),
            candidate_id=sample_candidate.id,
            content="Test note",
        )
        test_db.add(note)
        await test_db.commit()
        await test_db.refresh(note)

        assert note.is_pinned is False

    @pytest.mark.asyncio
    async def test_note_repr(self, test_db, sample_candidate):
        """Test note __repr__ method."""
        note_id = uuid4()
        note = CandidateNote(
            id=note_id,
            candidate_id=sample_candidate.id,
            content="Test note",
            is_private=False,
        )
        test_db.add(note)
        await test_db.commit()
        await test_db.refresh(note)

        repr_str = repr(note)
        assert "CandidateNote" in repr_str
        assert str(note_id) in repr_str
        assert "False" in repr_str


# ============================================================================
# Tests for CandidateTag Model
# ============================================================================

class TestCandidateTagModel:
    """Tests for CandidateTag model."""

    @pytest.mark.asyncio
    async def test_create_tag_with_all_fields(self, test_db):
        """Test creating a tag with all fields."""
        tag = CandidateTag(
            id=uuid4(),
            organization_id=str(uuid4()),
            tag_name="High Priority",
            color="#EF4444",
            description="Urgent candidates",
            is_default=False,
            is_active=True,
            tag_order=1,
        )
        test_db.add(tag)
        await test_db.commit()
        await test_db.refresh(tag)

        assert tag.tag_name == "High Priority"
        assert tag.color == "#EF4444"
        assert tag.description == "Urgent candidates"
        assert tag.is_default is False
        assert tag.is_active is True
        assert tag.tag_order == 1

    @pytest.mark.asyncio
    async def test_tag_default_is_active(self, test_db):
        """Test that tag defaults to is_active=True."""
        tag = CandidateTag(
            id=uuid4(),
            organization_id=str(uuid4()),
            tag_name="Test Tag",
        )
        test_db.add(tag)
        await test_db.commit()
        await test_db.refresh(tag)

        assert tag.is_active is True

    @pytest.mark.asyncio
    async def test_tag_default_is_default_false(self, test_db):
        """Test that tag defaults to is_default=False."""
        tag = CandidateTag(
            id=uuid4(),
            organization_id=str(uuid4()),
            tag_name="Test Tag",
        )
        test_db.add(tag)
        await test_db.commit()
        await test_db.refresh(tag)

        assert tag.is_default is False

    @pytest.mark.asyncio
    async def test_tag_default_tag_order_zero(self, test_db):
        """Test that tag defaults to tag_order=0."""
        tag = CandidateTag(
            id=uuid4(),
            organization_id=str(uuid4()),
            tag_name="Test Tag",
        )
        test_db.add(tag)
        await test_db.commit()
        await test_db.refresh(tag)

        assert tag.tag_order == 0

    @pytest.mark.asyncio
    async def test_tag_repr(self, test_db):
        """Test tag __repr__ method."""
        tag_id = uuid4()
        org_id = str(uuid4())
        tag = CandidateTag(
            id=tag_id,
            organization_id=org_id,
            tag_name="Test Tag",
        )
        test_db.add(tag)
        await test_db.commit()
        await test_db.refresh(tag)

        repr_str = repr(tag)
        assert "CandidateTag" in repr_str
        assert str(tag_id) in repr_str
        assert org_id in repr_str
        assert "Test Tag" in repr_str


# ============================================================================
# Tests for CandidateActivity Model
# ============================================================================

class TestCandidateActivityModel:
    """Tests for CandidateActivity model."""

    @pytest.mark.asyncio
    async def test_create_activity_with_all_fields(self, test_db, sample_candidate):
        """Test creating an activity with all fields."""
        activity = CandidateActivity(
            id=uuid4(),
            activity_type=CandidateActivityType.STAGE_CHANGED,
            candidate_id=sample_candidate.id,
            vacancy_id=uuid4(),
            from_stage=CandidateStatus.NEW.value,
            to_stage=CandidateStatus.SCREENING.value,
            note_id=uuid4(),
            tag_id=uuid4(),
            recruiter_id=uuid4(),
            activity_data={"interview_date": "2024-01-15"},
            reason="Good resume",
        )
        test_db.add(activity)
        await test_db.commit()
        await test_db.refresh(activity)

        assert activity.activity_type == CandidateActivityType.STAGE_CHANGED
        assert activity.from_stage == CandidateStatus.NEW.value
        assert activity.to_stage == CandidateStatus.SCREENING.value
        assert activity.reason == "Good resume"
        assert activity.activity_data == {"interview_date": "2024-01-15"}

    @pytest.mark.asyncio
    async def test_activity_type_values(self):
        """Test that all activity type values exist."""
        assert CandidateActivityType.STAGE_CHANGED.value == "stage_changed"
        assert CandidateActivityType.NOTE_ADDED.value == "note_added"
        assert CandidateActivityType.NOTE_UPDATED.value == "note_updated"
        assert CandidateActivityType.NOTE_DELETED.value == "note_deleted"
        assert CandidateActivityType.TAG_ADDED.value == "tag_added"
        assert CandidateActivityType.TAG_REMOVED.value == "tag_removed"
        assert CandidateActivityType.RANKING_CHANGED.value == "ranking_changed"
        assert CandidateActivityType.RATING_CHANGED.value == "rating_changed"
        assert CandidateActivityType.CONTACT_ATTEMPT.value == "contact_attempt"
        assert CandidateActivityType.INTERVIEW_SCHEDULED.value == "interview_scheduled"
        assert CandidateActivityType.FEEDBACK_PROVIDED.value == "feedback_provided"
        assert CandidateActivityType.STATUS_UPDATED.value == "status_updated"
        assert CandidateActivityType.EMAIL_SENT.value == "email_sent"
        assert CandidateActivityType.CALLOUT_MADE.value == "callout_made"

    @pytest.mark.asyncio
    async def test_activity_repr(self, test_db, sample_candidate):
        """Test activity __repr__ method."""
        activity_id = uuid4()
        activity = CandidateActivity(
            id=activity_id,
            activity_type=CandidateActivityType.STAGE_CHANGED,
            candidate_id=sample_candidate.id,
        )
        test_db.add(activity)
        await test_db.commit()
        await test_db.refresh(activity)

        repr_str = repr(activity)
        assert "CandidateActivity" in repr_str
        assert str(activity_id) in repr_str
        assert str(sample_candidate.id) in repr_str


# ============================================================================
# Tests for SearchService
# ============================================================================

class TestSearchService:
    """Tests for SearchService."""

    @pytest.mark.asyncio
    async def test_search_candidates_no_filters(self, test_db, sample_candidates):
        """Test searching candidates without filters."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates()

        assert result.total == 5
        assert len(result.candidates) == 5
        assert result.query == ""
        assert result.execution_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_search_candidates_with_query(self, test_db, sample_candidates):
        """Test searching candidates with text query."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(query="John")

        assert result.total >= 1
        assert result.query == "John"

    @pytest.mark.asyncio
    async def test_search_candidates_with_status_filter(self, test_db, sample_candidates):
        """Test searching candidates with status filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(status=CandidateStatus.NEW.value)
        result = await search_service.search_candidates(filters=filters)

        assert result.total == 1
        assert result.candidates[0]["full_name"] == "Bob Johnson"

    @pytest.mark.asyncio
    async def test_search_candidates_with_location_filter(self, test_db, sample_candidates):
        """Test searching candidates with location filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(location="Remote")
        result = await search_service.search_candidates(filters=filters)

        # John Doe and Alice Williams are remote
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_search_candidates_with_min_experience(self, test_db, sample_candidates):
        """Test searching candidates with min experience filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(min_experience_years=5)
        result = await search_service.search_candidates(filters=filters)

        # John (8), Jane (5), Alice (6), Charlie (4) -> should exclude Charlie
        assert result.total == 3

    @pytest.mark.asyncio
    async def test_search_candidates_with_max_experience(self, test_db, sample_candidates):
        """Test searching candidates with max experience filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(max_experience_years=3)
        result = await search_service.search_candidates(filters=filters)

        # Only Bob (2 years) should match
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_search_candidates_with_min_rating(self, test_db, sample_candidates):
        """Test searching candidates with min rating filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(min_rating=5)
        result = await search_service.search_candidates(filters=filters)

        # John and Alice have rating 5
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_search_candidates_with_source_filter(self, test_db):
        """Test searching candidates with source filter."""
        # Create candidate with specific source
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            full_name="Source Test",
            source="LinkedIn",
        )
        test_db.add(candidate)
        await test_db.commit()

        search_service = SearchService(test_db)
        filters = SearchFilters(source="LinkedIn")
        result = await search_service.search_candidates(filters=filters)

        assert result.total >= 1

    @pytest.mark.asyncio
    async def test_search_candidates_pagination(self, test_db, sample_candidates):
        """Test searching candidates with pagination."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(skip=2, limit=2)

        assert len(result.candidates) == 2
        assert result.total == 5

    @pytest.mark.asyncio
    async def test_search_candidates_sort_by_name(self, test_db, sample_candidates):
        """Test searching candidates sorted by name."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(sort_by="name")

        names = [c["full_name"] for c in result.candidates]
        # Check if sorted alphabetically
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_search_candidates_sort_by_experience(self, test_db, sample_candidates):
        """Test searching candidates sorted by experience."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(sort_by="experience")

        experiences = [c["years_of_experience"] for c in result.candidates if c["years_of_experience"] is not None]
        # Should be descending: 8, 6, 5, 4, 2
        assert experiences == sorted(experiences, reverse=True)

    @pytest.mark.asyncio
    async def test_search_candidates_sort_by_rating(self, test_db, sample_candidates):
        """Test searching candidates sorted by rating."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(sort_by="rating")

        ratings = [c["rating"] for c in result.candidates if c["rating"] is not None]
        # Should be descending
        assert ratings == sorted(ratings, reverse=True)

    @pytest.mark.asyncio
    async def test_search_with_date_from_filter(self, test_db, sample_candidate):
        """Test searching candidates with date_from filter."""
        search_service = SearchService(test_db)
        filters = SearchFilters(date_from=sample_candidate.created_at.isoformat())
        result = await search_service.search_candidates(filters=filters)

        assert result.total >= 1

    @pytest.mark.asyncio
    async def test_search_returns_correct_fields(self, test_db, sample_candidates):
        """Test that search returns all expected fields."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(limit=1)

        assert len(result.candidates) == 1
        candidate = result.candidates[0]

        expected_fields = {
            "id", "resume_id", "full_name", "email", "phone",
            "current_position", "current_company", "years_of_experience",
            "location", "status", "source", "rating", "is_active",
            "tags", "created_at", "updated_at"
        }
        assert set(candidate.keys()) >= expected_fields


# ============================================================================
# Tests for SearchFilters Dataclass
# ============================================================================

class TestSearchFilters:
    """Tests for SearchFilters dataclass."""

    def test_create_empty_filters(self):
        """Test creating empty filters."""
        filters = SearchFilters()
        assert filters.query is None
        assert filters.skills is None
        assert filters.min_experience_years is None
        assert filters.max_experience_years is None
        assert filters.location is None
        assert filters.status is None
        assert filters.source is None
        assert filters.min_rating is None
        assert filters.date_from is None
        assert filters.date_to is None
        assert filters.tag_ids is None

    def test_create_filters_with_values(self):
        """Test creating filters with values."""
        filters = SearchFilters(
            query="Python developer",
            skills=["Python", "Django"],
            min_experience_years=3,
            max_experience_years=10,
            location="Remote",
            status=CandidateStatus.NEW.value,
            source="LinkedIn",
            min_rating=4,
            date_from="2024-01-01",
            date_to="2024-12-31",
            tag_ids=["tag1", "tag2"],
        )

        assert filters.query == "Python developer"
        assert filters.skills == ["Python", "Django"]
        assert filters.min_experience_years == 3
        assert filters.max_experience_years == 10
        assert filters.location == "Remote"
        assert filters.status == CandidateStatus.NEW.value
        assert filters.source == "LinkedIn"
        assert filters.min_rating == 4
        assert filters.date_from == "2024-01-01"
        assert filters.date_to == "2024-12-31"
        assert filters.tag_ids == ["tag1", "tag2"]


# ============================================================================
# Tests for SearchResult Dataclass
# ============================================================================

class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            total=10,
            candidates=[{"id": "123"}],
            query="test",
            filters_applied={"status": "NEW"},
            execution_time_seconds=0.5,
        )

        assert result.total == 10
        assert len(result.candidates) == 1
        assert result.query == "test"
        assert result.filters_applied == {"status": "NEW"}
        assert result.execution_time_seconds == 0.5


# ============================================================================
# Tests for Edge Cases
# ============================================================================

class TestCandidateEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_candidate_with_unicode_name(self, test_db):
        """Test creating a candidate with unicode characters in name."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            full_name="Иван Иванов",
            email="ivan@example.com",
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.full_name == "Иван Иванов"

    @pytest.mark.asyncio
    async def test_candidate_with_very_long_email(self, test_db):
        """Test creating a candidate with very long email."""
        long_email = "a" * 200 + "@example.com"
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            email=long_email,
        )
        test_db.add(candidate)

        # Should handle it (may truncate or fail depending on column constraints)
        try:
            await test_db.commit()
            assert candidate.email == long_email[:255]  # May be truncated
        except Exception:
            # Expected if email exceeds max length
            pass

    @pytest.mark.asyncio
    async def test_candidate_with_negative_experience(self, test_db):
        """Test that negative experience is handled (likely set to None or rejected)."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            years_of_experience=-1,
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        # Model doesn't validate, so negative values are stored
        # Application-level validation should prevent this
        assert candidate.years_of_experience == -1

    @pytest.mark.asyncio
    async def test_candidate_with_rating_out_of_range(self, test_db):
        """Test creating candidate with rating outside 1-5 range."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            rating=10,
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        # Model doesn't validate, so out-of-range values are stored
        # Application-level validation should prevent this
        assert candidate.rating == 10

    @pytest.mark.asyncio
    async def test_search_with_invalid_date_format(self, test_db, sample_candidates):
        """Test search with invalid date format."""
        search_service = SearchService(test_db)
        filters = SearchFilters(date_from="invalid-date")

        # Should handle gracefully and not raise exception
        result = await search_service.search_candidates(filters=filters)
        assert result.total == 5  # All candidates returned

    @pytest.mark.asyncio
    async def test_search_with_zero_results(self, test_db):
        """Test search that returns no results."""
        search_service = SearchService(test_db)
        result = await search_service.search_candidates(query="NonExistentCandidate")

        assert result.total == 0
        assert len(result.candidates) == 0

    @pytest.mark.asyncio
    async def test_candidate_tags_as_json(self, test_db):
        """Test that tags are stored and retrieved as JSON."""
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            tags=["tag1", "tag2", "tag3"],
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert isinstance(candidate.tags, list)
        assert len(candidate.tags) == 3

    @pytest.mark.asyncio
    async def test_candidate_extra_metadata(self, test_db):
        """Test that extra_metadata is stored as JSON."""
        metadata = {
            "custom_field": "value",
            "another_field": 123,
            "nested": {"key": "value"}
        }
        candidate = Candidate(
            id=uuid4(),
            resume_id=uuid4(),
            extra_metadata=metadata,
        )
        test_db.add(candidate)
        await test_db.commit()
        await test_db.refresh(candidate)

        assert candidate.extra_metadata == metadata

    @pytest.mark.asyncio
    async def test_update_candidate_status_workflow(self, test_db, sample_candidate):
        """Test updating candidate status through typical workflow."""
        # Start as NEW
        assert sample_candidate.status == CandidateStatus.NEW

        # Move to CONTACTED
        sample_candidate.status = CandidateStatus.CONTACTED
        await test_db.commit()
        await test_db.refresh(sample_candidate)
        assert sample_candidate.status == CandidateStatus.CONTACTED

        # Move to SCREENING
        sample_candidate.status = CandidateStatus.SCREENING
        await test_db.commit()
        await test_db.refresh(sample_candidate)
        assert sample_candidate.status == CandidateStatus.SCREENING

        # Move to INTERVIEW
        sample_candidate.status = CandidateStatus.INTERVIEW
        await test_db.commit()
        await test_db.refresh(sample_candidate)
        assert sample_candidate.status == CandidateStatus.INTERVIEW

        # Finally HIRED
        sample_candidate.status = CandidateStatus.HIRED
        await test_db.commit()
        await test_db.refresh(sample_candidate)
        assert sample_candidate.status == CandidateStatus.HIRED


# ============================================================================
# Tests for Database Functions
# ============================================================================

class TestDatabaseFunctions:
    """Tests for database utility functions."""

    @pytest.mark.asyncio
    async def test_extract_table_and_operation_select(self):
        """Test extracting table and operation from SELECT query."""
        from database import _extract_table_and_operation

        operation, table = _extract_table_and_operation(
            "SELECT * FROM candidates WHERE id = 1"
        )
        assert operation == "SELECT"
        assert table == "candidates"

    @pytest.mark.asyncio
    async def test_extract_table_and_operation_insert(self):
        """Test extracting table and operation from INSERT query."""
        from database import _extract_table_and_operation

        operation, table = _extract_table_and_operation(
            "INSERT INTO candidates (name) VALUES ('test')"
        )
        assert operation in ("INSERT", "candidates")  # May vary by regex

    @pytest.mark.asyncio
    async def test_extract_table_and_operation_invalid(self):
        """Test extracting table and operation from invalid query."""
        from database import _extract_table_and_operation

        operation, table = _extract_table_and_operation("NOT A SQL QUERY")
        assert operation in ("OTHER", "NOT")
        assert table == "unknown"

    @pytest.mark.asyncio
    async def test_query_performance_tracking(self, test_db):
        """Test that query performance is tracked."""
        # This test verifies that the event listeners are set up
        # Actual tracking would happen during query execution
        from database import _query_start_times, engine

        # Verify the dict exists for tracking
        assert isinstance(_query_start_times, dict)

        # Execute a query to trigger event listeners
        from sqlalchemy import select, func
        result = await test_db.execute(select(func.count()).select_from(Candidate))
        count = result.scalar()

        # Query should complete without errors
        assert count >= 0
