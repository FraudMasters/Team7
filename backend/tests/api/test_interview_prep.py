"""
Unit tests for interview preparation API endpoints.

Tests cover:
- Generate interview prep endpoint
- Get interview prep by ID endpoint
- Update interview prep endpoint
- Export interview prep as PDF endpoint
- Request validation
- Error handling
"""
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.

    Returns:
        TestClient: Configured test client
    """
    return TestClient(app)


class TestGenerateInterviewPrepEndpoint:
    """Tests for POST /api/interview-prep/generate endpoint."""

    def test_returns_201_on_success(self, client):
        """Test endpoint returns 201 status code on success."""
        with patch('api.interview_prep.find_resume_file') as mock_find_file, \
             patch('api.interview_prep.extract_text_from_file') as mock_extract, \
             patch('api.interview_prep.extract_resume_entities') as mock_extract_entities, \
             patch('api.interview_prep.InterviewQuestionGenerator') as mock_generator_class, \
             patch('api.interview_prep.get_db') as mock_get_db:

            # Setup mocks
            mock_find_file.return_value = Path("data/uploads/test_resume.pdf")
            mock_extract.return_value = "Sample resume text with skills"
            mock_extract_entities.return_value = {
                "technical_skills": ["Python", "FastAPI", "SQL"],
                "skills": ["Python", "FastAPI", "SQL"]
            }

            # Mock generator
            mock_generator = MagicMock()
            mock_prep_result = MagicMock()
            mock_prep_result.technical_questions = [
                MagicMock(to_dict=lambda: {"id": "q1", "text": "Test technical question"})
            ]
            mock_prep_result.behavioral_questions = [
                MagicMock(to_dict=lambda: {"id": "q2", "text": "Test behavioral question"})
            ]
            mock_prep_result.situational_questions = []
            mock_prep_result.skill_verification_questions = []
            mock_prep_result.areas_to_probe = ["Experience with FastAPI"]
            mock_prep_result.skill_gaps_to_address = ["Docker"]
            mock_prep_result.interview_tips = ["Focus on practical examples"]
            mock_prep_result.provider = "openai"
            mock_prep_result.model = "gpt-4"
            mock_prep_result.generated_at = datetime.utcnow().isoformat()
            mock_generator.generate_questions.return_value = mock_prep_result
            mock_generator_class.return_value = mock_generator

            # Mock database session
            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = Mock(
                title="Software Engineer",
                description="Develop web applications",
                required_skills=["Python", "FastAPI", "Docker"],
                min_experience_months=24
            )
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "resume_id": "test_resume_123",
                "vacancy_id": str(uuid4()),
            }
            response = client.post("/api/interview-prep/generate", json=payload)
            assert response.status_code == 201

    def test_response_structure(self, client):
        """Test response has correct structure."""
        with patch('api.interview_prep.find_resume_file') as mock_find_file, \
             patch('api.interview_prep.extract_text_from_file') as mock_extract, \
             patch('api.interview_prep.extract_resume_entities') as mock_extract_entities, \
             patch('api.interview_prep.InterviewQuestionGenerator') as mock_generator_class, \
             patch('api.interview_prep.get_db') as mock_get_db:

            # Setup mocks
            mock_find_file.return_value = Path("data/uploads/test_resume.pdf")
            mock_extract.return_value = "Sample resume text"
            mock_extract_entities.return_value = {"technical_skills": ["Python"]}

            mock_generator = MagicMock()
            mock_prep_result = MagicMock()
            mock_prep_result.technical_questions = []
            mock_prep_result.behavioral_questions = []
            mock_prep_result.situational_questions = []
            mock_prep_result.skill_verification_questions = []
            mock_prep_result.areas_to_probe = []
            mock_prep_result.skill_gaps_to_address = []
            mock_prep_result.interview_tips = []
            mock_prep_result.provider = "openai"
            mock_prep_result.model = "gpt-4"
            mock_prep_result.generated_at = datetime.utcnow().isoformat()
            mock_generator.generate_questions.return_value = mock_prep_result
            mock_generator_class.return_value = mock_generator

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = Mock(
                title="Engineer",
                description="Test",
                required_skills=["Python"],
                min_experience_months=12
            )
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "resume_id": "test_resume",
                "vacancy_id": str(uuid4()),
            }
            response = client.post("/api/interview-prep/generate", json=payload)
            data = response.json()

            assert "id" in data
            assert "resume_id" in data
            assert "vacancy_id" in data
            assert "technical_questions" in data
            assert "behavioral_questions" in data
            assert "situational_questions" in data
            assert "skill_verification_questions" in data
            assert "areas_to_probe" in data
            assert "skill_gaps_to_address" in data
            assert "provider" in data
            assert "model" in data
            assert "generated_at" in data

    def test_with_candidate_skills(self, client):
        """Test generation with pre-provided candidate skills."""
        with patch('api.interview_prep.find_resume_file') as mock_find_file, \
             patch('api.interview_prep.extract_text_from_file') as mock_extract, \
             patch('api.interview_prep.InterviewQuestionGenerator') as mock_generator_class, \
             patch('api.interview_prep.get_db') as mock_get_db:

            mock_find_file.return_value = Path("data/uploads/test.pdf")
            mock_extract.return_value = "Resume text"
            mock_extract_entities = MagicMock()

            mock_generator = MagicMock()
            mock_prep_result = MagicMock()
            mock_prep_result.technical_questions = []
            mock_prep_result.behavioral_questions = []
            mock_prep_result.situational_questions = []
            mock_prep_result.skill_verification_questions = []
            mock_prep_result.areas_to_probe = []
            mock_prep_result.skill_gaps_to_address = []
            mock_prep_result.interview_tips = []
            mock_prep_result.provider = "openai"
            mock_prep_result.model = "gpt-4"
            mock_prep_result.generated_at = datetime.utcnow().isoformat()
            mock_generator.generate_questions.return_value = mock_prep_result
            mock_generator_class.return_value = mock_generator

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = Mock(
                title="Developer",
                description="Code",
                required_skills=["Python", "Django"],
                min_experience_months=12
            )
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "resume_id": "test_resume",
                "vacancy_id": str(uuid4()),
                "candidate_skills": ["Python", "Django"],
                "skill_gaps": ["Docker"]
            }
            response = client.post("/api/interview-prep/generate", json=payload)
            assert response.status_code == 201

    def test_resume_not_found(self, client):
        """Test when resume file is not found."""
        with patch('api.interview_prep.find_resume_file') as mock_find_file:
            from fastapi import HTTPException
            mock_find_file.side_effect = HTTPException(status_code=404, detail="File not found")

            payload = {
                "resume_id": "nonexistent_resume",
                "vacancy_id": str(uuid4()),
            }
            response = client.post("/api/interview-prep/generate", json=payload)
            assert response.status_code == 404

    def test_vacancy_not_found(self, client):
        """Test when vacancy is not found in database."""
        with patch('api.interview_prep.find_resume_file') as mock_find_file, \
             patch('api.interview_prep.extract_text_from_file') as mock_extract, \
             patch('api.interview_prep.get_db') as mock_get_db:

            mock_find_file.return_value = Path("data/uploads/test.pdf")
            mock_extract.return_value = "Resume text"

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "resume_id": "test_resume",
                "vacancy_id": str(uuid4()),
            }
            response = client.post("/api/interview-prep/generate", json=payload)
            assert response.status_code == 404

    def test_invalid_payload(self, client):
        """Test with invalid request payload."""
        payload = {
            "resume_id": "test_resume"
            # Missing required vacancy_id
        }
        response = client.post("/api/interview-prep/generate", json=payload)
        assert response.status_code == 422


class TestGetInterviewPrepEndpoint:
    """Tests for GET /api/interview-prep/{prep_id} endpoint."""

    def test_returns_200_on_success(self, client):
        """Test endpoint returns 200 status code on success."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}")
            assert response.status_code == 200

    def test_response_structure(self, client):
        """Test response has correct structure."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = [{"id": "q1", "text": "Question 1"}]
            mock_prep.behavioral_questions = [{"id": "q2", "text": "Question 2"}]
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = ["Test area"]
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}")
            data = response.json()

            assert data["id"] == prep_id
            assert "resume_id" in data
            assert "vacancy_id" in data
            assert "technical_questions" in data
            assert "behavioral_questions" in data
            assert "areas_to_probe" in data
            assert "provider" in data
            assert "model" in data
            assert "created_at" in data
            assert "updated_at" in data

    def test_prep_not_found(self, client):
        """Test when interview prep is not found."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}")
            assert response.status_code == 404

    def test_invalid_uuid_format(self, client):
        """Test with invalid UUID format."""
        response = client.get("/api/interview-prep/invalid-uuid")
        assert response.status_code in [422, 400]


class TestUpdateInterviewPrepEndpoint:
    """Tests for PUT /api/interview-prep/{prep_id} endpoint."""

    def test_update_custom_questions_success(self, client):
        """Test successful update with custom questions."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = ["Existing question"]
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["What is your greatest achievement?"]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

            # Verify custom questions were appended
            assert len(mock_prep.custom_questions) == 2

    def test_update_question_feedback_success(self, client):
        """Test successful update with question feedback."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {"q1": "helpful"}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "question_feedback": {"q2": "not relevant"}
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

    def test_update_both_fields(self, client):
        """Test update with both custom questions and feedback."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["Custom question 1"],
                "question_feedback": {"q1": "useful"}
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

    def test_update_no_fields_error(self, client):
        """Test update with no fields provided returns error."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {}
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 400

    def test_prep_not_found(self, client):
        """Test update when interview prep is not found."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["Test question"]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 404

    def test_invalid_custom_questions_type(self, client):
        """Test update with invalid custom_questions type."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": "not a list"
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 422

    def test_empty_question_error(self, client):
        """Test update with empty question string."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["   "]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 422

    def test_duplicate_questions_prevented(self, client):
        """Test that duplicate questions are not added."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = ["What is your greatest achievement?"]
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["What is your greatest achievement?"]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

            # Verify duplicate was not added
            assert len(mock_prep.custom_questions) == 1


class TestExportInterviewPrepPDFEndpoint:
    """Tests for GET /api/interview-prep/{prep_id}/export endpoint."""

    def test_export_success(self, client):
        """Test successful PDF export."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = [{"id": "q1", "text": "Technical question"}]
            mock_prep.behavioral_questions = [{"id": "q2", "text": "Behavioral question"}]
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = ["Test area"]
            mock_prep.custom_questions = ["Custom question"]
            mock_prep.question_feedback = {"q1": "helpful"}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}/export")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert "attachment" in response.headers["content-disposition"].lower()

    def test_export_includes_filename(self, client):
        """Test export response includes proper filename."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}/export")
            content_disposition = response.headers["content-disposition"]
            assert "interview_prep_" in content_disposition
            assert ".pdf" in content_disposition

    def test_prep_not_found(self, client):
        """Test export when interview prep is not found."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = None
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}/export")
            assert response.status_code == 404

    def test_invalid_uuid_format(self, client):
        """Test export with invalid UUID format."""
        response = client.get("/api/interview-prep/invalid-uuid/export")
        assert response.status_code in [422, 400]


class TestErrorHandling:
    """Tests for error handling across all endpoints."""

    def test_method_not_allowed(self, client):
        """Test unsupported HTTP methods."""
        # POST to GET endpoint
        response = client.post(f"/api/interview-prep/{uuid4()}")
        assert response.status_code == 405

    def test_invalid_json(self, client):
        """Test endpoints with invalid JSON."""
        response = client.post(
            "/api/interview-prep/generate",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_content_type(self, client):
        """Test POST endpoints without Content-Type."""
        response = client.post(
            "/api/interview-prep/generate",
            data="resume_id=test&vacancy_id=123",
        )
        # Should either work or return 415/422
        assert response.status_code in [200, 201, 415, 422]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_very_long_custom_question(self, client):
        """Test update with very long custom question."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            long_question = "This is a very long question " * 50
            payload = {
                "custom_questions": [long_question]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

    def test_special_characters_in_question(self, client):
        """Test update with special characters in question."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["Вопрос на русском? <>&\"'"]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

    def test_unicode_in_custom_questions(self, client):
        """Test update with unicode characters."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            payload = {
                "custom_questions": ["问一个问题 你好世界 مرحبا"]
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200

    def test_empty_areas_to_probe(self, client):
        """Test interview prep with no areas to probe."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.resume_id = uuid4()
            mock_prep.vacancy_id = uuid4()
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            response = client.get(f"/api/interview-prep/{prep_id}")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["areas_to_probe"], list)

    def test_large_feedback_dict(self, client):
        """Test update with large feedback dictionary."""
        with patch('api.interview_prep.get_db') as mock_get_db:
            prep_id = str(uuid4())
            mock_prep = MagicMock()
            mock_prep.id = UUID(prep_id)
            mock_prep.custom_questions = []
            mock_prep.question_feedback = {}
            mock_prep.technical_questions = []
            mock_prep.behavioral_questions = []
            mock_prep.situational_questions = []
            mock_prep.skill_verification_topics = []
            mock_prep.areas_to_probe = []
            mock_prep.provider = "openai"
            mock_prep.model = "gpt-4"
            mock_prep.created_at = datetime.utcnow()
            mock_prep.updated_at = datetime.utcnow()

            mock_db = MagicMock()
            mock_db.execute.return_value.scalar_one_or_none.return_value = mock_prep
            mock_get_db.return_value.__aenter__.return_value = mock_db

            large_feedback = {f"q{i}": f"feedback_{i}" for i in range(100)}
            payload = {
                "question_feedback": large_feedback
            }
            response = client.put(f"/api/interview-prep/{prep_id}", json=payload)
            assert response.status_code == 200
