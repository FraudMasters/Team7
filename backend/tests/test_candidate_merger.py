"""
Unit tests for CandidateMerger service.

Tests cover conflict detection, resolution strategies, field-level merging,
deduplication logic, and undo data generation.

Test Coverage:
- CandidateMerger initialization and configuration
- Merge strategy validation
- Field-level conflict detection
- Conflict resolution strategies (most_recent, most_complete, prefer_primary)
- Skills, keywords, and education deduplication
- Contact information merging
- Undo data generation
- Error handling for invalid inputs
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from services.candidate_merger import (
    CandidateMerger,
    MergeStrategy,
    MergeResult,
    get_candidate_merger,
)
from models.resume import Resume, ResumeStatus
from models.resume_analysis import ResumeAnalysis


class TestMergeStrategy:
    """Tests for MergeStrategy class."""

    def test_merge_strategy_constants(self):
        """Test that all merge strategy constants are defined."""
        assert MergeStrategy.MOST_RECENT == "most_recent"
        assert MergeStrategy.MOST_COMPLETE == "most_complete"
        assert MergeStrategy.PREFER_PRIMARY == "prefer_primary"
        assert MergeStrategy.CUSTOM == "custom"

    def test_is_valid_with_valid_strategies(self):
        """Test is_valid returns True for valid strategies."""
        assert MergeStrategy.is_valid("most_recent") is True
        assert MergeStrategy.is_valid("most_complete") is True
        assert MergeStrategy.is_valid("prefer_primary") is True
        assert MergeStrategy.is_valid("custom") is True

    def test_is_valid_with_invalid_strategy(self):
        """Test is_valid returns False for invalid strategies."""
        assert MergeStrategy.is_valid("invalid") is False
        assert MergeStrategy.is_valid("") is False
        assert MergeStrategy.is_valid(None) is False


class TestMergeResult:
    """Tests for MergeResult dataclass."""

    def test_merge_result_creation(self):
        """Test creating a MergeResult instance."""
        result = MergeResult(
            merged_data={"name": "John Doe"},
            undo_data={"original": "data"},
            conflicts_detected=["field1", "field2"],
            conflicts_resolved=2,
            merge_strategy_used="most_complete",
            metadata={"timestamp": "2024-01-01"},
        )

        assert result.merged_data == {"name": "John Doe"}
        assert result.undo_data == {"original": "data"}
        assert result.conflicts_detected == ["field1", "field2"]
        assert result.conflicts_resolved == 2
        assert result.merge_strategy_used == "most_complete"
        assert result.metadata == {"timestamp": "2024-01-01"}

    def test_merge_result_to_dict(self):
        """Test converting MergeResult to dictionary."""
        result = MergeResult(
            merged_data={"name": "John Doe"},
            undo_data={},
            conflicts_detected=["field1"],
            conflicts_resolved=1,
            merge_strategy_used="most_recent",
            metadata={},
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["merged_data"] == {"name": "John Doe"}
        assert result_dict["conflicts_resolved"] == 1
        assert result_dict["merge_strategy_used"] == "most_recent"


class TestCandidateMergerInitialization:
    """Tests for CandidateMerger initialization."""

    @pytest.mark.asyncio
    async def test_initialization_with_default_strategy(self, test_db):
        """Test CandidateMerger initialization with default strategy."""
        merger = CandidateMerger(test_db)

        assert merger.db == test_db
        assert merger.default_strategy == MergeStrategy.MOST_COMPLETE

    @pytest.mark.asyncio
    async def test_initialization_with_custom_strategy(self, test_db):
        """Test CandidateMerger initialization with custom strategy."""
        merger = CandidateMerger(test_db, default_strategy=MergeStrategy.MOST_RECENT)

        assert merger.default_strategy == MergeStrategy.MOST_RECENT

    @pytest.mark.asyncio
    async def test_initialization_with_invalid_strategy(self, test_db):
        """Test initialization with invalid strategy raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            CandidateMerger(test_db, default_strategy="invalid_strategy")

        assert "Invalid merge strategy" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_candidate_merger_factory(self, test_db):
        """Test get_candidate_merger factory function."""
        merger = get_candidate_merger(test_db)

        assert isinstance(merger, CandidateMerger)
        assert merger.db == test_db


class TestMergeCandidatesValidation:
    """Tests for merge_candidates input validation."""

    @pytest.mark.asyncio
    async def test_merge_with_missing_primary_id(self, test_db):
        """Test merge fails when primary_resume_id is missing."""
        merger = CandidateMerger(test_db)

        with pytest.raises(ValueError) as exc_info:
            await merger.merge_candidates("", "duplicate-id")

        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_merge_with_missing_duplicate_id(self, test_db):
        """Test merge fails when duplicate_resume_id is missing."""
        merger = CandidateMerger(test_db)

        with pytest.raises(ValueError) as exc_info:
            await merger.merge_candidates("primary-id", "")

        assert "required" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_merge_with_same_id(self, test_db):
        """Test merge fails when trying to merge resume with itself."""
        merger = CandidateMerger(test_db)
        resume_id = str(uuid4())

        with pytest.raises(ValueError) as exc_info:
            await merger.merge_candidates(resume_id, resume_id)

        assert "Cannot merge a resume with itself" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_with_invalid_strategy(self, test_db):
        """Test merge fails with invalid strategy."""
        merger = CandidateMerger(test_db)

        with pytest.raises(ValueError) as exc_info:
            await merger.merge_candidates(
                str(uuid4()), str(uuid4()), strategy="invalid"
            )

        assert "Invalid merge strategy" in str(exc_info.value)


class TestConflictDetection:
    """Tests for conflict detection across different field types."""

    def test_merge_simple_field_no_conflict_same_values(self):
        """Test simple field merge with same values detects no conflict."""
        merger = CandidateMerger(MagicMock())
        primary = {"language": "en"}
        duplicate = {"language": "en"}

        value, conflict = merger._merge_simple_field(
            "language", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert value == "en"
        assert conflict is False

    def test_merge_simple_field_no_conflict_duplicate_empty(self):
        """Test simple field merge with empty duplicate detects no conflict."""
        merger = CandidateMerger(MagicMock())
        primary = {"language": "en"}
        duplicate = {"language": None}

        value, conflict = merger._merge_simple_field(
            "language", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert value == "en"
        assert conflict is False

    def test_merge_simple_field_conflict_different_values(self):
        """Test simple field merge with different values detects conflict."""
        merger = CandidateMerger(MagicMock())
        primary = {"language": "en"}
        duplicate = {"language": "fr"}

        value, conflict = merger._merge_simple_field(
            "language", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert conflict is True

    def test_merge_text_field_conflict_different_text(self):
        """Test text field merge detects conflict with different content."""
        merger = CandidateMerger(MagicMock())
        primary = {"raw_text": "Short text"}
        duplicate = {"raw_text": "Much longer text content"}

        value, conflict = merger._merge_text_field(
            "raw_text", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert conflict is True

    def test_merge_numeric_field_conflict_different_values(self):
        """Test numeric field merge detects conflict with different values."""
        merger = CandidateMerger(MagicMock())
        primary = {"total_experience_months": 24}
        duplicate = {"total_experience_months": 36}

        value, conflict = merger._merge_numeric_field(
            "total_experience_months", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert conflict is True

    def test_merge_contact_info_conflict_different_emails(self):
        """Test contact info merge detects conflicts in email addresses."""
        merger = CandidateMerger(MagicMock())
        primary_contact = {"email": "john@example.com", "phone": "123-456-7890"}
        duplicate_contact = {"email": "john.doe@example.com", "phone": "123-456-7890"}

        merged, conflicts = merger._merge_contact_info(
            primary_contact, duplicate_contact, MergeStrategy.MOST_COMPLETE
        )

        assert "contact_info.email" in conflicts
        assert "contact_info.phone" not in conflicts


class TestConflictResolutionStrategies:
    """Tests for different conflict resolution strategies."""

    def test_prefer_primary_strategy_simple_field(self):
        """Test PREFER_PRIMARY strategy always chooses primary value."""
        merger = CandidateMerger(MagicMock())
        primary = {"language": "en"}
        duplicate = {"language": "fr"}

        value, conflict = merger._merge_simple_field(
            "language", primary, duplicate, MergeStrategy.PREFER_PRIMARY
        )

        assert value == "en"
        assert conflict is True

    def test_most_complete_strategy_text_field(self):
        """Test MOST_COMPLETE strategy prefers longer text."""
        merger = CandidateMerger(MagicMock())
        primary = {"raw_text": "Short"}
        duplicate = {"raw_text": "Much longer text content"}

        value, conflict = merger._merge_text_field(
            "raw_text", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert value == "Much longer text content"
        assert conflict is True

    def test_most_complete_strategy_numeric_field(self):
        """Test MOST_COMPLETE strategy prefers higher numeric values."""
        merger = CandidateMerger(MagicMock())
        primary = {"total_experience_months": 24}
        duplicate = {"total_experience_months": 36}

        value, conflict = merger._merge_numeric_field(
            "total_experience_months", primary, duplicate, MergeStrategy.MOST_COMPLETE
        )

        assert value == 36
        assert conflict is True

    def test_most_recent_strategy_uses_timestamps(self):
        """Test MOST_RECENT strategy uses updated_at timestamps."""
        merger = CandidateMerger(MagicMock())

        # Primary is older
        primary = {
            "language": "en",
            "updated_at": "2024-01-01T00:00:00+00:00"
        }
        # Duplicate is newer
        duplicate = {
            "language": "fr",
            "updated_at": "2024-01-15T00:00:00+00:00"
        }

        value, conflict = merger._merge_simple_field(
            "language", primary, duplicate, MergeStrategy.MOST_RECENT
        )

        assert value == "fr"  # Newer value
        assert conflict is True


class TestDeduplication:
    """Tests for deduplication of skills, education, and keywords."""

    def test_merge_skills_deduplicates_by_name(self):
        """Test skills are deduplicated by name (case-insensitive)."""
        merger = CandidateMerger(MagicMock())
        primary_skills = [
            {"name": "Python", "confidence": 0.9},
            {"name": "JavaScript", "confidence": 0.8},
        ]
        duplicate_skills = [
            {"name": "python", "confidence": 0.85},  # Duplicate (different case)
            {"name": "Java", "confidence": 0.7},
        ]

        merged = merger._merge_skills(primary_skills, duplicate_skills)

        # Should have 3 unique skills (Python, JavaScript, Java)
        assert len(merged) == 3
        skill_names = [s["name"].lower() for s in merged]
        assert "python" in skill_names
        assert "javascript" in skill_names
        assert "java" in skill_names

    def test_merge_skills_keeps_max_confidence(self):
        """Test skills merging keeps maximum confidence score."""
        merger = CandidateMerger(MagicMock())
        primary_skills = [{"name": "Python", "confidence": 0.7}]
        duplicate_skills = [{"name": "python", "confidence": 0.9}]

        merged = merger._merge_skills(primary_skills, duplicate_skills)

        assert len(merged) == 1
        python_skill = next(s for s in merged if s["name"].lower() == "python")
        assert python_skill["confidence"] == 0.9  # Max confidence

    def test_merge_keywords_deduplicates(self):
        """Test keywords are deduplicated (case-insensitive)."""
        merger = CandidateMerger(MagicMock())
        primary_keywords = ["Python", "Machine Learning", "AI"]
        duplicate_keywords = ["python", "Data Science", "AI"]

        merged = merger._merge_keywords(primary_keywords, duplicate_keywords)

        # Should have 4 unique keywords
        assert len(merged) == 4
        merged_lower = [k.lower() for k in merged]
        assert "python" in merged_lower
        assert "machine learning" in merged_lower
        assert "ai" in merged_lower
        assert "data science" in merged_lower

    def test_merge_education_deduplicates_by_institution_and_degree(self):
        """Test education is deduplicated by institution and degree."""
        merger = CandidateMerger(MagicMock())
        primary_education = [
            {"institution": "MIT", "degree": "BS Computer Science", "year": 2020},
            {"institution": "Stanford", "degree": "MS AI", "year": 2022},
        ]
        duplicate_education = [
            {"institution": "mit", "degree": "bs computer science", "year": 2020},  # Duplicate
            {"institution": "Harvard", "degree": "MBA", "year": 2024},
        ]

        merged = merger._merge_education(primary_education, duplicate_education)

        # Should have 3 unique education entries
        assert len(merged) == 3

    def test_merge_entities_combines_lists(self):
        """Test entities from both resumes are combined and deduplicated."""
        merger = CandidateMerger(MagicMock())
        primary_entities = {
            "organizations": ["Google", "Microsoft"],
            "locations": ["San Francisco"],
        }
        duplicate_entities = {
            "organizations": ["Microsoft", "Apple"],  # Microsoft is duplicate
            "skills": ["Python"],
        }

        merged = merger._merge_entities(primary_entities, duplicate_entities)

        assert "organizations" in merged
        assert "locations" in merged
        assert "skills" in merged
        # Organizations should be deduplicated
        assert len(set(merged["organizations"])) == len(merged["organizations"])


class TestTimestampComparison:
    """Tests for timestamp comparison utilities."""

    def test_is_more_recent_with_newer_timestamp(self):
        """Test is_more_recent returns True for newer timestamp."""
        merger = CandidateMerger(MagicMock())

        timestamp1 = "2024-01-15T00:00:00+00:00"
        timestamp2 = "2024-01-01T00:00:00+00:00"

        assert merger._is_more_recent(timestamp1, timestamp2) is True

    def test_is_more_recent_with_older_timestamp(self):
        """Test is_more_recent returns False for older timestamp."""
        merger = CandidateMerger(MagicMock())

        timestamp1 = "2024-01-01T00:00:00+00:00"
        timestamp2 = "2024-01-15T00:00:00+00:00"

        assert merger._is_more_recent(timestamp1, timestamp2) is False

    def test_is_more_recent_with_none_timestamps(self):
        """Test is_more_recent handles None timestamps."""
        merger = CandidateMerger(MagicMock())

        assert merger._is_more_recent(None, "2024-01-01T00:00:00+00:00") is False
        assert merger._is_more_recent("2024-01-01T00:00:00+00:00", None) is True
        assert merger._is_more_recent(None, None) is False

    def test_get_most_recent_timestamp(self):
        """Test get_most_recent_timestamp returns newer timestamp."""
        merger = CandidateMerger(MagicMock())

        timestamp1 = "2024-01-15T00:00:00+00:00"
        timestamp2 = "2024-01-01T00:00:00+00:00"

        result = merger._get_most_recent_timestamp(timestamp1, timestamp2)
        assert result == timestamp1


class TestUndoDataGeneration:
    """Tests for undo data generation."""

    def test_generate_undo_data_with_complete_resumes(self):
        """Test undo data generation with complete resume data."""
        merger = CandidateMerger(MagicMock())

        # Create mock resumes
        primary_resume = MagicMock(spec=Resume)
        primary_resume.id = uuid4()
        primary_resume.organization_id = "org-123"
        primary_resume.vacancy_id = "vac-456"
        primary_resume.filename = "primary.pdf"
        primary_resume.file_path = "/path/to/primary.pdf"
        primary_resume.content_type = "application/pdf"
        primary_resume.status = ResumeStatus.ANALYZED
        primary_resume.raw_text = "Primary resume text"
        primary_resume.language = "en"
        primary_resume.error_message = None

        duplicate_resume = MagicMock(spec=Resume)
        duplicate_resume.id = uuid4()
        duplicate_resume.organization_id = "org-123"
        duplicate_resume.vacancy_id = "vac-456"
        duplicate_resume.filename = "duplicate.pdf"
        duplicate_resume.file_path = "/path/to/duplicate.pdf"
        duplicate_resume.content_type = "application/pdf"
        duplicate_resume.status = ResumeStatus.ANALYZED
        duplicate_resume.raw_text = "Duplicate resume text"
        duplicate_resume.language = "en"
        duplicate_resume.error_message = None

        undo_data = merger._generate_undo_data(
            primary_resume, None, duplicate_resume, None
        )

        assert "primary_resume" in undo_data
        assert "duplicate_resume" in undo_data
        assert undo_data["primary_resume"]["filename"] == "primary.pdf"
        assert undo_data["duplicate_resume"]["filename"] == "duplicate.pdf"

    def test_generate_undo_data_with_analyses(self):
        """Test undo data includes analysis data when available."""
        merger = CandidateMerger(MagicMock())

        primary_resume = MagicMock(spec=Resume)
        primary_resume.id = uuid4()
        primary_resume.organization_id = "org-123"
        primary_resume.vacancy_id = None
        primary_resume.filename = "resume.pdf"
        primary_resume.file_path = "/path"
        primary_resume.content_type = "application/pdf"
        primary_resume.status = ResumeStatus.ANALYZED
        primary_resume.raw_text = "text"
        primary_resume.language = "en"
        primary_resume.error_message = None

        primary_analysis = MagicMock(spec=ResumeAnalysis)
        primary_analysis.skills = [{"name": "Python"}]
        primary_analysis.keywords = ["AI", "ML"]
        primary_analysis.entities = {"organizations": ["Google"]}
        primary_analysis.total_experience_months = 24
        primary_analysis.education = []
        primary_analysis.contact_info = {"email": "test@example.com"}
        primary_analysis.quality_score = 85

        undo_data = merger._generate_undo_data(
            primary_resume, primary_analysis, primary_resume, None
        )

        assert "primary_analysis" in undo_data
        assert undo_data["primary_analysis"]["skills"] == [{"name": "Python"}]
        assert undo_data["primary_analysis"]["total_experience_months"] == 24


class TestBuildCandidateData:
    """Tests for building candidate data structures."""

    def test_build_candidate_data_with_resume_only(self):
        """Test building candidate data with resume but no analysis."""
        merger = CandidateMerger(MagicMock())

        resume = MagicMock(spec=Resume)
        resume.id = uuid4()
        resume.organization_id = "org-123"
        resume.vacancy_id = "vac-456"
        resume.filename = "test.pdf"
        resume.file_path = "/path/to/test.pdf"
        resume.content_type = "application/pdf"
        resume.status = ResumeStatus.UPLOADED
        resume.raw_text = "Resume text"
        resume.language = "en"
        resume.error_message = None
        resume.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        resume.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        data = merger._build_candidate_data(resume, None)

        assert data["filename"] == "test.pdf"
        assert data["language"] == "en"
        assert data["organization_id"] == "org-123"
        # Should have empty defaults for analysis data
        assert data["skills"] == []
        assert data["keywords"] == []
        assert data["entities"] == {}
        assert data["analysis_id"] is None

    def test_build_candidate_data_with_analysis(self):
        """Test building candidate data with resume and analysis."""
        merger = CandidateMerger(MagicMock())

        resume = MagicMock(spec=Resume)
        resume.id = uuid4()
        resume.organization_id = "org-123"
        resume.vacancy_id = None
        resume.filename = "test.pdf"
        resume.file_path = "/path"
        resume.content_type = "application/pdf"
        resume.status = ResumeStatus.ANALYZED
        resume.raw_text = "text"
        resume.language = "en"
        resume.error_message = None
        resume.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
        resume.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

        analysis = MagicMock(spec=ResumeAnalysis)
        analysis.id = uuid4()
        analysis.skills = [{"name": "Python", "confidence": 0.9}]
        analysis.keywords = ["AI", "ML"]
        analysis.entities = {"organizations": ["Google"]}
        analysis.total_experience_months = 36
        analysis.education = [{"institution": "MIT", "degree": "BS CS"}]
        analysis.contact_info = {"email": "test@example.com"}
        analysis.grammar_issues = []
        analysis.warnings = []
        analysis.quality_score = 90
        analysis.processing_time_seconds = 1.5
        analysis.analyzer_version = "1.0.0"

        data = merger._build_candidate_data(resume, analysis)

        assert data["skills"] == [{"name": "Python", "confidence": 0.9}]
        assert data["total_experience_months"] == 36
        assert data["quality_score"] == 90
        assert data["contact_info"] == {"email": "test@example.com"}
        assert data["analyzer_version"] == "1.0.0"


class TestFieldOverrides:
    """Tests for field override functionality."""

    def test_field_overrides_applied(self):
        """Test that field overrides are applied during merge."""
        merger = CandidateMerger(MagicMock())

        primary_data = {"status": "UPLOADED", "language": "en"}
        duplicate_data = {"status": "ANALYZED", "language": "fr"}
        field_overrides = {"status": "REVIEWED", "custom_field": "custom_value"}

        merged, conflicts = merger._merge_fields(
            primary_data,
            duplicate_data,
            MergeStrategy.MOST_COMPLETE,
            field_overrides,
        )

        assert merged["status"] == "REVIEWED"
        assert merged["custom_field"] == "custom_value"


class TestMergeFields:
    """Tests for complete field merging logic."""

    def test_merge_fields_combines_warnings_and_grammar_issues(self):
        """Test that warnings and grammar issues from both resumes are combined."""
        merger = CandidateMerger(MagicMock())

        primary_data = {
            "warnings": ["Warning 1", "Warning 2"],
            "grammar_issues": ["Issue 1"],
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        duplicate_data = {
            "warnings": ["Warning 2", "Warning 3"],  # Warning 2 is duplicate
            "grammar_issues": ["Issue 1", "Issue 2"],  # Issue 1 is duplicate
            "updated_at": "2024-01-15T00:00:00+00:00",
        }

        merged, conflicts = merger._merge_fields(
            primary_data,
            duplicate_data,
            MergeStrategy.MOST_COMPLETE,
            {},
        )

        # Warnings should be deduplicated
        assert len(merged["warnings"]) == 3
        assert set(merged["warnings"]) == {"Warning 1", "Warning 2", "Warning 3"}

        # Grammar issues should be deduplicated
        assert len(merged["grammar_issues"]) == 2
        assert set(merged["grammar_issues"]) == {"Issue 1", "Issue 2"}

    def test_merge_fields_uses_most_recent_timestamp(self):
        """Test that merged data uses most recent updated_at timestamp."""
        merger = CandidateMerger(MagicMock())

        primary_data = {
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        duplicate_data = {
            "updated_at": "2024-01-15T00:00:00+00:00",
        }

        merged, conflicts = merger._merge_fields(
            primary_data,
            duplicate_data,
            MergeStrategy.MOST_COMPLETE,
            {},
        )

        assert merged["updated_at"] == "2024-01-15T00:00:00+00:00"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
