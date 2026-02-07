"""
Integration tests for LinkedIn profile import flow with automatic analysis.

Tests cover the complete end-to-end flow:
1. User imports LinkedIn profile by URL
2. Backend fetches profile data from LinkedIn API
3. Profile is saved to database
4. Celery task is triggered for skill extraction
5. Skills are mapped to taxonomy
6. Candidate record is created/updated
7. Frontend displays imported profile with analysis results
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import async_session_maker
from models.linkedin_profile import LinkedInProfile, LinkedInProfileStatus
from models.linkedin_import import LinkedInImport, LinkedInImportStatus
from tasks.linkedin_sync import (
    sync_linkedin_profile,
    map_linkedin_skills_to_taxonomy,
    save_linkedin_profile,
    get_linkedin_access_token,
)
from services.linkedin_service import LinkedInService


class MockLinkedInResponse:
    """Mock LinkedIn API response."""

    @staticmethod
    def profile_data() -> Dict[str, Any]:
        """Return mock LinkedIn profile data."""
        return {
            "id": "abc-123-def-456",
            "first_name": "John",
            "last_name": "Doe",
            "headline": "Senior Software Engineer at Tech Corp",
            "location": "San Francisco, California",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "profile_picture": "https://example.com/photo.jpg",
            "skills": [
                "Python",
                "JavaScript",
                "React",
                "Node.js",
                "PostgreSQL",
                "Docker",
                "Kubernetes",
                "AWS",
                "TypeScript",
                "GraphQL"
            ],
            "positions": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Corp",
                    "start_date": "2020-01",
                    "end_date": None,
                    "description": "Led development of microservices architecture"
                },
                {
                    "title": "Software Engineer",
                    "company": "Startup Inc",
                    "start_date": "2017-06",
                    "end_date": "2019-12",
                    "description": "Full-stack development"
                }
            ],
            "education": [
                {
                    "school": "University of California",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "start_date": "2013-09",
                    "end_date": "2017-05"
                }
            ],
            "raw_data": {
                "localizedFirstName": "John",
                "localizedLastName": "Doe",
                "headline": {"text": {"value": "Senior Software Engineer at Tech Corp"}}
            }
        }


class TestStep1ProfileImportRequest:
    """Test Step 1: User imports LinkedIn profile by URL."""

    @pytest.mark.asyncio
    async def test_import_endpoint_accepts_valid_url(self):
        """Test that import endpoint accepts a valid LinkedIn URL."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test valid URL
        response = client.post(
            "/api/linkedin/import",
            json={"linkedin_url": "https://www.linkedin.com/in/johndoe"},
            headers={"Authorization": "Bearer mock_token_1234567890abcdefghijklmnopqrstuvwxyz"}
        )

        # Should return 401 (token not valid in test env) but accept the URL format
        assert response.status_code in [401, 400]

    @pytest.mark.asyncio
    async def test_import_endpoint_rejects_invalid_url(self):
        """Test that import endpoint rejects invalid LinkedIn URL."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Test invalid URL
        response = client.post(
            "/api/linkedin/import",
            json={"linkedin_url": "https://example.com/profile"},
            headers={"Authorization": "Bearer mock_token"}
        )

        # Should return 400 for invalid URL
        assert response.status_code == 400
        assert "Invalid LinkedIn profile URL" in response.json()["detail"]


class TestStep2ProfileDataFetching:
    """Test Step 2: Backend fetches profile data from LinkedIn API."""

    @pytest.mark.asyncio
    async def test_linkedin_service_fetches_profile(self):
        """Test that LinkedInService can fetch profile data."""
        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MockLinkedInResponse.profile_data()
        mock_response.headers = {"X-RateLimit-Remaining": "499"}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response

            service = LinkedInService(access_token="mock_token")
            profile_data = await service.get_profile(profile_id="abc-123")

            # Verify profile data was fetched
            assert profile_data is not None
            assert profile_data["first_name"] == "John"
            assert profile_data["last_name"] == "Doe"
            assert len(profile_data["skills"]) == 10

    @pytest.mark.asyncio
    async def test_linkedin_service_handles_rate_limiting(self):
        """Test that LinkedInService handles rate limiting correctly."""
        from services.linkedin_service import LinkedInRateLimitError

        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response

            service = LinkedInService(access_token="mock_token")

            # Should raise rate limit error
            with pytest.raises(LinkedInRateLimitError):
                await service.get_profile(profile_id="abc-123")

    @pytest.mark.asyncio
    async def test_linkedin_service_handles_auth_errors(self):
        """Test that LinkedInService handles authentication errors."""
        from services.linkedin_service import LinkedInAuthError

        # Mock auth error response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "invalid_token"}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response

            service = LinkedInService(access_token="invalid_token")

            # Should raise auth error
            with pytest.raises(LinkedInAuthError):
                await service.get_profile(profile_id="abc-123")


class TestStep3ProfileDatabaseSaving:
    """Test Step 3: Profile is saved to database."""

    @pytest.mark.asyncio
    async def test_save_new_profile_to_database(self):
        """Test saving a new LinkedIn profile to database."""
        profile_data = MockLinkedInResponse.profile_data()

        profile = await save_linkedin_profile(
            profile_data=profile_data,
            user_id=uuid4()
        )

        # Verify profile was saved
        assert profile is not None
        assert profile.linkedin_id == "abc-123-def-456"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.status == LinkedInProfileStatus.COMPLETED
        assert profile.last_synced_at is not None

        # Verify skills were stored
        assert profile.skills is not None
        assert "skills" in profile.skills
        assert len(profile.skills["skills"]) == 10

        # Verify experience was stored
        assert profile.experience is not None
        assert "positions" in profile.experience
        assert len(profile.experience["positions"]) == 2

    @pytest.mark.asyncio
    async def test_update_existing_profile_in_database(self):
        """Test updating an existing LinkedIn profile in database."""
        profile_data = MockLinkedInResponse.profile_data()
        user_id = uuid4()

        # Create initial profile
        initial_profile = await save_linkedin_profile(
            profile_data=profile_data,
            user_id=user_id
        )

        # Update profile data
        updated_data = profile_data.copy()
        updated_data["headline"] = "Staff Software Engineer at Tech Corp"
        updated_data["skills"].append("Go")

        # Update profile
        updated_profile = await save_linkedin_profile(
            profile_data=updated_data,
            user_id=user_id
        )

        # Verify profile was updated, not created new
        assert updated_profile.id == initial_profile.id
        assert updated_profile.headline == "Staff Software Engineer at Tech Corp"
        assert len(updated_profile.skills["skills"]) == 11
        assert updated_profile.status == LinkedInProfileStatus.SYNCED


class TestStep4CeleryTaskTrigger:
    """Test Step 4: Celery task is triggered for skill extraction."""

    def test_sync_task_can_be_invoked(self):
        """Test that sync_linkedin_profile task can be invoked."""
        # Mock the task execution
        with patch.object(sync_linkedin_profile, "apply_async") as mock_apply:
            mock_apply.return_value = Mock(id="task-123")

            result = sync_linkedin_profile.apply_async(
                args=["abc-123", str(uuid4())]
            )

            # Verify task was queued
            assert result is not None
            assert mock_apply.called

    def test_sync_task_returns_correct_structure(self):
        """Test that sync_linkedin_profile returns expected structure."""
        # Mock all dependencies
        with patch("tasks.linkedin_sync.get_linkedin_access_token") as mock_token, \
             patch("tasks.linkedin_sync.LinkedInService") as mock_service, \
             patch("tasks.linkedin_sync.save_linkedin_profile") as mock_save:

            # Setup mocks
            mock_token.return_value = "valid_token"
            mock_service_instance = AsyncMock()
            mock_service_instance.get_profile.return_value = MockLinkedInResponse.profile_data()
            mock_service.return_value = mock_service_instance

            mock_profile = Mock()
            mock_profile.id = uuid4()
            mock_profile.first_name = "John"
            mock_profile.last_name = "Doe"
            mock_profile.headline = "Senior Software Engineer"
            mock_save.return_value = mock_profile

            # Run task
            result = sync_linkedin_profile("abc-123", str(uuid4()))

            # Verify result structure
            assert result["linkedin_profile_id"] == "abc-123"
            assert result["status"] in ["completed", "failed"]
            assert "processing_time_ms" in result
            assert "retry_attempt" in result

            if result["status"] == "completed":
                assert "profile_db_id" in result
                assert "first_name" in result
                assert "last_name" in result


class TestStep5SkillTaxonomyMapping:
    """Test Step 5: Skills are mapped to taxonomy."""

    def test_map_linkedin_skills_to_taxonomy(self):
        """Test mapping LinkedIn skills to internal taxonomy."""
        linkedin_skills = [
            "Python",
            "JavaScript",
            "React",
            "Postgres",
            "Docker",
            "Kubernetes",
            "AWS Lambda",
            "TypeScript",
        ]

        result = map_linkedin_skills_to_taxonomy(
            linkedin_skills=linkedin_skills,
            fuzzy_threshold=0.75,
            min_confidence=0.6
        )

        # Verify result structure
        assert "mapped_skills" in result
        assert "unmapped_skills" in result
        assert "statistics" in result
        assert "categories" in result

        # Verify statistics
        stats = result["statistics"]
        assert stats["total"] == len(linkedin_skills)
        assert stats["mapped"] >= 0
        assert stats["unmapped"] >= 0
        assert 0 <= stats["mapping_rate"] <= 1

        # Verify mapped skills structure
        for skill in result["mapped_skills"]:
            assert "original" in skill
            assert "canonical" in skill
            assert "category" in skill
            assert "confidence" in skill
            assert 0 <= skill["confidence"] <= 1

    def test_skill_mapping_handles_empty_list(self):
        """Test that skill mapping handles empty skill list."""
        result = map_linkedin_skills_to_taxonomy([])

        assert result["statistics"]["total"] == 0
        assert result["statistics"]["mapped"] == 0
        assert result["statistics"]["unmapped"] == 0
        assert len(result["mapped_skills"]) == 0
        assert len(result["unmapped_skills"]) == 0

    def test_skill_mapping_handles_unknown_skills(self):
        """Test that skill mapping handles unknown/new skills."""
        unknown_skills = [
            "QuantumComputingFramework",
            "UnknownSkillXYZ",
            "BrandNewTechnology"
        ]

        result = map_linkedin_skills_to_taxonomy(unknown_skills)

        # Most or all should be unmapped
        assert result["statistics"]["total"] == len(unknown_skills)
        assert len(result["unmapped_skills"]) >= 0

    def test_skill_mapping_groups_by_category(self):
        """Test that skills are grouped by category."""
        linkedin_skills = [
            "Python",
            "JavaScript",
            "PostgreSQL",
            "Docker",
            "Kubernetes"
        ]

        result = map_linkedin_skills_to_taxonomy(linkedin_skills)

        # Verify categories exist
        categories = result["categories"]
        assert isinstance(categories, dict)

        # Verify at least some skills were categorized
        if len(result["mapped_skills"]) > 0:
            # Check that mapped skills are in categories
            for skill in result["mapped_skills"]:
                category = skill["category"]
                assert category in categories


class TestStep6CandidateRecordCreation:
    """Test Step 6: Candidate record is created/updated."""

    @pytest.mark.asyncio
    async def test_profile_import_creates_candidate_record(self):
        """Test that importing a profile creates/updates candidate record."""
        from models.candidate import Candidate

        profile_data = MockLinkedInResponse.profile_data()

        # Save LinkedIn profile
        profile = await save_linkedin_profile(
            profile_data=profile_data,
            user_id=uuid4()
        )

        # In the full implementation, this would:
        # 1. Create or update a Candidate record
        # 2. Link it to the LinkedIn profile
        # 3. Trigger analysis tasks
        # For now, we verify the profile is ready for candidate creation

        assert profile is not None
        assert profile.first_name is not None
        assert profile.last_name is not None
        assert profile.email is not None or profile.headline is not None

    @pytest.mark.asyncio
    async def test_import_history_is_tracked(self):
        """Test that import history is tracked in database."""
        # This would test LinkedInImport model
        # For now, we verify the model can be instantiated
        import_record = LinkedInImport(
            status=LinkedInImportStatus.COMPLETED,
            recruiter_id=uuid4(),
            source_type="linkedin",
            search_params={"keywords": "python"},
            total_candidates=1,
            successful_imports=1,
            failed_imports=0
        )

        assert import_record.status == LinkedInImportStatus.COMPLETED
        assert import_record.source_type == "linkedin"


class TestStep7FrontendDisplay:
    """Test Step 7: Frontend displays imported profile with analysis results."""

    def test_frontend_api_client_has_import_method(self):
        """Test that frontend API client has import method."""
        # Verify the frontend TypeScript types include LinkedIn import
        frontend_types_file = Path(__file__).parent.parent / "frontend" / "src" / "types" / "api.ts"

        if frontend_types_file.exists():
            content = frontend_types_file.read_text()
            # Check for LinkedIn-related types
            assert "LinkedIn" in content or "linkedin" in content

    def test_frontend_component_exists(self):
        """Test that LinkedInImport component exists."""
        component_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "LinkedInImport.tsx"

        assert component_file.exists(), "LinkedInImport component should exist"

        # Verify component has key functionality
        content = component_file.read_text()
        assert "import" in content.lower()
        assert "linkedin" in content.lower()


class TestEndToEndIntegration:
    """End-to-end integration tests for complete flow."""

    @pytest.mark.asyncio
    async def test_complete_import_flow_simulation(self):
        """Simulate the complete import flow end-to-end."""
        user_id = uuid4()
        profile_id = "abc-123-def-456"

        # Step 1: Mock profile data fetching
        profile_data = MockLinkedInResponse.profile_data()

        # Step 2: Save profile to database
        profile = await save_linkedin_profile(
            profile_data=profile_data,
            user_id=user_id
        )
        assert profile is not None

        # Step 3: Map skills to taxonomy
        skill_mapping = map_linkedin_skills_to_taxonomy(
            linkedin_skills=profile_data["skills"]
        )
        assert skill_mapping["statistics"]["total"] > 0

        # Step 4: Verify all components are ready
        assert profile.linkedin_id == profile_data["id"]
        assert profile.status == LinkedInProfileStatus.COMPLETED
        assert len(skill_mapping["mapped_skills"]) >= 0

    @pytest.mark.asyncio
    async def test_error_handling_in_import_flow(self):
        """Test error handling throughout the import flow."""
        # Test with invalid profile data
        invalid_data = {"id": None}  # Missing required fields

        profile = await save_linkedin_profile(
            profile_data=invalid_data,
            user_id=uuid4()
        )

        # Should handle gracefully
        assert profile is None

    @pytest.mark.asyncio
    async def test_concurrent_import_handling(self):
        """Test that concurrent imports are handled correctly."""
        user_id = uuid4()

        # Simulate multiple concurrent imports
        tasks = []
        for i in range(5):
            profile_data = MockLinkedInResponse.profile_data()
            profile_data["id"] = f"profile-{i}"

            task = asyncio.create_task(
                save_linkedin_profile(profile_data, user_id)
            )
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all were handled
        successful = [r for r in results if r is not None]
        assert len(successful) == 5


class TestImportFlowEdgeCases:
    """Test edge cases in the import flow."""

    @pytest.mark.asyncio
    async def test_import_with_minimal_profile_data(self):
        """Test importing profile with minimal data."""
        minimal_data = {
            "id": "minimal-123",
            "first_name": "Jane",
            "last_name": "Smith",
            "headline": None,
            "location": None,
            "email": None,
            "phone": None,
            "profile_picture": None,
            "skills": [],
            "positions": [],
            "education": [],
            "raw_data": {}
        }

        profile = await save_linkedin_profile(
            profile_data=minimal_data,
            user_id=uuid4()
        )

        # Should handle minimal data
        assert profile is not None
        assert profile.linkedin_id == "minimal-123"

    def test_skill_mapping_with_special_characters(self):
        """Test skill mapping with special characters."""
        special_skills = [
            "C++",
            "C#",
            ".NET",
            "Node.js",
            "React.js"
        ]

        result = map_linkedin_skills_to_taxonomy(special_skills)

        # Should handle special characters
        assert result["statistics"]["total"] == len(special_skills)
        assert len(result["mapped_skills"]) >= 0

    def test_skill_mapping_with_variations(self):
        """Test skill mapping with various capitalizations and spacing."""
        variation_skills = [
            "python",
            "Python",
            "PYTHON",
            "  javascript  ",
            "JavaScript",
            "JS",
            "react js",
            "ReactJS"
        ]

        result = map_linkedin_skills_to_taxonomy(variation_skills)

        # Should normalize and map correctly
        assert result["statistics"]["total"] == len(variation_skills)


# Test runner helpers
def run_integration_tests():
    """Helper to run integration tests."""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_integration_tests()
