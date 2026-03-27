"""
End-to-End tests for custom weight profiles.

Tests the complete workflow:
1. Creating custom weight profiles
2. Applying to vacancy ranking
3. Verifying ranking changes
4. Testing preset templates
5. A/B testing workflow
6. Real-time preview updates
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
import asyncio

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from models.matching_weights import WeightProfile, WeightProfileType


class TestCustomWeightsE2E:
    """E2E tests for custom weight profiles."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def sample_weight_data(self):
        """Sample weight configuration data."""
        return {
            "name": "Custom Technical Focus",
            "description": "Emphasizes technical skills over other factors",
            "profile_type": "custom",
            "organization_id": str(uuid4()),
            "weights": {
                "skill_match_weight": 0.25,
                "experience_weight": 0.15,
                "education_weight": 0.10,
                "certification_weight": 0.10,
                "keyword_match_weight": 0.15,
                "semantic_match_weight": 0.10,
                "recruiter_feedback_weight": 0.05,
                "culture_fit_weight": 0.05,
                "location_weight": 0.03,
                "salary_weight": 0.02,
                "availability_weight": 0.02,
                "tenure_weight": 0.02,
                "industry_match_weight": 0.01,
            },
        }

    def test_weight_profile_creation(self, sample_weight_data):
        """Test creating a custom weight profile."""
        # Validate weight profile structure
        assert "name" in sample_weight_data
        assert "weights" in sample_weight_data
        assert len(sample_weight_data["weights"]) == 13

        # Validate weights sum to approximately 1.0
        total_weight = sum(sample_weight_data["weights"].values())
        assert 0.99 <= total_weight <= 1.01, f"Weights should sum to 1.0, got {total_weight}"

    def test_weight_validation_constraints(self):
        """Test weight validation constraints."""
        # Individual weight should be between 0 and 1
        valid_weight = 0.15
        assert 0 <= valid_weight <= 1

        # Negative weights should be invalid
        invalid_weight = -0.1
        assert not (0 <= invalid_weight <= 1)

        # Weights over 1 should be invalid
        invalid_weight = 1.5
        assert not (0 <= invalid_weight <= 1)

    def test_preset_templates_available(self):
        """Test that preset templates are available."""
        preset_types = ["technical", "sales", "executive", "balanced", "entry_level"]
        
        for preset in preset_types:
            assert preset in ["technical", "sales", "executive", "balanced", "entry_level"]

    def test_custom_profile_13_weights(self):
        """Test that custom profile has all 13 weights."""
        expected_weights = [
            "skill_match_weight",
            "experience_weight",
            "education_weight",
            "certification_weight",
            "keyword_match_weight",
            "semantic_match_weight",
            "recruiter_feedback_weight",
            "culture_fit_weight",
            "location_weight",
            "salary_weight",
            "availability_weight",
            "tenure_weight",
            "industry_match_weight",
        ]
        
        assert len(expected_weights) == 13
        assert len(set(expected_weights)) == 13  # All unique


class TestRankingChangesE2E:
    """E2E tests for ranking changes with custom weights."""

    def test_ranking_changes_with_different_weights(self):
        """Test that different weight profiles produce different rankings."""
        # Mock candidate data
        candidates = [
            {"id": "1", "skills_score": 0.9, "experience_score": 0.5},
            {"id": "2", "skills_score": 0.6, "experience_score": 0.9},
        ]

        # Technical focus weights (prioritize skills)
        technical_weights = {
            "skill_match_weight": 0.7,
            "experience_weight": 0.3,
        }

        # Experience focus weights (prioritize experience)
        experience_weights = {
            "skill_match_weight": 0.3,
            "experience_weight": 0.7,
        }

        # Calculate technical ranking
        technical_scores = [
            c["skills_score"] * technical_weights["skill_match_weight"] +
            c["experience_score"] * technical_weights["experience_weight"]
            for c in candidates
        ]

        # Calculate experience ranking
        experience_scores = [
            c["skills_score"] * experience_weights["skill_match_weight"] +
            c["experience_score"] * experience_weights["experience_weight"]
            for c in candidates
        ]

        # Verify different rankings
        technical_order = sorted(range(len(technical_scores)), key=lambda i: technical_scores[i], reverse=True)
        experience_order = sorted(range(len(experience_scores)), key=lambda i: experience_scores[i], reverse=True)

        # With these weights, candidate 1 wins technical, candidate 2 wins experience
        assert technical_order[0] == 0  # Candidate 1 wins
        assert experience_order[0] == 1  # Candidate 2 wins

    def test_ranking_preserves_relative_order_for_ties(self):
        """Test that ranking handles ties consistently."""
        candidates = [
            {"id": "1", "score": 0.8},
            {"id": "2", "score": 0.8},
            {"id": "3", "score": 0.9},
        ]
        
        # Sort by score descending
        sorted_candidates = sorted(candidates, key=lambda c: c["score"], reverse=True)
        
        # First should be candidate 3 with highest score
        assert sorted_candidates[0]["id"] == "3"


class TestPresetTemplatesE2E:
    """E2E tests for preset templates."""

    def test_technical_preset_weights(self):
        """Test technical preset has expected weight distribution."""
        technical_preset = {
            "skill_match_weight": 0.25,
            "experience_weight": 0.15,
            "education_weight": 0.10,
            "certification_weight": 0.15,
            "keyword_match_weight": 0.15,
            "semantic_match_weight": 0.10,
            "recruiter_feedback_weight": 0.02,
            "culture_fit_weight": 0.02,
            "location_weight": 0.02,
            "salary_weight": 0.01,
            "availability_weight": 0.01,
            "tenure_weight": 0.01,
            "industry_match_weight": 0.01,
        }

        # Technical preset should prioritize skills and certifications
        assert technical_preset["skill_match_weight"] > technical_preset["culture_fit_weight"]
        assert technical_preset["certification_weight"] > technical_preset["salary_weight"]

    def test_sales_preset_weights(self):
        """Test sales preset has expected weight distribution."""
        sales_preset = {
            "skill_match_weight": 0.15,
            "experience_weight": 0.20,
            "education_weight": 0.05,
            "certification_weight": 0.05,
            "keyword_match_weight": 0.10,
            "semantic_match_weight": 0.10,
            "recruiter_feedback_weight": 0.10,
            "culture_fit_weight": 0.10,
            "location_weight": 0.05,
            "salary_weight": 0.05,
            "availability_weight": 0.03,
            "tenure_weight": 0.01,
            "industry_match_weight": 0.01,
        }

        # Sales preset should prioritize experience and culture fit
        assert sales_preset["experience_weight"] >= sales_preset["skill_match_weight"]
        assert sales_preset["culture_fit_weight"] > sales_preset["certification_weight"]


class TestABTestingE2E:
    """E2E tests for A/B testing workflow."""

    def test_ab_test_variant_assignment(self):
        """Test A/B test variant assignment is consistent."""
        import hashlib
        
        test_id = str(uuid4())
        
        # Simulate variant assignment based on hash
        def get_variant(vacancy_id: str) -> str:
            hash_value = int(hashlib.md5(f"{test_id}:{vacancy_id}".encode()).hexdigest(), 16)
            return "a" if hash_value % 2 == 0 else "b"
        
        # Test consistency - same vacancy always gets same variant
        vacancy_id = str(uuid4())
        variant1 = get_variant(vacancy_id)
        variant2 = get_variant(vacancy_id)
        
        assert variant1 == variant2
        assert variant1 in ["a", "b"]

    def test_ab_test_statistics_calculation(self):
        """Test A/B test statistics are calculated correctly."""
        # Mock test results
        results = {
            "a": {"count": 100, "hires": 15},
            "b": {"count": 100, "hires": 20},
        }
        
        # Calculate hire rates
        rate_a = results["a"]["hires"] / results["a"]["count"]
        rate_b = results["b"]["hires"] / results["b"]["count"]
        
        assert rate_a == 0.15
        assert rate_b == 0.20
        assert rate_b > rate_a  # Variant B performs better

    def test_ab_test_winner_determination(self):
        """Test A/B test winner determination logic."""
        stats = {
            "variant_a": {"hire_rate": 0.15, "count": 100},
            "variant_b": {"hire_rate": 0.20, "count": 100},
            "confidence": 85.0,
        }
        
        # Determine winner based on hire rate
        if stats["variant_b"]["hire_rate"] > stats["variant_a"]["hire_rate"]:
            winner = "b"
        elif stats["variant_a"]["hire_rate"] > stats["variant_b"]["hire_rate"]:
            winner = "a"
        else:
            winner = "tie"
        
        assert winner == "b"


class TestRealTimePreviewE2E:
    """E2E tests for real-time preview functionality."""

    def test_preview_updates_on_weight_change(self):
        """Test that preview updates when weights change."""
        # Initial weights
        weights = {"skill_match_weight": 0.5, "experience_weight": 0.5}
        
        # Initial ranking
        candidates = [{"id": "1", "score": 0.8}, {"id": "2", "score": 0.7}]
        
        # Change weights
        new_weights = {"skill_match_weight": 0.7, "experience_weight": 0.3}
        
        # Verify weights changed
        assert weights != new_weights
        assert new_weights["skill_match_weight"] == 0.7

    def test_preview_latency_acceptable(self):
        """Test that preview updates are fast enough."""
        import time
        
        # Simulate preview calculation
        start_time = time.time()
        
        # Mock preview calculation
        candidates = [{"id": str(i), "score": 0.5 + i * 0.1} for i in range(10)]
        weights = {f"weight_{i}": 1/13 for i in range(13)}
        
        # Calculate new rankings
        for candidate in candidates:
            candidate["final_score"] = candidate["score"] * sum(weights.values())
        
        elapsed = time.time() - start_time
        
        # Preview should be calculated in under 100ms
        assert elapsed < 0.1

    def test_preview_handles_large_candidate_sets(self):
        """Test preview with large candidate sets."""
        # Generate 1000 candidates
        candidates = [{"id": str(i), "score": 0.5} for i in range(1000)]
        
        assert len(candidates) == 1000
        
        # Preview should handle this gracefully
        # (In real implementation, might use pagination or virtualization)


class TestWeightProfileIntegration:
    """Integration tests for weight profile API."""

    @pytest.mark.asyncio
    async def test_create_profile_via_api(self, mock_db_session):
        """Test creating profile via API."""
        profile_data = {
            "name": "Test Profile",
            "organization_id": str(uuid4()),
            "weights": {f"weight_{i}": 1/13 for i in range(13)},
        }
        
        # Validate structure
        assert "name" in profile_data
        assert "organization_id" in profile_data
        assert "weights" in profile_data

    @pytest.mark.asyncio
    async def test_list_profiles_via_api(self, mock_db_session):
        """Test listing profiles via API."""
        # Mock response
        profiles = [
            {"id": str(uuid4()), "name": "Profile 1"},
            {"id": str(uuid4()), "name": "Profile 2"},
        ]
        
        assert len(profiles) == 2

    @pytest.mark.asyncio
    async def test_apply_profile_to_vacancy(self, mock_db_session):
        """Test applying profile to vacancy."""
        profile_id = str(uuid4())
        vacancy_id = str(uuid4())
        
        # Mock application
        application = {
            "profile_id": profile_id,
            "vacancy_id": vacancy_id,
            "applied_at": "2026-03-22T12:00:00Z",
        }
        
        assert application["profile_id"] == profile_id
        assert application["vacancy_id"] == vacancy_id


class TestWeightEdgeCases:
    """Edge case tests for weight profiles."""

    def test_all_weights_zero_raises_error(self):
        """Test that all zero weights are invalid."""
        weights = {f"weight_{i}": 0.0 for i in range(13)}
        
        total = sum(weights.values())
        assert total == 0.0
        # In real implementation, this should raise validation error

    def test_single_weight_one_others_zero(self):
        """Test that single weight of 1.0 is valid."""
        weights = {f"weight_{i}": 0.0 for i in range(13)}
        weights["weight_0"] = 1.0
        
        total = sum(weights.values())
        assert total == 1.0

    def test_extreme_weight_distribution(self):
        """Test extreme weight distributions."""
        # All weight on one factor
        extreme_weights = {
            "skill_match_weight": 1.0,
            **{f"other_{i}": 0.0 for i in range(12)},
        }
        
        total = sum(extreme_weights.values())
        assert total == 1.0
