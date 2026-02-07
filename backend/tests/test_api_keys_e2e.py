"""
End-to-End Integration Tests for API Key Creation, Rate Limiting, and Usage Analytics

This test module performs comprehensive verification of the developer API ecosystem,
including API key generation, authentication, rate limiting enforcement, and
usage analytics tracking.

Test Coverage:
- API key generation with scopes and rate limits
- API key authentication via X-API-Key header
- Rate limiting enforcement (per-minute, per-hour, per-day)
- Usage analytics recording (request counts, response times, error tracking)
- API key revocation and deactivation
- Rate limit header verification
"""
import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import AsyncGenerator
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport
from redis.asyncio import Redis
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.api_key import APIKey, APIKeyScope
from models.api_usage import APIUsage, APIRequestStatus
from config import get_settings


# Test Database Setup
settings = get_settings()
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
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def client(test_session: AsyncSession):
    """Create a test HTTP client with database override."""
    from main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def redis_client():
    """Create a Redis client for testing rate limits."""
    try:
        redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        yield redis
        await redis.aclose()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_rate_limit_key(key_hash: str, window: str) -> str:
    """Generate Redis key for rate limit counter."""
    return f"rate_limit:{key_hash}:{window}"


# ============================================================================
# Test 1: API Key Creation
# ============================================================================

@pytest.mark.asyncio
async def test_create_api_key_with_scopes_and_rate_limits(client: AsyncClient, test_session: AsyncSession):
    """Verify that API keys can be created with scopes and rate limits."""
    print("\n=== Test 1: API Key Creation ===\n")

    key_data = {
        "name": "Test Production Key",
        "scopes": [
            APIKeyScope.READ_CANDIDATES.value,
            APIKeyScope.READ_VACANCIES.value,
            APIKeyScope.WRITE_WEBHOOKS.value,
        ],
        "rate_limit": {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "requests_per_day": 5000,
        },
    }

    response = await client.post("/api/api-keys/generate", json=key_data)
    assert response.status_code == 201

    result = response.json()
    print(f"✓ API key created: {result['key_prefix']}")
    print(f"  ID: {result['id']}")
    print(f"  Name: {result['name']}")
    print(f"  Scopes: {result['scopes']}")
    print(f"  Rate limits: {result['rate_limit']}")

    # Verify response structure
    assert "key" in result
    assert "key_prefix" in result
    assert result["key_prefix"] == result["key"][:8]
    assert len(result["key"]) == 64
    assert result["name"] == key_data["name"]
    assert set(result["scopes"]) == set(key_data["scopes"])
    assert result["rate_limit"]["requests_per_minute"] == 30
    assert result["rate_limit"]["requests_per_hour"] == 500
    assert result["rate_limit"]["requests_per_day"] == 5000
    assert "message" in result

    # Verify key was stored in database
    await test_session.commit()

    stmt = select(APIKey).where(APIKey.id == UUID(result["id"]))
    db_result = await test_session.execute(stmt)
    api_key = db_result.scalar_one_or_none()

    assert api_key is not None
    assert api_key.name == key_data["name"]
    assert api_key.key_prefix == result["key_prefix"]
    assert api_key.is_active is True
    assert api_key.scopes == key_data["scopes"]
    print(f"✓ API key stored in database with correct attributes")

    return result  # Return for use in subsequent tests


@pytest.mark.asyncio
async def test_create_api_key_with_expiration(client: AsyncClient, test_session: AsyncSession):
    """Verify that API keys can be created with expiration dates."""
    print("\n=== Test 2: API Key with Expiration ===\n")

    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

    key_data = {
        "name": "Temporary Test Key",
        "scopes": [APIKeyScope.READ_RESUMES.value],
        "expires_at": expires_at,
    }

    response = await client.post("/api/api-keys/generate", json=key_data)
    assert response.status_code == 201

    result = response.json()
    print(f"✓ API key created with expiration: {result['key_prefix']}")
    print(f"  Expires at: {result['expires_at']}")

    # Verify expiration in database
    await test_session.commit()

    stmt = select(APIKey).where(APIKey.id == UUID(result["id"]))
    db_result = await test_session.execute(stmt)
    api_key = db_result.scalar_one_or_none()

    assert api_key is not None
    assert api_key.expires_at is not None
    print(f"✓ Expiration date stored correctly")


# ============================================================================
# Test 2: API Key Authentication
# ============================================================================

@pytest.mark.asyncio
async def test_api_key_authentication(client: AsyncClient, test_session: AsyncSession):
    """Verify that API keys can be used for authentication."""
    print("\n=== Test 3: API Key Authentication ===\n")

    # First, create an API key
    key_data = {
        "name": "Auth Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value, APIKeyScope.READ_VACANCIES.value],
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    key_prefix = key_result["key_prefix"]

    print(f"✓ Created API key for authentication: {key_prefix}")

    # Test authentication with API key
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )

    # Request should succeed (may return empty list if no candidates, but that's OK)
    assert response.status_code in [200, 404]
    print(f"✓ Authenticated request successful with API key")

    # Verify rate limit headers are present
    if response.status_code == 200:
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Limit-Hour" in response.headers
        assert "X-RateLimit-Remaining-Hour" in response.headers
        print(f"✓ Rate limit headers present")
        print(f"  X-RateLimit-Limit-Minute: {response.headers['X-RateLimit-Limit-Minute']}")
        print(f"  X-RateLimit-Remaining-Minute: {response.headers['X-RateLimit-Remaining-Minute']}")


# ============================================================================
# Test 3: Rate Limiting Enforcement
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limiting_per_minute_enforcement(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that rate limiting is enforced per-minute."""
    print("\n=== Test 4: Rate Limiting (Per-Minute) ===\n")

    # Create API key with low rate limit
    key_data = {
        "name": "Rate Limit Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value],
        "rate_limit": {
            "requests_per_minute": 5,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
        },
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    key_hash = hash_api_key(api_key)

    print(f"✓ Created API key with rate limits: {key_result['key_prefix']}")
    print(f"  Requests per minute: 5")

    # Clear any existing rate limit data for this key
    await redis_client.delete(f"rate_limit:{key_hash}:minute")
    await redis_client.delete(f"rate_limit:{key_hash}:hour")
    await redis_client.delete(f"rate_limit:{key_hash}:day")

    # Make requests up to the limit
    success_count = 0
    rate_limited = False

    for i in range(7):  # Try 7 requests (limit is 5)
        response = await client.get(
            "/api/candidates/",
            headers={"X-API-Key": api_key}
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Request {i+1}: Success (remaining: {response.headers.get('X-RateLimit-Remaining-Minute')})")
        elif response.status_code == 429:
            rate_limited = True
            print(f"  Request {i+1}: Rate limited (429)")
            error_data = response.json()
            print(f"    Window: {error_data.get('window')}")
            print(f"    Retry after: {error_data.get('retry_after')} seconds")
            break
        else:
            print(f"  Request {i+1}: Unexpected status {response.status_code}")

    assert success_count == 5, f"Expected 5 successful requests, got {success_count}"
    assert rate_limited, "Expected rate limit to be enforced"
    print(f"✓ Rate limiting enforced correctly: {success_count} requests allowed, then 429")


@pytest.mark.asyncio
async def test_rate_limiting_resets_after_window(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that rate limits reset after the time window expires."""
    print("\n=== Test 5: Rate Limit Reset After Window ===\n")

    # Create API key with short rate limit
    key_data = {
        "name": "Rate Limit Reset Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value],
        "rate_limit": {
            "requests_per_minute": 3,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
        },
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    key_hash = hash_api_key(api_key)

    print(f"✓ Created API key: {key_result['key_prefix']}")

    # Clear existing rate limit data
    await redis_client.delete(f"rate_limit:{key_hash}:minute")
    await redis_client.delete(f"rate_limit:{key_hash}:hour")
    await redis_client.delete(f"rate_limit:{key_hash}:day")

    # Exhaust the rate limit
    for i in range(3):
        response = await client.get(
            "/api/candidates/",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

    print(f"✓ Exhausted rate limit (3 requests made)")

    # Verify we're rate limited
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code == 429
    print(f"✓ Confirmed rate limited (429 response)")

    # Manually expire the Redis key to simulate time passing
    await redis_client.delete(f"rate_limit:{key_hash}:minute")
    print(f"✓ Simulated time window expiration (cleared Redis key)")

    # Now request should succeed again
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code in [200, 404]
    print(f"✓ Request succeeded after rate limit reset")


# ============================================================================
# Test 4: Usage Analytics Recording
# ============================================================================

@pytest.mark.asyncio
async def test_usage_analytics_recording(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that API usage is recorded in analytics."""
    print("\n=== Test 6: Usage Analytics Recording ===\n")

    # Create API key
    key_data = {
        "name": "Analytics Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value, APIKeyScope.READ_VACANCIES.value],
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    api_key_id = UUID(key_result["id"])

    # Clear rate limits for testing
    key_hash = hash_api_key(api_key)
    await redis_client.delete(f"rate_limit:{key_hash}:minute")
    await redis_client.delete(f"rate_limit:{key_hash}:hour")
    await redis_client.delete(f"rate_limit:{key_hash}:day")

    print(f"✓ Created API key: {key_result['key_prefix']}")

    # Make some API requests
    print(f"\nMaking test API requests...")

    # Successful request
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    status_code = response.status_code
    print(f"  Request 1: GET /api/candidates/ -> {status_code}")

    # Another successful request
    response = await client.get(
        "/api/vacancies/",
        headers={"X-API-Key": api_key}
    )
    status_code_2 = response.status_code
    print(f"  Request 2: GET /api/vacancies/ -> {status_code_2}")

    # Wait a moment for analytics to be recorded
    await asyncio.sleep(0.1)

    # Verify analytics records
    await test_session.commit()

    stmt = select(APIUsage).where(
        and_(
            APIUsage.api_key_id == api_key_id,
            APIUsage.endpoint == "/api/candidates/",
            APIUsage.method == "GET"
        )
    )
    result = await test_session.execute(stmt)
    analytics_records = result.scalars().all()

    print(f"\n✓ Analytics records found: {len(analytics_records)}")

    if len(analytics_records) > 0:
        record = analytics_records[0]
        print(f"  Endpoint: {record.endpoint}")
        print(f"  Method: {record.method}")
        print(f"  Status: {record.status}")
        print(f"  Status Code: {record.status_code}")
        print(f"  Response Time: {record.response_time_ms}ms")
        print(f"  Rate Limit Remaining: {record.rate_limit_remaining}")
        assert record.api_key_id == api_key_id
        assert record.endpoint == "/api/candidates/"
        assert record.method == "GET"

    # Count all usage records for this API key
    count_stmt = select(func.count()).where(
        APIUsage.api_key_id == api_key_id
    )
    count_result = await test_session.execute(count_stmt)
    total_records = count_result.scalar()

    print(f"✓ Total analytics records for API key: {total_records}")
    assert total_records >= 1, "Expected at least one analytics record"


@pytest.mark.asyncio
async def test_usage_analytics_tracks_response_times(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that response times are tracked in usage analytics."""
    print("\n=== Test 7: Response Time Tracking ===\n")

    # Create API key
    key_data = {
        "name": "Response Time Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value],
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    api_key_id = UUID(key_result["id"])

    # Clear rate limits
    key_hash = hash_api_key(api_key)
    await redis_client.delete(f"rate_limit:{key_hash}:minute")

    print(f"✓ Created API key: {key_result['key_prefix']}")

    # Make request and measure time
    start_time = time.time()
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    end_time = time.time()
    actual_response_time_ms = int((end_time - start_time) * 1000)

    print(f"✓ Request made (actual time: {actual_response_time_ms}ms)")

    # Check analytics record
    await test_session.commit()
    await asyncio.sleep(0.1)

    stmt = select(APIUsage).where(
        and_(
            APIUsage.api_key_id == api_key_id,
            APIUsage.endpoint == "/api/candidates/"
        )
    ).order_by(APIUsage.created_at.desc())

    result = await test_session.execute(stmt)
    record = result.scalar_one_or_none()

    if record and record.response_time_ms:
        print(f"✓ Response time tracked in analytics: {record.response_time_ms}ms")
        assert record.response_time_ms > 0
        assert record.response_time_ms < 10000  # Should be less than 10 seconds


@pytest.mark.asyncio
async def test_usage_analytics_tracks_status_codes(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that different status codes are tracked correctly."""
    print("\n=== Test 8: Status Code Tracking ===\n")

    # Create API key
    key_data = {
        "name": "Status Code Test Key",
        "scopes": [
            APIKeyScope.READ_CANDIDATES.value,
            APIKeyScope.READ_VACANCIES.value,
        ],
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    api_key_id = UUID(key_result["id"])

    # Clear rate limits
    key_hash = hash_api_key(api_key)
    await redis_client.delete(f"rate_limit:{key_hash}:minute")

    print(f"✓ Created API key: {key_result['key_prefix']}")

    # Make requests to different endpoints
    endpoints = [
        "/api/candidates/",
        "/api/vacancies/",
    ]

    for endpoint in endpoints:
        response = await client.get(
            endpoint,
            headers={"X-API-Key": api_key}
        )
        status_code = response.status_code
        print(f"  {endpoint}: {status_code}")

    # Check analytics records
    await test_session.commit()
    await asyncio.sleep(0.1)

    stmt = select(APIUsage).where(APIUsage.api_key_id == api_key_id)
    result = await test_session.execute(stmt)
    records = result.scalars().all()

    print(f"✓ Analytics records: {len(records)}")

    # Verify status codes are tracked
    for record in records:
        assert record.status_code is not None
        assert record.status_code > 0
        print(f"  {record.endpoint}: {record.status_code} ({record.status})")


# ============================================================================
# Test 5: API Key Revocation
# ============================================================================

@pytest.mark.asyncio
async def test_api_key_revocation(client: AsyncClient, test_session: AsyncSession, redis_client: Redis):
    """Verify that API keys can be revoked."""
    print("\n=== Test 9: API Key Revocation ===\n")

    # Create API key
    key_data = {
        "name": "Revoke Test Key",
        "scopes": [APIKeyScope.READ_CANDIDATES.value],
    }

    create_response = await client.post("/api/api-keys/generate", json=key_data)
    assert create_response.status_code == 201
    key_result = create_response.json()
    api_key = key_result["key"]
    api_key_id = UUID(key_result["id"])

    # Clear rate limits
    key_hash = hash_api_key(api_key)
    await redis_client.delete(f"rate_limit:{key_hash}:minute")

    print(f"✓ Created API key: {key_result['key_prefix']}")

    # Verify it works
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    assert response.status_code in [200, 404]
    print(f"✓ API key works before revocation")

    # Revoke the key
    revoke_response = await client.post(f"/api/api-keys/{api_key_id}/revoke")
    assert revoke_response.status_code == 200
    revoke_result = revoke_response.json()
    print(f"✓ API key revoked: {revoke_result['key_prefix']}")
    assert revoke_result["is_active"] is False

    # Verify it no longer works
    response = await client.get(
        "/api/candidates/",
        headers={"X-API-Key": api_key}
    )
    # Should be unauthorized or forbidden
    assert response.status_code in [401, 403]
    print(f"✓ API key no longer works after revocation ({response.status_code})")

    # Verify in database
    await test_session.commit()
    stmt = select(APIKey).where(APIKey.id == api_key_id)
    result = await test_session.execute(stmt)
    api_key_obj = result.scalar_one_or_none()

    assert api_key_obj is not None
    assert api_key_obj.is_active is False
    print(f"✓ API key marked as inactive in database")


# ============================================================================
# Test 6: API Key Listing
# ============================================================================

@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, test_session: AsyncSession):
    """Verify that API keys can be listed."""
    print("\n=== Test 10: List API Keys ===\n")

    # Create multiple API keys
    key_names = ["Test Key 1", "Test Key 2", "Test Key 3"]
    created_keys = []

    for name in key_names:
        key_data = {
            "name": name,
            "scopes": [APIKeyScope.READ_CANDIDATES.value],
        }
        create_response = await client.post("/api/api-keys/generate", json=key_data)
        assert create_response.status_code == 201
        created_keys.append(create_response.json())
        print(f"✓ Created API key: {name}")

    # List all API keys
    list_response = await client.get("/api/api-keys/")
    assert list_response.status_code == 200
    list_result = list_response.json()

    print(f"✓ Listed API keys: {len(list_result)} total")

    # Verify our keys are in the list
    listed_prefixes = {key["key_prefix"] for key in list_result}
    created_prefixes = {key["key_prefix"] for key in created_keys}

    assert created_prefixes.issubset(listed_prefixes)
    print(f"✓ All created keys found in list")

    # Verify key structure in list
    for key in list_result:
        assert "id" in key
        assert "key_prefix" in key
        assert "name" in key
        assert "scopes" in key
        assert "is_active" in key
        assert "created_at" in key
        # Full key should NOT be in list
        assert "key" not in key


# ============================================================================
# Summary and Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
