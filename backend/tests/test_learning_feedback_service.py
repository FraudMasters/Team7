"""
Unit tests for LearningFeedbackService.

Tests cover pattern identification, feedback processing,
confidence scoring, and service functionality.

Test Coverage:
- LearningFeedbackService initialization
- process_correction method
- _analyze_correction method
- _find_similar_pattern method
- _count_similar_corrections method
- _create_pattern method
- _update_pattern method
- _calculate_confidence method
- get_patterns_by_field method
- get_pattern_by_id method
- get_high_confidence_patterns method
- mark_pattern_applied method
- get_pattern_summary method
- get_recent_patterns method
- delete_pattern method
- aggregate_field_patterns method
- Error handling for missing database session
- Async and sync session handling
"""
import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from services.learning_feedback_service import (
    LearningFeedbackService,
    get_learning_feedback_service,
)
from models.parsing_correction import ParsingCorrection
from models.learning_feedback import LearningFeedback


class TestLearningFeedbackServiceInit:
    """Tests for LearningFeedbackService initialization."""

    def test_initialization_with_no_session(self):
        """Test initialization when no database session is provided."""
        service = LearningFeedbackService()

        assert service.db_session is None
        assert service._is_async is False

    def test_initialization_with_sync_session(self):
        """Test initialization with a synchronous session."""
        mock_session = Mock(spec=Session)
        service = LearningFeedbackService(db_session=mock_session)

        assert service.db_session is mock_session
        assert service._is_async is False

    def test_initialization_with_async_session(self):
        """Test initialization with an async session."""
        mock_session = Mock(spec=AsyncSession)
        service = LearningFeedbackService(db_session=mock_session)

        assert service.db_session is mock_session
        assert service._is_async is True

    def test_pattern_type_constants(self):
        """Test that pattern type constants are defined."""
        service = LearningFeedbackService()

        assert service.PATTERN_TYPE_EXTRACTION == "extraction"
        assert service.PATTERN_TYPE_CLASSIFICATION == "classification"
        assert service.PATTERN_TYPE_FORMATTING == "formatting"
        assert service.PATTERN_TYPE_MERGE == "merge"
        assert service.PATTERN_TYPE_SPLIT == "split"

    def test_threshold_constants(self):
        """Test that threshold constants are defined."""
        service = LearningFeedbackService()

        assert service.MIN_CORRECTIONS_FOR_PATTERN == 3
        assert service.CONFIDENCE_HIGH == 0.8
        assert service.CONFIDENCE_MEDIUM == 0.5
        assert service.CONFIDENCE_LOW == 0.3
        assert service.MAX_EXAMPLES_PER_PATTERN == 10


class TestAnalyzeCorrection:
    """Tests for _analyze_correction method."""

    def test_analyze_classification_incorrect(self):
        """Test analysis of classification error (incorrect)."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "position"
        correction.reason = "position_was_incorrect"
        correction.original_value = {"value": "Software Engineer"}
        correction.corrected_value = {"value": "Senior Software Engineer"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_CLASSIFICATION
        assert "position" in error_pattern.lower()
        assert "review" in suggestion.lower()

    def test_analyze_extraction_missing(self):
        """Test analysis of extraction error (missing)."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "skills"
        correction.reason = "missing_skill"
        correction.original_value = None
        correction.corrected_value = {"value": "Python"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_EXTRACTION
        assert "missing" in error_pattern.lower()
        assert "improve" in suggestion.lower()

    def test_analyze_formatting_issue(self):
        """Test analysis of formatting error."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "phone"
        correction.reason = "format_incorrect"
        correction.original_value = {"value": "1234567890"}
        correction.corrected_value = {"value": "(123) 456-7890"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_FORMATTING
        assert "format" in error_pattern.lower()

    def test_analyze_merge_issue(self):
        """Test analysis of merge error."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "work_experience"
        correction.reason = "merge_failed"
        correction.original_value = {"value": "Job A, Job B"}
        correction.corrected_value = {"value": "Job A"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_MERGE

    def test_analyze_split_issue(self):
        """Test analysis of split error."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "skills"
        correction.reason = "split_needed"
        correction.original_value = {"value": "Python Django Flask"}
        correction.corrected_value = {"value": ["Python", "Django", "Flask"]}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_SPLIT

    def test_analyze_generic_error(self):
        """Test analysis when no specific pattern is identified."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "name"
        correction.reason = "user_correction"
        correction.original_value = {"value": "John"}
        correction.corrected_value = {"value": "Jane"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert pattern_type == service.PATTERN_TYPE_EXTRACTION
        assert "general" in error_pattern.lower()

    def test_analyze_with_value_transformation(self):
        """Test analysis includes value transformation in pattern."""
        service = LearningFeedbackService()

        correction = Mock(spec=ParsingCorrection)
        correction.field_name = "position"
        correction.reason = "position_was_incorrect"
        correction.original_value = {"value": "Dev"}
        correction.corrected_value = {"value": "Developer"}

        pattern_type, error_pattern, suggestion = service._analyze_correction(
            correction
        )

        assert "Dev" in error_pattern
        assert "Developer" in error_pattern


class TestCalculateConfidence:
    """Tests for _calculate_confidence method."""

    def test_confidence_zero_samples(self):
        """Test confidence with zero samples."""
        service = LearningFeedbackService()

        confidence = service._calculate_confidence(0)

        assert confidence == 0.0

    def test_confidence_one_sample(self):
        """Test confidence with one sample."""
        service = LearningFeedbackService()

        confidence = service._calculate_confidence(1)

        assert 0 < confidence < 1

    def test_confidence_multiple_samples(self):
        """Test confidence increases with more samples."""
        service = LearningFeedbackService()

        confidence_1 = service._calculate_confidence(1)
        confidence_5 = service._calculate_confidence(5)
        confidence_10 = service._calculate_confidence(10)

        assert confidence_5 > confidence_1
        assert confidence_10 > confidence_5

    def test_confidence_capped_at_one(self):
        """Test confidence is capped at 1.0."""
        service = LearningFeedbackService()

        confidence = service._calculate_confidence(1000)

        assert confidence <= 1.0

    def test_confidence_uses_logarithmic_scale(self):
        """Test confidence uses logarithmic scale."""
        service = LearningFeedbackService()

        # log2(8+1) / 3 = log2(9) / 3 ≈ 0.69
        confidence = service._calculate_confidence(8)

        expected = min(1.0, math.log2(8 + 1) / 3)
        assert confidence == round(expected, 2)


class TestProcessCorrection:
    """Tests for process_correction method."""

    @pytest.mark.asyncio
    async def test_process_without_session_raises_error(self):
        """Test that process raises error without database session."""
        service = LearningFeedbackService()
        correction = Mock(spec=ParsingCorrection)

        with pytest.raises(ValueError, match="Database session is required"):
            await service.process_correction(correction)

    @pytest.mark.asyncio
    async def test_process_correction_insufficient_similar(self):
        """Test processing when not enough similar corrections exist."""
        mock_session = AsyncMock(spec=AsyncSession)

        service = LearningFeedbackService(db_session=mock_session)
        service.MIN_CORRECTIONS_FOR_PATTERN = 3

        correction = Mock(spec=ParsingCorrection)
        correction.id = uuid4()
        correction.field_name = "position"
        correction.reason = "position_was_incorrect"
        correction.original_value = {"value": "Dev"}
        correction.corrected_value = {"value": "Developer"}

        # Mock _find_similar_pattern to return None (no existing pattern)
        # Mock _count_similar_corrections to return low count
        with patch.object(
            service, '_find_similar_pattern', return_value=None
        ), patch.object(
            service, '_count_similar_corrections', return_value=1
        ):
            result = await service.process_correction(correction)

        assert result is None


class TestFindSimilarPattern:
    """Tests for _find_similar_pattern method."""

    @pytest.mark.asyncio
    async def test_find_similar_pattern_found(self):
        """Test finding an existing similar pattern."""
        mock_feedback = Mock(spec=LearningFeedback)
        mock_feedback.error_pattern = "Incorrect position extracted: 'Dev' -> 'Developer'"

        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_feedback]
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._find_similar_pattern(
            field_name="position",
            error_pattern="Incorrect position extracted",
            pattern_type="classification",
        )

        assert result is mock_feedback

    @pytest.mark.asyncio
    async def test_find_similar_pattern_not_found(self):
        """Test when no similar pattern exists."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._find_similar_pattern(
            field_name="position",
            error_pattern="Incorrect position extracted",
            pattern_type="classification",
        )

        assert result is None


class TestCountSimilarCorrections:
    """Tests for _count_similar_corrections method."""

    @pytest.mark.asyncio
    async def test_count_with_reason(self):
        """Test counting corrections with reason filter."""
        mock_result = Mock()
        mock_result.scalar.return_value = 5

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        count = await service._count_similar_corrections(
            field_name="position",
            reason="position_was_incorrect",
        )

        assert count == 5

    @pytest.mark.asyncio
    async def test_count_without_reason(self):
        """Test counting corrections without reason filter."""
        mock_result = Mock()
        mock_result.scalar.return_value = 10

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        count = await service._count_similar_corrections(
            field_name="position",
            reason=None,
        )

        assert count == 10

    @pytest.mark.asyncio
    async def test_count_on_error_returns_zero(self):
        """Test that count returns 0 on database error."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        service = LearningFeedbackService(db_session=mock_session)

        count = await service._count_similar_corrections(
            field_name="position",
            reason="some_reason",
        )

        assert count == 0


class TestCreatePattern:
    """Tests for _create_pattern method."""

    @pytest.mark.asyncio
    async def test_create_pattern_success(self):
        """Test successful pattern creation."""
        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.id = uuid4()
        mock_correction.field_name = "position"
        mock_correction.reason = "position_was_incorrect"
        mock_correction.original_value = {"value": "Dev"}
        mock_correction.corrected_value = {"value": "Developer"}
        mock_correction.created_at = datetime.utcnow()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)

        # Mock _get_similar_corrections
        with patch.object(
            service,
            '_get_similar_corrections',
            return_value=[mock_correction]
        ):
            result = await service._create_pattern(
                correction=mock_correction,
                error_pattern="Test pattern",
                suggestion="Test suggestion",
                pattern_type="classification",
                parser_version="1.0.0",
            )

        mock_session.add.assert_called_once()
        assert isinstance(result, LearningFeedback)


class TestUpdatePattern:
    """Tests for _update_pattern method."""

    @pytest.mark.asyncio
    async def test_update_pattern_increments_count(self):
        """Test that updating pattern increments sample count."""
        mock_feedback = Mock(spec=LearningFeedback)
        mock_feedback.sample_count = 5
        mock_feedback.examples = []
        mock_feedback.id = uuid4()

        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.original_value = {"value": "old"}
        mock_correction.corrected_value = {"value": "new"}
        mock_correction.reason = "test"
        mock_correction.created_at = datetime.utcnow()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._update_pattern(
            feedback=mock_feedback,
            correction=mock_correction,
        )

        assert result.sample_count == 6
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_pattern_adds_example(self):
        """Test that updating pattern adds example if under limit."""
        mock_feedback = Mock(spec=LearningFeedback)
        mock_feedback.sample_count = 3
        mock_feedback.examples = []
        mock_feedback.id = uuid4()

        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.original_value = {"value": "old"}
        mock_correction.corrected_value = {"value": "new"}
        mock_correction.reason = "test"
        mock_correction.created_at = datetime.utcnow()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._update_pattern(
            feedback=mock_feedback,
            correction=mock_correction,
        )

        assert len(result.examples) == 1

    @pytest.mark.asyncio
    async def test_update_pattern_respects_max_examples(self):
        """Test that pattern doesn't exceed max examples."""
        mock_feedback = Mock(spec=LearningFeedback)
        mock_feedback.sample_count = 15
        mock_feedback.examples = [{"example": i} for i in range(10)]
        mock_feedback.id = uuid4()

        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.original_value = {"value": "old"}
        mock_correction.corrected_value = {"value": "new"}
        mock_correction.reason = "test"
        mock_correction.created_at = datetime.utcnow()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._update_pattern(
            feedback=mock_feedback,
            correction=mock_correction,
        )

        # Should still have only 10 examples
        assert len(result.examples) == 10


class TestGetPatternsByField:
    """Tests for get_patterns_by_field method."""

    @pytest.mark.asyncio
    async def test_get_patterns_without_session_raises_error(self):
        """Test that get_patterns raises error without session."""
        service = LearningFeedbackService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_patterns_by_field("position")

    @pytest.mark.asyncio
    async def test_get_patterns_by_field_basic(self):
        """Test basic retrieval of patterns by field."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_patterns_by_field("position")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_patterns_with_min_confidence(self):
        """Test retrieval with minimum confidence filter."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_patterns_by_field(
            "position",
            min_confidence=0.8,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_patterns_applied_only(self):
        """Test retrieval of only applied patterns."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_patterns_by_field(
            "position",
            applied_only=True,
        )

        assert result == []


class TestGetPatternById:
    """Tests for get_pattern_by_id method."""

    @pytest.mark.asyncio
    async def test_get_pattern_by_id_without_session_raises_error(self):
        """Test that get_pattern raises error without session."""
        service = LearningFeedbackService()
        pattern_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_pattern_by_id(pattern_id)

    @pytest.mark.asyncio
    async def test_get_pattern_by_id_found(self):
        """Test retrieval when pattern is found."""
        mock_pattern = Mock(spec=LearningFeedback)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_pattern

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        result = await service.get_pattern_by_id(pattern_id)

        assert result is mock_pattern

    @pytest.mark.asyncio
    async def test_get_pattern_by_id_not_found(self):
        """Test retrieval when pattern is not found."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        result = await service.get_pattern_by_id(pattern_id)

        assert result is None


class TestGetHighConfidencePatterns:
    """Tests for get_high_confidence_patterns method."""

    @pytest.mark.asyncio
    async def test_get_high_confidence_without_session_raises_error(self):
        """Test that get_high_confidence raises error without session."""
        service = LearningFeedbackService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_high_confidence_patterns()

    @pytest.mark.asyncio
    async def test_get_high_confidence_patterns_basic(self):
        """Test basic retrieval of high confidence patterns."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_high_confidence_patterns()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_high_confidence_with_limit(self):
        """Test retrieval with custom limit."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_high_confidence_patterns(limit=25)

        assert result == []


class TestMarkPatternApplied:
    """Tests for mark_pattern_applied method."""

    @pytest.mark.asyncio
    async def test_mark_applied_without_session_raises_error(self):
        """Test that mark_applied raises error without session."""
        service = LearningFeedbackService()
        pattern_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.mark_pattern_applied(pattern_id)

    @pytest.mark.asyncio
    async def test_mark_pattern_applied_success(self):
        """Test successfully marking pattern as applied."""
        mock_pattern = Mock(spec=LearningFeedback)
        mock_pattern.is_applied = False

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        with patch.object(
            service,
            'get_pattern_by_id',
            return_value=mock_pattern
        ):
            result = await service.mark_pattern_applied(pattern_id)

        assert result is True
        assert mock_pattern.is_applied is True

    @pytest.mark.asyncio
    async def test_mark_pattern_applied_not_found(self):
        """Test marking pattern as applied when not found."""
        mock_session = AsyncMock(spec=AsyncSession)

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        with patch.object(
            service,
            'get_pattern_by_id',
            return_value=None
        ):
            result = await service.mark_pattern_applied(pattern_id)

        assert result is False


class TestGetPatternSummary:
    """Tests for get_pattern_summary method."""

    @pytest.mark.asyncio
    async def test_get_summary_without_session_raises_error(self):
        """Test that get_summary raises error without session."""
        service = LearningFeedbackService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_pattern_summary()

    @pytest.mark.asyncio
    async def test_get_pattern_summary_empty(self):
        """Test summary when no patterns exist."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        summary = await service.get_pattern_summary()

        assert summary["total_count"] == 0
        assert summary["applied_count"] == 0
        assert summary["pending_count"] == 0

    @pytest.mark.asyncio
    async def test_get_pattern_summary_with_data(self):
        """Test summary with actual patterns."""
        mock_pattern1 = Mock(spec=LearningFeedback)
        mock_pattern1.field_name = "position"
        mock_pattern1.pattern_type = "classification"
        mock_pattern1.confidence_score = 0.9
        mock_pattern1.is_applied = True
        mock_pattern1.sample_count = 10

        mock_pattern2 = Mock(spec=LearningFeedback)
        mock_pattern2.field_name = "skills"
        mock_pattern2.pattern_type = "extraction"
        mock_pattern2.confidence_score = 0.4
        mock_pattern2.is_applied = False
        mock_pattern2.sample_count = 5

        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_pattern1, mock_pattern2]
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        summary = await service.get_pattern_summary()

        assert summary["total_count"] == 2
        assert summary["applied_count"] == 1
        assert summary["pending_count"] == 1
        assert summary["total_samples"] == 15
        assert "position" in summary["by_field"]
        assert "skills" in summary["by_field"]


class TestGetRecentPatterns:
    """Tests for get_recent_patterns method."""

    @pytest.mark.asyncio
    async def test_get_recent_without_session_raises_error(self):
        """Test that get_recent raises error without session."""
        service = LearningFeedbackService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_recent_patterns()

    @pytest.mark.asyncio
    async def test_get_recent_patterns_basic(self):
        """Test basic retrieval of recent patterns."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service.get_recent_patterns()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_patterns_with_since(self):
        """Test retrieval of patterns since a specific date."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)
        since = datetime.utcnow() - timedelta(days=7)

        result = await service.get_recent_patterns(since=since)

        assert result == []


class TestDeletePattern:
    """Tests for delete_pattern method."""

    @pytest.mark.asyncio
    async def test_delete_without_session_raises_error(self):
        """Test that delete raises error without session."""
        service = LearningFeedbackService()
        pattern_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.delete_pattern(pattern_id)

    @pytest.mark.asyncio
    async def test_delete_pattern_success(self):
        """Test successful pattern deletion."""
        mock_pattern = Mock(spec=LearningFeedback)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        with patch.object(
            service,
            'get_pattern_by_id',
            return_value=mock_pattern
        ):
            result = await service.delete_pattern(pattern_id)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_pattern)

    @pytest.mark.asyncio
    async def test_delete_pattern_not_found(self):
        """Test deleting pattern that doesn't exist."""
        mock_session = AsyncMock(spec=AsyncSession)

        service = LearningFeedbackService(db_session=mock_session)
        pattern_id = uuid4()

        with patch.object(
            service,
            'get_pattern_by_id',
            return_value=None
        ):
            result = await service.delete_pattern(pattern_id)

        assert result is False


class TestAggregateFieldPatterns:
    """Tests for aggregate_field_patterns method."""

    @pytest.mark.asyncio
    async def test_aggregate_without_session_raises_error(self):
        """Test that aggregate raises error without session."""
        service = LearningFeedbackService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.aggregate_field_patterns("position")

    @pytest.mark.asyncio
    async def test_aggregate_field_patterns_empty(self):
        """Test aggregation when no corrections exist."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        patterns = await service.aggregate_field_patterns("position")

        assert patterns == []

    @pytest.mark.asyncio
    async def test_aggregate_field_patterns_with_data(self):
        """Test aggregation with actual corrections."""
        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.id = uuid4()
        mock_correction.field_name = "position"
        mock_correction.reason = "position_was_incorrect"
        mock_correction.original_value = {"value": "Dev"}
        mock_correction.corrected_value = {"value": "Developer"}
        mock_correction.created_at = datetime.utcnow()

        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_correction]
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        # Mock process_correction to return None (insufficient samples)
        with patch.object(
            service,
            'process_correction',
            return_value=None
        ):
            patterns = await service.aggregate_field_patterns("position")

        assert patterns == []


class TestGetLearningFeedbackService:
    """Tests for get_learning_feedback_service factory function."""

    def test_factory_with_session(self):
        """Test factory returns new instance with session."""
        mock_session = Mock(spec=Session)
        service = get_learning_feedback_service(db_session=mock_session)

        assert isinstance(service, LearningFeedbackService)
        assert service.db_session is mock_session

    def test_factory_without_session_returns_global(self):
        """Test factory returns global instance without session."""
        # Clear global instance first
        import services.learning_feedback_service as module
        module._learning_feedback_service = None

        service1 = get_learning_feedback_service()
        service2 = get_learning_feedback_service()

        assert service1 is service2
        assert isinstance(service1, LearningFeedbackService)


class TestErrorHandling:
    """Tests for error handling in service methods."""

    @pytest.mark.asyncio
    async def test_process_correction_database_error(self):
        """Test handling of database errors during processing."""
        mock_correction = Mock(spec=ParsingCorrection)
        mock_correction.field_name = "position"
        mock_correction.reason = "test"
        mock_correction.original_value = {}
        mock_correction.corrected_value = {}

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        service = LearningFeedbackService(db_session=mock_session)

        with pytest.raises(Exception, match="Database error"):
            await service.process_correction(mock_correction)

    @pytest.mark.asyncio
    async def test_get_patterns_database_error(self):
        """Test handling of database errors during retrieval."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(
            side_effect=Exception("Connection error")
        )

        service = LearningFeedbackService(db_session=mock_session)

        with pytest.raises(Exception, match="Connection error"):
            await service.get_patterns_by_field("position")


class TestGetSimilarCorrections:
    """Tests for _get_similar_corrections method."""

    @pytest.mark.asyncio
    async def test_get_similar_corrections_success(self):
        """Test successful retrieval of similar corrections."""
        mock_correction = Mock(spec=ParsingCorrection)
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_correction]
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._get_similar_corrections(
            field_name="position",
            reason="test",
            limit=10,
        )

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_similar_corrections_on_error(self):
        """Test that method returns empty list on error."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        service = LearningFeedbackService(db_session=mock_session)

        result = await service._get_similar_corrections(
            field_name="position",
            reason="test",
        )

        assert result == []
