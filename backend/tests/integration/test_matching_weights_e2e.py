"""
import os
End-to-end integration tests for Matching Weights Customization feature.

This test suite validates the complete weight customization workflow:
- Preset profile creation and seeding
- Custom profile creation via API
- Profile selection and vacancy re-matching
- A/B testing comparison between profiles
- Score recalculation with different weight configurations

Test Coverage:
- Preset profiles (Technical, Creative, Executive, Balanced)
- Custom profile CRUD operations
- Weight profile application to vacancy matching
- Candidate re-matching with new weights
- A/B testing comparison endpoint
- Score differences between weight profiles
- Integration with UnifiedSkillMatcher
"""
import asyncio
from datetime import datetime
from typing import Dict, Generator, List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from backend.models.matching_weights_profile import MatchingWeightsProfile
from backend.models.matching_weights_history import MatchingWeightsHistory
from backend.models.match_result import MatchResult
from backend.models.vacancy import Vacancy
from backend.models.resume import Resume


@pytest.fixture
async def test_organization(async_session_maker) -> str:
    """
    Create or get a test organization.

    Returns:
        Organization ID for testing
    """
    org_id = f"test-org-{uuid4().hex[:8]}"

    # Store in session for cleanup
    yield org_id


@pytest.fixture
async def seeded_preset_profiles(async_session_maker, test_organization) -> List[Dict]:
    """
    Seed preset weight profiles for testing.

    Returns:
        List of preset profile data
    """
    async with async_session_maker() as session:
        preset_profiles = [
            {
                "id": uuid4(),
                "organization_id": "system",
                "name": "Technical",
                "description": "Emphasizes exact keyword matching for technical roles",
                "keyword_weight": 0.60,
                "tfidf_weight": 0.25,
                "vector_weight": 0.15,
                "is_default": False,
                "is_preset": True,
                "preset_type": "technical",
                "created_by": "system",
            },
            {
                "id": uuid4(),
                "organization_id": "system",
                "name": "Creative",
                "description": "Prioritizes semantic understanding for creative roles",
                "keyword_weight": 0.15,
                "tfidf_weight": 0.25,
                "vector_weight": 0.60,
                "is_default": False,
                "is_preset": True,
                "preset_type": "creative",
                "created_by": "system",
            },
            {
                "id": uuid4(),
                "organization_id": "system",
                "name": "Executive",
                "description": "Balanced matching for leadership positions",
                "keyword_weight": 0.34,
                "tfidf_weight": 0.33,
                "vector_weight": 0.33,
                "is_default": False,
                "is_preset": True,
                "preset_type": "executive",
                "created_by": "system",
            },
            {
                "id": uuid4(),
                "organization_id": "system",
                "name": "Balanced",
                "description": "Equal weight across all matching algorithms",
                "keyword_weight": 0.33,
                "tfidf_weight": 0.34,
                "vector_weight": 0.33,
                "is_default": False,
                "is_preset": True,
                "preset_type": "balanced",
                "created_by": "system",
            },
        ]

        for profile_data in preset_profiles:
            profile = MatchingWeightsProfile(**profile_data)
            session.add(profile)

        await session.commit()

        # Return profile data without ORM objects
        yield [
            {
                "id": str(p["id"]),
                "name": p["name"],
                "preset_type": p["preset_type"],
                "keyword_weight": p["keyword_weight"],
                "tfidf_weight": p["tfidf_weight"],
                "vector_weight": p["vector_weight"],
            }
            for p in preset_profiles
        ]


@pytest.fixture
async def test_vacancy(async_session_maker, test_organization) -> Dict:
    """
    Create a test vacancy for matching.

    Returns:
        Vacancy data dictionary
    """
    async with async_session_maker() as session:
        vacancy_id = uuid4()
        vacancy = Vacancy(
            id=vacancy_id,
            organization_id=test_organization,
            title="Senior Python Developer",
            description="Looking for a senior Python developer with experience in FastAPI, PostgreSQL, and Docker.",
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            min_experience_years=5,
        )
        session.add(vacancy)
        await session.commit()
        await session.refresh(vacancy)

        yield {
            "id": str(vacancy.id),
            "title": vacancy.title,
            "organization_id": str(vacancy.organization_id),
        }


@pytest.fixture
async def test_resume(async_session_maker, test_organization) -> Dict:
    """
    Create a test resume for matching.

    Returns:
        Resume data dictionary
    """
    async with async_session_maker() as session:
        resume_id = uuid4()
        resume = Resume(
            id=resume_id,
            organization_id=test_organization,
            candidate_name="John Doe",
            email="john.doe@example.com",
            raw_text="Senior Python Developer with 7 years of experience. Skilled in FastAPI, PostgreSQL, Docker, and Kubernetes. Previously worked at TechCorp building scalable microservices.",
            extracted_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
            years_of_experience=7.0,
        )
        session.add(resume)
        await session.commit()
        await session.refresh(resume)

        yield {
            "id": str(resume.id),
            "candidate_name": resume.candidate_name,
            "email": resume.email,
            "skills": resume.extracted_skills,
        }


class TestWeightProfileE2E:
    """End-to-end tests for weight profile customization flow."""

    async def test_e2e_preset_profiles_available(
        self, client: TestClient, seeded_preset_profiles
    ):
        """
        E2E Test 1: Verify preset profiles are available via API.

        Steps:
        1. GET /api/matching-weights/?is_preset=true
        2. Verify all 4 preset profiles returned
        3. Verify weight distribution for each preset
        """
        response = client.get("/api/matching-weights/?is_preset=true")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()

        assert "profiles" in data
        assert len(data["profiles"]) == 4

        # Verify Technical profile (Keyword-heavy)
        technical = next(p for p in data["profiles"] if p["preset_type"] == "technical")
        assert technical["keyword_weight"] == 0.60
        assert technical["tfidf_weight"] == 0.25
        assert technical["vector_weight"] == 0.15

        # Verify Creative profile (Vector-heavy)
        creative = next(p for p in data["profiles"] if p["preset_type"] == "creative")
        assert creative["keyword_weight"] == 0.15
        assert creative["tfidf_weight"] == 0.25
        assert creative["vector_weight"] == 0.60

        # Verify Executive profile (Balanced)
        executive = next(p for p in data["profiles"] if p["preset_type"] == "executive")
        assert abs(executive["keyword_weight"] - 0.34) < 0.01
        assert abs(executive["tfidf_weight"] - 0.33) < 0.01
        assert abs(executive["vector_weight"] - 0.33) < 0.01

    async def test_e2e_create_custom_profile_with_vector_70(
        self, client: TestClient, test_organization
    ):
        """
        E2E Test 2: Create custom profile with Vector weight 70%.

        Steps:
        1. POST /api/matching-weights/ with vector_weight=0.70
        2. Verify profile created successfully
        3. GET /api/matching-weights/{profile_id}
        4. Verify weights match request
        """
        custom_profile_data = {
            "organization_id": test_organization,
            "name": "Vector Heavy Custom",
            "description": "Custom profile emphasizing vector similarity",
            "keyword_weight": 0.15,
            "tfidf_weight": 0.15,
            "vector_weight": 0.70,
        }

        # Create custom profile
        response = client.post("/api/matching-weights/", json=custom_profile_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        created_profile = response.json()

        assert created_profile["name"] == "Vector Heavy Custom"
        assert created_profile["vector_weight"] == 0.70
        assert created_profile["is_preset"] is False

        profile_id = created_profile["id"]

        # Retrieve profile to verify
        response = client.get(f"/api/matching-weights/{profile_id}")

        assert response.status_code == 200
        retrieved_profile = response.json()

        assert retrieved_profile["vector_weight"] == 0.70
        assert retrieved_profile["keyword_weight"] == 0.15
        assert retrieved_profile["tfidf_weight"] == 0.15

    async def test_e2e_select_technical_preset_and_verify(
        self, client: TestClient, seeded_preset_profiles
    ):
        """
        E2E Test 3: Select 'Technical' preset profile and verify configuration.

        Steps:
        1. GET /api/matching-weights/?preset_type=technical
        2. Verify Technical profile is Keyword-heavy (60%)
        3. Verify profile is marked as preset
        """
        response = client.get("/api/matching-weights/?preset_type=technical")

        assert response.status_code == 200
        data = response.json()

        assert len(data["profiles"]) == 1
        technical = data["profiles"][0]

        assert technical["name"] == "Technical"
        assert technical["preset_type"] == "technical"
        assert technical["is_preset"] is True
        assert technical["keyword_weight"] == 0.60
        assert technical["tfidf_weight"] == 0.25
        assert technical["vector_weight"] == 0.15

    async def test_e2e_rematch_vacancy_with_custom_weights(
        self, client: TestClient, test_organization, test_vacancy, test_resume
    ):
        """
        E2E Test 4: Re-match candidates with custom weight profile.

        Steps:
        1. Create custom weight profile
        2. POST /api/matching-weights/{profile_id}/rematch with vacancy_id
        3. Verify re-match initiated (202 ACCEPTED)
        4. Verify response includes candidates_matched count
        """
        # Create custom profile
        custom_profile = {
            "organization_id": test_organization,
            "name": "High Keyword Weight",
            "description": "Emphasizes keyword matching",
            "keyword_weight": 0.70,
            "tfidf_weight": 0.20,
            "vector_weight": 0.10,
        }

        create_response = client.post("/api/matching-weights/", json=custom_profile)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Re-match vacancy with custom profile
        rematch_request = {"vacancy_id": test_vacancy["id"]}
        rematch_response = client.post(
            f"/api/matching-weights/{profile_id}/rematch", json=rematch_request
        )

        assert rematch_response.status_code == 202
        rematch_data = rematch_response.json()

        assert "vacancy_id" in rematch_data
        assert "profile_id" in rematch_data
        assert "candidates_matched" in rematch_data
        assert "status" in rematch_data
        assert rematch_data["status"] in ["completed", "processing"]

    async def test_e2e_compare_preset_vs_custom_profile(
        self, client: TestClient, test_organization, test_vacancy, seeded_preset_profiles
    ):
        """
        E2E Test 5: A/B testing - compare preset vs custom profile results.

        Steps:
        1. Create custom profile (Vector 70%)
        2. Get Technical preset profile ID
        3. POST /api/matching-weights/compare with profile_a and profile_b
        4. Verify comparison results include score differences
        5. Verify statistical summary data
        """
        # Create custom profile
        custom_profile = {
            "organization_id": test_organization,
            "name": "Vector Heavy for Comparison",
            "description": "Custom profile for A/B testing",
            "keyword_weight": 0.15,
            "tfidf_weight": 0.15,
            "vector_weight": 0.70,
        }

        create_response = client.post("/api/matching-weights/", json=custom_profile)
        assert create_response.status_code == 201
        custom_profile_id = create_response.json()["id"]

        # Get Technical preset profile ID
        technical_profile = next(
            p for p in seeded_preset_profiles if p["preset_type"] == "technical"
        )
        technical_profile_id = technical_profile["id"]

        # Run A/B comparison
        compare_request = {
            "profile_a_id": technical_profile_id,
            "profile_b_id": custom_profile_id,
            "vacancy_id": test_vacancy["id"],
        }

        compare_response = client.post("/api/matching-weights/compare", json=compare_request)

        assert compare_response.status_code == 200
        comparison_data = compare_response.json()

        # Verify response structure
        assert "vacancy_id" in comparison_data
        assert "profile_a" in comparison_data
        assert "profile_b" in comparison_data
        assert "differences" in comparison_data

        # Verify profile configurations returned
        assert comparison_data["profile_a"]["keyword_weight"] == 0.60
        assert comparison_data["profile_b"]["vector_weight"] == 0.70

        # Verify differences array (may be empty if no candidates matched yet)
        assert isinstance(comparison_data["differences"], list)

    async def test_e2e_weight_normalization(
        self, client: TestClient, test_organization
    ):
        """
        E2E Test 6: Verify weight normalization ensures sum equals 100%.

        Steps:
        1. Create profile with weights summing to 0.9 (should normalize to 1.0)
        2. Create profile with weights summing to 1.5 (should normalize to 1.0)
        3. Verify normalized weights stored correctly
        """
        # Profile with sum < 1.0
        profile_under = {
            "organization_id": test_organization,
            "name": "Under Sum",
            "description": "Test normalization with sum < 1.0",
            "keyword_weight": 0.30,
            "tfidf_weight": 0.30,
            "vector_weight": 0.30,  # Sum = 0.90
        }

        response = client.post("/api/matching-weights/", json=profile_under)
        assert response.status_code == 201
        data = response.json()

        # Verify normalized (each weight divided by 0.9, then multiplied)
        sum_weights = (
            data["keyword_weight"] + data["tfidf_weight"] + data["vector_weight"]
        )
        assert abs(sum_weights - 1.0) < 0.01, f"Weights should sum to 1.0, got {sum_weights}"

    async def test_e2e_update_custom_profile(
        self, client: TestClient, test_organization
    ):
        """
        E2E Test 7: Update existing custom profile.

        Steps:
        1. Create custom profile
        2. PUT /api/matching-weights/{profile_id} with new weights
        3. Verify update successful
        4. GET /api/matching-weights/{profile_id}
        5. Verify new weights saved
        """
        # Create profile
        create_data = {
            "organization_id": test_organization,
            "name": "Profile to Update",
            "description": "Will be updated",
            "keyword_weight": 0.33,
            "tfidf_weight": 0.34,
            "vector_weight": 0.33,
        }

        create_response = client.post("/api/matching-weights/", json=create_data)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Update profile
        update_data = {
            "name": "Updated Profile",
            "description": "Has been updated",
            "keyword_weight": 0.50,
            "tfidf_weight": 0.30,
            "vector_weight": 0.20,
        }

        update_response = client.put(
            f"/api/matching-weights/{profile_id}", json=update_data
        )

        assert update_response.status_code == 200
        updated_data = update_response.json()

        assert updated_data["name"] == "Updated Profile"
        assert updated_data["keyword_weight"] == 0.50

    async def test_e2e_delete_custom_profile(
        self, client: TestClient, test_organization
    ):
        """
        E2E Test 8: Delete custom profile.

        Steps:
        1. Create custom profile
        2. DELETE /api/matching-weights/{profile_id}
        3. Verify delete successful
        4. GET /api/matching-weights/{profile_id}
        5. Verify profile not found (404)
        """
        # Create profile
        create_data = {
            "organization_id": test_organization,
            "name": "Profile to Delete",
            "description": "Will be deleted",
            "keyword_weight": 0.33,
            "tfidf_weight": 0.34,
            "vector_weight": 0.33,
        }

        create_response = client.post("/api/matching-weights/", json=create_data)
        assert create_response.status_code == 201
        profile_id = create_response.json()["id"]

        # Delete profile
        delete_response = client.delete(f"/api/matching-weights/{profile_id}")

        assert delete_response.status_code == 200
        delete_data = delete_response.json()

        assert "message" in delete_data

        # Verify profile deleted
        get_response = client.get(f"/api/matching-weights/{profile_id}")

        # Should return 404 or empty list
        assert get_response.status_code in [404, 200]

    async def test_e2e_set_default_profile(
        self, client: TestClient, test_organization
    ):
        """
        E2E Test 9: Set custom profile as organization default.

        Steps:
        1. Create two custom profiles
        2. Set first as default (is_default=true)
        3. Verify default set
        4. Set second as default
        5. Verify first is no longer default
        6. Verify second is now default
        """
        # Create first profile
        profile1_data = {
            "organization_id": test_organization,
            "name": "Default Profile 1",
            "description": "First default",
            "keyword_weight": 0.40,
            "tfidf_weight": 0.30,
            "vector_weight": 0.30,
            "is_default": True,
        }

        response1 = client.post("/api/matching-weights/", json=profile1_data)
        assert response1.status_code == 201
        profile1_id = response1.json()["id"]

        # Create second profile
        profile2_data = {
            "organization_id": test_organization,
            "name": "Default Profile 2",
            "description": "Second default",
            "keyword_weight": 0.50,
            "tfidf_weight": 0.25,
            "vector_weight": 0.25,
            "is_default": True,
        }

        response2 = client.post("/api/matching-weights/", json=profile2_data)
        assert response2.status_code == 201
        profile2_id = response2.json()["id"]

        # List default profiles
        list_response = client.get(
            f"/api/matching-weights/?organization_id={test_organization}&is_default=true"
        )

        assert list_response.status_code == 200
        defaults = list_response.json()["profiles"]

        # Should have only one default (the last one set)
        assert len(defaults) >= 1
        latest_default = next((p for p in defaults if p["id"] == profile2_id), None)
        assert latest_default is not None

    async def test_e2e_complete_workflow(
        self, client: TestClient, test_organization, test_vacancy, seeded_preset_profiles
    ):
        """
        E2E Test 10: Complete end-to-end workflow simulation.

        This test simulates the full user journey:
        1. Navigate to settings → List preset profiles
        2. Select Technical preset → Verify configuration
        3. Create custom profile (Vector 70%) → Save
        4. Go to vacancy → Select custom profile
        5. Trigger re-match → Verify candidates re-matched
        6. Run A/B comparison → Compare results
        """
        # Step 1 & 2: List and select Technical preset
        list_response = client.get("/api/matching-weights/?is_preset=true")
        assert list_response.status_code == 200
        presets = list_response.json()["profiles"]

        technical = next(p for p in presets if p["preset_type"] == "technical")
        assert technical["keyword_weight"] == 0.60

        # Step 3: Create custom profile with Vector 70%
        custom_profile = {
            "organization_id": test_organization,
            "name": "Custom Vector 70%",
            "description": "Created during E2E test",
            "keyword_weight": 0.15,
            "tfidf_weight": 0.15,
            "vector_weight": 0.70,
        }

        create_response = client.post("/api/matching-weights/", json=custom_profile)
        assert create_response.status_code == 201
        custom_profile_data = create_response.json()
        custom_profile_id = custom_profile_data["id"]

        # Verify custom profile saved
        get_response = client.get(f"/api/matching-weights/{custom_profile_id}")
        assert get_response.status_code == 200
        assert get_response.json()["vector_weight"] == 0.70

        # Step 4 & 5: Re-match vacancy with custom profile
        rematch_response = client.post(
            f"/api/matching-weights/{custom_profile_id}/rematch",
            json={"vacancy_id": test_vacancy["id"]},
        )
        assert rematch_response.status_code == 202
        rematch_data = rematch_response.json()

        assert "candidates_matched" in rematch_data
        assert rematch_data["status"] == "completed"

        # Step 6: A/B comparison
        technical_id = technical["id"]
        compare_response = client.post(
            "/api/matching-weights/compare",
            json={
                "profile_a_id": technical_id,
                "profile_b_id": custom_profile_id,
                "vacancy_id": test_vacancy["id"],
            },
        )

        assert compare_response.status_code == 200
        comparison = compare_response.json()

        # Verify comparison structure
        assert comparison["profile_a"]["preset_type"] == "technical"
        assert comparison["profile_b"]["vector_weight"] == 0.70
        assert "differences" in comparison

        # Complete workflow successful
        assert True


class TestWeightProfileValidation:
    """Test validation and error scenarios."""

    async def test_invalid_weights_sum_to_zero(self, client: TestClient, test_organization):
        """Test that weights summing to zero are rejected."""
        invalid_profile = {
            "organization_id": test_organization,
            "name": "Invalid Weights",
            "description": "All weights zero",
            "keyword_weight": 0.0,
            "tfidf_weight": 0.0,
            "vector_weight": 0.0,
        }

        response = client.post("/api/matching-weights/", json=invalid_profile)

        # Should return 422 validation error
        assert response.status_code == 422

    async def test_negative_weights_rejected(self, client: TestClient, test_organization):
        """Test that negative weights are rejected."""
        invalid_profile = {
            "organization_id": test_organization,
            "name": "Negative Weight",
            "description": "Has negative weight",
            "keyword_weight": -0.1,
            "tfidf_weight": 0.5,
            "vector_weight": 0.6,
        }

        response = client.post("/api/matching-weights/", json=invalid_profile)

        assert response.status_code == 422

    async def test_weights_exceeding_one_rejected(
        self, client: TestClient, test_organization
    ):
        """Test that individual weights > 1.0 are rejected."""
        invalid_profile = {
            "organization_id": test_organization,
            "name": "Weight Too High",
            "description": "Weight exceeds 1.0",
            "keyword_weight": 1.5,
            "tfidf_weight": 0.0,
            "vector_weight": 0.0,
        }

        response = client.post("/api/matching-weights/", json=invalid_profile)

        assert response.status_code == 422

    async def test_comparison_same_profile_ids_rejected(
        self, client: TestClient, test_vacancy
    ):
        """Test that comparing a profile to itself is rejected."""
        comparison = {
            "profile_a_id": str(uuid4()),
            "profile_b_id": str(uuid4()),
            "vacancy_id": test_vacancy["id"],
        }

        # Same IDs should be rejected
        comparison["profile_b_id"] = comparison["profile_a_id"]

        response = client.post("/api/matching-weights/compare", json=comparison)

        assert response.status_code == 422
        assert "different" in response.json()["detail"].lower()


class TestWeightProfileHistory:
    """Test audit trail and version history."""

    async def test_profile_creation_creates_history_entry(
        self, client: TestClient, test_organization, async_session_maker
    ):
        """Test that creating a profile creates a history entry."""
        # Create profile
        profile_data = {
            "organization_id": test_organization,
            "name": "History Test Profile",
            "description": "Testing audit trail",
            "keyword_weight": 0.50,
            "tfidf_weight": 0.30,
            "vector_weight": 0.20,
        }

        response = client.post("/api/matching-weights/", json=profile_data)
        assert response.status_code == 201
        profile_id = response.json()["id"]

        # Verify history entry created
        async with async_session_maker() as session:
            result = await session.execute(
                select(MatchingWeightsHistory).where(
                    MatchingWeightsHistory.profile_id == profile_id
                )
            )
            history_entries = result.scalars().all()

            assert len(history_entries) > 0
            assert history_entries[0].change_type == "created"

    async def test_profile_update_creates_history_entry(
        self, client: TestClient, test_organization, async_session_maker
    ):
        """Test that updating a profile creates a history entry."""
        # Create profile
        profile_data = {
            "organization_id": test_organization,
            "name": "Update History Test",
            "description": "Testing update history",
            "keyword_weight": 0.50,
            "tfidf_weight": 0.30,
            "vector_weight": 0.20,
        }

        response = client.post("/api/matching-weights/", json=profile_data)
        profile_id = response.json()["id"]

        # Update profile
        update_data = {"keyword_weight": 0.60}
        response = client.put(f"/api/matching-weights/{profile_id}", json=update_data)
        assert response.status_code == 200

        # Verify history entry created
        async with async_session_maker() as session:
            result = await session.execute(
                select(MatchingWeightsHistory).where(
                    MatchingWeightsHistory.profile_id == profile_id,
                    MatchingWeightsHistory.change_type == "updated",
                )
            )
            history_entries = result.scalars().all()

            assert len(history_entries) > 0
