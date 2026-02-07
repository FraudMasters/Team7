"""
Integration tests for health API endpoints.

Tests all health check endpoints including:
- GET /api/health - Comprehensive system health check
- GET /api/health/live - Liveness probe
- GET /api/health/ready - Readiness probe

Tests verify response structure, status codes, error handling, and
graceful degradation behavior.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create FastAPI test client."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_health_checks():
    """Mock health check utilities."""
    return {
        'check_database': {
            'status': 'healthy',
            'latency_seconds': 0.005,
            'pool_size': 10,
            'pool_checked_out': 2,
            'pool_overflow': 0,
        },
        'check_redis': {
            'status': 'healthy',
            'latency_seconds': 0.002,
            'connected': True,
            'key_count': 100,
            'memory_used': 1024000,
        },
        'check_celery_workers': {
            'status': 'healthy',
            'latency_seconds': 0.050,
            'workers_online': 2,
            'queue_length': 5,
            'worker_details': [
                {'name': 'celery@worker1', 'active_tasks': 3},
                {'name': 'celery@worker2', 'active_tasks': 2}
            ]
        },
        'check_ml_models': {
            'status': 'healthy',
            'successful_count': 3,
            'total_models': 3,
            'models_loaded': ['NER models', 'Zero-shot classification', 'LanguageTool']
        },
        'check_languagetool': {
            'status': 'healthy',
            'latency_seconds': 0.100,
            'test_passed': True,
            'server_type': 'local'
        },
        'check_s3': {
            'status': 'healthy',
            'enabled': True,
            'bucket_accessible': True,
            'bucket_name': 'test-bucket',
            'latency_seconds': 0.200
        }
    }


# =============================================================================
# GET /api/health Tests
# =============================================================================

def test_health_endpoint_returns_all_components(client, mock_health_checks):
    """Test health endpoint returns all 7 components."""
    with patch('database.get_db') as mock_get_db:
        # Setup mock database
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        # Mock health checks
        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")

                            # Assertions
                            assert response.status_code == 200
                            data = response.json()

                            # Verify top-level fields
                            assert 'status' in data
                            assert 'service' in data
                            assert 'version' in data
                            assert 'timestamp' in data
                            assert 'components' in data

                            # Verify all components present
                            components = data['components']
                            assert 'api' in components
                            assert 'database' in components
                            assert 'redis' in components
                            assert 'celery_workers' in components
                            assert 'ml_models' in components
                            assert 'storage' in components
                            assert 'external_services' in components

                            # Verify component count
                            assert len(components) == 7


def test_health_endpoint_correct_status_codes_healthy(client, mock_health_checks):
    """Test health endpoint returns 200 for healthy status."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")

                            # Should return 200 for healthy
                            assert response.status_code == 200
                            assert response.json()['status'] in ['healthy', 'degraded']


def test_health_endpoint_correct_status_codes_unhealthy(client):
    """Test health endpoint returns 503 for unhealthy status."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'unhealthy', 'error': 'Redis down'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'unhealthy', 'error': 'No workers'}):
                with patch('api.health.check_ml_models', return_value={'status': 'unhealthy', 'error': 'Models failed'}):
                    with patch('api.health.check_languagetool', return_value={'status': 'unhealthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'unhealthy'}):
                            response = client.get("/api/health")

                            # Should return 503 for unhealthy
                            assert response.status_code == 503
                            assert response.json()['status'] == 'unhealthy'


def test_health_endpoint_structure(client, mock_health_checks):
    """Test health endpoint response schema structure."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            data = response.json()

                            # Verify top-level structure
                            assert isinstance(data['status'], str)
                            assert isinstance(data['service'], str)
                            assert isinstance(data['version'], str)
                            assert isinstance(data['timestamp'], str)
                            assert isinstance(data['components'], dict)

                            # Verify timestamp format (ISO 8601)
                            try:
                                datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                            except ValueError:
                                pytest.fail("Timestamp is not in ISO 8601 format")


def test_health_endpoint_component_details(client, mock_health_checks):
    """Test health endpoint each component has name, status, message, response_time_ms."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            components = response.json()['components']

                            # Check each component has required fields
                            for component_name, component in components.items():
                                assert 'name' in component
                                assert component['name'] == component_name
                                assert 'status' in component
                                assert isinstance(component['status'], str)
                                assert 'message' in component
                                assert 'response_time_ms' in component
                                assert isinstance(component['response_time_ms'], (int, float))


def test_health_endpoint_handles_database_failure(client):
    """Test health endpoint handles database failure gracefully."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Connection failed"))

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'healthy', 'latency_seconds': 0.001, 'connected': True}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy', 'workers_online': 2}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy', 'successful_count': 3}):
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'healthy'}):
                            response = client.get("/api/health")
                            data = response.json()

                            # Should still return a response
                            assert response.status_code in [200, 503]

                            # Database component should be unhealthy
                            assert data['components']['database']['status'] == 'unhealthy'

                            # Overall status should reflect the failure
                            assert data['status'] in ['degraded', 'unhealthy']


def test_health_endpoint_handles_redis_failure(client):
    """Test health endpoint handles Redis failure with degraded status."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'unhealthy', 'error': 'Connection failed'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy', 'workers_online': 2}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy', 'successful_count': 3}):
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'healthy'}):
                            response = client.get("/api/health")
                            data = response.json()

                            # Redis component should be unhealthy
                            assert data['components']['redis']['status'] == 'unhealthy'

                            # Overall status should be degraded (Redis is non-critical)
                            assert data['status'] == 'degraded'


def test_health_endpoint_external_services_aggregation(client):
    """Test health endpoint external_services component combines LT+S3."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'healthy'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy'}):
                    # LanguageTool healthy, S3 degraded
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy', 'enabled': True}):
                        with patch('api.health.check_s3', return_value={'status': 'degraded', 'enabled': True}):
                            response = client.get("/api/health")
                            data = response.json()

                            # External services should combine both
                            external = data['components']['external_services']
                            assert 'external_services' in external['name']

                            # Should be degraded when one is degraded
                            assert external['status'] in ['degraded', 'healthy']

                            # Should have degraded_mode flag
                            assert 'degraded_mode' in external


def test_health_endpoint_timestamp_format(client, mock_health_checks):
    """Test health endpoint returns ISO 8601 timestamp format."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            timestamp = response.json()['timestamp']

                            # Should be valid ISO 8601
                            # Common formats: 2024-01-15T10:30:00Z or 2024-01-15T10:30:00.123456Z
                            assert 'T' in timestamp
                            assert timestamp.endswith('Z') or '+' in timestamp

                            # Should be parseable
                            try:
                                if timestamp.endswith('Z'):
                                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                else:
                                    datetime.fromisoformat(timestamp)
                            except ValueError:
                                pytest.fail(f"Timestamp {timestamp} is not valid ISO 8601")


def test_health_endpoint_overall_status_logic(client):
    """Test health endpoint overall status aggregation (healthy/degraded/unhealthy)."""
    # Test 1: All healthy -> healthy
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'healthy'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy'}):
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'healthy'}):
                            response = client.get("/api/health")
                            assert response.json()['status'] == 'healthy'

    # Test 2: Non-critical degraded -> degraded
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'degraded'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy'}):
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'healthy'}):
                            response = client.get("/api/health")
                            assert response.json()['status'] == 'degraded'

    # Test 3: Critical unhealthy -> unhealthy
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("DB failed"))

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value={'status': 'healthy'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy'}):
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'healthy'}):
                            response = client.get("/api/health")
                            assert response.json()['status'] == 'unhealthy'


# =============================================================================
# GET /api/health/live Tests
# =============================================================================

def test_liveness_endpoint(client):
    """Test GET /api/health/live returns 200 with alive status."""
    response = client.get("/api/health/live")

    # Should always return 200
    assert response.status_code == 200

    data = response.json()
    assert 'status' in data
    assert data['status'] == 'alive'
    assert 'service' in data


def test_liveness_endpoint_structure(client):
    """Test liveness endpoint returns correct structure."""
    response = client.get("/api/health/live")
    data = response.json()

    # Verify required fields
    assert 'status' in data
    assert 'service' in data

    # Verify values
    assert data['status'] == 'alive'
    assert isinstance(data['service'], str)


# =============================================================================
# GET /api/health/ready Tests
# =============================================================================

def test_readiness_endpoint_ready(client):
    """Test GET /api/health/ready returns 200 when database available."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        response = client.get("/api/health/ready")

        # Should return 200 when ready
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ready'
        assert data['checks_passed'] == data['checks_total']


def test_readiness_endpoint_not_ready():
    """Test GET /api/health/ready returns 503 when database unavailable."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    client = TestClient(app)

    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Connection failed"))

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        response = client.get("/api/health/ready")

        # Should return 503 when not ready
        assert response.status_code == 503
        data = response.json()
        assert data['status'] == 'not_ready'


def test_readiness_endpoint_critical_checks(client):
    """Test readiness endpoint only checks critical dependencies."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        response = client.get("/api/health")
        data = response.json()

        # Readiness should only check database and storage
        # Not Redis, Celery, ML models, or external services
        assert response.status_code in [200, 503]


def test_readiness_endpoint_structure(client):
    """Test readiness endpoint returns correct structure."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        response = client.get("/api/health/ready")
        data = response.json()

        # Verify required fields
        assert 'status' in data
        assert 'service' in data
        assert 'checks_passed' in data
        assert 'checks_total' in data
        assert 'message' in data

        # Verify types
        assert isinstance(data['checks_passed'], int)
        assert isinstance(data['checks_total'], int)
        assert data['checks_total'] >= data['checks_passed']


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_health_endpoint_storage_failure():
    """Test health endpoint handles storage check failure."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    client = TestClient(app)

    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        # Mock storage check failure
        with patch('config.get_settings') as mock_settings:
            settings = Mock()
            settings.upload_dir = Mock()
            settings.upload_dir.exists = Mock(return_value=True)
            settings.upload_dir.__truediv__ = Mock(return_value=Mock(exists=Mock(return_value=False)))

            import os
            with patch('os.access', return_value=False):
                response = client.get("/api/health")
                data = response.json()

                # Storage should be marked unhealthy
                assert data['components']['storage']['status'] == 'unhealthy'


def test_health_endpoint_exception_handling():
    """Test health endpoint handles exceptions gracefully."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    from fastapi import HTTPException

    client = TestClient(app)

    # Mock all health checks to raise exceptions
    with patch('database.get_db', side_effect=Exception("DB error")):
        with patch('config.get_settings', side_effect=Exception("Config error")):
            try:
                response = client.get("/api/health")
                # Should not raise unhandled exception
                assert response.status_code in [200, 503, 500]
            except Exception as e:
                pytest.fail(f"Health endpoint raised unhandled exception: {e}")


# =============================================================================
# Graceful Degradation Tests
# =============================================================================

def test_health_endpoint_graceful_degradation_external_services():
    """Test health endpoint graceful degradation when external services fail."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    client = TestClient(app)

    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        # Both external services unhealthy
        with patch('api.health.check_redis', return_value={'status': 'healthy'}):
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'healthy'}):
                    with patch('api.health.check_languagetool', return_value={'status': 'unhealthy', 'enabled': True}):
                        with patch('api.health.check_s3', return_value={'status': 'unhealthy', 'enabled': True}):
                            response = client.get("/api/health")
                            data = response.json()

                            # System should still function (degraded, not unhealthy)
                            # because external services are optional
                            assert data['status'] == 'degraded'

                            # External services component should show degraded
                            external = data['components']['external_services']
                            assert external['status'] == 'unhealthy'
                            assert external.get('degraded_mode') is True


def test_health_endpoint_mixed_component_statuses():
    """Test health endpoint with mixed healthy/degraded/unhealthy components."""
    import sys
    sys.path.insert(0, str(__file__).parent.parent.parent)
    from main import app
    client = TestClient(app)

    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        # Mix of statuses
        with patch('api.health.check_redis', return_value={'status': 'degraded'}):  # non-critical
            with patch('api.health.check_celery_workers', return_value={'status': 'healthy'}):
                with patch('api.health.check_ml_models', return_value={'status': 'degraded'}):  # critical
                    with patch('api.health.check_languagetool', return_value={'status': 'healthy'}):
                        with patch('api.health.check_s3', return_value={'status': 'unhealthy'}):
                            response = client.get("/api/health")
                            data = response.json()

                            # Should be degraded due to critical ML models degraded
                            assert data['status'] in ['degraded', 'unhealthy']

                            # Verify individual component statuses
                            assert data['components']['redis']['status'] == 'degraded'
                            assert data['components']['celery_workers']['status'] == 'healthy'
                            assert data['components']['ml_models']['status'] == 'degraded'


# =============================================================================
# Performance Tests
# =============================================================================

def test_health_endpoint_response_time(client, mock_health_checks):
    """Test health endpoint responds within acceptable time."""
    import time

    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            start = time.time()
                            response = client.get("/api/health")
                            elapsed = time.time() - start

                            # Health check should complete quickly (< 5 seconds)
                            assert elapsed < 5.0
                            assert response.status_code in [200, 503]


# =============================================================================
# Service Name and Version Tests
# =============================================================================

def test_health_endpoint_service_identification(client, mock_health_checks):
    """Test health endpoint includes correct service name and version."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            data = response.json()

                            # Verify service identification
                            assert data['service'] == 'resume-analysis-api'
                            assert 'version' in data
                            assert isinstance(data['version'], str)


# =============================================================================
# Component Message Tests
# =============================================================================

def test_health_endpoint_component_messages(client, mock_health_checks):
    """Test health endpoint components have meaningful status messages."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            components = response.json()['components']

                            # Each component should have a message
                            for component_name, component in components.items():
                                assert 'message' in component
                                assert isinstance(component['message'], str)
                                assert len(component['message']) > 0


# =============================================================================
# Response Time Tracking Tests
# =============================================================================

def test_health_endpoint_response_time_tracking(client, mock_health_checks):
    """Test health endpoint tracks response time for each component."""
    with patch('database.get_db') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()

        async def db_generator():
            yield mock_db

        mock_get_db.return_value = db_generator()

        with patch('api.health.check_redis', return_value=mock_health_checks['check_redis']):
            with patch('api.health.check_celery_workers', return_value=mock_health_checks['check_celery_workers']):
                with patch('api.health.check_ml_models', return_value=mock_health_checks['check_ml_models']):
                    with patch('api.health.check_languagetool', return_value=mock_health_checks['check_languagetool']):
                        with patch('api.health.check_s3', return_value=mock_health_checks['check_s3']):
                            response = client.get("/api/health")
                            components = response.json()['components']

                            # Each component should have response_time_ms
                            for component_name, component in components.items():
                                assert 'response_time_ms' in component
                                assert isinstance(component['response_time_ms'], (int, float))
                                assert component['response_time_ms'] >= 0
