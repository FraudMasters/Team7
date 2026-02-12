"""
Unit tests for ParsingCorrectionService.

Tests cover correction management, database operations,
error handling, and service functionality.

Test Coverage:
- ParsingCorrectionService initialization
- save_correction method
- get_corrections_by_resume method
- get_correction_by_id method
- get_corrections_by_field method
- get_correction_count_by_field method
- get_corrections_by_user method
- delete_correction method
- get_recent_corrections method
- Error handling for missing database session
- Validation of field names
- Async and sync session handling
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4, UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from services.parsing_correction_service import (
    ParsingCorrectionService,
    get_parsing_correction_service,
)
from models.parsing_correction import ParsingCorrection


class TestParsingCorrectionServiceInit:
    """Tests for ParsingCorrectionService initialization."""

    def test_initialization_with_no_session(self):
        """Test initialization when no database session is provided."""
        service = ParsingCorrectionService()

        assert service.db_session is None
        assert service._is_async is False

    def test_initialization_with_sync_session(self):
        """Test initialization with a synchronous session."""
        mock_session = Mock(spec=Session)
        service = ParsingCorrectionService(db_session=mock_session)

        assert service.db_session is mock_session
        assert service._is_async is False

    def test_initialization_with_async_session(self):
        """Test initialization with an async session."""
        mock_session = Mock(spec=AsyncSession)
        service = ParsingCorrectionService(db_session=mock_session)

        assert service.db_session is mock_session
        assert service._is_async is True

    def test_valid_field_names_constant(self):
        """Test that VALID_FIELD_NAMES contains expected fields."""
        service = ParsingCorrectionService()

        expected_fields = {
            "position",
            "skills",
            "education",
            "work_experience",
            "languages",
            "email",
            "phone",
            "name",
            "location",
            "summary",
            "certifications",
            "projects",
        }

        assert service.VALID_FIELD_NAMES == expected_fields


class TestValidateFieldName:
    """Tests for _validate_field_name method."""

    def test_validate_standard_field_name(self):
        """Test validation of standard field names."""
        service = ParsingCorrectionService()

        assert service._validate_field_name("position") is True
        assert service._validate_field_name("skills") is True
        assert service._validate_field_name("education") is True

    def test_validate_non_standard_field_name(self):
        """Test validation of non-standard field names."""
        service = ParsingCorrectionService()

        assert service._validate_field_name("custom_field") is False
        assert service._validate_field_name("unknown") is False


class TestSaveCorrection:
    """Tests for save_correction method."""

    @pytest.mark.asyncio
    async def test_save_correction_without_session_raises_error(self):
        """Test that save_correction raises error without database session."""
        service = ParsingCorrectionService()
        resume_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.save_correction(
                resume_id=resume_id,
                field_name="position",
                original_value={"value": "Software Engineer"},
                corrected_value={"value": "Senior Software Engineer"},
            )

    @pytest.mark.asyncio
    async def test_save_correction_with_async_session(self):
        """Test saving correction with async session."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()
        user_id = uuid4()

        result = await service.save_correction(
            resume_id=resume_id,
            field_name="position",
            original_value={"value": "Software Engineer"},
            corrected_value={"value": "Senior Software Engineer"},
            reason="position_was_incorrect",
            corrected_by=user_id,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert isinstance(result, ParsingCorrection)

    @pytest.mark.asyncio
    async def test_save_correction_with_sync_session(self):
        """Test saving correction with sync session."""
        mock_session = Mock(spec=Session)
        mock_session.flush = Mock()
        mock_session.refresh = Mock()

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        result = await service.save_correction(
            resume_id=resume_id,
            field_name="skills",
            original_value={"value": ["Python"]},
            corrected_value={"value": ["Python", "Django"]},
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        assert isinstance(result, ParsingCorrection)

    @pytest.mark.asyncio
    async def test_save_correction_with_non_standard_field(self):
        """Test saving correction with non-standard field name (logs warning)."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        # Should not raise error, just log warning
        result = await service.save_correction(
            resume_id=resume_id,
            field_name="custom_field",
            original_value={"value": "old"},
            corrected_value={"value": "new"},
        )

        assert isinstance(result, ParsingCorrection)

    @pytest.mark.asyncio
    async def test_save_correction_with_all_parameters(self):
        """Test saving correction with all optional parameters."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()
        user_id = uuid4()

        result = await service.save_correction(
            resume_id=resume_id,
            field_name="education",
            original_value={"degree": "BS"},
            corrected_value={"degree": "MS"},
            reason="education_was_incorrect",
            source_text_location={"page": 1, "line": 10},
            corrected_by=user_id,
        )

        assert isinstance(result, ParsingCorrection)


class TestGetCorrectionsByResume:
    """Tests for get_corrections_by_resume method."""

    @pytest.mark.asyncio
    async def test_get_corrections_without_session_raises_error(self):
        """Test that get_corrections raises error without database session."""
        service = ParsingCorrectionService()
        resume_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_corrections_by_resume(resume_id)

    @pytest.mark.asyncio
    async def test_get_corrections_by_resume_basic(self):
        """Test basic retrieval of corrections by resume."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        result = await service.get_corrections_by_resume(resume_id)

        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_corrections_with_field_filter(self):
        """Test retrieval with field name filter."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        result = await service.get_corrections_by_resume(
            resume_id=resume_id,
            field_name="skills",
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_get_corrections_with_pagination(self):
        """Test retrieval with limit and offset."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        result = await service.get_corrections_by_resume(
            resume_id=resume_id,
            limit=10,
            offset=5,
        )

        assert result == []


class TestGetCorrectionById:
    """Tests for get_correction_by_id method."""

    @pytest.mark.asyncio
    async def test_get_correction_by_id_without_session_raises_error(self):
        """Test that get_correction_by_id raises error without session."""
        service = ParsingCorrectionService()
        correction_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_correction_by_id(correction_id)

    @pytest.mark.asyncio
    async def test_get_correction_by_id_found(self):
        """Test retrieval when correction is found."""
        mock_correction = Mock(spec=ParsingCorrection)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_correction

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        correction_id = uuid4()

        result = await service.get_correction_by_id(correction_id)

        assert result is mock_correction

    @pytest.mark.asyncio
    async def test_get_correction_by_id_not_found(self):
        """Test retrieval when correction is not found."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        correction_id = uuid4()

        result = await service.get_correction_by_id(correction_id)

        assert result is None


class TestGetCorrectionsByField:
    """Tests for get_corrections_by_field method."""

    @pytest.mark.asyncio
    async def test_get_corrections_by_field_without_session_raises_error(self):
        """Test that get_corrections_by_field raises error without session."""
        service = ParsingCorrectionService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_corrections_by_field("position")

    @pytest.mark.asyncio
    async def test_get_corrections_by_field_basic(self):
        """Test basic retrieval of corrections by field name."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)

        result = await service.get_corrections_by_field("position")

        assert result == []


class TestGetCorrectionCountByField:
    """Tests for get_correction_count_by_field method."""

    @pytest.mark.asyncio
    async def test_count_without_session_raises_error(self):
        """Test that count raises error without database session."""
        service = ParsingCorrectionService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_correction_count_by_field()

    @pytest.mark.asyncio
    async def test_count_all_fields(self):
        """Test counting corrections for all fields."""
        mock_row1 = Mock()
        mock_row1.field_name = "position"
        mock_row1.count = 10
        mock_row2 = Mock()
        mock_row2.field_name = "skills"
        mock_row2.count = 5

        mock_result = Mock()
        mock_result.all.return_value = [mock_row1, mock_row2]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)

        result = await service.get_correction_count_by_field()

        assert result == {"position": 10, "skills": 5}

    @pytest.mark.asyncio
    async def test_count_specific_field(self):
        """Test counting corrections for a specific field."""
        mock_result = Mock()
        mock_result.scalar.return_value = 15

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)

        result = await service.get_correction_count_by_field("position")

        assert result == {"position": 15}


class TestGetCorrectionsByUser:
    """Tests for get_corrections_by_user method."""

    @pytest.mark.asyncio
    async def test_get_corrections_by_user_without_session_raises_error(self):
        """Test that get_corrections_by_user raises error without session."""
        service = ParsingCorrectionService()
        user_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_corrections_by_user(user_id)

    @pytest.mark.asyncio
    async def test_get_corrections_by_user_basic(self):
        """Test basic retrieval of corrections by user."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        user_id = uuid4()

        result = await service.get_corrections_by_user(user_id)

        assert result == []


class TestDeleteCorrection:
    """Tests for delete_correction method."""

    @pytest.mark.asyncio
    async def test_delete_without_session_raises_error(self):
        """Test that delete raises error without database session."""
        service = ParsingCorrectionService()
        correction_id = uuid4()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.delete_correction(correction_id)

    @pytest.mark.asyncio
    async def test_delete_correction_not_found(self):
        """Test deleting a correction that doesn't exist."""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        correction_id = uuid4()

        # Mock get_correction_by_id to return None
        with patch.object(
            service,
            'get_correction_by_id',
            return_value=None
        ):
            result = await service.delete_correction(correction_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_correction_success(self):
        """Test successful deletion of a correction."""
        mock_correction = Mock(spec=ParsingCorrection)

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        service = ParsingCorrectionService(db_session=mock_session)
        correction_id = uuid4()

        with patch.object(
            service,
            'get_correction_by_id',
            return_value=mock_correction
        ):
            result = await service.delete_correction(correction_id)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_correction)


class TestGetRecentCorrections:
    """Tests for get_recent_corrections method."""

    @pytest.mark.asyncio
    async def test_get_recent_without_session_raises_error(self):
        """Test that get_recent raises error without database session."""
        service = ParsingCorrectionService()

        with pytest.raises(ValueError, match="Database session is required"):
            await service.get_recent_corrections()

    @pytest.mark.asyncio
    async def test_get_recent_corrections_basic(self):
        """Test basic retrieval of recent corrections."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)

        result = await service.get_recent_corrections()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_corrections_with_since(self):
        """Test retrieval of corrections since a specific date."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)
        since = datetime.utcnow() - timedelta(days=7)

        result = await service.get_recent_corrections(since=since)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_corrections_with_limit(self):
        """Test retrieval with custom limit."""
        mock_result = Mock()
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars

        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = ParsingCorrectionService(db_session=mock_session)

        result = await service.get_recent_corrections(limit=50)

        assert result == []


class TestGetParsingCorrectionService:
    """Tests for get_parsing_correction_service factory function."""

    def test_factory_with_session(self):
        """Test factory returns new instance with session."""
        mock_session = Mock(spec=Session)
        service = get_parsing_correction_service(db_session=mock_session)

        assert isinstance(service, ParsingCorrectionService)
        assert service.db_session is mock_session

    def test_factory_without_session_returns_global(self):
        """Test factory returns global instance without session."""
        # Clear global instance first
        import services.parsing_correction_service as module
        module._parsing_correction_service = None

        service1 = get_parsing_correction_service()
        service2 = get_parsing_correction_service()

        assert service1 is service2
        assert isinstance(service1, ParsingCorrectionService)


class TestErrorHandling:
    """Tests for error handling in service methods."""

    @pytest.mark.asyncio
    async def test_save_correction_database_error(self):
        """Test handling of database errors during save."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.add = Mock(side_effect=Exception("Database error"))

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        with pytest.raises(Exception, match="Database error"):
            await service.save_correction(
                resume_id=resume_id,
                field_name="position",
                original_value={"value": "old"},
                corrected_value={"value": "new"},
            )

    @pytest.mark.asyncio
    async def test_get_corrections_database_error(self):
        """Test handling of database errors during retrieval."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute = AsyncMock(
            side_effect=Exception("Connection error")
        )

        service = ParsingCorrectionService(db_session=mock_session)
        resume_id = uuid4()

        with pytest.raises(Exception, match="Connection error"):
            await service.get_corrections_by_resume(resume_id)
