"""
End-to-End Integration Tests for Explanation Preferences API

Tests the complete explanation preferences workflow:
1. Get default preferences for an organization
2. Create/update explanation preferences
3. Verify preference persistence
4. Test validation and error handling
"""
import pytest
import requests
from typing import Dict, Any
from uuid import uuid4


class TestExplanationPreferencesE2E:
    """End-to-end tests for the explanation preferences API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_organization(self):
        """Create a test organization for preference tests."""
        # Use a random organization ID to avoid conflicts
        org_id = f"test-org-{uuid4().hex[:8]}"
        yield org_id
        # Cleanup - delete preferences if they exist
        try:
            requests.delete(f"{self.BASE_URL}/api/explainability/preferences/{org_id}")
        except Exception:
            pass

    @pytest.fixture(scope="class")
    def another_organization(self):
        """Create another test organization for multi-tenant tests."""
        org_id = f"another-org-{uuid4().hex[:8]}"
        yield org_id
        # Cleanup
        try:
            requests.delete(f"{self.BASE_URL}/api/explainability/preferences/{org_id}")
        except Exception:
            pass

    def test_get_default_preferences(self, test_organization):
        """Test retrieving default preferences for a new organization."""
        response = requests.get(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}"
        )

        assert response.status_code == 200

        preferences = response.json()

        # Verify response structure
        assert "id" in preferences
        assert "organization_id" in preferences
        assert preferences["organization_id"] == test_organization
        assert "tone" in preferences
        assert "style" in preferences
        assert "detail_level" in preferences
        assert "include_percentiles" in preferences
        assert "include_skill_names" in preferences
        assert "include_experience_details" in preferences
        assert "include_education_details" in preferences
        assert "language" in preferences
        assert "custom_prompt_template" in preferences
        assert "is_active" in preferences
        assert "created_by" in preferences
        assert "created_at" in preferences
        assert "updated_at" in preferences

        # Verify default values
        assert preferences["tone"] == "professional"
        assert preferences["style"] == "balanced"
        assert preferences["detail_level"] == "medium"
        assert preferences["include_percentiles"] is True
        assert preferences["include_skill_names"] is True
        assert preferences["include_experience_details"] is True
        assert preferences["include_education_details"] is True
        assert preferences["is_active"] is False

    def test_create_preferences(self, test_organization):
        """Test creating new explanation preferences for an organization."""
        create_request = {
            "tone": "casual",
            "style": "detailed",
            "detail_level": "high",
            "include_percentiles": False,
            "include_skill_names": True,
            "include_experience_details": True,
            "include_education_details": False,
            "language": "en",
            "is_active": True,
        }

        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json=create_request
        )

        assert response.status_code == 200

        preferences = response.json()

        # Verify created values
        assert preferences["organization_id"] == test_organization
        assert preferences["tone"] == "casual"
        assert preferences["style"] == "detailed"
        assert preferences["detail_level"] == "high"
        assert preferences["include_percentiles"] is False
        assert preferences["include_skill_names"] is True
        assert preferences["include_experience_details"] is True
        assert preferences["include_education_details"] is False
        assert preferences["language"] == "en"
        assert preferences["is_active"] is True

        # Verify ID was generated
        assert preferences["id"] != ""
        assert len(preferences["id"]) > 0

    def test_update_existing_preferences(self, test_organization):
        """Test updating existing explanation preferences."""
        # First create preferences
        create_request = {
            "tone": "formal",
            "style": "concise",
            "detail_level": "low",
            "is_active": True,
        }

        create_response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json=create_request
        )
        assert create_response.status_code == 200

        # Now update with partial changes
        update_request = {
            "tone": "friendly",
            "detail_level": "medium",
        }

        update_response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json=update_request
        )

        assert update_response.status_code == 200

        updated = update_response.json()

        # Verify updated fields
        assert updated["tone"] == "friendly"
        assert updated["detail_level"] == "medium"

        # Verify unchanged fields remain
        assert updated["style"] == "concise"
        assert updated["is_active"] is True

    def test_preference_persistence(self, test_organization):
        """Test that preferences are persisted across requests."""
        # Create preferences
        create_request = {
            "tone": "casual",
            "style": "balanced",
            "detail_level": "medium",
            "language": "es",
            "is_active": True,
        }

        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json=create_request
        )

        # Retrieve preferences
        get_response = requests.get(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}"
        )

        assert get_response.status_code == 200

        retrieved = get_response.json()

        # Verify persisted values match
        assert retrieved["tone"] == "casual"
        assert retrieved["style"] == "balanced"
        assert retrieved["detail_level"] == "medium"
        assert retrieved["language"] == "es"
        assert retrieved["is_active"] is True

    def test_all_tone_options(self, test_organization):
        """Test all valid tone options."""
        valid_tones = ["professional", "casual", "friendly", "formal"]

        for tone in valid_tones:
            response = requests.put(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
                json={"tone": tone}
            )

            assert response.status_code == 200
            assert response.json()["tone"] == tone

    def test_all_style_options(self, test_organization):
        """Test all valid style options."""
        valid_styles = ["detailed", "concise", "balanced"]

        for style in valid_styles:
            response = requests.put(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
                json={"style": style}
            )

            assert response.status_code == 200
            assert response.json()["style"] == style

    def test_all_detail_levels(self, test_organization):
        """Test all valid detail level options."""
        valid_levels = ["high", "medium", "low"]

        for level in valid_levels:
            response = requests.put(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
                json={"detail_level": level}
            )

            assert response.status_code == 200
            assert response.json()["detail_level"] == level

    def test_custom_prompt_template(self, test_organization):
        """Test setting custom prompt template."""
        custom_template = (
            "Generate a {tone} explanation in {style} style with {detail_level} detail. "
            "Focus on {key_features} and provide actionable insights."
        )

        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"custom_prompt_template": custom_template}
        )

        assert response.status_code == 200

        preferences = response.json()
        assert preferences["custom_prompt_template"] == custom_template

    def test_all_inclusion_flags(self, test_organization):
        """Test all inclusion flags independently."""
        # Test all flags False
        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={
                "include_percentiles": False,
                "include_skill_names": False,
                "include_experience_details": False,
                "include_education_details": False,
            }
        )

        assert response.status_code == 200

        preferences = response.json()
        assert preferences["include_percentiles"] is False
        assert preferences["include_skill_names"] is False
        assert preferences["include_experience_details"] is False
        assert preferences["include_education_details"] is False

        # Test all flags True
        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={
                "include_percentiles": True,
                "include_skill_names": True,
                "include_experience_details": True,
                "include_education_details": True,
            }
        )

        assert response.status_code == 200

        preferences = response.json()
        assert preferences["include_percentiles"] is True
        assert preferences["include_skill_names"] is True
        assert preferences["include_experience_details"] is True
        assert preferences["include_education_details"] is True

    def test_multi_organization_isolation(self, test_organization, another_organization):
        """Test that preferences are isolated between organizations."""
        # Set preferences for first org
        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={
                "tone": "professional",
                "style": "detailed",
                "detail_level": "high",
                "language": "en",
            }
        )

        # Set different preferences for second org
        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{another_organization}",
            json={
                "tone": "casual",
                "style": "concise",
                "detail_level": "low",
                "language": "es",
            }
        )

        # Verify first org preferences
        response1 = requests.get(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}"
        )
        assert response1.status_code == 200
        prefs1 = response1.json()
        assert prefs1["tone"] == "professional"
        assert prefs1["style"] == "detailed"
        assert prefs1["detail_level"] == "high"
        assert prefs1["language"] == "en"

        # Verify second org preferences
        response2 = requests.get(
            f"{self.BASE_URL}/api/explainability/preferences/{another_organization}"
        )
        assert response2.status_code == 200
        prefs2 = response2.json()
        assert prefs2["tone"] == "casual"
        assert prefs2["style"] == "concise"
        assert prefs2["detail_level"] == "low"
        assert prefs2["language"] == "es"

    def test_partial_update_behavior(self, test_organization):
        """Test that partial updates only modify specified fields."""
        # Create full preferences
        create_request = {
            "tone": "professional",
            "style": "balanced",
            "detail_level": "medium",
            "include_percentiles": True,
            "include_skill_names": True,
            "include_experience_details": True,
            "include_education_details": True,
            "language": "en",
            "is_active": True,
        }

        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json=create_request
        )

        # Update only one field
        update_response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"tone": "friendly"}
        )

        assert update_response.status_code == 200

        updated = update_response.json()

        # Verify only tone changed
        assert updated["tone"] == "friendly"
        assert updated["style"] == "balanced"
        assert updated["detail_level"] == "medium"
        assert updated["language"] == "en"

    def test_concurrent_preference_updates(self, test_organization):
        """Test that concurrent preference updates are handled properly."""
        import concurrent.futures

        def update_preference(field_name: str, value: Any):
            return requests.put(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
                json={field_name: value}
            )

        # Send concurrent updates
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(update_preference, "tone", "casual"),
                executor.submit(update_preference, "style", "detailed"),
                executor.submit(update_preference, "detail_level", "high"),
                executor.submit(update_preference, "language", "fr"),
            ]

            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should complete without error
        for result in results:
            assert result.status_code == 200

    def test_organization_with_special_characters(self):
        """Test organization IDs with special characters."""
        special_org_ids = [
            "test-org-with-dashes",
            "test_org_with_underscores",
            "test.org.with.dots",
            "TestOrgMixedCase",
        ]

        for org_id in special_org_ids:
            response = requests.get(
                f"{self.BASE_URL}/api/explainability/preferences/{org_id}"
            )

            # Should return defaults for any org_id
            assert response.status_code == 200
            assert response.json()["organization_id"] == org_id


class TestExplanationPreferencesValidation:
    """Tests for validation and error handling."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_organization(self):
        """Create a test organization for validation tests."""
        org_id = f"validation-test-org-{uuid4().hex[:8]}"
        yield org_id

    def test_empty_update_request(self, test_organization):
        """Test sending an empty update request."""
        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={}
        )

        # Should succeed with no changes (or create with defaults)
        assert response.status_code in [200, 422]

    def test_null_values_handling(self, test_organization):
        """Test handling of null/None values."""
        # Create preferences first
        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={
                "tone": "professional",
                "style": "balanced",
                "language": "en",
            }
        )

        # Try setting language to null
        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"language": None}
        )

        assert response.status_code == 200

    def test_long_custom_prompt_template(self, test_organization):
        """Test handling of long custom prompt templates."""
        long_template = "Generate a detailed explanation. " * 100  # ~3000 chars

        response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"custom_prompt_template": long_template}
        )

        assert response.status_code == 200

        preferences = response.json()
        assert len(preferences["custom_prompt_template"]) == len(long_template)

    def test_unicode_language_codes(self, test_organization):
        """Test various language code formats."""
        language_codes = [
            "en",
            "es",
            "fr",
            "de",
            "zh",
            "ja",
            "en-US",
            "en-GB",
            "es-MX",
        ]

        for lang_code in language_codes:
            response = requests.put(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
                json={"language": lang_code}
            )

            assert response.status_code == 200
            assert response.json()["language"] == lang_code


class TestExplanationPreferencesIntegration:
    """Integration tests with other explainability features."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy."""
        vacancy_data = {
            "position": "Software Engineer",
            "industry": "Technology",
            "mandatory_requirements": ["Python", "FastAPI", "PostgreSQL"],
            "additional_requirements": ["Docker", "Kubernetes"],
            "experience_levels": ["middle", "senior"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        assert response.status_code == 201

        vacancy = response.json()
        yield vacancy

        # Cleanup
        requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")

    @pytest.fixture(scope="class")
    def test_resume(self):
        """Create a test resume."""
        resume_data = {
            "filename": "test_engineer.pdf",
            "raw_text": """
            Jane Engineer
            Senior Software Engineer with 5 years of experience.

            Skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, Redis, Celery.
            Experience: Built microservices architecture, led team of 3 developers.
            Education: Master's in Computer Science
            """,
        }

        response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
        if response.status_code == 201:
            resume = response.json()
            yield resume
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume['id']}")
        else:
            yield None

    @pytest.fixture(scope="class")
    def test_organization(self):
        """Create a test organization with custom preferences."""
        org_id = f"integration-test-org-{uuid4().hex[:8]}"

        # Set up custom preferences
        requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{org_id}",
            json={
                "tone": "casual",
                "style": "detailed",
                "detail_level": "high",
                "include_percentiles": True,
                "include_skill_names": True,
                "language": "en",
                "is_active": True,
            }
        )

        yield org_id

        # Cleanup
        try:
            requests.delete(f"{self.BASE_URL}/api/explainability/preferences/{org_id}")
        except Exception:
            pass

    def test_preferences_retrieval_consistency(self, test_organization):
        """Test that preferences are consistently retrieved across multiple calls."""
        responses = []
        for _ in range(5):
            response = requests.get(
                f"{self.BASE_URL}/api/explainability/preferences/{test_organization}"
            )
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical
        first_response = responses[0]
        for resp in responses[1:]:
            assert resp == first_response

    def test_preference_update_timestamp_changes(self, test_organization):
        """Test that updated_at timestamp changes when preferences are updated."""
        # Create preferences
        create_response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"tone": "professional"}
        )
        assert create_response.status_code == 200

        initial_updated_at = create_response.json()["updated_at"]

        # Wait a moment and update
        import time
        time.sleep(0.1)

        update_response = requests.put(
            f"{self.BASE_URL}/api/explainability/preferences/{test_organization}",
            json={"tone": "casual"}
        )
        assert update_response.status_code == 200

        new_updated_at = update_response.json()["updated_at"]

        # Timestamp should have changed
        assert new_updated_at != initial_updated_at
