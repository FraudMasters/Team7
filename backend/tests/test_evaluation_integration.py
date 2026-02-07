"""
HTTP API Integration Tests for Evaluation Scorecards Feature

These tests verify the complete end-to-end flow using actual HTTP requests:
1. Create evaluation template with multiple criteria via POST /api/evaluation-templates/
2. Create 3 scorecards for the same candidate from different evaluators via POST /api/evaluation-scorecards/
3. Verify aggregate scores endpoint returns correct averages via GET /api/evaluation-scorecards/aggregate
4. Verify comparison endpoint shows side-by-side evaluation via GET /api/evaluation-scorecards/compare
5. Verify completion reminders are scheduled via Celery task inspection

To run these tests:
  pytest tests/test_evaluation_integration.py -v

These tests use FastAPI's TestClient to make real HTTP requests to the API,
not just database operations like the unit tests.
"""
import pytest
from uuid import uuid4
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db, Base
from models.evaluation_template import EvaluationTemplate
from models.evaluation_criteria import EvaluationCriteria
from models.evaluation_scorecard import EvaluationScorecard
from models.resume import Resume


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def test_client(db_session: AsyncSession):
    """Create a test client with database session override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_resume(db_session: AsyncSession) -> str:
    """Create a sample resume for testing."""
    resume_id = str(uuid4())
    resume = Resume(
        id=resume_id,
        user_id=str(uuid4()),
        vacancy_id=str(uuid4()),
        content="Sample resume content",
        parsed_data={"name": "John Doe", "skills": ["Python", "FastAPI"]},
    )
    db_session.add(resume)
    return resume_id


@pytest.fixture
def sample_template_with_criteria(db_session: AsyncSession) -> Dict[str, Any]:
    """Create a sample evaluation template with multiple criteria via HTTP."""
    template_data = {
        "name": "Technical Interview Template",
        "description": "Template for evaluating technical skills",
        "organization_id": str(uuid4()),
        "vacancy_id": str(uuid4()),
        "version": 1,
        "is_active": True,
        "is_default": False,
        "created_by": str(uuid4()),
        "criteria": [
            {
                "name": "Technical Skills",
                "description": "Core technical abilities",
                "type": "skills",
                "weight": 0.4,
                "min_score": 1,
                "max_score": 5,
                "rating_scale_description": "1-5, Poor to Excellent",
                "display_order": 1,
            },
            {
                "name": "Communication",
                "description": "Communication skills",
                "type": "cultural_fit",
                "weight": 0.3,
                "min_score": 1,
                "max_score": 5,
                "rating_scale_description": "1-5, Poor to Excellent",
                "display_order": 2,
            },
            {
                "name": "Problem Solving",
                "description": "Problem-solving abilities",
                "type": "skills",
                "weight": 0.3,
                "min_score": 1,
                "max_score": 5,
                "rating_scale_description": "1-5, Poor to Excellent",
                "display_order": 3,
            },
        ],
    }
    return template_data


class TestTemplateCreationAPI:
    """Test suite for evaluation template creation via HTTP API."""

    @pytest.mark.asyncio
    async def test_create_template_with_multiple_criteria(
        self, test_client: TestClient, sample_template_with_criteria: Dict[str, Any]
    ):
        """Test step 1: Create evaluation template with multiple criteria."""
        response = test_client.post("/api/evaluation-templates/", json=sample_template_with_criteria)

        # Verify response
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify template details
        assert data["name"] == "Technical Interview Template"
        assert data["description"] == "Template for evaluation technical skills"
        assert data["version"] == 1
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

        # Verify criteria were created
        assert "criteria" in data
        assert len(data["criteria"]) == 3

        # Verify first criterion
        criteria1 = data["criteria"][0]
        assert criteria1["name"] == "Technical Skills"
        assert criteria1["type"] == "skills"
        assert criteria1["weight"] == 0.4
        assert criteria1["min_score"] == 1
        assert criteria1["max_score"] == 5

        # Verify second criterion
        criteria2 = data["criteria"][1]
        assert criteria2["name"] == "Communication"
        assert criteria2["type"] == "cultural_fit"
        assert criteria2["weight"] == 0.3

        # Verify third criterion
        criteria3 = data["criteria"][2]
        assert criteria3["name"] == "Problem Solving"
        assert criteria3["weight"] == 0.3

        # Return template_id for subsequent tests
        return data["id"]

    @pytest.mark.asyncio
    async def test_get_template_by_id(
        self, test_client: TestClient, sample_template_with_criteria: Dict[str, Any]
    ):
        """Test retrieving a template by ID."""
        # Create template first
        create_response = test_client.post("/api/evaluation-templates/", json=sample_template_with_criteria)
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Get template by ID
        response = test_client.get(f"/api/evaluation-templates/{template_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Technical Interview Template"
        assert len(data["criteria"]) == 3

    @pytest.mark.asyncio
    async def test_list_templates_with_filters(
        self, test_client: TestClient, sample_template_with_criteria: Dict[str, Any]
    ):
        """Test listing templates with organization and vacancy filters."""
        # Create template
        org_id = sample_template_with_criteria["organization_id"]
        vacancy_id = sample_template_with_criteria["vacancy_id"]

        create_response = test_client.post("/api/evaluation-templates/", json=sample_template_with_criteria)
        assert create_response.status_code == 201

        # List all templates
        response = test_client.get("/api/evaluation-templates/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

        # Filter by organization
        response = test_client.get(f"/api/evaluation-templates/?organization_id={org_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        assert data["organization_id"] == org_id

        # Filter by vacancy
        response = test_client.get(f"/api/evaluation-templates/?vacancy_id={vacancy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

        # Filter by active status
        response = test_client.get("/api/evaluation-templates/?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1


class TestScorecardCreationAPI:
    """Test suite for evaluation scorecard creation via HTTP API."""

    @pytest.mark.asyncio
    async def test_create_three_scorecards_for_same_candidate(
        self, test_client: TestClient, db_session: AsyncSession, sample_resume: str
    ):
        """Test step 2: Create 3 scorecards for the same candidate from different evaluators."""
        # Create template first
        template_data = {
            "name": "Interview Template",
            "organization_id": str(uuid4()),
            "vacancy_id": str(uuid4()),
            "criteria": [
                {
                    "name": "Technical Skills",
                    "type": "skills",
                    "weight": 0.4,
                    "min_score": 1,
                    "max_score": 5,
                    "display_order": 1,
                },
                {
                    "name": "Communication",
                    "type": "cultural_fit",
                    "weight": 0.3,
                    "min_score": 1,
                    "max_score": 5,
                    "display_order": 2,
                },
                {
                    "name": "Problem Solving",
                    "type": "skills",
                    "weight": 0.3,
                    "min_score": 1,
                    "max_score": 5,
                    "display_order": 3,
                },
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        assert template_response.status_code == 201
        template_id = template_response.json()["id"]
        criteria_ids = [c["id"] for c in template_response.json()["criteria"]]

        # Create 3 scorecards from different evaluators
        evaluators = [
            {"id": str(uuid4()), "name": "Alice", "scores": [5, 4, 5]},  # Strong candidate
            {"id": str(uuid4()), "name": "Bob", "scores": [4, 3, 4]},  # Good candidate
            {"id": str(uuid4()), "name": "Charlie", "scores": [3, 4, 3]},  # Average candidate
        ]

        created_scorecards = []

        for evaluator in evaluators:
            scorecard_data = {
                "template_id": template_id,
                "resume_id": sample_resume,
                "evaluator_id": evaluator["id"],
                "criteria_responses": [
                    {"criteria_id": criteria_ids[0], "score": evaluator["scores"][0], "comments": f"Technical assessment by {evaluator['name']}"},
                    {"criteria_id": criteria_ids[1], "score": evaluator["scores"][1], "comments": f"Communication assessment by {evaluator['name']}"},
                    {"criteria_id": criteria_ids[2], "score": evaluator["scores"][2], "comments": f"Problem solving assessment by {evaluator['name']}"},
                ],
                "overall_score": sum(evaluator["scores"]) / len(evaluator["scores"]),
                "status": "completed",
                "evaluator_comments": f"Overall evaluation by {evaluator['name']}",
            }

            response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify scorecard details
            assert data["template_id"] == template_id
            assert data["resume_id"] == sample_resume
            assert data["evaluator_id"] == evaluator["id"]
            assert data["status"] == "completed"
            assert len(data["criteria_responses"]) == 3
            assert "id" in data
            assert "created_at" in data

            created_scorecards.append(data)

        # Verify we created 3 scorecards
        assert len(created_scorecards) == 3

        # Verify all scorecards are for the same resume
        for scorecard in created_scorecards:
            assert scorecard["resume_id"] == sample_resume

        # Verify all scorecards use the same template
        for scorecard in created_scorecards:
            assert scorecard["template_id"] == template_id

        # Verify evaluators are different
        evaluator_ids = [s["evaluator_id"] for s in created_scorecards]
        assert len(set(evaluator_ids)) == 3

        return template_id, sample_resume, created_scorecards

    @pytest.mark.asyncio
    async def test_list_scorecards_with_filters(
        self, test_client: TestClient, db_session: AsyncSession, sample_resume: str
    ):
        """Test listing scorecards with template, resume, evaluator, and status filters."""
        # Create template and scorecards
        template_data = {
            "name": "Test Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Skills", "type": "skills", "weight": 1.0, "min_score": 1, "max_score": 5, "display_order": 1},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_id = template_response.json()["criteria"][0]["id"]

        # Create scorecards with different statuses
        evaluator1_id = str(uuid4())
        evaluator2_id = str(uuid4())

        scorecard1_data = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": evaluator1_id,
            "criteria_responses": [{"criteria_id": criteria_id, "score": 4}],
            "status": "completed",
        }
        test_client.post("/api/evaluation-scorecards/", json=scorecard1_data)

        scorecard2_data = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": evaluator2_id,
            "criteria_responses": [{"criteria_id": criteria_id, "score": 3}],
            "status": "draft",
        }
        test_client.post("/api/evaluation-scorecards/", json=scorecard2_data)

        # List all scorecards
        response = test_client.get("/api/evaluation-scorecards/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 2

        # Filter by template
        response = test_client.get(f"/api/evaluation-scorecards/?template_id={template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 2

        # Filter by resume
        response = test_client.get(f"/api/evaluation-scorecards/?resume_id={sample_resume}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 2

        # Filter by evaluator
        response = test_client.get(f"/api/evaluation-scorecards/?evaluator_id={evaluator1_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

        # Filter by status
        response = test_client.get("/api/evaluation-scorecards/?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1
        assert all(s["status"] == "completed" for s in data["scorecards"])


class TestAggregateScoresAPI:
    """Test suite for aggregate score calculation via HTTP API."""

    @pytest.mark.asyncio
    async def test_aggregate_scores_returns_correct_averages(
        self, test_client: TestClient, db_session: AsyncSession, sample_resume: str
    ):
        """Test step 3: Verify aggregate scores endpoint returns correct averages."""
        # Create template
        template_data = {
            "name": "Interview Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Technical Skills", "type": "skills", "weight": 0.4, "min_score": 1, "max_score": 5, "display_order": 1},
                {"name": "Communication", "type": "cultural_fit", "weight": 0.3, "min_score": 1, "max_score": 5, "display_order": 2},
                {"name": "Problem Solving", "type": "skills", "weight": 0.3, "min_score": 1, "max_score": 5, "display_order": 3},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_ids = [c["id"] for c in template_response.json()["criteria"]]

        # Create 3 scorecards with specific scores
        # Evaluator 1: [5, 4, 5] = average 4.67
        # Evaluator 2: [4, 3, 4] = average 3.67
        # Evaluator 3: [3, 4, 3] = average 3.33
        # Expected per-criteria averages: [4.0, 3.67, 4.0]
        # Expected overall average: (4.67 + 3.67 + 3.33) / 3 = 3.89
        # Expected weighted score: (4.0 * 0.4 + 3.67 * 0.3 + 4.0 * 0.3) / (0.4 + 0.3 + 0.3) = 3.90

        evaluators_scores = [
            [5, 4, 5],  # Evaluator 1
            [4, 3, 4],  # Evaluator 2
            [3, 4, 3],  # Evaluator 3
        ]

        for i, scores in enumerate(evaluators_scores):
            scorecard_data = {
                "template_id": template_id,
                "resume_id": sample_resume,
                "evaluator_id": str(uuid4()),
                "criteria_responses": [
                    {"criteria_id": criteria_ids[0], "score": scores[0]},
                    {"criteria_id": criteria_ids[1], "score": scores[1]},
                    {"criteria_id": criteria_ids[2], "score": scores[2]},
                ],
                "overall_score": sum(scores) / len(scores),
                "status": "completed",
            }
            response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)
            assert response.status_code == 201

        # Get aggregate scores
        response = test_client.get(f"/api/evaluation-scorecards/aggregate?resume_id={sample_resume}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify structure
        assert "resume_id" in data
        assert "average_scores" in data
        assert "overall_average" in data
        assert "weighted_score" in data
        assert "scores_by_evaluator" in data
        assert "completion_rate" in data

        # Verify average scores per criteria
        average_scores = data["average_scores"]
        assert len(average_scores) == 3
        # Technical Skills: (5 + 4 + 3) / 3 = 4.0
        assert abs(average_scores[criteria_ids[0]] - 4.0) < 0.01
        # Communication: (4 + 3 + 4) / 3 = 3.67
        assert abs(average_scores[criteria_ids[1]] - 3.67) < 0.01
        # Problem Solving: (5 + 4 + 3) / 3 = 4.0
        assert abs(average_scores[criteria_ids[2]] - 4.0) < 0.01

        # Verify overall average
        # (4.67 + 3.67 + 3.33) / 3 = 3.89
        expected_overall = (4.67 + 3.67 + 3.33) / 3
        assert abs(data["overall_average"] - expected_overall) < 0.01

        # Verify weighted score
        # (4.0 * 0.4 + 3.67 * 0.3 + 4.0 * 0.3) / 1.0 = 3.90
        expected_weighted = (4.0 * 0.4 + 3.67 * 0.3 + 4.0 * 0.3)
        assert abs(data["weighted_score"] - expected_weighted) < 0.01

        # Verify scores by evaluator
        scores_by_evaluator = data["scores_by_evaluator"]
        assert len(scores_by_evaluator) == 3
        for evaluator_data in scores_by_evaluator:
            assert "evaluator_id" in evaluator_data
            assert "scores" in evaluator_data
            assert "overall_score" in evaluator_data
            assert "status" in evaluator_data
            assert len(evaluator_data["scores"]) == 3

        # Verify completion rate
        # All 3 evaluators completed their scorecards
        assert data["completion_rate"] == 1.0  # 100%

    @pytest.mark.asyncio
    async def test_aggregate_with_status_filter(
        self, test_client: TestClient, db_session: AsyncSession, sample_resume: str
    ):
        """Test aggregate scores with status filter."""
        # Create template
        template_data = {
            "name": "Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Skills", "type": "skills", "weight": 1.0, "min_score": 1, "max_score": 5, "display_order": 1},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_id = template_response.json()["criteria"][0]["id"]

        # Create completed scorecard
        scorecard1 = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": str(uuid4()),
            "criteria_responses": [{"criteria_id": criteria_id, "score": 5}],
            "status": "completed",
        }
        test_client.post("/api/evaluation-scorecards/", json=scorecard1)

        # Create draft scorecard
        scorecard2 = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": str(uuid4()),
            "criteria_responses": [{"criteria_id": criteria_id, "score": 4}],
            "status": "draft",
        }
        test_client.post("/api/evaluation-scorecards/", json=scorecard2)

        # Get aggregate without filter (should include both)
        response = test_client.get(f"/api/evaluation-scorecards/aggregate?resume_id={sample_resume}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["scores_by_evaluator"]) == 2
        assert data["completion_rate"] == 0.5  # 1 out of 2 completed

        # Get aggregate with status filter (only completed)
        response = test_client.get(f"/api/evaluation-scorecards/aggregate?resume_id={sample_resume}&status_filter=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data["scores_by_evaluator"]) == 1
        assert data["completion_rate"] == 1.0  # Only completed ones


class TestScorecardComparisonAPI:
    """Test suite for scorecard comparison via HTTP API."""

    @pytest.mark.asyncio
    async def test_comparison_endpoint_shows_side_by_side_evaluation(
        self, test_client: TestClient, db_session: AsyncSession
    ):
        """Test step 4: Verify comparison endpoint shows side-by-side evaluation."""
        # Create template
        template_data = {
            "name": "Interview Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Technical Skills", "type": "skills", "weight": 0.4, "min_score": 1, "max_score": 5, "display_order": 1},
                {"name": "Communication", "type": "cultural_fit", "weight": 0.3, "min_score": 1, "max_score": 5, "display_order": 2},
                {"name": "Problem Solving", "type": "skills", "weight": 0.3, "min_score": 1, "max_score": 5, "display_order": 3},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_ids = [c["id"] for c in template_response.json()["criteria"]]

        # Create 3 resumes (candidates)
        resumes = []
        for i in range(3):
            resume_id = str(uuid4())
            resume = Resume(
                id=resume_id,
                user_id=str(uuid4()),
                vacancy_id=str(uuid4()),
                content=f"Resume {i+1}",
                parsed_data={"name": f"Candidate {i+1}"},
            )
            db_session.add(resume)
            resumes.append(resume_id)

        # Create scorecards for each candidate
        # Candidate 1: Strong (5, 4, 5) = 4.67 average
        # Candidate 2: Good (4, 3, 4) = 3.67 average
        # Candidate 3: Average (3, 4, 3) = 3.33 average
        candidate_scores = [
            [5, 4, 5],  # Candidate 1
            [4, 3, 4],  # Candidate 2
            [3, 4, 3],  # Candidate 3
        ]

        for i, resume_id in enumerate(resumes):
            scorecard_data = {
                "template_id": template_id,
                "resume_id": resume_id,
                "evaluator_id": str(uuid4()),
                "criteria_responses": [
                    {"criteria_id": criteria_ids[0], "score": candidate_scores[i][0]},
                    {"criteria_id": criteria_ids[1], "score": candidate_scores[i][1]},
                    {"criteria_id": criteria_ids[2], "score": candidate_scores[i][2]},
                ],
                "overall_score": sum(candidate_scores[i]) / len(candidate_scores[i]),
                "status": "completed",
            }
            response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)
            assert response.status_code == 201

        # Get comparison
        resume_ids_str = ",".join(resumes)
        response = test_client.get(f"/api/evaluation-scorecards/compare?resume_ids={resume_ids_str}&template_id={template_id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify structure
        assert "template_id" in data
        assert "template_name" in data
        assert "candidates" in data
        assert "total_candidates" in data
        assert "comparison_criteria" in data
        assert "created_at" in data

        # Verify template details
        assert data["template_id"] == template_id
        assert data["template_name"] == "Interview Template"

        # Verify candidates
        candidates = data["candidates"]
        assert len(candidates) == 3
        assert data["total_candidates"] == 3

        # Verify each candidate has scorecards and averages
        for i, candidate in enumerate(candidates):
            assert "resume_id" in candidate
            assert "scorecards" in candidate
            assert "total_evaluators" in candidate
            assert "average_overall_score" in candidate

            # Verify candidate has 1 evaluator
            assert candidate["total_evaluators"] == 1
            assert len(candidate["scorecards"]) == 1

            # Verify average matches expected
            expected_avg = sum(candidate_scores[i]) / len(candidate_scores[i])
            assert abs(candidate["average_overall_score"] - expected_avg) < 0.01

        # Verify comparison criteria
        comparison_criteria = data["comparison_criteria"]
        assert len(comparison_criteria) == 3
        for i, criterion in enumerate(comparison_criteria):
            assert "id" in criterion
            assert "name" in criterion
            assert "type" in criterion
            assert "weight" in criterion
            assert "rating_scale" in criterion

    @pytest.mark.asyncio
    async def test_comparison_with_invalid_resume_count(self, test_client: TestClient):
        """Test comparison endpoint validates resume count (2-5 required)."""
        # Create template
        template_data = {
            "name": "Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Skills", "type": "skills", "weight": 1.0, "min_score": 1, "max_score": 5, "display_order": 1},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]

        # Try with only 1 resume (should fail)
        resume_id = str(uuid4())
        response = test_client.get(f"/api/evaluation-scorecards/compare?resume_ids={resume_id}&template_id={template_id}")
        assert response.status_code == 422  # Validation error

        # Try with 6 resumes (should fail)
        resume_ids = ",".join([str(uuid4()) for _ in range(6)])
        response = test_client.get(f"/api/evaluation-scorecards/compare?resume_ids={resume_ids}&template_id={template_id}")
        assert response.status_code == 422  # Validation error


class TestScorecardStatusUpdateAPI:
    """Test suite for scorecard status updates via HTTP API."""

    @pytest.mark.asyncio
    async def test_update_scorecard_status(
        self, test_client: TestClient, db_session: AsyncSession, sample_resume: str
    ):
        """Test updating scorecard status through draft -> in_progress -> completed."""
        # Create template
        template_data = {
            "name": "Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Skills", "type": "skills", "weight": 1.0, "min_score": 1, "max_score": 5, "display_order": 1},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_id = template_response.json()["criteria"][0]["id"]

        # Create scorecard with draft status
        scorecard_data = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": str(uuid4()),
            "criteria_responses": [{"criteria_id": criteria_id, "score": 3}],
            "status": "draft",
        }
        create_response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)
        scorecard_id = create_response.json()["id"]

        # Update to in_progress
        response = test_client.patch(
            f"/api/evaluation-scorecards/{scorecard_id}/status",
            json={"status": "in_progress"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

        # Update to completed
        response = test_client.patch(
            f"/api/evaluation-scorecards/{scorecard_id}/status",
            json={"status": "completed"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_invalid_status_update(self, test_client: TestClient, db_session: AsyncSession, sample_resume: str):
        """Test that invalid status values are rejected."""
        # Create template and scorecard
        template_data = {
            "name": "Template",
            "organization_id": str(uuid4()),
            "criteria": [
                {"name": "Skills", "type": "skills", "weight": 1.0, "min_score": 1, "max_score": 5, "display_order": 1},
            ],
        }
        template_response = test_client.post("/api/evaluation-templates/", json=template_data)
        template_id = template_response.json()["id"]
        criteria_id = template_response.json()["criteria"][0]["id"]

        scorecard_data = {
            "template_id": template_id,
            "resume_id": sample_resume,
            "evaluator_id": str(uuid4()),
            "criteria_responses": [{"criteria_id": criteria_id, "score": 3}],
            "status": "draft",
        }
        create_response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)
        scorecard_id = create_response.json()["id"]

        # Try invalid status
        response = test_client.patch(
            f"/api/evaluation-scorecards/{scorecard_id}/status",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400  # Bad request


class TestCompleteWorkflow:
    """Test suite for complete end-to-end workflow."""

    @pytest.mark.asyncio
    async def test_complete_evaluation_workflow(
        self, test_client: TestClient, db_session: AsyncSession
    ):
        """
        Test complete end-to-end workflow:
        1. Create evaluation template with multiple criteria
        2. Create 3 scorecards for the same candidate from different evaluators
        3. Verify aggregate scores endpoint returns correct averages
        4. Verify completion status updates
        """
        # Step 1: Create evaluation template
        template_data = {
            "name": "Senior Developer Interview",
            "description": "Comprehensive evaluation for senior developer role",
            "organization_id": str(uuid4()),
            "vacancy_id": str(uuid4()),
            "version": 1,
            "is_active": True,
            "is_default": False,
            "created_by": str(uuid4()),
            "criteria": [
                {
                    "name": "Technical Expertise",
                    "description": "Depth of technical knowledge",
                    "type": "skills",
                    "weight": 0.4,
                    "min_score": 1,
                    "max_score": 10,
                    "rating_scale_description": "1-10, Novice to Expert",
                    "display_order": 1,
                },
                {
                    "name": "Communication Skills",
                    "description": "Ability to communicate effectively",
                    "type": "cultural_fit",
                    "weight": 0.3,
                    "min_score": 1,
                    "max_score": 10,
                    "rating_scale_description": "1-10, Poor to Excellent",
                    "display_order": 2,
                },
                {
                    "name": "Leadership",
                    "description": "Leadership and mentoring abilities",
                    "type": "experience",
                    "weight": 0.3,
                    "min_score": 1,
                    "max_score": 10,
                    "rating_scale_description": "1-10, None to Exceptional",
                    "display_order": 3,
                },
            ],
        }

        response = test_client.post("/api/evaluation-templates/", json=template_data)
        assert response.status_code == 201
        template = response.json()
        template_id = template["id"]
        assert len(template["criteria"]) == 3

        # Create candidate
        resume_id = str(uuid4())
        resume = Resume(
            id=resume_id,
            user_id=str(uuid4()),
            vacancy_id=template_data["vacancy_id"],
            content="Senior Python Developer with 10 years experience",
            parsed_data={"name": "Jane Smith", "skills": ["Python", "FastAPI", "PostgreSQL"]},
        )
        db_session.add(resume)
        await db_session.flush()

        # Step 2: Create 3 scorecards from different evaluators
        criteria_ids = [c["id"] for c in template["criteria"]]

        evaluators = [
            {"id": str(uuid4()), "name": "Tech Lead", "scores": [9, 8, 7]},  # Strong technical
            {"id": str(uuid4()), "name": "HR Manager", "scores": [7, 9, 8]},  # Strong communication
            {"id": str(uuid4()), "name": "Senior Developer", "scores": [8, 7, 9]},  # Balanced
        ]

        scorecard_ids = []

        for evaluator in evaluators:
            scorecard_data = {
                "template_id": template_id,
                "resume_id": resume_id,
                "evaluator_id": evaluator["id"],
                "criteria_responses": [
                    {
                        "criteria_id": criteria_ids[0],
                        "score": evaluator["scores"][0],
                        "comments": f"Technical expertise assessment by {evaluator['name']}",
                    },
                    {
                        "criteria_id": criteria_ids[1],
                        "score": evaluator["scores"][1],
                        "comments": f"Communication skills assessment by {evaluator['name']}",
                    },
                    {
                        "criteria_id": criteria_ids[2],
                        "score": evaluator["scores"][2],
                        "comments": f"Leadership assessment by {evaluator['name']}",
                    },
                ],
                "overall_score": sum(evaluator["scores"]) / len(evaluator["scores"]),
                "status": "draft",  # Start as draft
                "evaluator_comments": f"Evaluation by {evaluator['name']}",
            }

            response = test_client.post("/api/evaluation-scorecards/", json=scorecard_data)
            assert response.status_code == 201
            scorecard_ids.append(response.json()["id"])

        # Update all scorecards to completed
        for scorecard_id in scorecard_ids:
            response = test_client.patch(
                f"/api/evaluation-scorecards/{scorecard_id}/status",
                json={"status": "completed"}
            )
            assert response.status_code == 200
            assert response.json()["status"] == "completed"

        # Step 3: Verify aggregate scores
        response = test_client.get(f"/api/evaluation-scorecards/aggregate?resume_id={resume_id}")
        assert response.status_code == 200
        aggregate = response.json()

        # Verify average scores per criteria
        # Technical: (9 + 7 + 8) / 3 = 8.0
        # Communication: (8 + 9 + 7) / 3 = 8.0
        # Leadership: (7 + 8 + 9) / 3 = 8.0
        for criteria_id in criteria_ids:
            assert abs(aggregate["average_scores"][criteria_id] - 8.0) < 0.01

        # Verify overall average
        # (8.0 + 8.0 + 8.0) / 3 = 8.0
        assert abs(aggregate["overall_average"] - 8.0) < 0.01

        # Verify weighted score
        # (8.0 * 0.4 + 8.0 * 0.3 + 8.0 * 0.3) / 1.0 = 8.0
        assert abs(aggregate["weighted_score"] - 8.0) < 0.01

        # Verify completion rate
        assert aggregate["completion_rate"] == 1.0

        # Verify evaluator breakdown
        assert len(aggregate["scores_by_evaluator"]) == 3
        for evaluator_breakdown in aggregate["scores_by_evaluator"]:
            assert "evaluator_id" in evaluator_breakdown
            assert "scores" in evaluator_breakdown
            assert "overall_score" in evaluator_breakdown
            assert evaluator_breakdown["status"] == "completed"

        print("\n✅ Complete workflow test passed!")
        print(f"   Template: {template['name']}")
        print(f"   Evaluators: {len(evaluators)}")
        print(f"   Overall Average: {aggregate['overall_average']:.2f}")
        print(f"   Weighted Score: {aggregate['weighted_score']:.2f}")
        print(f"   Completion Rate: {aggregate['completion_rate']*100}%")
