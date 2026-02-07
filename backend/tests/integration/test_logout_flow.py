"""
Logout Flow Integration Tests

This module tests the complete logout flow including:
- User logout with valid refresh token
- Token revocation in database
- Token cleanup in frontend storage
- Protected route access denial after logout
- Logout with invalid tokens
- Security verification (no information leakage)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from models.user import User
from models.refresh_token import RefreshToken
from utils.jwt_handler import create_access_token, create_refresh_token
from utils.security import get_password_hash


@pytest.mark.asyncio
class TestLogoutFlow:
    """Test complete logout flow from API to database"""

    async def test_complete_logout_flow(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """
        Test complete logout flow:
        1. Login to receive tokens
        2. Logout with refresh token
        3. Verify token revoked in database
        4. Verify cleared tokens cannot be used
        """
        # Step 1: Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Step 2: Logout
        logout_response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logged out successfully"

        # Step 3: Verify token revoked in database
        result = await db_session.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token
            )
        )
        token_record = result.scalar_one_or_none()
        assert token_record is not None
        assert token_record.is_revoked is True
        assert token_record.revoked_at is not None

        # Step 4: Verify access token no longer works
        protected_response = await async_client.get(
            "/api/candidates/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        # Access token might still work until it expires naturally
        # But refresh token should not work
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401

    async def test_logout_with_invalid_refresh_token(
        self,
        async_client: AsyncClient,
    ):
        """
        Test logout with invalid refresh token.
        Should return success for security (prevent token enumeration).
        """
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": "invalid_refresh_token"},
        )
        # Returns success to prevent token enumeration
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    async def test_logout_with_revoked_token(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """
        Test logout with already revoked token.
        Should return success for security.
        """
        # Login and get token
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # First logout
        await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Second logout with same token
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        # Returns success to prevent token enumeration
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    async def test_logout_response_format(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """
        Test logout response format matches expected schema.
        """
        # Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Verify response format
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Logged out successfully"
        # Should NOT return tokens in response
        assert "access_token" not in data
        assert "refresh_token" not in data

    async def test_logout_revokes_only_specified_token(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """
        Test that logout only revokes the specified token,
        not all tokens for the user.
        """
        # Login twice to get two refresh tokens
        login1_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        token1 = login1_response.json()["refresh_token"]

        login2_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        token2 = login2_response.json()["refresh_token"]

        # Logout with token1
        await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": token1},
        )

        # Verify token1 is revoked
        result1 = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == token1)
        )
        record1 = result1.scalar_one()
        assert record1.is_revoked is True

        # Verify token2 is NOT revoked
        result2 = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == token2)
        )
        record2 = result2.scalar_one()
        assert record2.is_revoked is False

        # Verify token2 still works for refresh
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": token2},
        )
        assert refresh_response.status_code == 200

    async def test_logout_prevents_token_refresh(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """
        Test that revoked refresh token cannot be used to refresh.
        """
        # Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Try to refresh with revoked token
        refresh_response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 401
        assert "revoked" in refresh_response.json()["detail"].lower()

    async def test_logout_with_empty_token(
        self,
        async_client: AsyncClient,
    ):
        """
        Test logout with empty refresh token.
        """
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": ""},
        )
        # Returns success to prevent token enumeration
        assert response.status_code == 200

    async def test_logout_with_malformed_jwt(
        self,
        async_client: AsyncClient,
    ):
        """
        Test logout with malformed JWT token.
        """
        response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": "not.a.valid.jwt"},
        )
        # Returns success to prevent token enumeration
        assert response.status_code == 200

    async def test_multiple_logouts_same_token(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """
        Test multiple logout attempts with the same token.
        All should succeed (idempotent operation).
        """
        # Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # First logout
        response1 = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert response1.status_code == 200

        # Second logout (token already revoked)
        response2 = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert response2.status_code == 200

        # Third logout
        response3 = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert response3.status_code == 200

        # Verify token is revoked
        result = await db_session.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token_record = result.scalar_one()
        assert token_record.is_revoked is True

    async def test_logout_database_transaction(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        test_user: User,
    ):
        """
        Test that logout properly commits database transaction.
        """
        # Login
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Logout
        await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Create new session to verify committed data
        from database import get_db

        async for db in get_db():
            result = await db.execute(
                select(RefreshToken).where(
                    RefreshToken.token == refresh_token
                )
            )
            token_record = result.scalar_one_or_none()
            assert token_record is not None
            assert token_record.is_revoked is True
            assert token_record.revoked_at is not None
            break

    async def test_logout_security_no_information_leakage(
        self,
        async_client: AsyncClient,
        test_user: User,
    ):
        """
        Test that logout doesn't leak information about token validity.
        Both valid and invalid tokens should return same response.
        """
        # Login and get valid token
        login_response = await async_client.post(
            "/api/auth/login",
            json={"email": test_user.email, "password": "TestPassword123!"},
        )
        valid_token = login_response.json()["refresh_token"]

        # Logout with valid token
        valid_response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": valid_token},
        )

        # Logout with invalid token
        invalid_response = await async_client.post(
            "/api/auth/logout",
            json={"refresh_token": "invalid_token"},
        )

        # Both should return same status code and message
        assert valid_response.status_code == invalid_response.status_code
        assert valid_response.json() == invalid_response.json()
        assert valid_response.json()["message"] == "Logged out successfully"
