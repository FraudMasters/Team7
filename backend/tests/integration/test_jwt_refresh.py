"""
Integration tests for JWT refresh flow.

This test suite validates the end-to-end integration between:
- Frontend (simulated via HTTP requests)
- Backend auth endpoints (/api/auth/refresh)
- JWT token validation and generation
- Refresh token storage and rotation
- Database token tracking and revocation
- User account status validation

Test Coverage:
- Successful refresh token usage to obtain new access token
- Refresh token validation (format, signature, expiration)
- Revoked refresh token rejection
- Expired refresh token handling
- Invalid token format rejection
- Wrong token type rejection (access token used for refresh)
- Inactive user account handling
- Token expiration time verification
- Token payload validation
- Database synchronization (token storage and revocation)
"""
import asyncio
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from main import app
from database import get_db
from models.user import User
from models.refresh_token import RefreshToken
from config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_jwt_refresh.db"


@pytest.fixture
async def test_db():
    """
    Create test database session.

    Yields:
        AsyncSession instance for testing
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """
    Create test client with database override.

    Args:
        test_db: Test database session

    Yields:
        AsyncClient instance for making HTTP requests
    """
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def registered_user(client: AsyncClient):
    """
    Create and register a test user.

    Args:
        client: HTTP test client

    Returns:
        Dictionary with user credentials
    """
    user_data = {
        "email": "refreshtest@example.com",
        "password": "RefreshPass123!",
        "full_name": "Refresh Test User"
    }

    response = await client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest.fixture
async def user_with_tokens(client: AsyncClient, registered_user: dict):
    """
    Create a user and obtain authentication tokens.

    Args:
        client: HTTP test client
        registered_user: Registered user credentials

    Returns:
        Dictionary with user data, access_token, and refresh_token
    """
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }

    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200

    response_data = response.json()

    return {
        "email": registered_user["email"],
        "password": registered_user["password"],
        "access_token": response_data["access_token"],
        "refresh_token": response_data["refresh_token"],
        "user_id": response_data["user"]["id"]
    }


class TestSuccessfulRefresh:
    """Tests for successful JWT refresh flow."""

    @pytest.mark.asyncio
    async def test_successful_refresh_returns_new_access_token(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that a valid refresh token successfully returns a new access token."""
        # Make refresh request
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Verify successful response
        assert response.status_code == 200

        # Verify response structure
        response_data = response.json()
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert "expires_in" in response_data
        assert response_data["token_type"] == "bearer"

        # Verify new access token is different from old one
        assert response_data["access_token"] != user_with_tokens["access_token"]

        # Verify new token is valid
        new_access_token = response_data["access_token"]
        decoded = pyjwt.decode(
            new_access_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        assert decoded["email"] == user_with_tokens["email"]
        assert decoded["type"] == "access"

    @pytest.mark.asyncio
    async def test_new_access_token_has_correct_expiration(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that the new access token has the correct expiration time."""
        # Make refresh request
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        response_data = response.json()

        # Verify expires_in matches settings
        expected_expires_in = settings.access_token_expire_minutes * 60
        assert response_data["expires_in"] == expected_expires_in

        # Decode token and verify expiration claim
        new_access_token = response_data["access_token"]
        decoded = pyjwt.decode(
            new_access_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # Verify expiration is set correctly (within 1 minute tolerance)
        exp_timestamp = decoded["exp"]
        iat_timestamp = decoded["iat"]
        token_lifetime_seconds = exp_timestamp - iat_timestamp
        expected_lifetime = settings.access_token_expire_minutes * 60

        # Allow 60 second tolerance for test execution time
        assert abs(token_lifetime_seconds - expected_lifetime) <= 60

    @pytest.mark.asyncio
    async def test_new_access_token_contains_user_data(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that the new access token contains correct user data."""
        # Make refresh request
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        new_access_token = response.json()["access_token"]

        # Decode and verify token claims
        decoded = pyjwt.decode(
            new_access_token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # Verify user information
        assert "sub" in decoded  # user_id
        assert "email" in decoded
        assert decoded["email"] == user_with_tokens["email"]
        assert decoded["type"] == "access"
        assert "iat" in decoded  # issued at
        assert "exp" in decoded  # expiration

    @pytest.mark.asyncio
    async def test_refresh_token_can_be_used_multiple_times(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that a refresh token can be used multiple times (if rotation is not enforced)."""
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}

        # First refresh
        response1 = await client.post("/api/auth/refresh", json=refresh_data)
        assert response1.status_code == 200
        token1 = response1.json()["access_token"]

        # Small delay to ensure different issued-at times
        await asyncio.sleep(1)

        # Second refresh with same refresh token
        response2 = await client.post("/api/auth/refresh", json=refresh_data)

        # If token rotation is NOT enforced, this should succeed
        # If token rotation IS enforced, this would fail with 401
        # Adjust this test based on your implementation
        if response2.status_code == 200:
            token2 = response2.json()["access_token"]
            # Tokens should be different due to different iat
            assert token1 != token2
        else:
            # Token rotation is enforced
            assert response2.status_code == 401


class TestInvalidRefreshToken:
    """Tests for invalid refresh token handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_refresh_token_rejected(self, client: AsyncClient):
        """Test that a non-existent refresh token is rejected."""
        # Create a valid-looking but non-existent token
        fake_token_data = {
            "sub": "nonexistent-user-id",
            "email": "fake@example.com",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
        }
        fake_token = pyjwt.encode(
            fake_token_data,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        refresh_data = {"refresh_token": fake_token}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected (not in database)
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self, client: AsyncClient):
        """Test that a malformed JWT token is rejected."""
        refresh_data = {"refresh_token": "not.a.valid.jwt.token"}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected with 401 or 422
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_empty_token_rejected(self, client: AsyncClient):
        """Test that an empty token is rejected."""
        refresh_data = {"refresh_token": ""}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected with 422 (validation error)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_token_with_invalid_signature_rejected(self, client: AsyncClient):
        """Test that a token with an invalid signature is rejected."""
        # Create a token with wrong secret key
        fake_token_data = {
            "sub": "user-id",
            "email": "test@example.com",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
        }
        fake_token = pyjwt.encode(
            fake_token_data,
            "wrong-secret-key",
            algorithm=settings.algorithm
        )

        refresh_data = {"refresh_token": fake_token}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401


class TestExpiredRefreshToken:
    """Tests for expired refresh token handling."""

    @pytest.mark.asyncio
    async def test_expired_refresh_token_rejected(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        user_with_tokens: dict
    ):
        """Test that an expired refresh token is rejected."""
        # Create an expired token
        expired_token_data = {
            "sub": user_with_tokens["user_id"],
            "email": user_with_tokens["email"],
            "type": "refresh",
            "exp": datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            "iat": datetime.utcnow() - timedelta(days=8)
        }
        expired_token = pyjwt.encode(
            expired_token_data,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        # Store it in database with expired timestamp
        refresh_token_record = RefreshToken(
            user_id=user_with_tokens["user_id"],
            token=expired_token,
            expires_at=datetime.utcnow() - timedelta(days=1),
            is_revoked=False
        )
        test_db.add(refresh_token_record)
        await test_db.commit()

        # Try to use expired token
        refresh_data = {"refresh_token": expired_token}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401
        response_detail = response.json()["detail"]
        assert "expired" in response_detail.lower() or "invalid" in response_detail.lower()


class TestRevokedRefreshToken:
    """Tests for revoked refresh token handling."""

    @pytest.mark.asyncio
    async def test_revoked_refresh_token_rejected(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        user_with_tokens: dict
    ):
        """Test that a revoked refresh token is rejected."""
        # Revoke the refresh token in database
        result = await test_db.execute(
            select(RefreshToken).where(
                RefreshToken.token == user_with_tokens["refresh_token"]
            )
        )
        refresh_token_record = result.scalar_one_or_none()

        if refresh_token_record:
            refresh_token_record.is_revoked = True
            refresh_token_record.revoked_at = datetime.utcnow()
            await test_db.commit()

        # Try to use revoked token
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]


class TestWrongTokenType:
    """Tests for using wrong token type."""

    @pytest.mark.asyncio
    async def test_access_token_cannot_be_used_for_refresh(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that an access token cannot be used to refresh."""
        # Try to use access token as refresh token
        refresh_data = {"refresh_token": user_with_tokens["access_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_without_type_claim_rejected(self, client: AsyncClient):
        """Test that a token without a type claim is rejected."""
        # Create a token without type claim
        token_data = {
            "sub": "user-id",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
            # Missing "type" claim
        }
        token = pyjwt.encode(
            token_data,
            settings.secret_key,
            algorithm=settings.algorithm
        )

        refresh_data = {"refresh_token": token}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401


class TestInactiveUserAccount:
    """Tests for inactive user account handling."""

    @pytest.mark.asyncio
    async def test_inactive_user_cannot_refresh(
        self,
        client: AsyncClient,
        test_db: AsyncSession,
        user_with_tokens: dict
    ):
        """Test that an inactive user cannot refresh their token."""
        # Deactivate the user account
        result = await test_db.execute(
            select(User).where(User.email == user_with_tokens["email"])
        )
        user = result.scalar_one_or_none()

        if user:
            user.is_active = False
            await test_db.commit()

        # Try to refresh token
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}
        response = await client.post("/api/auth/refresh", json=refresh_data)

        # Should be rejected
        assert response.status_code == 401
        response_detail = response.json()["detail"]
        assert "inactive" in response_detail.lower() or "not found" in response_detail.lower()


class TestTokenDatabaseSynchronization:
    """Tests for token database synchronization."""

    @pytest.mark.asyncio
    async def test_refresh_token_exists_in_database(
        self,
        test_db: AsyncSession,
        user_with_tokens: dict
    ):
        """Test that refresh token is stored in database after login."""
        # Query database for refresh token
        result = await test_db.execute(
            select(RefreshToken).where(
                RefreshToken.token == user_with_tokens["refresh_token"]
            )
        )
        token_record = result.scalar_one_or_none()

        # Verify token exists in database
        assert token_record is not None
        assert token_record.user_id == user_with_tokens["user_id"]
        assert token_record.is_revoked == False
        assert token_record.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_refresh_token_expiration_stored_correctly(
        self,
        test_db: AsyncSession,
        user_with_tokens: dict
    ):
        """Test that refresh token expiration is stored correctly in database."""
        # Query database for refresh token
        result = await test_db.execute(
            select(RefreshToken).where(
                RefreshToken.token == user_with_tokens["refresh_token"]
            )
        )
        token_record = result.scalar_one_or_none()

        assert token_record is not None

        # Verify expiration is in the future
        assert token_record.expires_at > datetime.utcnow()

        # Verify expiration is approximately correct (within 1 hour tolerance)
        expected_expires_at = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
        time_diff = abs((token_record.expires_at - expected_expires_at).total_seconds())
        assert time_diff <= 3600  # Within 1 hour


class TestConcurrentRefresh:
    """Tests for concurrent refresh token usage."""

    @pytest.mark.asyncio
    async def test_concurrent_refresh_requests(
        self,
        client: AsyncClient,
        user_with_tokens: dict
    ):
        """Test that concurrent refresh requests are handled correctly."""
        refresh_data = {"refresh_token": user_with_tokens["refresh_token"]}

        # Make two concurrent refresh requests
        responses = await asyncio.gather(
            client.post("/api/auth/refresh", json=refresh_data),
            client.post("/api/auth/refresh", json=refresh_data),
            return_exceptions=True
        )

        # At least one should succeed
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        assert success_count >= 1

        # If token rotation is enforced, only one should succeed
        # If not enforced, both can succeed
        # This depends on your implementation


class TestRefreshTokenPayload:
    """Tests for refresh token payload validation."""

    @pytest.mark.asyncio
    async def test_refresh_token_payload_structure(
        self,
        user_with_tokens: dict
    ):
        """Test that refresh token has the correct payload structure."""
        # Decode refresh token (without verification for inspection)
        decoded = pyjwt.decode(
            user_with_tokens["refresh_token"],
            options={"verify_signature": False}
        )

        # Verify required claims
        assert "sub" in decoded  # user_id
        assert "email" in decoded
        assert "type" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

        # Verify token type
        assert decoded["type"] == "refresh"

        # Verify user data
        assert decoded["email"] == user_with_tokens["email"]

    @pytest.mark.asyncio
    async def test_refresh_token_is_long_lived(
        self,
        user_with_tokens: dict
    ):
        """Test that refresh token has a longer expiration than access token."""
        # Decode both tokens
        access_decoded = pyjwt.decode(
            user_with_tokens["access_token"],
            options={"verify_signature": False}
        )
        refresh_decoded = pyjwt.decode(
            user_with_tokens["refresh_token"],
            options={"verify_signature": False}
        )

        # Verify refresh token expires later than access token
        assert refresh_decoded["exp"] > access_decoded["exp"]

        # Verify refresh token lifetime is significantly longer
        access_lifetime = access_decoded["exp"] - access_decoded["iat"]
        refresh_lifetime = refresh_decoded["exp"] - refresh_decoded["iat"]

        # Refresh should be at least 10x longer than access
        assert refresh_lifetime > access_lifetime * 10
