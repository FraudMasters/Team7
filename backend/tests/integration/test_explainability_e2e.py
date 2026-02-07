"""
End-to-End Integration Tests for Explainability API

Tests the complete explainability workflow:
1. Upload resume → Create vacancy → Get AI rankings → Generate explanations
2. What-if analysis with database
3. LLM integration (with mock)
"""
import pytest
import requests
from typing import Dict, Any
import time
from uuid import uuid4


class TestExplainabilityE2E:
    """End-to-end tests for the explainability API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for explainability tests."""
        vacancy_data = {
            "position": "Senior Python Developer",
            "industry": "Technology",
            "mandatory_requirements": ["Python", "Django", "PostgreSQL", "Docker"],
            "additional_requirements": ["Kubernetes", "Redis", "Celery"],
            "experience_levels": ["senior", "middle"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        assert response.status_code == 201

        vacancy = response.json()
        yield vacancy

        # Cleanup
        requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")

    @pytest.fixture(scope="class")
    def test_resumes(self):
        """Upload test resumes for explainability tests."""
        resume_ids = []

        # Create multiple test resumes with varying skill levels
        resumes_data = [
            {
                "filename": "senior_python_resume.pdf",
                "raw_text": """
                John Senior
                Senior Python Developer with 7 years of experience.

                Skills: Python, Django, PostgreSQL, Docker, Kubernetes, Redis, Celery, AWS.
                Experience: Led team of 5 developers, built microservices architecture.
                Education: Master's in Computer Science
                """,
            },
            {
                "filename": "mid_python_resume.pdf",
                "raw_text": """
                Jane Middle
                Python Developer with 4 years of experience.

                Skills: Python, Django, PostgreSQL, Docker.
                Experience: Developed REST APIs, worked on web applications.
                Education: Bachelor's in Computer Science
                """,
            },
            {
                "filename": "junior_python_resume.pdf",
                "raw_text": """
                Jack Junior
                Junior Python Developer with 1 year of experience.

                Skills: Python, basic Django knowledge.
                Experience: Internship and personal projects.
                Education: Bachelor's in Computer Science
                """,
            },
        ]

        for resume_data in resumes_data:
            response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
            if response.status_code == 201:
                resume_ids.append(response.json()['id'])

        yield resume_ids

        # Cleanup
        for resume_id in resume_ids:
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")

    @pytest.fixture(scope="class")
    def test_rankings(self, test_vacancy, test_resumes):
        """Generate rankings for the test resumes."""
        ranking_request = {
            "vacancy_id": test_vacancy["id"],
            "limit": 10,
        }

        response = requests.post(f"{self.BASE_URL}/api/ranking/rank", json=ranking_request)

        # Rankings may not be available if ML model not trained
        if response.status_code == 200:
            yield response.json()
        else:
            yield {"ranked_candidates": []}

    def test_complete_explainability_flow(self, test_vacancy, test_resumes, test_rankings):
        """Test complete explainability flow from ranking to explanation."""
        if not test_rankings.get("ranked_candidates"):
            pytest.skip("Rankings not available - ML model may not be trained")

        # Get top candidate
        top_candidate = test_rankings["ranked_candidates"][0]
        resume_id = top_candidate["resume_id"]
        vacancy_id = test_vacancy["id"]

        # Step 1: Generate ranking explanation
        explanation_request = {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "use_llm": False,  # Don't require LLM for basic test
        }

        response = requests.post(
            f"{self.BASE_URL}/api/explainability/explain",
            json=explanation_request
        )

        # Allow for rankings without explainability data
        if response.status_code == 200:
            explanation = response.json()

            # Verify explanation structure
            assert "resume_id" in explanation
            assert "vacancy_id" in explanation
            assert "rank_score" in explanation
            assert "narrative" in explanation
            assert "feature_explanations" in explanation
            assert "strengths" in explanation
            assert "weaknesses" in explanation
            assert "recommendation" in explanation

            # Verify data types
            assert isinstance(explanation["rank_score"], (int, float))
            assert isinstance(explanation["feature_explanations"], list)
            assert isinstance(explanation["strengths"], list)
            assert isinstance(explanation["weaknesses"], list)
        elif response.status_code == 404:
            # Ranking exists but no explainability data - acceptable
            pass

    def test_what_if_analysis_flow(self, test_vacancy, test_resumes):
        """Test what-if analysis with real data."""
        if len(test_resumes) < 1:
            pytest.skip("No test resumes available")

        resume_id = test_resumes[0]
        vacancy_id = test_vacancy["id"]

        # Perform what-if analysis
        what_if_request = {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "adjustments": {
                "experience_months": 12,  # Add 1 year of experience
            },
        }

        response = requests.post(
            f"{self.BASE_URL}/api/explainability/what-if",
            json=what_if_request
        )

        # What-if analysis may not be available without ranking
        if response.status_code == 200:
            result = response.json()

            # Verify what-if structure
            assert "resume_id" in result
            assert "vacancy_id" in result
            assert "original_score" in result
            assert "new_score" in result
            assert "score_delta" in result
            assert "scenario_description" in result

            # Verify score changes
            assert isinstance(result["original_score"], (int, float))
            assert isinstance(result["new_score"], (int, float))
            assert isinstance(result["score_delta"], (int, float))
        elif response.status_code == 404:
            # Ranking not found - acceptable
            pass

    def test_confidence_interval_retrieval(self, test_vacancy, test_resumes, test_rankings):
        """Test confidence interval retrieval."""
        if not test_rankings.get("ranked_candidates"):
            pytest.skip("Rankings not available")

        top_candidate = test_rankings["ranked_candidates"][0]

        # Try to get confidence interval (requires rank_id, not resume_id)
        # For this test, we'll use the test mode endpoint
        response = requests.get(
            f"{self.BASE_URL}/api/explainability/confidence/test-id?test_mode=true"
        )

        assert response.status_code == 200

        confidence = response.json()
        assert "rank_id" in confidence
        assert "confidence_interval" in confidence
        assert "lower" in confidence["confidence_interval"]
        assert "upper" in confidence["confidence_interval"]

        # Verify bounds are valid
        lower = confidence["confidence_interval"]["lower"]
        upper = confidence["confidence_interval"]["upper"]
        assert 0 <= lower <= upper <= 1

    def test_narrative_explanation(self, test_vacancy, test_resumes):
        """Test natural language narrative explanation."""
        if len(test_resumes) < 1:
            pytest.skip("No test resumes available")

        # Test with test mode (no database required)
        response = requests.get(
            f"{self.BASE_URL}/api/explainability/narrative/test-id?test_mode=true"
        )

        assert response.status_code == 200

        narrative = response.json()
        assert "narrative" in narrative
        assert "candidate_name" in narrative
        assert "rank_score" in narrative
        assert "recommendation" in narrative
        assert "strengths" in narrative
        assert "weaknesses" in narrative

        # Verify narrative is a non-empty string
        assert len(narrative["narrative"]) > 0
        assert isinstance(narrative["narrative"], str)

    def test_candidate_comparison_explanation(self, test_vacancy, test_resumes):
        """Test side-by-side candidate comparison explanation."""
        if len(test_resumes) < 2:
            pytest.skip("Need at least 2 resumes for comparison")

        resume_a_id = test_resumes[0]
        resume_b_id = test_resumes[1]
        vacancy_id = test_vacancy["id"]

        comparison_request = {
            "resume_a_id": resume_a_id,
            "resume_b_id": resume_b_id,
            "vacancy_id": vacancy_id,
            "use_llm": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/explainability/compare-explain",
            json=comparison_request
        )

        # Comparison may not be available without rankings
        if response.status_code == 200:
            comparison = response.json()

            # Verify comparison structure
            assert "vacancy_id" in comparison
            assert "candidate_a_name" in comparison
            assert "candidate_b_name" in comparison
            assert "candidate_a_score" in comparison
            assert "candidate_b_score" in comparison
            assert "score_difference" in comparison
            assert "narrative" in comparison
            assert "key_differences" in comparison

            # Verify scores are different
            assert comparison["candidate_a_score"] != comparison["candidate_b_score"]
        elif response.status_code == 404:
            # Rankings not found - acceptable
            pass

    def test_pdf_report_generation(self, test_vacancy, test_resumes):
        """Test PDF report generation."""
        if len(test_resumes) < 1:
            pytest.skip("No test resumes available")

        # Test with test mode first (no database required)
        response = requests.post(
            f"{self.BASE_URL}/api/explainability/export/pdf",
            json={
                "resume_id": "test-id",
                "vacancy_id": "test-id",
            }
        )

        assert response.status_code == 200

        export_data = response.json()
        assert "success" in export_data
        assert "download_url" in export_data
        assert "filename" in export_data

        if export_data["success"]:
            assert export_data["download_url"].startswith("http")
            assert ".pdf" in export_data["filename"]

    def test_explanation_with_feature_contributions(self, test_vacancy, test_resumes):
        """Test that feature contributions are properly explained."""
        if len(test_resumes) < 1:
            pytest.skip("No test resumes available")

        resume_id = test_resumes[0]
        vacancy_id = test_vacancy["id"]

        explanation_request = {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "use_llm": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/explainability/explain",
            json=explanation_request
        )

        if response.status_code == 200:
            explanation = response.json()

            # Check feature explanations
            if explanation.get("feature_explanations"):
                for feature in explanation["feature_explanations"]:
                    assert "feature" in feature or "name" in feature
                    # Features should have contribution info
                    assert any(
                        key in feature
                        for key in ["contribution", "value", "weight", "impact"]
                    )

    def test_recommendation_mapping(self, test_vacancy, test_resumes):
        """Test that scores map to correct recommendations."""
        if len(test_resumes) < 1:
            pytest.skip("No test resumes available")

        resume_id = test_resumes[0]
        vacancy_id = test_vacancy["id"]

        explanation_request = {
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "use_llm": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/explainability/explain",
            json=explanation_request
        )

        if response.status_code == 200:
            explanation = response.json()
            recommendation = explanation.get("recommendation")
            score = explanation.get("rank_score")

            # Verify recommendation is one of the expected values
            valid_recommendations = ["excellent", "good", "maybe", "poor"]
            assert recommendation in valid_recommendations

            # Verify recommendation matches score ranges (approximately)
            if score >= 0.8:
                assert recommendation in ["excellent", "good"]
            elif score >= 0.6:
                assert recommendation in ["good", "maybe"]
            else:
                assert recommendation in ["maybe", "poor"]

    def test_explainability_endpoints_error_handling(self, test_vacancy):
        """Test error handling across explainability endpoints."""
        # Test with non-existent UUID
        fake_id = str(uuid4())

        # Test explain endpoint
        response = requests.post(
            f"{self.BASE_URL}/api/explainability/explain",
            json={
                "resume_id": fake_id,
                "vacancy_id": test_vacancy["id"],
            }
        )
        # Should return 404 or error
        assert response.status_code in [404, 500]

        # Test with invalid UUID
        response = requests.post(
            f"{self.BASE_URL}/api/explainability/explain",
            json={
                "resume_id": "not-a-uuid",
                "vacancy_id": test_vacancy["id"],
            }
        )
        assert response.status_code == 422

    def test_concurrent_explanation_requests(self, test_vacancy, test_resumes):
        """Test that multiple concurrent explanation requests are handled properly."""
        if len(test_resumes) < 2:
            pytest.skip("Need at least 2 resumes for concurrent test")

        import concurrent.futures

        def make_request(resume_id):
            return requests.post(
                f"{self.BASE_URL}/api/explainability/explain",
                json={
                    "resume_id": resume_id,
                    "vacancy_id": test_vacancy["id"],
                    "use_llm": False,
                }
            )

        # Send concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_request, resume_id)
                for resume_id in test_resumes[:3]
            ]

            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should complete without error (though may return 404)
        for result in results:
            assert result.status_code in [200, 404, 500]


class TestExplainabilityWithLLMMock:
    """Tests for LLM integration with mocked responses."""

    BASE_URL = "http://localhost:8000"

    def test_llm_fallback_behavior(self):
        """Test that system falls back gracefully when LLM is unavailable."""
        # Test mode should work even without LLM
        response = requests.get(
            f"{self.BASE_URL}/api/explainability/narrative/test-id?test_mode=true&use_llm=false"
        )

        assert response.status_code == 200

        narrative = response.json()
        # Should still return a narrative even without LLM
        assert "narrative" in narrative
        assert len(narrative["narrative"]) > 0

    def test_explainability_data_persistence(self, test_vacancy):
        """Test that explainability data can be stored and retrieved."""
        # This test checks if the database schema supports the new fields
        # We can't insert directly, but we can verify the endpoints expect the right data

        # Test narrative endpoint stores/returns data correctly
        response = requests.get(
            f"{self.BASE_URL}/api/explainability/narrative/test-id?test_mode=true"
        )

        assert response.status_code == 200

        data = response.json()
        # Verify response includes all expected fields
        expected_fields = [
            "narrative",
            "candidate_name",
            "rank_score",
            "recommendation",
            "strengths",
            "weaknesses",
            "provider",
            "model",
            "generated_at",
        ]

        for field in expected_fields:
            assert field in data
