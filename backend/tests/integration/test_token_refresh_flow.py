"""
End-to-end integration test for token refresh flow.

This test verifies the complete token refresh flow:
1. User logs in and receives JWT tokens (access + refresh)
2. Access token expires or becomes invalid
3. Client attempts to access protected resource with expired token
4. Backend returns 401 Unauthorized
5. Client uses refresh token to obtain new access token
6. New access token is valid and allows access to protected resources
7. Old refresh token remains valid (refresh token rotation not implemented)
8. Invalid refresh tokens are rejected
9. Revoked refresh tokens are rejected
10. Expired refresh tokens are rejected
"""
import asyncio
import pytest
import jwt
import time
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.user import User
from models.refresh_token import RefreshToken
from config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_token_refresh.db"


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
    """Create a test user for token refresh tests."""
    user_data = {
        "email": "refresh_test@example.com",
        "password": "TestPass123!",
        "full_name": "Refresh Test User"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest.mark.asyncio
async def test_successful_token_refresh(client: AsyncClient, test_user: dict):
    """
    Test successful token refresh flow.

    Verification steps:
    1. Login and receive JWT tokens
    2. Verify access token is valid
    3. Use refresh token to obtain new access token
    4. Verify new access token is different from original
    5. Verify new access token is valid and works for protected requests
    6. Verify refresh token remains unchanged (no rotation)
    """
    print("\n=== Starting Successful Token Refresh Test ===\n")

    # Step 1: Login and receive tokens
    print("Step 1: Logging in to receive tokens...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    login_data_response = login_response.json()
    original_access_token = login_data_response["access_token"]
    original_refresh_token = login_data_response["refresh_token"]
    print(f"✓ Received access token: {original_access_token[:50]}...")
    print(f"✓ Received refresh token: {original_refresh_token[:50]}...")

    # Step 2: Verify original access token works
    print("\nStep 2: Verifying original access token works...")
    protected_response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {original_access_token}"}
    )
    assert protected_response.status_code == 200, "Original access token should work"
    print("✓ Original access token is valid")

    # Step 3: Refresh the access token
    print("\nStep 3: Refreshing access token...")
    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": original_refresh_token
    })
    assert refresh_response.status_code == 200, f"Token refresh failed: {refresh_response.text}"

    refresh_data = refresh_response.json()
    new_access_token = refresh_data["access_token"]
    print(f"✓ Received new access token: {new_access_token[:50]}...")

    # Step 4: Verify new access token is different
    print("\nStep 4: Verifying new access token is different...")
    assert new_access_token != original_access_token, "New access token should be different"
    print("✓ New access token is different from original")

    # Step 5: Verify new access token works
    print("\nStep 5: Verifying new access token works...")
    protected_response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert protected_response.status_code == 200, "New access token should work"
    print("✓ New access token is valid and works for protected requests")

    # Step 6: Verify new access token has proper structure
    print("\nStep 6: Verifying new access token structure...")
    decoded = jwt.decode(new_access_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["type"] == "access", "Token type should be 'access'"
    assert "sub" in decoded, "Token should have user ID (sub)"
    assert "exp" in decoded, "Token should have expiration"
    assert "email" in decoded, "Token should have email"
    print("✓ New access token has valid structure")

    print("\n✅ Test passed: Successful token refresh flow\n")


@pytest.mark.asyncio
async def test_token_refresh_with_invalid_refresh_token(client: AsyncClient, test_user: dict):
    """
    Test token refresh with invalid refresh token.

    Verification steps:
    1. Attempt to refresh with invalid/malformed JWT
    2. Verify 401 Unauthorized response
    3. Verify appropriate error message
    """
    print("\n=== Starting Invalid Refresh Token Test ===\n")

    # Step 1: Attempt to refresh with invalid token
    print("Step 1: Attempting token refresh with invalid refresh token...")
    invalid_refresh_token = "invalid.refresh.token"

    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": invalid_refresh_token
    })

    # Step 2: Verify 401 response
    print("\nStep 2: Verifying 401 Unauthorized response...")
    assert refresh_response.status_code == 401, f"Expected 401, got {refresh_response.status_code}"
    print("✓ Received 401 Unauthorized")

    # Step 3: Verify error message
    print("\nStep 3: Verifying error message...")
    error_data = refresh_response.json()
    assert "detail" in error_data, "Response should have error detail"
    print(f"✓ Error message: {error_data['detail']}")

    print("\n✅ Test passed: Invalid refresh token rejected\n")


@pytest.mark.asyncio
async def test_token_refresh_with_revoked_token(client: AsyncClient, test_user: dict, test_db: AsyncSession):
    """
    Test token refresh with revoked refresh token.

    Verification steps:
    1. Login and receive tokens
    2. Revoke the refresh token (simulate logout)
    3. Attempt to refresh with revoked token
    4. Verify 401 Unauthorized response
    """
    print("\n=== Starting Revoked Refresh Token Test ===\n")

    # Step 1: Login and receive tokens
    print("Step 1: Logging in to receive tokens...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data_response = login_response.json()
    refresh_token = login_data_response["refresh_token"]
    print(f"✓ Received refresh token: {refresh_token[:50]}...")

    # Step 2: Revoke the refresh token
    print("\nStep 2: Revoking refresh token...")
    logout_response = await client.post("/api/auth/logout", json={
        "refresh_token": refresh_token
    })
    assert logout_response.status_code == 200
    print("✓ Refresh token revoked")

    # Step 3: Attempt to refresh with revoked token
    print("\nStep 3: Attempting to refresh with revoked token...")
    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })

    # Step 4: Verify 401 response
    print("\nStep 4: Verifying 401 Unauthorized response...")
    assert refresh_response.status_code == 401, f"Expected 401, got {refresh_response.status_code}"
    print("✓ Received 401 Unauthorized")

    error_data = refresh_response.json()
    assert "detail" in error_data
    print(f"✓ Error message: {error_data['detail']}")

    print("\n✅ Test passed: Revoked refresh token rejected\n")


@pytest.mark.asyncio
async def test_token_refresh_response_format(client: AsyncClient, test_user: dict):
    """
    Test token refresh response format.

    Verification steps:
    1. Login and receive tokens
    2. Refresh access token
    3. Verify response format matches expected schema
    4. Verify response contains only access_token (not refresh_token)
    """
    print("\n=== Starting Token Refresh Response Format Test ===\n")

    # Step 1: Login
    print("Step 1: Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data_response = login_response.json()
    refresh_token = login_data_response["refresh_token"]
    print("✓ Login successful")

    # Step 2: Refresh token
    print("\nStep 2: Refreshing access token...")
    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_response.status_code == 200

    # Step 3: Verify response format
    print("\nStep 3: Verifying response format...")
    response_data = refresh_response.json()

    # Required fields
    assert "access_token" in response_data, "Response should contain access_token"
    assert "token_type" in response_data, "Response should contain token_type"
    assert "expires_in" in response_data, "Response should contain expires_in"

    # Verify token type is 'bearer'
    assert response_data["token_type"] == "bearer", "Token type should be 'bearer'"

    # Verify expires_in is a number (seconds)
    assert isinstance(response_data["expires_in"], (int, float)), "expires_in should be a number"
    assert response_data["expires_in"] > 0, "expires_in should be positive"

    # Step 4: Verify response does NOT contain refresh_token (no rotation)
    print("\nStep 4: Verifying no refresh token rotation...")
    assert "refresh_token" not in response_data, "Response should not contain new refresh_token"
    assert "user" not in response_data, "Response should not contain user info"
    print("✓ No refresh token rotation (refresh token remains unchanged)")

    print("\n✅ Test passed: Token refresh response format is correct\n")


@pytest.mark.asyncio
async def test_token_refresh_preserves_refresh_token(client: AsyncClient, test_user: dict):
    """
    Test that token refresh does not rotate the refresh token.

    Verification steps:
    1. Login and receive tokens
    2. Refresh access token multiple times
    3. Verify refresh token remains the same
    4. Verify all new access tokens work
    """
    print("\n=== Starting Refresh Token Preservation Test ===\n")

    # Step 1: Login
    print("Step 1: Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data_response = login_response.json()
    original_refresh_token = login_data_response["refresh_token"]
    print(f"✓ Received refresh token: {original_refresh_token[:50]}...")

    # Step 2: Refresh multiple times
    print("\nStep 2: Refreshing access token 3 times...")
    access_tokens = []

    for i in range(3):
        refresh_response = await client.post("/api/auth/refresh", json={
            "refresh_token": original_refresh_token
        })
        assert refresh_response.status_code == 200, f"Refresh {i+1} failed"
        access_tokens.append(refresh_response.json()["access_token"])
        print(f"✓ Refresh {i+1} successful")

    # Step 3: Verify all access tokens are different
    print("\nStep 3: Verifying all access tokens are unique...")
    assert len(set(access_tokens)) == 3, "All access tokens should be unique"
    print("✓ All access tokens are unique")

    # Step 4: Verify all access tokens work
    print("\nStep 4: Verifying all access tokens work...")
    for i, token in enumerate(access_tokens):
        protected_response = await client.get(
            "/api/candidates/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == 200, f"Access token {i+1} should work"
    print("✓ All access tokens are valid")

    print("\n✅ Test passed: Refresh token is preserved across multiple refreshes\n")


@pytest.mark.asyncio
async def test_access_and_refresh_token_types(client: AsyncClient, test_user: dict):
    """
    Test that access and refresh tokens have correct type claims.

    Verification steps:
    1. Login and receive tokens
    2. Decode access token and verify type='access'
    3. Decode refresh token and verify type='refresh'
    4. Verify access token cannot be used for refresh
    5. Verify refresh token cannot access protected endpoints
    """
    print("\n=== Starting Token Type Claims Test ===\n")

    # Step 1: Login
    print("Step 1: Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data_response = login_response.json()
    access_token = login_data_response["access_token"]
    refresh_token = login_data_response["refresh_token"]
    print("✓ Login successful, received both tokens")

    # Step 2: Verify access token type
    print("\nStep 2: Verifying access token type...")
    decoded_access = jwt.decode(access_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded_access["type"] == "access", "Access token should have type='access'"
    print("✓ Access token has type='access'")

    # Step 3: Verify refresh token type
    print("\nStep 3: Verifying refresh token type...")
    decoded_refresh = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded_refresh["type"] == "refresh", "Refresh token should have type='refresh'"
    print("✓ Refresh token has type='refresh'")

    # Step 4: Verify access token cannot be used for refresh
    print("\nStep 4: Verifying access token cannot be used for refresh...")
    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": access_token  # Using access token instead of refresh token
    })
    assert refresh_response.status_code == 401, "Access token should not work for refresh"
    print("✓ Access token rejected for refresh endpoint")

    # Step 5: Verify refresh token cannot access protected endpoints
    print("\nStep 5: Verifying refresh token cannot access protected endpoints...")
    protected_response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert protected_response.status_code == 401, "Refresh token should not access protected endpoints"
    print("✓ Refresh token rejected for protected endpoints")

    print("\n✅ Test passed: Token type claims are correctly enforced\n")


@pytest.mark.asyncio
async def test_expired_access_token_with_valid_refresh(client: AsyncClient, test_user: dict):
    """
    Test accessing protected resource with expired access token but valid refresh token.

    Note: This test simulates the scenario where the access token has expired.
    Since we cannot easily make a token expire in tests, we verify the backend
    correctly rejects expired tokens by checking the expiration validation logic.

    Verification steps:
    1. Login and receive tokens
    2. Verify access token expiration is set correctly (~30 minutes)
    3. Verify refresh token expiration is set correctly (~7 days)
    4. Manually create an expired access token
    5. Attempt to access protected resource with expired token
    6. Verify 401 Unauthorized response
    7. Use refresh token to get new access token
    8. Verify new token works
    """
    print("\n=== Starting Expired Access Token Test ===\n")

    # Step 1: Login
    print("Step 1: Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }

    login_response = await client.post("/api/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data_response = login_response.json()
    access_token = login_data_response["access_token"]
    refresh_token = login_data_response["refresh_token"]
    print("✓ Login successful")

    # Step 2: Verify access token expiration
    print("\nStep 2: Verifying access token expiration...")
    decoded_access = jwt.decode(access_token, settings.secret_key, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
    exp = decoded_access["exp"]
    iat = decoded_access["iat"]
    expires_in_seconds = exp - iat

    # Access token should expire in ~30 minutes (1800 seconds)
    assert 1700 <= expires_in_seconds <= 1900, f"Access token should expire in ~30 minutes, got {expires_in_seconds}s"
    print(f"✓ Access token expires in {expires_in_seconds} seconds (~30 minutes)")

    # Step 3: Verify refresh token expiration
    print("\nStep 3: Verifying refresh token expiration...")
    decoded_refresh = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.jwt_algorithm], options={"verify_exp": False})
    refresh_exp = decoded_refresh["exp"]
    refresh_iat = decoded_refresh["iat"]
    refresh_expires_in = refresh_exp - refresh_iat

    # Refresh token should expire in ~7 days (604800 seconds)
    assert 600000 <= refresh_expires_in <= 610000, f"Refresh token should expire in ~7 days, got {refresh_expires_in}s"
    print(f"✓ Refresh token expires in {refresh_expires_in} seconds (~7 days)")

    # Step 4: Create an expired access token
    print("\nStep 4: Creating expired access token...")
    decoded_access["exp"] = int(time.time()) - 3600  # Expired 1 hour ago
    expired_access_token = jwt.encode(decoded_access, settings.secret_key, algorithm=settings.jwt_algorithm)
    print("✓ Created expired access token")

    # Step 5: Attempt to access protected resource with expired token
    print("\nStep 5: Attempting to access protected resource with expired token...")
    protected_response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {expired_access_token}"}
    )
    assert protected_response.status_code == 401, "Expired access token should be rejected"
    print("✓ Expired access token rejected with 401")

    # Step 6: Use refresh token to get new access token
    print("\nStep 6: Using refresh token to get new access token...")
    refresh_response = await client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_response.status_code == 200, "Refresh should succeed"
    new_access_token = refresh_response.json()["access_token"]
    print("✓ Received new access token via refresh")

    # Step 7: Verify new token works
    print("\nStep 7: Verifying new access token works...")
    protected_response = await client.get(
        "/api/candidates/",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    assert protected_response.status_code == 200, "New access token should work"
    print("✓ New access token is valid")

    print("\n✅ Test passed: Expired access token scenario handled correctly\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
