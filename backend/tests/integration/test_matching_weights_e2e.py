"""
End-to-End Integration Test for Matching Weights CRUD Workflow

This script tests the complete flow of matching weights profile management,
including create, read, update, delete, and set-active operations.

Test Steps:
1. Create a profile via POST /api/matching-weights/
2. Verify profile appears in GET /api/matching-weights/
3. Get single profile via GET /api/matching-weights/{id}
4. Update profile via PUT /api/matching-weights/{id}
5. Verify update persisted
6. Set profile as active via POST /api/matching-weights/{id}/set-active
7. Delete profile via DELETE /api/matching-weights/{id}
8. Verify profile deleted

Requirements:
- Backend server running on http://localhost:8000
- Database available and migrations applied

Usage:
    cd backend
    pytest tests/integration/test_matching_weights_e2e.py -v
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app
from database import get_db
from models.matching_weights_profile import MatchingWeightsProfile


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
async def test_organization_id() -> str:
    """Generate a test organization ID."""
    return str(uuid4())


@pytest.fixture
async def test_profile_data(test_organization_id) -> dict:
    """Generate test profile data."""
    return {
        "organization_id": test_organization_id,
        "name": "E2E Test Profile",
        "description": "Test profile for end-to-end verification",
        "keyword_weight": 0.5,
        "tfidf_weight": 0.3,
        "vector_weight": 0.2,
        "is_default": False,
        "is_preset": False,
        "created_by": "test-user-001",
    }


@pytest.fixture
async def update_profile_data() -> dict:
    """Generate data for updating profile."""
    return {
        "name": "Updated E2E Test Profile",
        "description": "Updated test profile description",
        "keyword_weight": 0.6,
        "tfidf_weight": 0.2,
        "vector_weight": 0.2,
    }


# ============================================================================
# Test Class
# ============================================================================

@pytest.mark.e2e
@pytest.mark.integration
class TestWeightProfileE2E:
    """
    End-to-end test suite for matching weights CRUD operations.

    Tests the complete workflow from creation to deletion,
    verifying database persistence at each step.
    """

    async def test_e2e_complete_workflow(
        self,
        test_db: AsyncSession,
        test_profile_data: dict,
        update_profile_data: dict,
    ) -> None:
        """
        Test complete CRUD workflow for matching weights profiles.

        This test verifies:
        1. Creating a new profile
        2. Listing profiles (profile appears in list)
        3. Getting single profile by ID
        4. Updating profile fields
        5. Verifying update persisted
        6. Setting profile as active
        7. Deleting profile
        8. Verifying deletion
        """
        # Use ASGI transport for direct app testing (no server needed)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # ========================================================================
            # Step 1: Create profile via POST /api/matching-weights/
            # ========================================================================
            response = await client.post("/api/matching-weights/", json=test_profile_data)

            assert response.status_code == 201, f"Create failed: {response.text}"
            created_profile = response.json()

            # Verify response contains required fields
            assert "id" in created_profile
            assert created_profile["name"] == test_profile_data["name"]
            assert created_profile["organization_id"] == test_profile_data["organization_id"]
            assert created_profile["keyword_weight"] == test_profile_data["keyword_weight"]
            assert created_profile["tfidf_weight"] == test_profile_data["tfidf_weight"]
            assert created_profile["vector_weight"] == test_profile_data["vector_weight"]
            assert "created_at" in created_profile
            assert "updated_at" in created_profile

            profile_id = created_profile["id"]

            # Verify profile exists in database
            result = await test_db.execute(
                select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
            )
            db_profile = result.scalar_one_or_none()
            assert db_profile is not None, "Profile not found in database after creation"
            assert db_profile.name == test_profile_data["name"]

            # ========================================================================
            # Step 2: Verify profile appears in GET /api/matching-weights/
            # ========================================================================
            response = await client.get(
                f"/api/matching-weights/?organization_id={test_profile_data['organization_id']}"
            )

            assert response.status_code == 200
            profiles_response = response.json()

            assert "profiles" in profiles_response
            assert "total_count" in profiles_response
            assert profiles_response["total_count"] >= 1

            # Find our created profile in the list
            found_profile = None
            for p in profiles_response["profiles"]:
                if p["id"] == profile_id:
                    found_profile = p
                    break

            assert found_profile is not None, "Created profile not found in list"
            assert found_profile["name"] == test_profile_data["name"]

            # ========================================================================
            # Step 3: Get single profile via GET /api/matching-weights/{id}
            # ========================================================================
            response = await client.get(f"/api/matching-weights/{profile_id}")

            assert response.status_code == 200
            single_profile = response.json()

            assert single_profile["id"] == profile_id
            assert single_profile["name"] == test_profile_data["name"]
            assert single_profile["keyword_weight"] == test_profile_data["keyword_weight"]
            assert "created_at" in single_profile
            assert "updated_at" in single_profile

            # ========================================================================
            # Step 4: Update profile via PUT /api/matching-weights/{id}
            # ========================================================================
            response = await client.put(
                f"/api/matching-weights/{profile_id}",
                json=update_profile_data
            )

            assert response.status_code == 200
            updated_profile = response.json()

            # Verify updated fields
            assert updated_profile["id"] == profile_id
            assert updated_profile["name"] == update_profile_data["name"]
            assert updated_profile["description"] == update_profile_data["description"]
            assert updated_profile["keyword_weight"] == update_profile_data["keyword_weight"]
            assert updated_profile["tfidf_weight"] == update_profile_data["tfidf_weight"]
            assert updated_profile["vector_weight"] == update_profile_data["vector_weight"]

            # ========================================================================
            # Step 5: Verify update persisted (get profile again)
            # ========================================================================
            response = await client.get(f"/api/matching-weights/{profile_id}")

            assert response.status_code == 200
            verified_profile = response.json()

            # Verify update persisted
            assert verified_profile["name"] == update_profile_data["name"]
            assert verified_profile["description"] == update_profile_data["description"]
            assert verified_profile["keyword_weight"] == update_profile_data["keyword_weight"]
            assert verified_profile["tfidf_weight"] == update_profile_data["tfidf_weight"]
            assert verified_profile["vector_weight"] == update_profile_data["vector_weight"]

            # Also verify in database
            result = await test_db.execute(
                select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
            )
            db_profile = result.scalar_one_or_none()
            assert db_profile is not None
            assert db_profile.name == update_profile_data["name"]
            assert db_profile.description == update_profile_data["description"]

            # ========================================================================
            # Step 6: Set profile as active via POST /api/matching-weights/{id}/set-active
            # ========================================================================
            response = await client.post(f"/api/matching-weights/{profile_id}/set-active")

            assert response.status_code == 200
            active_profile = response.json()

            # Verify is_default is now True
            assert active_profile["id"] == profile_id
            assert active_profile["is_default"] is True

            # Verify in database
            await test_db.refresh(db_profile)
            assert db_profile.is_default is True

            # ========================================================================
            # Step 7: Delete profile via DELETE /api/matching-weights/{id}
            # ========================================================================
            # First, unset is_default so we can delete it
            unset_data = {"is_default": False}
            response = await client.put(f"/api/matching-weights/{profile_id}", json=unset_data)
            assert response.status_code == 200

            # Now delete the profile
            response = await client.delete(f"/api/matching-weights/{profile_id}")

            assert response.status_code == 200
            delete_response = response.json()

            assert "message" in delete_response
            assert delete_response["id"] == profile_id

            # ========================================================================
            # Step 8: Verify profile deleted
            # ========================================================================
            # Try to get the deleted profile (should return 404)
            response = await client.get(f"/api/matching-weights/{profile_id}")

            assert response.status_code == 404

            # Verify profile not in database
            result = await test_db.execute(
                select(MatchingWeightsProfile).where(MatchingWeightsProfile.id == profile_id)
            )
            db_profile = result.scalar_one_or_none()
            assert db_profile is None, "Profile still exists in database after deletion"


@pytest.mark.e2e
@pytest.mark.integration
class TestWeightProfileEdgeCases:
    """Test edge cases and error conditions."""

    async def test_get_nonexistent_profile_returns_404(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that getting a non-existent profile returns 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_id = str(uuid4())
            response = await client.get(f"/api/matching-weights/{fake_id}")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    async def test_update_nonexistent_profile_returns_404(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that updating a non-existent profile returns 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_id = str(uuid4())
            update_data = {"name": "Updated Name"}
            response = await client.put(f"/api/matching-weights/{fake_id}", json=update_data)

            assert response.status_code == 404

    async def test_delete_nonexistent_profile_returns_404(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that deleting a non-existent profile returns 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_id = str(uuid4())
            response = await client.delete(f"/api/matching-weights/{fake_id}")

            assert response.status_code == 404

    async def test_delete_preset_profile_returns_400(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that preset profiles cannot be deleted."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a preset profile
            preset_data = {
                "organization_id": str(uuid4()),
                "name": "Preset Profile",
                "description": "A preset profile",
                "keyword_weight": 0.5,
                "tfidf_weight": 0.3,
                "vector_weight": 0.2,
                "is_preset": True,
                "preset_type": "technical",
            }

            response = await client.post("/api/matching-weights/", json=preset_data)
            assert response.status_code == 201
            preset_profile = response.json()
            preset_id = preset_profile["id"]

            # Try to delete the preset profile
            response = await client.delete(f"/api/matching-weights/{preset_id}")

            assert response.status_code == 400
            assert "preset" in response.json()["detail"].lower()

            # Clean up - update to non-preset then delete
            update_data = {"is_preset": False, "is_default": False}
            await client.put(f"/api/matching-weights/{preset_id}", json=update_data)
            await client.delete(f"/api/matching-weights/{preset_id}")

    async def test_delete_default_profile_returns_400(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that default profiles cannot be deleted."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a profile and set it as default
            profile_data = {
                "organization_id": str(uuid4()),
                "name": "Default Profile",
                "description": "A default profile",
                "keyword_weight": 0.5,
                "tfidf_weight": 0.3,
                "vector_weight": 0.2,
                "is_default": True,
            }

            response = await client.post("/api/matching-weights/", json=profile_data)
            assert response.status_code == 201
            default_profile = response.json()
            default_id = default_profile["id"]

            # Try to delete the default profile
            response = await client.delete(f"/api/matching-weights/{default_id}")

            assert response.status_code == 400
            assert "default" in response.json()["detail"].lower()

            # Clean up - unset default then delete
            update_data = {"is_default": False}
            await client.put(f"/api/matching-weights/{default_id}", json=update_data)
            await client.delete(f"/api/matching-weights/{default_id}")

    async def test_set_active_nonexistent_profile_returns_404(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that setting a non-existent profile as active returns 404."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_id = str(uuid4())
            response = await client.post(f"/api/matching-weights/{fake_id}/set-active")

            assert response.status_code == 404

    async def test_create_profile_with_empty_organization_id_returns_422(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that creating a profile with empty organization_id returns 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            invalid_data = {
                "organization_id": "",
                "name": "Test Profile",
                "keyword_weight": 0.5,
                "tfidf_weight": 0.3,
                "vector_weight": 0.2,
            }

            response = await client.post("/api/matching-weights/", json=invalid_data)

            assert response.status_code == 422

    async def test_create_profile_with_empty_name_returns_422(
        self,
        test_db: AsyncSession,
    ) -> None:
        """Test that creating a profile with empty name returns 422."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            invalid_data = {
                "organization_id": str(uuid4()),
                "name": "",
                "keyword_weight": 0.5,
                "tfidf_weight": 0.3,
                "vector_weight": 0.2,
            }

            response = await client.post("/api/matching-weights/", json=invalid_data)

            assert response.status_code == 422


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
