"""
Tests for candidate tags API intelligent suggestions endpoint.

Tests cover:
- Intelligent tag suggestions with valid inputs
- Validation error cases (empty/invalid parameters)
- Resume not found scenarios
- Organization tags handling
- Edge cases and error handling
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from unittest.mock import patch, MagicMock

from models.candidate_tag import CandidateTag
from models.resume import Resume, ResumeStatus
from models.hiring_stage import HiringStage, HiringStageName


class TestIntelligentTagSuggestions:
    """Tests for GET /api/candidate-tags/intelligent-suggestions"""

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_success_with_resume(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test successful intelligent suggestions response with existing resume."""
        # Create organization tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
            color="#00FF00",
            description="Python developers"
        )
        tag2 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Django Expert",
            tag_order=2,
            is_default=False,
            is_active=True,
            color="#0000FF",
            description="Django framework experts"
        )
        test_db.add(tag1)
        test_db.add(tag2)
        await test_db.flush()

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Experienced Python developer with Django and FastAPI skills. Built multiple web applications.",
            location="Remote",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        # Should return 200 (may have suggestions or not depending on keyword extraction)
        assert response.status_code == 200
        data = response.json()
        assert "organization_id" in data
        assert "resume_id" in data
        assert "suggestions" in data
        assert "total_count" in data
        assert data["organization_id"] == "test-org"
        assert data["resume_id"] == str(resume.id)

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_resume_not_found(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with non-existent resume ID."""
        # Create organization tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)
        await test_db.commit()

        fake_resume_id = uuid4()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(fake_resume_id),
                "limit": 5
            }
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_empty_organization_id(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with empty organization_id."""
        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_empty_resume_id(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with empty resume_id."""
        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": "",
                "limit": 5
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_invalid_resume_id_format(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with invalid UUID format for resume_id."""
        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": "not-a-uuid",
                "limit": 5
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_limit_validation_exceeds_max(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test limit parameter validation - exceeds max of 100."""
        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 101  # Exceeds max of 100
            }
        )

        # FastAPI validates this - should return 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_limit_validation_zero(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test limit parameter validation - zero is invalid."""
        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 0  # Below minimum of 1
            }
        )

        # FastAPI validates this - should return 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_resume_with_no_text(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with resume that has no text content."""
        # Create organization tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)

        # Create a resume with no text
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="",  # No text
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should return empty suggestions
        assert data["total_count"] == 0
        assert data["suggestions"] == []

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_no_organization_tags(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test when organization has no tags configured."""
        # Create a resume without creating any tags
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer with Django skills",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should return empty suggestions when no tags exist
        assert data["total_count"] == 0
        assert data["suggestions"] == []

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_only_inactive_tags(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test when organization only has inactive tags."""
        # Create only inactive tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=False,  # Inactive
        )
        test_db.add(tag1)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should return empty suggestions when only inactive tags exist
        assert data["total_count"] == 0

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_limit_respected(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test that limit parameter is respected."""
        # Create multiple tags
        for i in range(10):
            tag = CandidateTag(
                id=uuid4(),
                organization_id="test-org",
                tag_name=f"Tag {i}",
                tag_order=i,
                is_default=False,
                is_active=True,
            )
            test_db.add(tag)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Experienced developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should not exceed the limit
        assert data["total_count"] <= 3

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_max_limit(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with maximum limit of 100."""
        # Create multiple tags
        for i in range(50):
            tag = CandidateTag(
                id=uuid4(),
                organization_id="test-org",
                tag_name=f"Tag {i}",
                tag_order=i,
                is_default=False,
                is_active=True,
            )
            test_db.add(tag)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Experienced developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 100  # Maximum allowed
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should not exceed the limit
        assert data["total_count"] <= 100

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_response_structure(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test that response has correct structure."""
        # Create organization tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
            color="#00FF00",
            description="Python developers"
        )
        test_db.add(tag1)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer with Django skills",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "organization_id" in data
        assert "resume_id" in data
        assert "suggestions" in data
        assert "keywords_extracted" in data
        assert "total_count" in data

        # If there are suggestions, verify their structure
        if data["total_count"] > 0:
            suggestion = data["suggestions"][0]
            assert "id" in suggestion
            assert "organization_id" in suggestion
            assert "tag_name" in suggestion
            assert "relevance_score" in suggestion
            assert "is_active" in suggestion
            assert 0 <= suggestion["relevance_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_long_resume_text(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with very long resume text (truncation behavior)."""
        # Create a tag
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)

        # Create a resume with very long text (> 50,000 characters)
        long_text = "Python developer " * 2000  # ~20,000 characters
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text=long_text,
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        # Should handle long text gracefully
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    @pytest.mark.asyncio
    async def test_intelligent_suggestions_with_language_detection(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test with different resume languages."""
        # Create a tag
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)

        # Create a resume with Russian language
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python разработчик с опытом работы",
            language="ru",  # Russian
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        # Should handle different languages
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data


class TestIntelligentTagSuggestionsIntegration:
    """Integration tests for intelligent suggestions with actual keyword extraction."""

    @pytest.mark.asyncio
    @patch('analyzers.tag_suggester.extract_keywords')
    async def test_intelligent_suggestions_with_mocked_keyword_extraction(
        self, mock_extract, client: AsyncClient, test_db: AsyncSession
    ):
        """Test intelligent suggestions with mocked keyword extraction."""
        # Mock keyword extraction to return specific keywords
        mock_extract.return_value = {
            "keywords": ["python", "django", "developer"],
            "keywords_with_scores": [("python", 0.9), ("django", 0.85), ("developer", 0.8)],
            "count": 3,
            "error": None
        }

        # Create matching tags
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        tag2 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Django Expert",
            tag_order=2,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)
        test_db.add(tag2)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python Django developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        assert response.status_code == 200
        data = response.json()

        # With mocked keywords matching tags, should get suggestions
        assert "suggestions" in data
        assert "keywords_extracted" in data
        # The mocked keywords should be reflected in the response
        assert isinstance(data["keywords_extracted"], list)

    @pytest.mark.asyncio
    @patch('analyzers.tag_suggester.extract_keywords')
    async def test_intelligent_suggestions_with_keyword_extraction_error(
        self, mock_extract, client: AsyncClient, test_db: AsyncSession
    ):
        """Test intelligent suggestions when keyword extraction fails."""
        # Mock keyword extraction to return an error
        mock_extract.return_value = {
            "keywords": None,
            "keywords_with_scores": None,
            "count": 0,
            "error": "Model not loaded"
        }

        # Create a tag
        tag1 = CandidateTag(
            id=uuid4(),
            organization_id="test-org",
            tag_name="Python Developer",
            tag_order=1,
            is_default=False,
            is_active=True,
        )
        test_db.add(tag1)

        # Create a resume
        resume = Resume(
            id=uuid4(),
            filename="test_resume.pdf",
            file_path="/test/test_resume.pdf",
            status=ResumeStatus.COMPLETED,
            raw_text="Python developer",
        )
        test_db.add(resume)
        await test_db.commit()

        response = await client.get(
            "/api/candidate-tags/intelligent-suggestions",
            params={
                "organization_id": "test-org",
                "resume_id": str(resume.id),
                "limit": 5
            }
        )

        # Should return empty suggestions rather than erroring
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["suggestions"] == []
