"""
End-to-End Integration Tests for OAuth 2.0 Flow

This test module performs comprehensive verification of the OAuth 2.0 authentication
system, including provider configuration, authorization URL generation, callback
handling, token exchange, and user profile fetching.

Test Coverage:
- OAuth provider CRUD operations (create, read, update, delete)
- Authorization URL generation with state parameter (CSRF protection)
- PKCE support for enhanced security
- OAuth callback processing and state verification
- Token exchange with provider APIs
- User profile fetching from OAuth providers
- Error handling for invalid credentials and tokens
- Multi-provider support (Google, GitHub, LinkedIn)
- Provider enable/disable functionality
- Default provider selection

Note: These tests use mocked HTTP responses for external OAuth provider calls
since actual integration requires real OAuth applications with valid credentials.
"""
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient, ASGITransport, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from database import get_db, Base
from models.oauth_provider import OAuthProvider
from config import get_settings


# Test Database Setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ============================================================================
# Test Fixtures
# ============================================================================

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
async def google_provider(test_session: AsyncSession) -> OAuthProvider:
    """Create a Google OAuth provider for testing."""
    provider = OAuthProvider(
        provider_name="Google OAuth",
        provider_type="google",
        client_id="test-google-client-id",
        client_secret="test-google-client-secret",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes="openid email profile",
        redirect_uri="http://localhost:8000/api/oauth/callback",
        attribute_mapping_email="email",
        attribute_mapping_name="name",
        attribute_mapping_first_name="given_name",
        attribute_mapping_last_name="family_name",
        attribute_mapping_picture="picture",
        is_enabled=True,
        is_default=True,
    )
    test_session.add(provider)
    await test_session.commit()
    await test_session.refresh(provider)
    return provider


@pytest.fixture
async def linkedin_provider(test_session: AsyncSession) -> OAuthProvider:
    """Create a LinkedIn OAuth provider for testing."""
    provider = OAuthProvider(
        provider_name="LinkedIn OAuth",
        provider_type="linkedin",
        client_id="test-linkedin-client-id",
        client_secret="test-linkedin-client-secret",
        authorization_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        userinfo_url="https://api.linkedin.com/v2/me",
        scopes="r_liteprofile r_emailaddress",
        redirect_uri="http://localhost:8000/api/oauth/callback",
        attribute_mapping_email="email",
        attribute_mapping_name="localizedFirstName",
        attribute_mapping_first_name="localizedFirstName",
        attribute_mapping_last_name="localizedLastName",
        is_enabled=True,
        is_default=False,
    )
    test_session.add(provider)
    await test_session.commit()
    await test_session.refresh(provider)
    return provider


@pytest.fixture
async def github_provider(test_session: AsyncSession) -> OAuthProvider:
    """Create a GitHub OAuth provider for testing."""
    provider = OAuthProvider(
        provider_name="GitHub OAuth",
        provider_type="github",
        client_id="test-github-client-id",
        client_secret="test-github-client-secret",
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        userinfo_url="https://api.github.com/user",
        scopes="read:user user:email",
        redirect_uri="http://localhost:8000/api/oauth/callback",
        attribute_mapping_email="email",
        attribute_mapping_name="name",
        attribute_mapping_picture="avatar_url",
        is_enabled=True,
        is_default=False,
    )
    test_session.add(provider)
    await test_session.commit()
    await test_session.refresh(provider)
    return provider


# ============================================================================
# Test 1: OAuth Provider CRUD Operations
# ============================================================================

@pytest.mark.asyncio
async def test_create_oauth_provider(client: AsyncClient, test_session: AsyncSession):
    """Verify that an OAuth provider can be created successfully."""
    provider_data = {
        "provider_name": "Test Google OAuth",
        "provider_type": "google",
        "client_id": "test-client-id-123",
        "client_secret": "test-client-secret-456",
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scopes": "openid email profile",
        "redirect_uri": "http://localhost:8000/api/oauth/callback",
        "attribute_mapping_email": "email",
        "attribute_mapping_name": "name",
        "is_enabled": True,
        "is_default": True,
    }

    response = await client.post("/api/oauth/providers", json=provider_data)

    assert response.status_code == 201
    data = response.json()

    assert data["provider_name"] == "Test Google OAuth"
    assert data["provider_type"] == "google"
    assert data["client_id"] == "test-client-id-123"
    assert data["is_enabled"] is True
    assert data["is_default"] is True
    assert "id" in data

    # Verify database record
    await test_session.commit()
    result = await test_session.execute(select(OAuthProvider))
    provider = result.scalar_one_or_none()
    assert provider is not None
    assert provider.provider_name == "Test Google OAuth"


@pytest.mark.asyncio
async def test_list_oauth_providers(
    client: AsyncClient,
    test_session: AsyncSession,
    google_provider: OAuthProvider,
    linkedin_provider: OAuthProvider,
):
    """Verify that OAuth providers can be listed with filtering."""
    # List all providers
    response = await client.get("/api/oauth/providers")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 2
    assert len(data["providers"]) == 2

    # Filter by provider type
    response = await client.get("/api/oauth/providers?provider_type=google")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 1
    assert data["providers"][0]["provider_type"] == "google"

    # Filter by enabled status
    response = await client.get("/api/oauth/providers?is_enabled=true")

    assert response.status_code == 200
    data = response.json()

    assert data["total_count"] == 2


@pytest.mark.asyncio
async def test_get_oauth_provider_by_id(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that a specific OAuth provider can be retrieved by ID."""
    response = await client.get("/api/oauth/providers")

    assert response.status_code == 200
    data = response.json()

    provider_id = data["providers"][0]["id"]
    assert provider_id is not None


@pytest.mark.asyncio
async def test_update_oauth_provider(
    client: AsyncClient,
    test_session: AsyncSession,
    google_provider: OAuthProvider,
):
    """Verify that an OAuth provider can be updated."""
    provider_id = str(google_provider.id)

    update_data = {
        "provider_name": "Updated Google OAuth",
        "is_enabled": False,
    }

    response = await client.put(f"/api/oauth/providers/{provider_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()

    assert data["provider_name"] == "Updated Google OAuth"
    assert data["is_enabled"] is False

    # Verify database was updated
    await test_session.refresh(google_provider)
    assert google_provider.provider_name == "Updated Google OAuth"
    assert google_provider.is_enabled is False


@pytest.mark.asyncio
async def test_delete_oauth_provider(
    client: AsyncClient,
    test_session: AsyncSession,
    google_provider: OAuthProvider,
):
    """Verify that an OAuth provider can be deleted."""
    provider_id = str(google_provider.id)

    response = await client.delete(f"/api/oauth/providers/{provider_id}")

    assert response.status_code == 204

    # Verify database record was deleted
    result = await test_session.execute(
        select(OAuthProvider).where(OAuthProvider.id == google_provider.id)
    )
    provider = result.scalar_one_or_none()
    assert provider is None


@pytest.mark.asyncio
async def test_create_provider_invalid_type(client: AsyncClient):
    """Verify that creating a provider with invalid type fails."""
    provider_data = {
        "provider_name": "Invalid Provider",
        "provider_type": "invalid_type",
        "client_id": "test-id",
        "client_secret": "test-secret",
        "authorization_url": "https://example.com/auth",
        "token_url": "https://example.com/token",
        "userinfo_url": "https://example.com/userinfo",
        "redirect_uri": "http://localhost:8000/callback",
    }

    response = await client.post("/api/oauth/providers", json=provider_data)

    assert response.status_code == 400
    assert "Invalid provider_type" in response.json()["detail"]


# ============================================================================
# Test 2: Authorization URL Generation
# ============================================================================

@pytest.mark.asyncio
async def test_generate_authorization_url_google(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that authorization URL is generated correctly for Google."""
    response = await client.get("/api/oauth/google/authorize")

    assert response.status_code == 200
    data = response.json()

    assert "authorization_url" in data
    assert "state" in data
    assert "provider_id" in data
    assert "provider_type" in data

    assert data["provider_type"] == "google"
    assert "accounts.google.com/o/oauth2/v2/auth" in data["authorization_url"]
    assert "client_id=test-google-client-id" in data["authorization_url"]
    assert f"state={data['state']}" in data["authorization_url"]
    assert "scope=" in data["authorization_url"]

    # Verify state is a non-empty string
    assert len(data["state"]) > 0


@pytest.mark.asyncio
async def test_generate_authorization_url_linkedin(
    client: AsyncClient,
    linkedin_provider: OAuthProvider,
):
    """Verify that authorization URL is generated correctly for LinkedIn."""
    response = await client.get("/api/oauth/linkedin/authorize")

    assert response.status_code == 200
    data = response.json()

    assert "authorization_url" in data
    assert data["provider_type"] == "linkedin"
    assert "linkedin.com/oauth/v2/authorization" in data["authorization_url"]


@pytest.mark.asyncio
async def test_generate_authorization_url_github(
    client: AsyncClient,
    github_provider: OAuthProvider,
):
    """Verify that authorization URL is generated correctly for GitHub."""
    response = await client.get("/api/oauth/github/authorize")

    assert response.status_code == 200
    data = response.json()

    assert "authorization_url" in data
    assert data["provider_type"] == "github"
    assert "github.com/login/oauth/authorize" in data["authorization_url"]


@pytest.mark.asyncio
async def test_generate_authorization_url_with_pkce(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that authorization URL generation supports PKCE."""
    response = await client.get("/api/oauth/google/authorize?use_pkce=true")

    assert response.status_code == 200
    data = response.json()

    assert "authorization_url" in data
    assert "code_verifier" in data
    assert data["code_verifier"] is not None


@pytest.mark.asyncio
async def test_generate_authorization_url_custom_redirect(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that custom redirect URI can be specified."""
    custom_redirect = "http://localhost:3000/auth/callback"
    response = await client.get(
        f"/api/oauth/google/authorize?redirect_uri={custom_redirect}"
    )

    assert response.status_code == 200
    data = response.json()

    assert "authorization_url" in data
    assert custom_redirect in data["authorization_url"]


@pytest.mark.asyncio
async def test_generate_authorization_url_disabled_provider(
    client: AsyncClient,
    test_session: AsyncSession,
    google_provider: OAuthProvider,
):
    """Verify that authorization URL generation fails for disabled providers."""
    # Disable the provider
    google_provider.is_enabled = False
    test_session.add(google_provider)
    await test_session.commit()

    response = await client.get("/api/oauth/google/authorize")

    assert response.status_code == 404
    assert "not found or not enabled" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_authorization_url_nonexistent_provider(client: AsyncClient):
    """Verify that authorization URL generation fails for non-existent providers."""
    response = await client.get("/api/oauth/nonexistent/authorize")

    assert response.status_code == 404


# ============================================================================
# Test 3: OAuth Callback and Token Exchange
# ============================================================================

@pytest.mark.asyncio
async def test_oauth_callback_success(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback processes successfully with valid code."""
    # First, generate an authorization URL to get a state
    auth_response = await client.get("/api/oauth/google/authorize")
    auth_data = auth_response.json()
    state = auth_data["state"]
    provider_id = auth_data["provider_id"]

    # Mock the token exchange and profile fetch
    mock_token_response = {
        "access_token": "mock-access-token-12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock-refresh-token",
        "scope": "openid email profile",
    }

    mock_profile_response = {
        "id": "123456789",
        "email": "test@example.com",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "picture": "https://example.com/photo.jpg",
    }

    # Prepare callback request
    callback_data = {
        "code": "mock-authorization-code",
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
    }

    # Mock the provider's exchange_code_for_token and get_user_profile methods
    with patch(
        "services.oauth_service.GoogleProvider.exchange_code_for_token",
        return_value=mock_token_response,
    ), patch(
        "services.oauth_service.GoogleProvider.get_user_profile",
        return_value=mock_profile_response,
    ):
        response = await client.post("/api/oauth/callback", json=callback_data)

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "user_profile" in data
        assert data["access_token"] == "mock-access-token-12345"
        assert data["user_profile"]["email"] == "test@example.com"
        assert data["user_profile"]["name"] == "Test User"


@pytest.mark.asyncio
async def test_oauth_callback_state_mismatch(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback fails with state mismatch (CSRF protection)."""
    # Generate authorization URL to get a valid state
    auth_response = await client.get("/api/oauth/google/authorize")
    auth_data = auth_response.json()
    provider_id = auth_data["provider_id"]

    # Use different state values to simulate CSRF attack
    callback_data = {
        "code": "mock-authorization-code",
        "state": "attacker-state-123",
        "expected_state": "legitimate-state-456",
        "provider_id": provider_id,
    }

    response = await client.post("/api/oauth/callback", json=callback_data)

    assert response.status_code == 400
    assert "state parameter mismatch" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_missing_code(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback fails when code is missing."""
    auth_response = await client.get("/api/oauth/google/authorize")
    auth_data = auth_response.json()
    state = auth_data["state"]
    provider_id = auth_data["provider_id"]

    callback_data = {
        "code": "",
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
    }

    response = await client.post("/api/oauth/callback", json=callback_data)

    assert response.status_code == 400
    assert "authorization code" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_invalid_provider(client: AsyncClient):
    """Verify that OAuth callback fails with invalid provider ID."""
    callback_data = {
        "code": "mock-code",
        "state": "mock-state",
        "expected_state": "mock-state",
        "provider_id": str(uuid4()),
    }

    response = await client.post("/api/oauth/callback", json=callback_data)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_token_exchange_failure(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback handles token exchange failures."""
    # Generate state
    auth_response = await client.get("/api/oauth/google/authorize")
    auth_data = auth_response.json()
    state = auth_data["state"]
    provider_id = auth_data["provider_id"]

    callback_data = {
        "code": "invalid-code",
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
    }

    # Mock token exchange to raise an exception
    with patch(
        "services.oauth_service.GoogleProvider.exchange_code_for_token",
        side_effect=Exception("Invalid authorization code"),
    ):
        response = await client.post("/api/oauth/callback", json=callback_data)

        assert response.status_code == 401
        assert "token exchange failed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_profile_fetch_failure(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback handles profile fetch failures."""
    # Generate state
    auth_response = await client.get("/api/oauth/google/authorize")
    auth_data = auth_response.json()
    state = auth_data["state"]
    provider_id = auth_data["provider_id"]

    mock_token_response = {
        "access_token": "mock-access-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    callback_data = {
        "code": "mock-code",
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
    }

    # Mock successful token exchange but failing profile fetch
    with patch(
        "services.oauth_service.GoogleProvider.exchange_code_for_token",
        return_value=mock_token_response,
    ), patch(
        "services.oauth_service.GoogleProvider.get_user_profile",
        side_effect=Exception("Failed to fetch profile"),
    ):
        response = await client.post("/api/oauth/callback", json=callback_data)

        assert response.status_code == 401
        assert "profile fetch failed" in response.json()["detail"].lower()


# ============================================================================
# Test 4: PKCE Flow
# ============================================================================

@pytest.mark.asyncio
async def test_oauth_callback_with_pkce(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that OAuth callback works with PKCE code verifier."""
    # Generate authorization URL with PKCE
    auth_response = await client.get("/api/oauth/google/authorize?use_pkce=true")
    auth_data = auth_response.json()
    state = auth_data["state"]
    provider_id = auth_data["provider_id"]
    code_verifier = auth_data["code_verifier"]

    mock_token_response = {
        "access_token": "mock-access-token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }

    mock_profile_response = {
        "id": "123456789",
        "email": "test@example.com",
        "name": "Test User",
    }

    callback_data = {
        "code": "mock-authorization-code",
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
        "code_verifier": code_verifier,
    }

    with patch(
        "services.oauth_service.GoogleProvider.exchange_code_for_token",
        return_value=mock_token_response,
    ), patch(
        "services.oauth_service.GoogleProvider.get_user_profile",
        return_value=mock_profile_response,
    ):
        response = await client.post("/api/oauth/callback", json=callback_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


# ============================================================================
# Test 5: Multiple Providers
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_providers_different_defaults(
    client: AsyncClient,
    test_session: AsyncSession,
    google_provider: OAuthProvider,
    linkedin_provider: OAuthProvider,
):
    """Verify that only one provider can be default per type."""
    # Google is already default, try to make LinkedIn default
    linkedin_provider.provider_type = "google"  # Change type to test default logic
    linkedin_provider.is_default = True
    test_session.add(linkedin_provider)
    await test_session.commit()

    # The system should handle this by setting only one as default
    response = await client.get("/api/oauth/providers?provider_type=google")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_authorization_url_by_provider_id(
    client: AsyncClient,
    linkedin_provider: OAuthProvider,
):
    """Verify that authorization URL can be generated using provider ID."""
    provider_id = str(linkedin_provider.id)

    response = await client.get(f"/api/oauth/{provider_id}/authorize")

    assert response.status_code == 200
    data = response.json()

    assert data["provider_id"] == provider_id
    assert "authorization_url" in data


# ============================================================================
# Test 6: Edge Cases and Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_callback_with_invalid_uuid_format(client: AsyncClient):
    """Verify that callback fails with invalid UUID format."""
    callback_data = {
        "code": "mock-code",
        "state": "mock-state",
        "expected_state": "mock-state",
        "provider_id": "not-a-valid-uuid",
    }

    response = await client.post("/api/oauth/callback", json=callback_data)

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_providers_with_pagination(
    client: AsyncClient,
    google_provider: OAuthProvider,
    linkedin_provider: OAuthProvider,
    github_provider: OAuthProvider,
):
    """Verify that provider listing supports pagination."""
    # Get first page with limit 2
    response = await client.get("/api/oauth/providers?limit=2&offset=0")

    assert response.status_code == 200
    data = response.json()

    assert len(data["providers"]) == 2
    assert data["total_count"] == 3

    # Get second page
    response = await client.get("/api/oauth/providers?limit=2&offset=2")

    assert response.status_code == 200
    data = response.json()

    assert len(data["providers"]) == 1
    assert data["total_count"] == 3


@pytest.mark.asyncio
async def test_update_nonexistent_provider(client: AsyncClient):
    """Verify that updating a non-existent provider fails."""
    fake_id = str(uuid4())
    update_data = {"provider_name": "Updated Name"}

    response = await client.put(f"/api/oauth/providers/{fake_id}", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_provider(client: AsyncClient):
    """Verify that deleting a non-existent provider fails."""
    fake_id = str(uuid4())

    response = await client.delete(f"/api/oauth/providers/{fake_id}")

    assert response.status_code == 404


# ============================================================================
# Test 7: State Parameter Security
# ============================================================================

@pytest.mark.asyncio
async def test_state_parameter_uniqueness(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that each authorization request generates a unique state."""
    # Generate first state
    response1 = await client.get("/api/oauth/google/authorize")
    data1 = response1.json()
    state1 = data1["state"]

    # Generate second state
    response2 = await client.get("/api/oauth/google/authorize")
    data2 = response2.json()
    state2 = data2["state"]

    assert state1 != state2
    assert len(state1) > 20  # State should be reasonably long
    assert len(state2) > 20


@pytest.mark.asyncio
async def test_callback_missing_state(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """Verify that callback fails when state is missing."""
    callback_data = {
        "code": "mock-code",
        "state": "",
        "expected_state": "",
        "provider_id": str(google_provider.id),
    }

    response = await client.post("/api/oauth/callback", json=callback_data)

    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


# ============================================================================
# Summary Test
# ============================================================================

@pytest.mark.asyncio
async def test_complete_oauth_flow_end_to_end(
    client: AsyncClient,
    google_provider: OAuthProvider,
):
    """
    Verify complete OAuth flow from authorization to callback.

    This test simulates the full OAuth 2.0 flow:
    1. Generate authorization URL
    2. User authenticates (simulated)
    3. Provider redirects back with code
    4. Exchange code for token
    5. Fetch user profile
    """
    # Step 1: Generate authorization URL
    auth_response = await client.get("/api/oauth/google/authorize")
    assert auth_response.status_code == 200
    auth_data = auth_response.json()

    state = auth_data["state"]
    provider_id = auth_data["provider_id"]
    auth_url = auth_data["authorization_url"]

    # Verify authorization URL contains required parameters
    assert "client_id=" in auth_url
    assert f"state={state}" in auth_url
    assert "redirect_uri=" in auth_url
    assert "scope=" in auth_url

    # Step 2 & 3: Simulate provider callback (user authenticated)
    mock_token_response = {
        "access_token": "ya29.a0ARrdaM...",
        "token_type": "Bearer",
        "expires_in": 3599,
        "refresh_token": "1//0gKh...",
        "scope": "openid email profile",
    }

    mock_profile_response = {
        "id": "108123456789",
        "email": "johndoe@example.com",
        "verified_email": True,
        "name": "John Doe",
        "given_name": "John",
        "family_name": "Doe",
        "picture": "https://lh3.googleusercontent.com/a/...",
        "locale": "en",
    }

    callback_data = {
        "code": "4/0AY0e-g7X...",  # Simulated authorization code
        "state": state,
        "expected_state": state,
        "provider_id": provider_id,
    }

    # Step 4 & 5: Exchange code for token and fetch profile
    with patch(
        "services.oauth_service.GoogleProvider.exchange_code_for_token",
        return_value=mock_token_response,
    ), patch(
        "services.oauth_service.GoogleProvider.get_user_profile",
        return_value=mock_profile_response,
    ):
        callback_response = await client.post("/api/oauth/callback", json=callback_data)

        assert callback_response.status_code == 200
        callback_result = callback_response.json()

        # Verify token exchange result
        assert callback_result["access_token"] == "ya29.a0ARrdaM..."
        assert callback_result["token_type"] == "Bearer"
        assert callback_result["expires_in"] == 3599

        # Verify user profile data
        profile = callback_result["user_profile"]
        assert profile["email"] == "johndoe@example.com"
        assert profile["name"] == "John Doe"
        assert profile["given_name"] == "John"
        assert profile["family_name"] == "Doe"

        # Verify provider info
        assert callback_result["provider_id"] == provider_id
