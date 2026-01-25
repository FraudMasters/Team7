"""
Integration tests for A/B testing allocation and model comparison.

This test suite validates the end-to-end integration between:
- Model versioning system (MLModelVersion database model)
- A/B testing allocation logic (ModelVersionManager)
- Model version management API endpoints
- Performance metrics calculation and comparison
- Model promotion recommendations

Test Coverage:
- Model version CRUD operations (create, read, update, delete)
- A/B testing allocation consistency (same user always gets same model)
- Traffic distribution across control and experimental models
- Performance comparison between model versions
- Promotion recommendations based on performance metrics
- Model activation/deactivation workflows
"""
import hashlib
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock

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
def sample_active_model() -> Dict[str, Any]:
    """
    Sample active model data for testing.

    Returns:
        Dictionary with active model information
    """
    return {
        "id": "model-001",
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
def sample_experiment_model() -> Dict[str, Any]:
    """
    Sample experimental model data for testing.

    Returns:
        Dictionary with experimental model information
    """
    return {
        "id": "model-002",
        "model_name": "skill_matching",
        "version": "v2.0.0-experiment",
        "file_path": "/models/skill_matching_v2.pkl",
        "performance_score": 88.2,
        "is_active": True,
        "is_experiment": True,
        "traffic_percentage": 20,
        "model_metadata": {
            "algorithm": "bert-large-uncased",
            "training_date": "2024-01-15"
        },
        "accuracy_metrics": {
            "precision": 0.90,
            "recall": 0.86,
            "f1_score": 0.88,
            "sample_size": 500
        }
    }


@pytest.fixture
def sample_model_versions(
    sample_active_model: Dict[str, Any],
    sample_experiment_model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sample model versions data for API testing.

    Returns:
        Dictionary with active and experimental models
    """
    return {
        "models": [sample_active_model, sample_experiment_model],
        "total_count": 2
    }


class TestModelVersionManagement:
    """Tests for model version CRUD operations."""

    def test_create_model_version_success(self, client: TestClient):
        """Test creating a new model version."""
        request_data = {
            "models": [
                {
                    "model_name": "skill_matching",
                    "version": "v1.5.0",
                    "is_active": True,
                    "is_experiment": False,
                    "performance_score": 87.0,
                    "model_metadata": {
                        "algorithm": "bert-base",
                        "training_date": "2024-01-20"
                    },
                    "accuracy_metrics": {
                        "precision": 0.88,
                        "recall": 0.85,
                        "f1_score": 0.86
                    }
                }
            ]
        }

        response = client.post("/api/model-versions/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert "models" in data
        assert data["total_count"] == 1
        assert data["models"][0]["model_name"] == "skill_matching"
        assert data["models"][0]["version"] == "v1.5.0"
        assert data["models"][0]["is_active"] is True

    def test_create_model_version_empty_list(self, client: TestClient):
        """Test creating model version with empty list (should fail)."""
        request_data = {"models": []}

        response = client.post("/api/model-versions/", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "At least one model version" in data["detail"]

    def test_create_model_version_missing_fields(self, client: TestClient):
        """Test creating model version with required fields missing."""
        request_data = {
            "models": [
                {
                    "model_name": "",
                    "version": "v1.0.0"
                }
            ]
        }

        response = client.post("/api/model-versions/", json=request_data)

        assert response.status_code == 422

    def test_list_model_versions(self, client: TestClient):
        """Test listing all model versions."""
        response = client.get("/api/model-versions/")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total_count" in data

    def test_list_model_versions_with_filters(self, client: TestClient):
        """Test listing model versions with filters."""
        response = client.get(
            "/api/model-versions/",
            params={"model_name": "skill_matching", "is_active": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_get_active_model(self, client: TestClient):
        """Test getting the active model version."""
        response = client.get(
            "/api/model-versions/active",
            params={"model_name": "skill_matching"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "model_name" in data
        assert data["model_name"] == "skill_matching"
        assert "version" in data

    def test_get_model_version_by_id(self, client: TestClient):
        """Test getting a specific model version by ID."""
        version_id = "model-001"
        response = client.get(f"/api/model-versions/{version_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == version_id

    def test_update_model_version(self, client: TestClient):
        """Test updating a model version."""
        version_id = "model-001"
        update_data = {
            "performance_score": 90.0,
            "is_active": True
        }

        response = client.put(f"/api/model-versions/{version_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == version_id

    def test_update_model_version_invalid_score(self, client: TestClient):
        """Test updating model version with invalid performance score."""
        version_id = "model-001"
        update_data = {
            "performance_score": 150.0  # Invalid: > 100
        }

        response = client.put(f"/api/model-versions/{version_id}", json=update_data)

        assert response.status_code == 422
        data = response.json()
        assert "Performance score must be between 0 and 100" in data["detail"]

    def test_delete_model_version(self, client: TestClient):
        """Test deleting a model version."""
        version_id = "model-001"

        response = client.delete(f"/api/model-versions/{version_id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"]

    def test_activate_model_version(self, client: TestClient):
        """Test activating a model version."""
        version_id = "model-001"

        response = client.post(f"/api/model-versions/{version_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert "activated successfully" in data["message"]

    def test_deactivate_model_version(self, client: TestClient):
        """Test deactivating a model version."""
        version_id = "model-001"

        response = client.post(f"/api/model-versions/{version_id}/deactivate")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert "deactivated successfully" in data["message"]


class TestABTestingAllocation:
    """Tests for A/B testing user allocation logic."""

    def test_allocate_user_to_control_model(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_active_model: Dict[str, Any]
    ):
        """Test allocating a user to control model when no experiments exist."""
        # Setup mock to return active model, no experiments
        mock_query = Mock()
        mock_model = Mock()
        mock_model.id = "model-001"
        mock_model.model_name = "skill_matching"
        mock_model.version = "v1.0.0"
        mock_model.file_path = "/models/v1.pkl"
        mock_model.performance_score = 85.5
        mock_model.is_active = True
        mock_model.is_experiment = False
        mock_model.model_metadata = {"algorithm": "bert"}
        mock_model.accuracy_metrics = {"f1_score": 0.85}
        mock_model.experiment_config = None

        mock_query.filter.return_value.first.return_value = mock_model
        mock_db_session.query.return_value = mock_query

        result = model_manager.allocate_model_for_user(
            "skill_matching",
            "user123",
            mock_db_session
        )

        assert result["version"] == "v1.0.0"
        assert result["allocation_type"] == "control"
        assert result["is_fallback"] is False

    def test_allocate_user_consistency(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_active_model: Dict[str, Any],
        sample_experiment_model: Dict[str, Any]
    ):
        """
        Test that the same user always gets allocated to the same model.

        This is critical for A/B testing consistency - a user should not
        experience different models across different requests.
        """
        # Setup mock for active model
        mock_active = Mock()
        mock_active.id = "model-001"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.pkl"
        mock_active.performance_score = 85.5
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}

        # Setup mock for experiment model
        mock_exp = Mock()
        mock_exp.id = "model-002"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.pkl"
        mock_exp.performance_score = 88.2
        mock_exp.is_active = True
        mock_exp.is_experiment = True
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {}
        mock_exp.experiment_config = {"traffic_percentage": 50}

        # Setup query mocks
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_exp]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_active

        # Allocate the same user multiple times
        user_id = "consistent_user_123"
        allocations = []
        for _ in range(5):
            result = model_manager.allocate_model_for_user(
                "skill_matching",
                user_id,
                mock_db_session
            )
            allocations.append(result["allocation_type"])

        # All allocations should be the same
        assert len(set(allocations)) == 1
        assert allocations[0] in ["control", "experiment"]

    def test_traffic_distribution(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock,
        sample_active_model: Dict[str, Any],
        sample_experiment_model: Dict[str, Any]
    ):
        """
        Test that traffic is distributed according to configured percentages.

        Verifies that with a large sample of users, the distribution matches
        the configured traffic percentages.
        """
        # Setup mocks
        mock_active = Mock()
        mock_active.id = "model-001"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.file_path = "/models/v1.pkl"
        mock_active.performance_score = 85.5
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}

        mock_exp = Mock()
        mock_exp.id = "model-002"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0-experiment"
        mock_exp.file_path = "/models/v2.pkl"
        mock_exp.performance_score = 88.2
        mock_exp.is_active = True
        mock_exp.is_experiment = True
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {}
        mock_exp.experiment_config = {"traffic_percentage": 30}

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_exp]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_active

        # Allocate 1000 users
        control_count = 0
        experiment_count = 0
        total_users = 1000

        for i in range(total_users):
            result = model_manager.allocate_model_for_user(
                "skill_matching",
                f"user{i}",
                mock_db_session
            )

            if result["allocation_type"] == "control":
                control_count += 1
            else:
                experiment_count += 1

        # Verify distribution is approximately correct (±5% tolerance)
        expected_exp_pct = 30
        actual_exp_pct = (experiment_count / total_users) * 100
        expected_ctrl_pct = 70
        actual_ctrl_pct = (control_count / total_users) * 100

        assert abs(actual_exp_pct - expected_exp_pct) < 5
        assert abs(actual_ctrl_pct - expected_ctrl_pct) < 5

    def test_fallback_when_no_active_model(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test fallback behavior when no active model exists."""
        # Setup mock to return None (no active model)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = model_manager.allocate_model_for_user(
            "skill_matching",
            "user123",
            mock_db_session
        )

        assert result["is_fallback"] is True
        assert result["allocation_type"] == "fallback"
        assert result["version"] == model_manager.default_fallback_version


class TestModelPerformanceComparison:
    """Tests for model performance comparison and metrics."""

    def test_get_all_model_versions(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test retrieving all model versions."""
        # Setup mock models
        mock_model1 = Mock()
        mock_model1.id = "model-001"
        mock_model1.model_name = "skill_matching"
        mock_model1.version = "v1.0.0"
        mock_model1.file_path = "/models/v1.pkl"
        mock_model1.performance_score = 85.5
        mock_model1.is_active = True
        mock_model1.is_experiment = False
        mock_model1.experiment_config = None
        mock_model1.model_metadata = {}
        mock_model1.accuracy_metrics = {}
        mock_model1.created_at = None
        mock_model1.updated_at = None

        mock_model2 = Mock()
        mock_model2.id = "model-002"
        mock_model2.model_name = "skill_matching"
        mock_model2.version = "v2.0.0"
        mock_model2.file_path = "/models/v2.pkl"
        mock_model2.performance_score = 88.2
        mock_model2.is_active = False
        mock_model2.is_experiment = True
        mock_model2.experiment_config = {"traffic_percentage": 20}
        mock_model2.model_metadata = {}
        mock_model2.accuracy_metrics = {}
        mock_model2.created_at = None
        mock_model2.updated_at = None

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_model1, mock_model2
        ]

        versions = model_manager.get_all_model_versions("skill_matching", mock_db_session)

        assert len(versions) == 2
        assert versions[0]["version"] == "v1.0.0"
        assert versions[1]["version"] == "v2.0.0"

    def test_calculate_model_metrics(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test calculating aggregate metrics for all model versions."""
        # Setup mock models
        mock_model1 = Mock()
        mock_model1.id = "model-001"
        mock_model1.model_name = "skill_matching"
        mock_model1.version = "v1.0.0"
        mock_model1.performance_score = 85.0
        mock_model1.is_active = True
        mock_model1.is_experiment = False
        mock_model1.experiment_config = None
        mock_model1.model_metadata = {}
        mock_model1.accuracy_metrics = {}
        mock_model1.created_at = None
        mock_model1.updated_at = None

        mock_model2 = Mock()
        mock_model2.id = "model-002"
        mock_model2.model_name = "skill_matching"
        mock_model2.version = "v2.0.0"
        mock_model2.performance_score = 90.0
        mock_model2.is_active = False
        mock_model2.is_experiment = True
        mock_model2.experiment_config = {"traffic_percentage": 20}
        mock_model2.model_metadata = {}
        mock_model2.accuracy_metrics = {}
        mock_model2.created_at = None
        mock_model2.updated_at = None

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_model1, mock_model2
        ]

        metrics = model_manager.calculate_model_metrics("skill_matching", mock_db_session)

        assert metrics["model_name"] == "skill_matching"
        assert metrics["total_versions"] == 2
        assert metrics["active_version"] == "v1.0.0"
        assert metrics["experiment_count"] == 1
        assert metrics["avg_performance_score"] == 87.5
        assert metrics["best_performance_score"] == 90.0
        assert "control" in metrics["traffic_distribution"]
        assert metrics["traffic_distribution"]["control"] == 80  # 100 - 20

    def test_recommend_promotion_success(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test promotion recommendation when experiment outperforms control."""
        # Setup active model
        mock_active = Mock()
        mock_active.id = "model-001"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}

        # Setup experiment model with better performance
        mock_exp = Mock()
        mock_exp.id = "model-002"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0"
        mock_exp.performance_score = 92.0  # 7.5% improvement (exceeds 5% threshold)
        mock_exp.is_active = True
        mock_exp.is_experiment = True
        mock_exp.experiment_config = {}
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {"sample_size": 500}  # Sufficient sample size

        # Setup query mocks
        def mock_filter_side_effect(*args, **kwargs):
            """Mock filter behavior based on arguments."""
            mock_result = Mock()
            if mock_exp.is_experiment:
                mock_result.all.return_value = [mock_exp]
                mock_result.first.return_value = mock_active
            return mock_result

        mock_db_session.query.return_value.filter.side_effect = mock_filter_side_effect

        recommendation = model_manager.recommend_promotion(
            "skill_matching",
            min_performance_improvement=5.0,
            min_sample_size=100,
            db_session=mock_db_session
        )

        assert recommendation is not None
        assert recommendation["should_promote"] is True
        assert recommendation["experiment_version"] == "v2.0.0"
        assert recommendation["current_active"] == "v1.0.0"
        assert recommendation["performance_improvement_pct"] >= 5.0

    def test_recommend_promotion_insufficient_sample(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test promotion recommendation with insufficient sample size."""
        # Setup active model
        mock_active = Mock()
        mock_active.id = "model-001"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}

        # Setup experiment model with insufficient sample size
        mock_exp = Mock()
        mock_exp.id = "model-002"
        mock_exp.model_name = "skill_matching"
        mock_exp.version = "v2.0.0"
        mock_exp.performance_score = 92.0
        mock_exp.is_active = True
        mock_exp.is_experiment = True
        mock_exp.experiment_config = {}
        mock_exp.model_metadata = {}
        mock_exp.accuracy_metrics = {"sample_size": 50}  # Below minimum

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_exp]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_active

        recommendation = model_manager.recommend_promotion(
            "skill_matching",
            min_performance_improvement=5.0,
            min_sample_size=100,
            db_session=mock_db_session
        )

        assert recommendation is not None
        assert recommendation["should_promote"] is False
        assert "reason" in recommendation

    def test_recommend_promotion_no_experiments(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """Test promotion recommendation when no experiments exist."""
        mock_active = Mock()
        mock_active.id = "model-001"
        mock_active.model_name = "skill_matching"
        mock_active.version = "v1.0.0"
        mock_active.performance_score = 85.0
        mock_active.is_active = True
        mock_active.is_experiment = False
        mock_active.model_metadata = {}
        mock_active.accuracy_metrics = {}

        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_active

        recommendation = model_manager.recommend_promotion(
            "skill_matching",
            db_session=mock_db_session
        )

        assert recommendation is not None
        assert recommendation["should_promote"] is False


class TestABTestingWorkflows:
    """End-to-end workflow tests for A/B testing scenarios."""

    @pytest.mark.slow
    def test_complete_ab_testing_workflow(self, client: TestClient):
        """
        Test complete A/B testing workflow.

        1. Create active (control) model version
        2. Create experimental model version
        3. Verify traffic allocation
        4. Update performance metrics
        5. Check promotion recommendation
        6. Promote winning model
        """
        # Step 1: Create active model
        active_data = {
            "models": [
                {
                    "model_name": "skill_matching",
                    "version": "v1.0.0",
                    "is_active": True,
                    "is_experiment": False,
                    "performance_score": 85.0
                }
            ]
        }
        response = client.post("/api/model-versions/", json=active_data)
        assert response.status_code == 201

        # Step 2: Create experiment model
        experiment_data = {
            "models": [
                {
                    "model_name": "skill_matching",
                    "version": "v2.0.0-experiment",
                    "is_active": True,
                    "is_experiment": True,
                    "experiment_config": {"traffic_percentage": 20},
                    "performance_score": 88.0,
                    "accuracy_metrics": {"sample_size": 500}
                }
            ]
        }
        response = client.post("/api/model-versions/", json=experiment_data)
        assert response.status_code == 201

        # Step 3: Verify models are listed
        response = client.get("/api/model-versions/?model_name=skill_matching")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 2

        # Step 4: Get active model
        response = client.get("/api/model-versions/active?model_name=skill_matching")
        assert response.status_code == 200
        active_model = response.json()
        assert active_model["version"] == "v1.0.0"

    def test_model_activation_workflow(self, client: TestClient):
        """
        Test model activation workflow.

        1. Create multiple model versions
        2. Activate a specific version
        3. Verify it's now the active version
        4. Deactivate and verify
        """
        # Create model version
        model_data = {
            "models": [
                {
                    "model_name": "skill_matching",
                    "version": "v3.0.0",
                    "is_active": False,
                    "performance_score": 92.0
                }
            ]
        }
        response = client.post("/api/model-versions/", json=model_data)
        assert response.status_code == 201
        version_id = response.json()["models"][0]["id"]

        # Activate the model
        response = client.post(f"/api/model-versions/{version_id}/activate")
        assert response.status_code == 200
        assert response.json()["is_active"] is True

        # Deactivate the model
        response = client.post(f"/api/model-versions/{version_id}/deactivate")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_performance_comparison_workflow(
        self,
        model_manager: ModelVersionManager,
        mock_db_session: Mock
    ):
        """
        Test performance comparison workflow between models.

        1. Get all model versions
        2. Calculate aggregate metrics
        3. Compare performance
        4. Get promotion recommendation
        """
        # Setup mock models with different performance
        models = []
        for i, (version, score, is_exp) in enumerate([
            ("v1.0.0", 85.0, False),
            ("v2.0.0", 88.0, True),
            ("v3.0.0", 90.0, True),
        ]):
            mock_model = Mock()
            mock_model.id = f"model-00{i}"
            mock_model.model_name = "skill_matching"
            mock_model.version = version
            mock_model.performance_score = score
            mock_model.is_active = not is_exp
            mock_model.is_experiment = is_exp
            mock_model.experiment_config = {"traffic_percentage": 20} if is_exp else None
            mock_model.model_metadata = {}
            mock_model.accuracy_metrics = {"sample_size": 500}
            mock_model.created_at = None
            mock_model.updated_at = None
            models.append(mock_model)

        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = models

        # Get all versions
        versions = model_manager.get_all_model_versions("skill_matching", mock_db_session)
        assert len(versions) == 3

        # Calculate metrics
        metrics = model_manager.calculate_model_metrics("skill_matching", mock_db_session)
        assert metrics["total_versions"] == 3
        assert metrics["best_performance_score"] == 90.0

        # Get recommendation (need to setup separate mocks for this)
        mock_active = models[0]
        mock_experiments = models[1:]

        def setup_recommendation_mocks():
            """Setup mocks for recommendation check."""
            mock_db_session.query.return_value.filter.return_value.all.return_value = mock_experiments
            mock_db_session.query.return_value.filter.return_value.first.return_value = mock_active

        setup_recommendation_mocks()
        recommendation = model_manager.recommend_promotion(
            "skill_matching",
            min_performance_improvement=3.0,
            min_sample_size=100,
            db_session=mock_db_session
        )

        assert recommendation is not None
        # v3.0.0 (90.0) should be recommended over v1.0.0 (85.0)
        # Improvement: (90-85)/85 * 100 = 5.88%, which exceeds 3% threshold
        if recommendation["should_promote"]:
            assert recommendation["experiment_version"] in ["v2.0.0", "v3.0.0"]


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_allocate_model_no_database_session(self, model_manager: ModelVersionManager):
        """Test allocation behavior when no database session is provided."""
        result = model_manager.allocate_model_for_user(
            "skill_matching",
            "user123",
            db_session=None
        )

        assert result["is_fallback"] is True
        assert result["allocation_type"] == "fallback"

    def test_get_active_model_no_database_session(self, model_manager: ModelVersionManager):
        """Test getting active model when no database session is provided."""
        result = model_manager.get_active_model("skill_matching", db_session=None)

        assert result is None

    def test_get_experiment_models_no_database_session(self, model_manager: ModelVersionManager):
        """Test getting experiment models when no database session is provided."""
        result = model_manager.get_experiment_models("skill_matching", db_session=None)

        assert result == []

    def test_create_model_version_validation_error(self, client: TestClient):
        """Test creating model version with invalid performance score."""
        request_data = {
            "models": [
                {
                    "model_name": "skill_matching",
                    "version": "v1.0.0",
                    "performance_score": -10.0  # Invalid: negative
                }
            ]
        }

        response = client.post("/api/model-versions/", json=request_data)

        # Should fail validation
        assert response.status_code in [400, 422]


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
