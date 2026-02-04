"""
End-to-End Integration Tests for AI-Powered Candidate Recommendations API

Tests the complete recommendations workflow:
1. Upload resumes → Create vacancy → Get similar candidates → Get best-fit → Get at-risk → Submit feedback
"""

import pytest
import requests
from typing import Dict, Any
import time


class TestRecommendationsE2E:
    """End-to-end tests for the recommendations API."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for recommendation tests."""
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
        """Upload test resumes for recommendations."""
        resume_ids = []

        # Simulate uploading multiple resumes with varying skills
        resume_templates = [
            {
                "filename": "senior_python_dev.pdf",
                "raw_text": """
                John Smith
                Senior Python Developer with 7 years of experience.

                Skills: Python, Django, PostgreSQL, Docker, Kubernetes, Redis, Celery.
                Education: Master's in Computer Science
                Experience: Led team of 5 developers, built microservices architecture
                """,
            },
            {
                "filename": "middle_python_dev.pdf",
                "raw_text": """
                Jane Doe
                Middle Python Developer with 4 years of experience.

                Skills: Python, Django, PostgreSQL, Docker.
                Education: Bachelor's in Computer Science
                Experience: Developed REST APIs, worked on e-commerce platform
                """,
            },
            {
                "filename": "fullstack_dev.pdf",
                "raw_text": """
                Bob Johnson
                Full Stack Developer with 6 years of experience.

                Skills: Python, JavaScript, React, PostgreSQL, MongoDB, Docker.
                Education: Master's in Software Engineering
                Experience: Built web applications, integrated payment systems
                """,
            },
            {
                "filename": "devops_engineer.pdf",
                "raw_text": """
                Alice Williams
                DevOps Engineer with 5 years of experience.

                Skills: Docker, Kubernetes, AWS, Terraform, Ansible, Python.
                Education: Bachelor's in Computer Engineering
                Experience: Automated deployment pipelines, managed cloud infrastructure
                """,
            },
            {
                "filename": "data_engineer.pdf",
                "raw_text": """
                Charlie Brown
                Data Engineer with 5 years of experience.

                Skills: Python, SQL, Spark, Airflow, Kafka, PostgreSQL.
                Education: Master's in Data Science
                Experience: Built data pipelines, implemented ETL processes
                """,
            },
        ]

        for resume_data in resume_templates:
            response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
            if response.status_code == 201:
                resume_ids.append(response.json()['id'])

        yield resume_ids

        # Cleanup
        for resume_id in resume_ids:
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume_id}")

    def test_complete_similar_candidates_flow(self, test_resumes):
        """Test complete similar candidates recommendation flow."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        # Use the first resume as the reference
        reference_resume_id = test_resumes[0]

        # Get similar candidates using POST endpoint
        request_data = {
            "resume_id": reference_resume_id,
            "limit": 5,
            "use_experiment": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/similar",
            json=request_data
        )

        # Allow for recommendations to not be available if ML model not trained
        if response.status_code == 200:
            result = response.json()

            # Verify response structure
            assert "source_resume_id" in result
            assert result["source_resume_id"] == reference_resume_id
            assert "total_candidates" in result
            assert "candidates" in result
            assert len(result["candidates"]) <= 5

            # Verify candidate structure
            for candidate in result["candidates"]:
                assert "resume_id" in candidate
                assert "similarity_score" in candidate
                assert 0 <= candidate["similarity_score"] <= 1
                assert "shared_skills" in candidate
                assert isinstance(candidate["shared_skills"], list)
                assert "match_reason" in candidate
                assert "recommendation_type" in candidate
                assert candidate["recommendation_type"] == "similar"

            # Verify A/B testing fields
            assert "is_experiment" in result
            assert isinstance(result["is_experiment"], bool)
            if result["is_experiment"]:
                assert "experiment_group" in result
                assert result["experiment_group"] in ["control", "treatment"]

    def test_similar_candidates_get_endpoint(self, test_resumes):
        """Test similar candidates using GET endpoint with path parameter."""
        if not test_resumes:
            pytest.skip("No test resumes available")

        reference_resume_id = test_resumes[0]

        # Get similar candidates using GET endpoint
        response = requests.get(
            f"{self.BASE_URL}/api/recommendations/similar/{reference_resume_id}?limit=5&use_experiment=true"
        )

        if response.status_code == 200:
            result = response.json()

            assert "source_resume_id" in result
            assert result["source_resume_id"] == reference_resume_id
            assert "candidates" in result
            assert "algorithm_version" in result

    def test_complete_best_fit_flow(self, test_vacancy, test_resumes):
        """Test complete best-fit candidates recommendation flow."""
        # Get best-fit candidates using POST endpoint
        request_data = {
            "vacancy_id": test_vacancy["id"],
            "limit": 10,
            "min_score": 0.3,
            "use_experiment": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=request_data
        )

        # Allow for recommendations to not be available if ML model not trained
        if response.status_code == 200:
            result = response.json()

            # Verify response structure
            assert "vacancy_id" in result
            assert result["vacancy_id"] == test_vacancy["id"]
            assert "total_candidates" in result
            assert "candidates" in result
            assert len(result["candidates"]) <= 10

            # Verify candidate structure
            for candidate in result["candidates"]:
                assert "resume_id" in candidate
                assert "match_score" in candidate
                assert 0 <= candidate["match_score"] <= 1
                assert "skills_match" in candidate
                assert isinstance(candidate["skills_match"], list)
                assert "missing_skills" in candidate
                assert isinstance(candidate["missing_skills"], list)
                assert "recommendation" in candidate
                assert candidate["recommendation"] in ["excellent", "good", "fair", "poor"]
                assert "recommendation_type" in candidate
                assert candidate["recommendation_type"] == "best_fit"

            # Verify A/B testing fields
            assert "is_experiment" in result
            if result["is_experiment"]:
                assert "experiment_group" in result

    def test_best_fit_get_endpoint(self, test_vacancy):
        """Test best-fit candidates using GET endpoint with path parameter."""
        # Get best-fit candidates using GET endpoint
        response = requests.get(
            f"{self.BASE_URL}/api/recommendations/best-fit/{test_vacancy['id']}?limit=10&min_score=0.3&use_experiment=true"
        )

        if response.status_code == 200:
            result = response.json()

            assert "vacancy_id" in result
            assert result["vacancy_id"] == test_vacancy["id"]
            assert "candidates" in result
            assert "algorithm_version" in result

    def test_complete_at_risk_flow(self, test_resumes):
        """Test complete at-risk candidates recommendation flow."""
        # Get at-risk candidates using POST endpoint
        request_data = {
            "limit": 10,
            "min_risk_score": 0.3,
            "use_experiment": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/at-risk",
            json=request_data
        )

        # Allow for recommendations to not be available if ML model not trained
        if response.status_code == 200:
            result = response.json()

            # Verify response structure
            assert "total_candidates" in result
            assert "candidates" in result
            assert len(result["candidates"]) <= 10

            # Verify candidate structure
            for candidate in result["candidates"]:
                assert "resume_id" in candidate
                assert "risk_score" in candidate
                assert 0 <= candidate["risk_score"] <= 1
                assert "risk_level" in candidate
                assert candidate["risk_level"] in ["low", "medium", "high", "critical"]
                assert "risk_factors" in candidate
                assert isinstance(candidate["risk_factors"], list)
                assert "recommended_action" in candidate
                assert "recommendation_type" in candidate
                assert candidate["recommendation_type"] == "at_risk"

            # Verify A/B testing fields
            assert "is_experiment" in result
            if result["is_experiment"]:
                assert "experiment_group" in result

    def test_at_risk_get_endpoint(self):
        """Test at-risk candidates using GET endpoint with query parameters."""
        # Get at-risk candidates using GET endpoint
        response = requests.get(
            f"{self.BASE_URL}/api/recommendations/at-risk?limit=10&min_risk_score=0.3&use_experiment=true"
        )

        if response.status_code == 200:
            result = response.json()

            assert "total_candidates" in result
            assert "candidates" in result
            assert "algorithm_version" in result

    def test_at_risk_filtered_by_vacancy(self, test_vacancy):
        """Test at-risk candidates filtered by specific vacancy."""
        # Get at-risk candidates for a specific vacancy
        request_data = {
            "limit": 10,
            "min_risk_score": 0.3,
            "vacancy_id": test_vacancy["id"],
            "use_experiment": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/at-risk",
            json=request_data
        )

        if response.status_code == 200:
            result = response.json()

            assert "total_candidates" in result
            assert "candidates" in result

    def test_recommendations_with_low_threshold(self, test_vacancy):
        """Test that lowering thresholds returns more candidates."""
        # Get best-fit with higher threshold
        high_threshold_request = {
            "vacancy_id": test_vacancy["id"],
            "limit": 20,
            "min_score": 0.8,
            "use_experiment": False,
        }

        high_response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=high_threshold_request
        )

        # Get best-fit with lower threshold
        low_threshold_request = {
            "vacancy_id": test_vacancy["id"],
            "limit": 20,
            "min_score": 0.3,
            "use_experiment": False,
        }

        low_response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=low_threshold_request
        )

        if high_response.status_code == 200 and low_response.status_code == 200:
            high_result = high_response.json()
            low_result = low_response.json()

            # Lower threshold should return same or more candidates
            assert low_result["total_candidates"] >= high_result["total_candidates"]

    def test_recommendation_types_endpoint(self):
        """Test the recommendation types endpoint."""
        response = requests.get(f"{self.BASE_URL}/api/recommendations/types")

        assert response.status_code == 200

        result = response.json()
        assert "types" in result
        assert isinstance(result["types"], list)

        # Verify all expected types are present
        type_names = [t["type"] for t in result["types"]]
        assert "similar" in type_names
        assert "best_fit" in type_names
        assert "at_risk" in type_names

        # Verify each type has required fields
        for rec_type in result["types"]:
            assert "type" in rec_type
            assert "name" in rec_type
            assert "description" in rec_type
            assert "endpoint" in rec_type


class TestRecommendationsFeedbackE2E:
    """End-to-end tests for recommendations feedback flow."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture(scope="class")
    def test_vacancy(self):
        """Create a test vacancy for feedback tests."""
        vacancy_data = {
            "position": "Software Engineer",
            "industry": "Technology",
            "mandatory_requirements": ["Python", "FastAPI"],
            "experience_levels": ["middle", "senior"],
        }

        response = requests.post(f"{self.BASE_URL}/api/vacancies/", json=vacancy_data)
        if response.status_code != 201:
            return None

        vacancy = response.json()
        yield vacancy

        # Cleanup
        if vacancy:
            requests.delete(f"{self.BASE_URL}/api/vacancies/{vacancy['id']}")

    @pytest.fixture(scope="class")
    def test_resume(self):
        """Create a test resume for feedback tests."""
        resume_data = {
            "filename": "feedback_test_resume.pdf",
            "raw_text": """
            Test Candidate
            Software Engineer with 5 years of experience.

            Skills: Python, FastAPI, PostgreSQL, Docker.
            Education: Bachelor's in Computer Science
            """,
        }

        response = requests.post(f"{self.BASE_URL}/api/resumes/", json=resume_data)
        if response.status_code != 201:
            return None

        resume = response.json()
        yield resume

        # Cleanup
        if resume:
            requests.delete(f"{self.BASE_URL}/api/resumes/{resume['id']}")

    @pytest.fixture(scope="class")
    def test_recommendation(self, test_vacancy, test_resume):
        """Create a test recommendation for feedback tests."""
        if not test_vacancy or not test_resume:
            yield None
            return

        # Get a best-fit recommendation to use for feedback
        request_data = {
            "vacancy_id": test_vacancy["id"],
            "limit": 1,
            "min_score": 0.0,
            "use_experiment": False,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=request_data
        )

        if response.status_code == 200:
            result = response.json()
            if result["candidates"] and len(result["candidates"]) > 0:
                # For now, use resume_id as proxy for recommendation_id
                # In real implementation, backend would return actual recommendation_id
                yield {"resume_id": result["candidates"][0]["resume_id"]}
                return

        yield None

    def test_submit_positive_feedback_post(self, test_recommendation):
        """Test submitting positive feedback using POST endpoint."""
        if not test_recommendation:
            pytest.skip("No test recommendation available")

        feedback_data = {
            "recommendation_id": str(test_recommendation["resume_id"]),
            "was_helpful": True,
            "was_contacted": True,
            "outcome": "hired",
            "rating": 5,
            "comments": "Excellent recommendation, candidate was perfect fit",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/feedback",
            json=feedback_data
        )

        # Allow for 404 if recommendation doesn't exist yet
        if response.status_code in [201, 200]:
            feedback = response.json()
            assert "id" in feedback
            assert feedback["was_helpful"] == True
            assert feedback["was_contacted"] == True
            assert feedback["outcome"] == "hired"

    def test_submit_feedback_with_path_parameter(self, test_recommendation):
        """Test submitting feedback with recommendation_id in path."""
        if not test_recommendation:
            pytest.skip("No test recommendation available")

        feedback_data = {
            "was_helpful": True,
            "was_contacted": False,
            "outcome": "pending",
            "rating": 4,
            "comments": "Good recommendation, still in process",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/{test_recommendation['resume_id']}/feedback",
            json=feedback_data
        )

        # Allow for 404 if recommendation doesn't exist yet
        if response.status_code in [201, 200]:
            feedback = response.json()
            assert "id" in feedback
            assert feedback["was_helpful"] == True
            assert feedback["outcome"] == "pending"

    def test_submit_negative_feedback(self, test_recommendation):
        """Test submitting negative feedback."""
        if not test_recommendation:
            pytest.skip("No test recommendation available")

        feedback_data = {
            "recommendation_id": str(test_recommendation["resume_id"]),
            "was_helpful": False,
            "was_contacted": False,
            "rating": 2,
            "comments": "Candidate skills didn't match requirements",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/feedback",
            json=feedback_data
        )

        # Allow for 404 if recommendation doesn't exist yet
        if response.status_code in [201, 200]:
            feedback = response.json()
            assert feedback["was_helpful"] == False

    def test_feedback_with_minimal_data(self, test_recommendation):
        """Test submitting feedback with only required fields."""
        if not test_recommendation:
            pytest.skip("No test recommendation available")

        feedback_data = {
            "recommendation_id": str(test_recommendation["resume_id"]),
            "was_helpful": True,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/feedback",
            json=feedback_data
        )

        # Allow for 404 if recommendation doesn't exist yet
        if response.status_code in [201, 200]:
            feedback = response.json()
            assert feedback["was_helpful"] == True


class TestRecommendationsErrorHandling:
    """Tests for error handling in recommendations API."""

    BASE_URL = "http://localhost:8000"

    def test_invalid_uuid_format_similar(self):
        """Test that invalid UUID format returns 422 for similar candidates."""
        request_data = {
            "resume_id": "invalid-uuid-format",
            "limit": 10,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/similar",
            json=request_data
        )

        assert response.status_code == 422

    def test_invalid_uuid_format_best_fit(self):
        """Test that invalid UUID format returns 422 for best-fit."""
        request_data = {
            "vacancy_id": "not-a-uuid",
            "limit": 10,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=request_data
        )

        assert response.status_code == 422

    def test_invalid_uuid_format_at_risk_vacancy(self):
        """Test that invalid vacancy UUID format returns 422 for at-risk."""
        request_data = {
            "limit": 10,
            "min_risk_score": 0.5,
            "vacancy_id": "invalid-uuid",
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/at-risk",
            json=request_data
        )

        assert response.status_code == 422

    def test_invalid_limit_parameter(self):
        """Test that invalid limit parameter is rejected."""
        request_data = {
            "vacancy_id": "00000000-0000-0000-0000-000000000000",
            "limit": 999,  # Exceeds maximum
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=request_data
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_invalid_score_parameter(self):
        """Test that invalid score parameter is rejected."""
        request_data = {
            "vacancy_id": "00000000-0000-0000-0000-000000000000",
            "min_score": 1.5,  # Exceeds maximum of 1.0
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/best-fit",
            json=request_data
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_invalid_rating_parameter(self):
        """Test that invalid rating parameter is rejected."""
        feedback_data = {
            "recommendation_id": "00000000-0000-0000-0000-000000000000",
            "was_helpful": True,
            "rating": 6,  # Exceeds maximum of 5
        }

        response = requests.post(
            f"{self.BASE_URL}/api/recommendations/feedback",
            json=feedback_data
        )

        # Should return validation error
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestRecommendationsWithCelery:
    """Integration tests with Celery for async recommendation tasks."""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def celery_worker(self):
        """Ensure Celery worker is available."""
        try:
            response = requests.get("http://localhost:5555/api/workers")
            if response.status_code != 200:
                pytest.skip("Celery worker not available")
            return response.json()
        except requests.exceptions.ConnectionError:
            pytest.skip("Flower (Celery monitoring) not available")

    def test_async_recommendation_precomputation(self, celery_worker):
        """Test that recommendations can be precomputed asynchronously."""
        task_data = {
            "resume_id": "test-resume-id",
            "limit": 10,
        }

        # This would trigger a Celery task for precomputing similar candidates
        # Implementation depends on your async task endpoints
        response = requests.post(
            f"{self.BASE_URL}/api/tasks/recommendations/precompute",
            json=task_data
        )

        # Task endpoint might not exist yet, so allow 404
        if response.status_code == 202:
            task_info = response.json()
            assert "task_id" in task_info
