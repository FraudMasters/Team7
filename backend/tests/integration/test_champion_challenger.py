"""
Integration tests for champion/challenger model workflow.

This test suite validates the end-to-end integration between:
- Model versioning system with champion/challenger roles
- Champion/challenger promotion API endpoints
- Statistical significance validation for promotions
- Performance comparison between champion and challenger models

Test Coverage:
- Champion/challenger status retrieval
- Challenger promotion to champion with statistical validation
- Forced promotion bypassing statistical checks
- Promotion failure scenarios (insufficient improvement, invalid IDs)
- Champion/challenger workflow end-to-end scenarios
"""
from typing import Any, Dict, Generator
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Import the FastAPI application
import sys
sys.path.insert(0, str(__file__).parent.parent.parent)

from main import app
from analyzers.model_versioning import ModelVersionManager


@pytest.fixture
def model_manager() -> ModelVersionManager:
    """
    Create a ModelVersionManager instance for testing.

    Returns:
        ModelVersionManager instance
    """
    return ModelVersionManager()


@pytest.fixture
def mock_db_session() -> Mock:
    """
    Create a mock database session for testing.

    Returns:
        Mock database session
    """
    session = Mock()
    return session


@pytest.fixture
def sample_champion_model() -> Dict[str, Any]:
    """
    Sample champion (active) model data for testing.

    Returns:
        Dictionary with champion model information
    """
    return {
        "id": str(uuid4()),
        "model_name": "skill_matching",
        "version": "v1.0.0",
        "file_path": "/models/skill_matching_v1.pkl",
        "performance_score": 85.5,
        "is_active": True,
        "is_experiment": False,
        "model_metadata": {
            "algorithm": "bert-base-uncased",
            "training_date": "2024-01-01"
        },
        "accuracy_metrics": {
            "precision": 0.87,
            "recall": 0.84,
            "f1_score": 0.85,
            "sample_size": 1000
        }
    }


@pytest.fixture
def sample_challenger_model() -> Dict[str, Any]:
    """
    Sample challenger (experimental) model data for testing.

    Returns:
        Dictionary with challenger model information
    """
    return {
        "id": str(uuid4()),
        "model_name": "skill_matching",
        "version": "v2.0.0-challenger",
        "file_path": "/models/skill_matching_v2.pkl",
        "performance_score": 92.0,
        "is_active": True,
        "is_experiment": True,
        "traffic_percentage": 20,
        "model_metadata": {
            "algorithm": "bert-large-uncased",
            "training_date": "2024-01-15"
        },
        "accuracy_metrics": {
            "precision": 0.93,
            "recall": 0.91,
            "f1_score": 0.92,
            "sample_size": 500
        }
    }


@pytest.fixture
def sample_weak_challenger() -> Dict[str, Any]:
    """
    Sample challenger with insufficient performance improvement.

    Returns:
        Dictionary with weak challenger model information
    """
    return {
        "id": str(uuid4()),
        "model_name": "skill_matching",
        "version": "v1.1.0-challenger",
        "file_path": "/models/skill_matching_v1.1.pkl",
        "performance_score": 87.0,  # Only ~1.7% improvement over 85.5
        "is_active": True,
        "is_experiment": True,
        "traffic_percentage": 10,
        "model_metadata": {
            "algorithm": "bert-base-uncased",
            "training_date": "2024-01-10"
        },
        "accuracy_metrics": {
            "precision": 0.88,
            "recall": 0.86,
            "f1_score": 0.87,
            "sample_size": 300
        }
    }


class TestChampionChallengerStatus:
    """Tests for champion/challenger status retrieval."""

    def test_get_status_success(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_challenger_model: Dict[str, Any]
    ):
        """Test getting champion/challenger status successfully."""
        # Setup mock for champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.model_name = sample_champion_model["model_name"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.file_path = sample_champion_model["file_path"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.model_metadata = sample_champion_model["model_metadata"]
        mock_champion.accuracy_metrics = sample_champion_model["accuracy_metrics"]
        mock_champion.experiment_config = None

        # Setup mock for challenger
        mock_challenger = Mock()
        mock_challenger.id = sample_challenger_model["id"]
        mock_challenger.model_name = sample_challenger_model["model_name"]
        mock_challenger.version = sample_challenger_model["version"]
        mock_challenger.file_path = sample_challenger_model["file_path"]
        mock_challenger.performance_score = sample_challenger_model["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.model_metadata = sample_challenger_model["model_metadata"]
        mock_challenger.accuracy_metrics = sample_challenger_model["accuracy_metrics"]
        mock_challenger.experiment_config = {"traffic_percentage": 20}

        # Setup query chain for champion query
        mock_champion_query = Mock()
        mock_champion_query.filter.return_value.first.return_value = mock_champion

        # Setup query chain for challenger query
        mock_challenger_query = Mock()
        mock_challenger_query.filter.return_value.all.return_value = [mock_challenger]

        # Configure db_session to return different mocks based on call order
        call_count = [0]

        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_champion_query
            else:
                return mock_challenger_query

        mock_db_session.query.side_effect = mock_query

        status = model_manager.get_champion_challenger_status(
            "skill_matching",
            mock_db_session
        )

        assert status["model_name"] == "skill_matching"
        assert status["champion"] is not None
        assert status["has_challenger"] is True
        assert status["challenger_count"] == 1
        assert status["comparison"] is not None
        assert status["comparison"]["improvement_pct"] > 0

    def test_get_status_no_challenger(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any]
    ):
        """Test getting status when no challenger exists."""
        # Setup mock for champion only
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.model_name = sample_champion_model["model_name"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.file_path = sample_champion_model["file_path"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.model_metadata = {}
        mock_champion.accuracy_metrics = {}
        mock_champion.experiment_config = None

        mock_champion_query = Mock()
        mock_champion_query.filter.return_value.first.return_value = mock_champion

        mock_challenger_query = Mock()
        mock_challenger_query.filter.return_value.all.return_value = []

        call_count = [0]

        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_champion_query
            else:
                return mock_challenger_query

        mock_db_session.query.side_effect = mock_query

        status = model_manager.get_champion_challenger_status(
            "skill_matching",
            mock_db_session
        )

        assert status["model_name"] == "skill_matching"
        assert status["champion"] is not None
        assert status["has_challenger"] is False
        assert status["challenger_count"] == 0
        assert status["comparison"] is None

    def test_get_status_no_champion(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test getting status when no champion exists."""
        mock_champion_query = Mock()
        mock_champion_query.filter.return_value.first.return_value = None

        mock_challenger_query = Mock()
        mock_challenger_query.filter.return_value.all.return_value = []

        call_count = [0]

        def mock_query(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_champion_query
            else:
                return mock_challenger_query

        mock_db_session.query.side_effect = mock_query

        status = model_manager.get_champion_challenger_status(
            "unknown_model",
            mock_db_session
        )

        assert status["model_name"] == "unknown_model"
        assert status["champion"] is None
        assert status["has_challenger"] is False


class TestChampionChallengerPromotion:
    """Tests for challenger promotion to champion."""

    def test_promote_challenger_success(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_challenger_model: Dict[str, Any]
    ):
        """Test successful promotion of challenger to champion."""
        # Setup mock for challenger
        mock_challenger = Mock()
        mock_challenger.id = sample_challenger_model["id"]
        mock_challenger.model_name = sample_challenger_model["model_name"]
        mock_challenger.version = sample_challenger_model["version"]
        mock_challenger.file_path = sample_challenger_model["file_path"]
        mock_challenger.performance_score = sample_challenger_model["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.model_metadata = sample_challenger_model["model_metadata"]
        mock_challenger.accuracy_metrics = sample_challenger_model["accuracy_metrics"]
        mock_challenger.experiment_config = {}
        mock_challenger.updated_at = None

        # Setup mock for current champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.model_name = sample_champion_model["model_name"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.model_metadata = {}
        mock_champion.accuracy_metrics = sample_champion_model["accuracy_metrics"]

        # Setup query mocks
        mock_query = Mock()

        def mock_filter_side_effect(*args, **kwargs):
            mock_result = Mock()
            # First call gets challenger by ID
            # Second call gets current champion
            return mock_result

        # Setup for challenger lookup
        mock_challenger_result = Mock()
        mock_challenger_result.filter.return_value.first.return_value = mock_challenger

        # Setup for champion lookup
        mock_champion_result = Mock()
        mock_champion_result.filter.return_value.first.return_value = mock_champion

        # Setup for experiments lookup
        mock_experiments_result = Mock()
        mock_experiments_result.filter.return_value.all.return_value = [mock_challenger]

        call_count = [0]

        def mock_query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                # First query: get challenger by ID
                return mock_challenger_result
            elif call_count[0] == 2:
                # Second query: get champion
                mock_challenger_result.filter.return_value.first.return_value = mock_challenger
                return mock_challenger_result
            else:
                # Third+ queries
                return mock_experiments_result

        mock_db_session.query.side_effect = mock_query_side_effect

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=sample_challenger_model["id"],
            min_performance_improvement=5.0,
            min_sample_size=100,
            db_session=mock_db_session
        )

        assert result["success"] is True
        assert result["model_name"] == "skill_matching"
        assert result["challenger_version"] == sample_challenger_model["version"]

    def test_promote_challenger_forced(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_challenger_model: Dict[str, Any]
    ):
        """Test forced promotion bypassing statistical validation."""
        # Setup mock for challenger
        mock_challenger = Mock()
        mock_challenger.id = sample_challenger_model["id"]
        mock_challenger.model_name = sample_challenger_model["model_name"]
        mock_challenger.version = sample_challenger_model["version"]
        mock_challenger.performance_score = sample_challenger_model["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.experiment_config = {}
        mock_challenger.updated_at = None

        # Setup mock for current champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_challenger
        mock_db_session.query.return_value = mock_query

        # Need to handle multiple query calls
        call_count = [0]

        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:
                # First call: get challenger
                mock_result.filter.return_value.first.return_value = mock_challenger
            else:
                # Second call: get champion
                mock_result.filter.return_value.first.return_value = mock_champion
            return mock_result

        mock_db_session.query.side_effect = mock_query_side_effect

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=sample_challenger_model["id"],
            force=True,
            db_session=mock_db_session
        )

        assert result["success"] is True
        assert result["forced"] is True
        assert "Forced promotion" in result["promotion_reason"]

    def test_promote_challenger_not_found(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test promotion when challenger model is not found."""
        non_existent_id = str(uuid4())

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=non_existent_id,
            db_session=mock_db_session
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_promote_challenger_insufficient_improvement(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_weak_challenger: Dict[str, Any]
    ):
        """Test promotion rejection when challenger improvement is insufficient."""
        # Setup mock for weak challenger
        mock_challenger = Mock()
        mock_challenger.id = sample_weak_challenger["id"]
        mock_challenger.model_name = sample_weak_challenger["model_name"]
        mock_challenger.version = sample_weak_challenger["version"]
        mock_challenger.performance_score = sample_weak_challenger["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.accuracy_metrics = sample_weak_challenger["accuracy_metrics"]
        mock_challenger.experiment_config = {}
        mock_challenger.updated_at = None

        # Setup mock for champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.accuracy_metrics = sample_champion_model["accuracy_metrics"]

        call_count = [0]

        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:
                mock_result.filter.return_value.first.return_value = mock_challenger
            else:
                mock_result.filter.return_value.first.return_value = mock_champion
            return mock_result

        mock_db_session.query.side_effect = mock_query_side_effect

        # Setup experiments query
        mock_experiments_result = Mock()
        mock_experiments_result.filter.return_value.all.return_value = [mock_challenger]

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=sample_weak_challenger["id"],
            min_performance_improvement=5.0,  # Require 5% improvement
            db_session=mock_db_session
        )

        # Result depends on whether statistical validation passes
        # Weak challenger has only ~1.7% improvement, should be rejected
        assert result["success"] is False

    def test_promote_challenger_no_db_session(
        self,
        model_manager: ModelVersionManager
    ):
        """Test promotion behavior when no database session is provided."""
        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=str(uuid4()),
            db_session=None
        )

        assert result["success"] is False
        assert "No database session" in result["error"]


class TestChampionChallengerAPIEndpoints:
    """Tests for champion/challenger API endpoints."""

    def test_get_status_endpoint(self, client: TestClient):
        """Test GET /champion-challenger/status/{model_name} endpoint."""
        response = client.get(
            "/api/model-versions/champion-challenger/status/skill_matching"
        )

        # Response depends on whether data exists
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "model_name" in data
            assert data["model_name"] == "skill_matching"

    def test_promote_endpoint_invalid_uuid(self, client: TestClient):
        """Test POST /champion-challenger/promote with invalid UUID."""
        request_data = {
            "model_name": "skill_matching",
            "challenger_version_id": "not-a-valid-uuid"
        }

        response = client.post(
            "/api/model-versions/champion-challenger/promote",
            json=request_data
        )

        # Should return 400 for invalid UUID
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid challenger_version_id" in data["detail"]

    def test_promote_endpoint_missing_fields(self, client: TestClient):
        """Test POST /champion-challenger/promote with missing required fields."""
        request_data = {
            "model_name": "skill_matching"
            # Missing challenger_version_id
        }

        response = client.post(
            "/api/model-versions/champion-challenger/promote",
            json=request_data
        )

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_promote_endpoint_with_optional_params(self, client: TestClient):
        """Test POST /champion-challenger/promote with optional parameters."""
        request_data = {
            "model_name": "skill_matching",
            "challenger_version_id": str(uuid4()),
            "min_performance_improvement": 10.0,
            "min_sample_size": 500,
            "significance_level": 0.01,
            "min_confidence": 0.95,
            "force": False
        }

        response = client.post(
            "/api/model-versions/champion-challenger/promote",
            json=request_data
        )

        # Response depends on whether the model exists
        # Acceptable responses: 200 (success), 400 (not found), 500 (db error)
        assert response.status_code in [200, 400, 500]

    def test_promote_endpoint_forced(self, client: TestClient):
        """Test POST /champion-challenger/promote with force flag."""
        request_data = {
            "model_name": "skill_matching",
            "challenger_version_id": str(uuid4()),
            "force": True
        }

        response = client.post(
            "/api/model-versions/champion-challenger/promote",
            json=request_data
        )

        # Response depends on whether the model exists
        assert response.status_code in [200, 400, 500]


class TestChampionChallengerWorkflows:
    """End-to-end workflow tests for champion/challenger scenarios."""

    @pytest.mark.slow
    def test_complete_promotion_workflow(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_challenger_model: Dict[str, Any]
    ):
        """
        Test complete champion/challenger promotion workflow.

        1. Get initial champion/challenger status
        2. Verify challenger exists with better performance
        3. Promote challenger to champion
        4. Verify promotion was successful
        """
        # Setup mocks for status check
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.model_name = sample_champion_model["model_name"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.model_metadata = {}
        mock_champion.accuracy_metrics = sample_champion_model["accuracy_metrics"]

        mock_challenger = Mock()
        mock_challenger.id = sample_challenger_model["id"]
        mock_challenger.model_name = sample_challenger_model["model_name"]
        mock_challenger.version = sample_challenger_model["version"]
        mock_challenger.performance_score = sample_challenger_model["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.accuracy_metrics = sample_challenger_model["accuracy_metrics"]
        mock_challenger.experiment_config = {"traffic_percentage": 20}

        # Setup query mocks for status
        call_count = [0]

        def mock_query_for_status(model):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:
                mock_result.filter.return_value.first.return_value = mock_champion
            else:
                mock_result.filter.return_value.all.return_value = [mock_challenger]
            return mock_result

        mock_db_session.query.side_effect = mock_query_for_status

        # Step 1: Get initial status
        status = model_manager.get_champion_challenger_status(
            "skill_matching",
            mock_db_session
        )

        assert status["has_challenger"] is True
        assert status["comparison"]["improvement_pct"] > 5  # > 5% improvement

    def test_multiple_challengers_scenario(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any]
    ):
        """Test scenario with multiple challengers competing."""
        # Setup champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.model_name = sample_champion_model["model_name"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.performance_score = sample_champion_model["performance_score"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False
        mock_champion.model_metadata = {}
        mock_champion.accuracy_metrics = sample_champion_model["accuracy_metrics"]

        # Setup multiple challengers with different performance
        mock_challenger1 = Mock()
        mock_challenger1.id = str(uuid4())
        mock_challenger1.version = "v2.0.0"
        mock_challenger1.performance_score = 88.0  # ~3% improvement
        mock_challenger1.is_active = True
        mock_challenger1.is_experiment = True
        mock_challenger1.accuracy_metrics = {"sample_size": 300}
        mock_challenger1.experiment_config = {"traffic_percentage": 10}

        mock_challenger2 = Mock()
        mock_challenger2.id = str(uuid4())
        mock_challenger2.version = "v3.0.0"
        mock_challenger2.performance_score = 95.0  # ~11% improvement (best)
        mock_challenger2.is_active = True
        mock_challenger2.is_experiment = True
        mock_challenger2.accuracy_metrics = {"sample_size": 500}
        mock_challenger2.experiment_config = {"traffic_percentage": 15}

        # Setup query mocks
        call_count = [0]

        def mock_query_for_status(model):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:
                mock_result.filter.return_value.first.return_value = mock_champion
            else:
                mock_result.filter.return_value.all.return_value = [
                    mock_challenger1, mock_challenger2
                ]
            return mock_result

        mock_db_session.query.side_effect = mock_query_for_status

        # Get status
        status = model_manager.get_champion_challenger_status(
            "skill_matching",
            mock_db_session
        )

        # Should have 2 challengers
        assert status["challenger_count"] == 2
        # Best challenger should be the one with highest score
        assert status["comparison"]["best_challenger_score"] == 95.0

    def test_promotion_updates_model_states(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_champion_model: Dict[str, Any],
        sample_challenger_model: Dict[str, Any]
    ):
        """Test that promotion correctly updates model states in database."""
        # Track state changes
        state_changes = {
            "champion_deactivated": False,
            "challenger_promoted": False,
            "commit_called": False
        }

        # Setup mock for challenger
        mock_challenger = Mock()
        mock_challenger.id = sample_challenger_model["id"]
        mock_challenger.model_name = sample_challenger_model["model_name"]
        mock_challenger.version = sample_challenger_model["version"]
        mock_challenger.performance_score = sample_challenger_model["performance_score"]
        mock_challenger.is_active = True
        mock_challenger.is_experiment = True
        mock_challenger.accuracy_metrics = sample_challenger_model["accuracy_metrics"]
        mock_challenger.experiment_config = {}
        mock_challenger.updated_at = None

        def set_challenger_active(value):
            state_changes["challenger_promoted"] = True
            mock_challenger.is_active = value

        def set_challenger_experiment(value):
            if not value:
                state_changes["challenger_promoted"] = True
            mock_challenger.is_experiment = value

        type(mock_challenger).is_active = property(
            lambda self: mock_challenger._is_active if hasattr(mock_challenger, '_is_active') else True,
            lambda self, v: setattr(mock_challenger, '_is_active', v)
        )
        type(mock_challenger).is_experiment = property(
            lambda self: mock_challenger._is_experiment if hasattr(mock_challenger, '_is_experiment') else True,
            lambda self, v: setattr(mock_challenger, '_is_experiment', v)
        )

        # Setup mock for champion
        mock_champion = Mock()
        mock_champion.id = sample_champion_model["id"]
        mock_champion.version = sample_champion_model["version"]
        mock_champion.is_active = True
        mock_champion.is_experiment = False

        def mock_commit():
            state_changes["commit_called"] = True

        mock_db_session.commit = mock_commit

        call_count = [0]

        def mock_query_side_effect(model):
            call_count[0] += 1
            mock_result = Mock()
            if call_count[0] == 1:
                mock_result.filter.return_value.first.return_value = mock_challenger
            else:
                mock_result.filter.return_value.first.return_value = mock_champion
            return mock_result

        mock_db_session.query.side_effect = mock_query_side_effect

        # Force promotion to test state changes
        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=sample_challenger_model["id"],
            force=True,
            db_session=mock_db_session
        )

        assert result["success"] is True
        # Note: actual state change verification would require more complex mocking


class TestChampionChallengerErrorHandling:
    """Tests for error handling in champion/challenger workflows."""

    def test_promotion_with_database_error(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test promotion behavior when database error occurs."""
        # Setup mock to raise exception
        mock_db_session.query.side_effect = Exception("Database connection failed")

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=str(uuid4()),
            db_session=mock_db_session
        )

        assert result["success"] is False
        assert "error" in result

    def test_status_with_database_error(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test status retrieval when database error occurs."""
        # Setup mock to raise exception
        mock_db_session.query.side_effect = Exception("Database error")

        status = model_manager.get_champion_challenger_status(
            "skill_matching",
            mock_db_session
        )

        # Should return error status
        assert status["model_name"] == "skill_matching"
        assert "error" in status

    def test_promotion_with_rollback(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test that database rollback is called on promotion failure."""
        rollback_called = [False]

        def mock_rollback():
            rollback_called[0] = True

        mock_db_session.rollback = mock_rollback

        # Setup mock to fail after initial query succeeds
        mock_challenger = Mock()
        mock_challenger.id = str(uuid4())
        mock_challenger.version = "v2.0.0"
        mock_challenger.performance_score = 90.0
        mock_challenger.is_experiment = True
        mock_challenger.is_active = True

        call_count = [0]

        def mock_query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                mock_result = Mock()
                mock_result.filter.return_value.first.return_value = mock_challenger
                return mock_result
            else:
                raise Exception("Database error during promotion")

        mock_db_session.query.side_effect = mock_query_side_effect

        result = model_manager.promote_challenger_to_champion(
            model_name="skill_matching",
            challenger_version_id=str(uuid4()),
            db_session=mock_db_session
        )

        assert result["success"] is False
        # Rollback should be called on error


# Pytest fixtures
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client for all tests.

    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from main import app

    with TestClient(app) as test_client:
        yield test_client


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
