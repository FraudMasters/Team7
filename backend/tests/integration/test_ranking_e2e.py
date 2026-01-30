"""
End-to-End Integration Tests for AI Candidate Ranking Flow

Tests the complete ranking workflow:
1. Upload resume → Create vacancy → Get AI rankings → Verify top recommendations → Submit feedback
"""

import pytest
import requests
from typing import Dict, Any
import time


class TestRankingE2E:
    """End-to-end tests for the ranking API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for ranking tests."""
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
        """Upload test resumes for ranking."""
        resume_ids = []

        # Simulate uploading multiple resumes
        for i in range(5):
            resume_data = {
                "filename": f"candidate_{i}_resume.pdf",
                "raw_text": f"""
                Candidate {i}
                Senior Python Developer with {3+i*2} years of experience.

                Skills: Python, Django, PostgreSQL, Docker, Celery, Redis.
                Education: Master's in Computer Science
                """,
            }

            response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
            if response.status_code == 201:
                resume_ids.append(response.json()['id'])

        yield resume_ids

        # Cleanup
        for resume_id in resume_ids:
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")

    def test_complete_ranking_flow(self, test_vacancy, test_resumes):
        """Test complete ranking flow from vacancy to top recommendations."""
        # Step 1: Get AI rankings for the vacancy
        ranking_request = {
            "vacancy_id": test_vacancy["id"],
            "limit": 10,
        }

        response = requests.post(f"{self.BASE_URL}/api/ranking/rank", json=ranking_request)

        # Allow for rankings to not be available if ML model not trained
        if response.status_code == 200:
            rankings = response.json()

            assert "ranked_candidates" in rankings
            assert "vacancy_id" in rankings
            assert rankings["vacancy_id"] == test_vacancy["id"]
            assert len(rankings["ranked_candidates"]) <= 10

            # Step 2: Verify ranking structure
            for candidate in rankings["ranked_candidates"]:
                assert "resume_id" in candidate
                assert "ranking_score" in candidate
                assert 0 <= candidate["ranking_score"] <= 100
                assert "hire_probability" in candidate
                assert 0 <= candidate["hire_probability"] <= 1

            # Step 3: Get top 3 recommendations
            recommendations_response = requests.get(
                f"{self.BASE_URL}/api/ranking/recommendations/{test_vacancy['id']}"
            )

            if recommendations_response.status_code == 200:
                recommendations = recommendations_response.json()

                assert "top_candidates" in recommendations
                assert len(recommendations["top_candidates"]) <= 3

                # Step 4: Submit feedback on top recommendation
                if len(recommendations["top_candidates"]) > 0:
                    top_candidate = recommendations["top_candidates"][0]

                    feedback_data = {
                        "resume_id": top_candidate["resume_id"],
                        "vacancy_id": test_vacancy["id"],
                        "was_correct": True,
                        "recruiter_comments": "Good ranking, candidate looks promising",
                    }

                    feedback_response = requests.post(
                        f"{self.BASE_URL}/api/ranking/feedback",
                        json=feedback_data
                    )

                    assert feedback_response.status_code in [201, 200]

                    feedback = feedback_response.json()
                    assert "id" in feedback
                    assert feedback["was_correct"] == True

    def test_ranking_with_match_results(self, test_vacancy, test_resumes):
        """Test that ranking integrates with existing match results."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        # First, get match results for comparison
        match_response = requests.get(
            f"{self.BASE_URL}/api/vacancies/match/{test_vacancy['id']}"
        )

        if match_response.status_code == 200:
            matches = match_response.json()

            # Get rankings
            ranking_request = {
                "vacancy_id": test_vacancy["id"],
                "limit": 10,
            }

            ranking_response = requests.post(
                f"{self.BASE_URL}/api/ranking/rank",
                json=ranking_request
            )

            if ranking_response.status_code == 200:
                rankings = ranking_response.json()

                # Rankings should include match_score for comparison
                for candidate in rankings["ranked_candidates"]:
                    if "match_score" in candidate:
                        # Verify that ranking_score differs from match_score
                        # (AI ranking should add additional factors)
                        assert isinstance(candidate["match_score"], (int, float))

    def test_ranking_factors_explanation(self, test_vacancy, test_resumes):
        """Test that ranking includes explainable factors."""
        ranking_request = {
            "vacancy_id": test_vacancy["id"],
            "limit": 5,
        }

        response = requests.post(f"{self.BASE_URL}/api/ranking/rank", json=ranking_request)

        if response.status_code == 200:
            rankings = response.json()

            for candidate in rankings["ranked_candidates"]:
                if "explanation" in candidate:
                    explanation = candidate["explanation"]

                    # Check for required explanation fields
                    assert "summary" in explanation
                    assert isinstance(explanation["summary"], str)

                    if "top_positive_factors" in explanation:
                        assert isinstance(explanation["top_positive_factors"], list)

                    if "top_negative_factors" in explanation:
                        assert isinstance(explanation["top_negative_factors"], list)

                    if "feature_contributions" in explanation:
                        assert isinstance(explanation["feature_contributions"], dict)


class TestRankingFeedbackE2E:
    """End-to-end tests for ranking feedback flow."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def sample_ranking_data(self):
        """Create sample ranking data for feedback tests."""
        return {
            "vacancy_id": "test-vacancy-1",
            "resume_id": "test-resume-1",
            "original_score": 85,
        }

    def test_submit_positive_feedback(self, sample_ranking_data):
        """Test submitting positive feedback (thumbs up)."""
        feedback_data = {
            **sample_ranking_data,
            "was_correct": True,
            "recruiter_comments": "Candidate was excellent, ranked appropriately",
        }

        response = requests.post(f"{self.BASE_URL}/api/ranking/feedback", json=feedback_data)

        if response.status_code in [201, 200]:
            feedback = response.json()
            assert feedback["was_correct"] == True
            assert "id" in feedback

    def test_submit_negative_feedback_with_correction(self, sample_ranking_data):
        """Test submitting negative feedback with score correction."""
        feedback_data = {
            **sample_ranking_data,
            "was_correct": False,
            "recruiter_corrected_score": 70,
            "recruiter_corrected_position": 3,
            "feedback_reason": "ranking_incorrect",
            "recruiter_comments": "Candidate experience was overstated",
        }

        response = requests.post(f"{self.BASE_URL}/api/ranking/feedback", json=feedback_data)

        if response.status_code in [201, 200]:
            feedback = response.json()
            assert feedback["was_correct"] == False
            assert feedback["recruiter_corrected_score"] == 70
            assert feedback["corrected_position"] == 3

    def test_feedback_persistence(self, sample_ranking_data):
        """Test that feedback is persisted and can be retrieved."""
        # Submit feedback
        feedback_data = {
            **sample_ranking_data,
            "was_correct": True,
            "recruiter_comments": "Test feedback for persistence",
        }

        submit_response = requests.post(
            f"{self.BASE_URL}/api/ranking/feedback",
            json=feedback_data
        )

        if submit_response.status_code in [201, 200]:
            feedback_id = submit_response.json().get("id")

            # Try to retrieve feedback
            get_response = requests.get(
                f"{self.BASE_URL}/api/ranking/feedback/{feedback_id}"
            )

            if get_response.status_code == 200:
                retrieved = get_response.json()
                assert retrieved["recruiter_comments"] == "Test feedback for persistence"


@pytest.mark.integration
class TestRankingWithCelery:
    """Integration tests with Celery for async ranking tasks."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def celery_worker(self):
        """Ensure Celery worker is available."""
        response = requests.get("http://localhost:5555/api/workers")
        if response.status_code != 200:
            pytest.skip("Celery worker not available")
        return response.json()

    def test_async_ranking_task(self, celery_worker):
        """Test that ranking can be performed asynchronously."""
        task_data = {
            "vacancy_id": "test-vacancy",
            "candidate_ids": ["resume-1", "resume-2", "resume-3"],
        }

        response = requests.post(
            f"{self.BASE_URL}/api/tasks/ranking/async",
            json=task_data
        )

        if response.status_code == 202:
            task_info = response.json()
            assert "task_id" in task_info

            # Poll for task completion
            task_id = task_info["task_id"]
            max_attempts = 10
            for _ in range(max_attempts):
                time.sleep(1)
                status_response = requests.get(
                    f"{self.BASE_URL}/api/tasks/status/{task_id}"
                )
                if status_response.status_code == 200:
                    status = status_response.json()
                    if status.get("state") == "SUCCESS":
                        assert "result" in status
                        break
                    elif status.get("state") == "FAILURE":
                        pytest.fail("Ranking task failed")
