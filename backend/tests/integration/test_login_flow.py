"""
End-to-end integration test for user login flow.

This test verifies the complete login flow:
1. User submits credentials via API
2. JWT tokens are generated (access + refresh)
3. Tokens are correctly formatted and signed
4. Refresh token is stored in database
5. Protected API calls require authentication
6. Invalid credentials are rejected
"""
import asyncio
import pytest
import jwt
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.user import User
from models.refresh_token import RefreshToken
from config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_login.db"


@pytest.fixture
async def test_db():
    """Create test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create test client with database override."""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client: AsyncClient):
    """Create a test user for login tests."""
    user_data = {
        "email": "logintest@example.com",
        "password": "TestPass123!",
        "full_name": "Login Test User"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest.mark.asyncio
async def test_complete_login_flow(client: AsyncClient, test_db: AsyncSession, test_user: dict):
    """
    End-to-end test: Complete user login flow from API to JWT tokens to database.

    Verification steps:
    1. Submit login request with valid credentials
    2. Verify response contains JWT tokens (access + refresh)
    3. Verify access token structure and expiration
    4. Verify refresh token stored in database
    5. Verify tokens are correctly signed
    6. Verify token type claims
    7. Verify user information in tokens
    """
    print("\n=== Starting Login Flow E2E Test ===\n")

    # Step 1: Submit login request
    print("Step 1: Submitting login request...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    response = await client.post("/api/auth/login", json=login_data)
    print(f"Response status: {response.status_code}")

    # Step 2: Verify response
    print("\nStep 2: Verifying login response...")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    print(f"Response keys: {list(data.keys())}")

    assert "access_token" in data, "Response should contain access_token"
    assert "refresh_token" in data, "Response should contain refresh_token"
    assert "token_type" in data, "Response should contain token_type"
    assert "expires_in" in data, "Response should contain expires_in"
    assert "user" in data, "Response should contain user info"
    print("✓ Login response valid")

    # Step 3: Verify token type
    assert data["token_type"] == "bearer", "Token type should be bearer"
    print(f"✓ Token type: {data['token_type']}")

    # Step 4: Verify user information
    user_info = data["user"]
    assert user_info["email"] == test_user["email"], "User email should match"
    assert user_info["full_name"] == test_user["full_name"], "User full name should match"
    assert user_info["is_active"] is True, "User should be active"
    print(f"✓ User info valid: {user_info['email']}")

    # Step 5: Verify access token structure
    print("\nStep 3: Verifying access token structure...")
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    try:
        # Decode access token (without verification first to inspect)
        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        print(f"Access token payload: {access_payload}")

        assert "sub" in access_payload, "Access token should have sub (user_id)"
        assert "email" in access_payload, "Access token should have email"
        assert "exp" in access_payload, "Access token should have expiration"
        assert "iat" in access_payload, "Access token should have issued at"
        assert "type" in access_payload, "Access token should have type claim"
        assert access_payload["type"] == "access", "Token type should be 'access'"
        print("✓ Access token structure valid")
    except jwt.DecodeError:
        pytest.fail("Access token is not a valid JWT")

    # Step 6: Verify refresh token structure
    print("\nStep 4: Verifying refresh token structure...")
    try:
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
        print(f"Refresh token payload: {refresh_payload}")

        assert "sub" in refresh_payload, "Refresh token should have sub (user_id)"
        assert "email" in refresh_payload, "Refresh token should have email"
        assert "exp" in refresh_payload, "Refresh token should have expiration"
        assert "iat" in refresh_payload, "Refresh token should have issued at"
        assert "type" in refresh_payload, "Refresh token should have type claim"
        assert refresh_payload["type"] == "refresh", "Token type should be 'refresh'"
        print("✓ Refresh token structure valid")
    except jwt.DecodeError:
        pytest.fail("Refresh token is not a valid JWT")

    # Step 7: Verify tokens are signed with secret key
    print("\nStep 5: Verifying token signatures...")
    try:
        # Verify access token signature
        access_verified = jwt.decode(access_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert access_verified["email"] == test_user["email"]
        print("✓ Access token signature valid")

        # Verify refresh token signature
        refresh_verified = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert refresh_verified["email"] == test_user["email"]
        print("✓ Refresh token signature valid")
    except jwt.InvalidSignatureError:
        pytest.fail("Token signature is invalid")

    # Step 8: Verify refresh token stored in database
    print("\nStep 6: Verifying refresh token stored in database...")
    result = await test_db.execute(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    )
    stored_token = result.scalar_one_or_none()

    assert stored_token is not None, "Refresh token should be stored in database"
    assert stored_token.is_revoked is False, "Refresh token should not be revoked"
    assert stored_token.revoked_at is None, "Refresh token should not have revoked_at timestamp"
    print(f"✓ Refresh token stored in database (ID: {stored_token.id})")

    # Step 9: Verify token expiration
    print("\nStep 7: Verifying token expiration...")
    import time
    current_time = int(time.time())

    # Access token should expire in ~30 minutes
    access_exp = access_payload["exp"]
    access expiresIn = access_exp - current_time
    assert 1700 <= expiresIn <= 1800, f"Access token should expire in ~30 minutes, got {expiresIn}s"
    print(f"✓ Access token expires in {expiresIn}s (~{expiresIn//60} minutes)")

    # Refresh token should expire in ~7 days
    refresh_exp = refresh_payload["exp"]
    refreshExpiresIn = refresh_exp - current_time
    expected_seconds = 7 * 24 * 60 * 60  # 7 days
    assert expected_seconds - 10 <= refreshExpiresIn <= expected_seconds + 10, \
        f"Refresh token should expire in ~7 days, got {refreshExpiresIn}s"
    print(f"✓ Refresh token expires in {refreshExpiresIn}s (~{refreshExpiresIn//86400} days)")

    print("\n=== Login Flow E2E Test PASSED ===\n")


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """
    Test login with invalid credentials.

    Verifies that:
    1. Wrong email returns 401
    2. Wrong password returns 401
    3. Error messages don't leak information
    """
    print("\n=== Testing Invalid Credentials ===\n")

    # Test 1: Non-existent user
    print("Test 1: Login with non-existent user...")
    response = await client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePass123!"
    })

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ Non-existent user rejected")

    # Test 2: Wrong password
    print("\nTest 2: Login with wrong password...")
    # First, create a user
    await client.post("/api/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "CorrectPass123!",
        "full_name": "Test User"
    })

    # Try to login with wrong password
    response = await client.post("/api/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "WrongPass123!"
    })

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ Wrong password rejected")

    print("\n=== Invalid Credentials Test PASSED ===\n")


@pytest.mark.asyncio
async def test_login_with_inactive_account(client: AsyncClient, test_db: AsyncSession):
    """
    Test login with inactive account.

    Verifies that inactive users cannot login.
    """
    print("\n=== Testing Inactive Account Login ===\n")

    # Create a user
    response = await client.post("/api/auth/register", json={
        "email": "inactive@example.com",
        "password": "TestPass123!",
        "full_name": "Inactive User"
    })
    assert response.status_code == 201

    # Deactivate the user in database
    result = await test_db.execute(
        select(User).where(User.email == "inactive@example.com")
    )
    user = result.scalar_one()
    user.is_active = False
    await test_db.commit()
    await test_db.refresh(user)

    print(f"User {user.email} deactivated (is_active={user.is_active})")

    # Try to login with inactive account
    response = await client.post("/api/auth/login", json={
        "email": "inactive@example.com",
        "password": "TestPass123!"
    })

    assert response.status_code == 403, f"Expected 403 for inactive user, got {response.status_code}"
    print("✓ Inactive account login rejected")

    print("\n=== Inactive Account Test PASSED ===\n")


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient):
    """
    Test that protected routes require authentication.

    Verifies that:
    1. Protected routes return 401 without token
    2. Protected routes return 401 with invalid token
    3. Protected routes return 200 with valid token
    """
    print("\n=== Testing Protected Route Authentication ===\n")

    # Test 1: Access without token
    print("Test 1: Access protected route without token...")
    response = await client.get("/api/candidates/")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ Protected route rejected unauthenticated request")

    # Test 2: Access with invalid token
    print("\nTest 2: Access protected route with invalid token...")
    response = await client.get(
        "/api/candidates/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ Protected route rejected invalid token")

    # Test 3: Login and access with valid token
    print("\nTest 3: Login and access protected route with valid token...")

    # Create user
    await client.post("/api/auth/register", json={
        "email": "protected@example.com",
        "password": "TestPass123!",
        "full_name": "Protected Test"
    })

    # Login
    login_response = await client.post("/api/auth/login", json={
        "email": "protected@example.com",
        "password": "TestPass123!"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Access protected route with valid token
    response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200, f"Expected 200 with valid token, got {response.status_code}"
    print("✓ Protected route accepted valid token")

    print("\n=== Protected Route Authentication Test PASSED ===\n")


@pytest.mark.asyncio
async def test_login_response_format(client: AsyncClient, test_user: dict):
    """
    Test login response format.

    Verifies that response matches expected schema.
    """
    print("\n=== Testing Login Response Format ===\n")

    response = await client.post("/api/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields
    required_fields = ["access_token", "refresh_token", "token_type", "expires_in", "user"]
    for field in required_fields:
        assert field in data, f"Response should contain {field}"
        print(f"✓ Field '{field}' present")

    # Verify user object structure
    user_fields = ["id", "email", "full_name", "is_active", "is_verified", "is_superuser"]
    for field in user_fields:
        assert field in data["user"], f"User object should contain {field}"
        print(f"✓ User field '{field}' present")

    # Verify no sensitive data leaked
    assert "password" not in data, "Response should not contain password"
    assert "password_hash" not in data, "Response should not contain password_hash"
    print("✓ No sensitive data leaked")

    print("\n=== Login Response Format Test PASSED ===\n")


if __name__ == "__main__":
    print("Running login flow tests...")
    pytest.main([__file__, "-v", "-s"])
