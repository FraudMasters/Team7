"""
Unit tests for authentication middleware.

Tests cover JWT token validation, role-based authorization,
TokenData model validation, and authentication dependencies.
"""
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from pydantic import ValidationError

from middleware.auth import (
    TokenData,
    AuthMiddleware,
    get_current_token,
    get_optional_token,
    require_role,
    require_any_role,
    require_all_roles,
    auth_middleware,
)


class TestTokenData:
    """Tests for TokenData model validation."""

    def test_valid_token_data(self):
        """Test creating valid TokenData with all required fields."""
        token_data = TokenData(
            sub="user123",
            username="testuser",
            email="test@example.com",
            roles=["Admin", "Recruiter"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )
        assert token_data.sub == "user123"
        assert token_data.username == "testuser"
        assert token_data.email == "test@example.com"
        assert token_data.roles == ["Admin", "Recruiter"]
        assert token_data.exp > 0

    def test_token_data_with_minimal_fields(self):
        """Test creating TokenData with only required fields."""
        token_data = TokenData(
            sub="user123",
            username="testuser",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )
        assert token_data.sub == "user123"
        assert token_data.username == "testuser"
        assert token_data.email is None
        assert token_data.roles == []
        assert token_data.exp > 0

    def test_token_data_missing_required_field_sub(self):
        """Test TokenData validation fails without 'sub' field."""
        with pytest.raises(ValidationError):
            TokenData(
                username="testuser",
                exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
            )

    def test_token_data_missing_required_field_username(self):
        """Test TokenData validation fails without 'username' field."""
        with pytest.raises(ValidationError):
            TokenData(
                sub="user123",
                exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
            )

    def test_token_data_missing_required_field_exp(self):
        """Test TokenData validation fails without 'exp' field."""
        with pytest.raises(ValidationError):
            TokenData(
                sub="user123",
                username="testuser",
            )

    def test_token_data_default_empty_roles(self):
        """Test TokenData roles field defaults to empty list."""
        token_data = TokenData(
            sub="user123",
            username="testuser",
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )
        assert token_data.roles == []

    def test_token_data_optional_email(self):
        """Test TokenData email field is optional."""
        token_data = TokenData(
            sub="user123",
            username="testuser",
            email=None,
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )
        assert token_data.email is None


class TestAuthMiddlewareDecodeToken:
    """Tests for AuthMiddleware.decode_token() method."""

    def test_decode_valid_jwt_token(self):
        """Test decoding a valid JWT token with all claims."""
        # Create a mock JWT token
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "realm_access": {"roles": ["Admin", "Recruiter"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        # Decode token
        credentials_exception = HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )
        result = auth_middleware.decode_token(token, credentials_exception)

        # Verify decoded data
        assert isinstance(result, TokenData)
        assert result.sub == "user123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.roles == ["Admin", "Recruiter"]
        assert result.exp == int(exp_time.timestamp())

    def test_decode_token_without_email(self):
        """Test decoding token without optional email claim."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["Viewer"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        result = auth_middleware.decode_token(token, credentials_exception)

        assert result.sub == "user123"
        assert result.username == "testuser"
        assert result.email is None
        assert result.roles == ["Viewer"]

    def test_decode_token_without_preferred_username(self):
        """Test decoding token falls back to 'sub' when 'preferred_username' is missing."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "realm_access": {"roles": ["Admin"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        result = auth_middleware.decode_token(token, credentials_exception)

        assert result.username == "user123"  # Should fall back to sub

    def test_decode_token_without_realm_access(self):
        """Test decoding token without realm_access returns empty roles list."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        result = auth_middleware.decode_token(token, credentials_exception)

        assert result.roles == []

    def test_decode_token_with_empty_roles(self):
        """Test decoding token with empty roles list."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "realm_access": {"roles": []},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        result = auth_middleware.decode_token(token, credentials_exception)

        assert result.roles == []

    def test_decode_token_missing_sub_raises_exception(self):
        """Test decoding token without 'sub' claim raises HTTPException."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "preferred_username": "testuser",
            "realm_access": {"roles": ["Admin"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        with pytest.raises(HTTPException) as exc_info:
            auth_middleware.decode_token(token, credentials_exception)

        assert exc_info.value.status_code == 401

    def test_decode_invalid_jwt_token_raises_exception(self):
        """Test decoding invalid JWT token raises HTTPException."""
        invalid_token = "invalid.jwt.token"

        credentials_exception = HTTPException(status_code=401, detail="Invalid")
        with pytest.raises(HTTPException) as exc_info:
            auth_middleware.decode_token(invalid_token, credentials_exception)

        assert exc_info.value.status_code == 401


class TestGetCurrentToken:
    """Tests for get_current_token dependency."""

    @pytest.mark.asyncio
    async def test_get_current_token_with_valid_token(self):
        """Test get_current_token returns TokenData for valid token."""
        # Create a mock JWT token
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "realm_access": {"roles": ["Admin"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        # Create mock request and credentials
        mock_request = Mock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token

        # Call dependency
        result = await get_current_token(mock_request, mock_credentials)

        # Verify result
        assert isinstance(result, TokenData)
        assert result.sub == "user123"
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.roles == ["Admin"]

        # Verify token data stored in request state
        assert hasattr(mock_request.state, "token_data")
        assert mock_request.state.token_data == result

    @pytest.mark.asyncio
    async def test_get_current_token_without_credentials_raises_401(self):
        """Test get_current_token raises 401 when credentials is None."""
        mock_request = Mock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_token(mock_request, None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_token_with_invalid_token_raises_401(self):
        """Test get_current_token raises 401 for invalid token."""
        mock_request = Mock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_token(mock_request, mock_credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in exc_info.value.detail


class TestGetOptionalToken:
    """Tests for get_optional_token dependency."""

    @pytest.mark.asyncio
    async def test_get_optional_token_with_valid_token(self):
        """Test get_optional_token returns TokenData for valid token."""
        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "user123",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "realm_access": {"roles": ["Viewer"]},
            "exp": int(exp_time.timestamp()),
        }
        token = jwt.encode(payload, "secret", algorithm="HS256")

        mock_request = Mock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token

        result = await get_optional_token(mock_request, mock_credentials)

        assert isinstance(result, TokenData)
        assert result.sub == "user123"
        assert result.username == "testuser"
        assert mock_request.state.token_data == result

    @pytest.mark.asyncio
    async def test_get_optional_token_without_credentials_returns_none(self):
        """Test get_optional_token returns None when credentials is None."""
        mock_request = Mock()

        result = await get_optional_token(mock_request, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_optional_token_with_invalid_token_returns_none(self):
        """Test get_optional_token returns None for invalid token."""
        mock_request = Mock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid.jwt.token"

        result = await get_optional_token(mock_request, mock_credentials)

        assert result is None


class TestRequireRole:
    """Tests for require_role() factory function."""

    @pytest.mark.asyncio
    async def test_require_role_with_matching_role_grants_access(self):
        """Test require_role grants access when user has required role."""
        # Create mock token data with Admin role
        token_data = TokenData(
            sub="user123",
            username="adminuser",
            roles=["Admin", "Recruiter"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        # Create require_role dependency
        admin_role_dep = require_role("Admin")

        # Mock get_current_token to return our token_data
        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await admin_role_dep(token_data)

        # Should return token_data unchanged
        assert result == token_data
        assert result.roles == ["Admin", "Recruiter"]

    @pytest.mark.asyncio
    async def test_require_role_without_matching_role_raises_403(self):
        """Test require_role raises 403 when user lacks required role."""
        token_data = TokenData(
            sub="user123",
            username="vieweruser",
            roles=["Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        admin_role_dep = require_role("Admin")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await admin_role_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail
        assert "Admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_role_with_multiple_roles_matching(self):
        """Test require_role works when user has multiple roles including required."""
        token_data = TokenData(
            sub="user123",
            username="superuser",
            roles=["Viewer", "Recruiter", "Admin"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        recruiter_role_dep = require_role("Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await recruiter_role_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_role_case_sensitive(self):
        """Test require_role is case sensitive."""
        token_data = TokenData(
            sub="user123",
            username="testuser",
            roles=["admin"],  # lowercase
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        admin_role_dep = require_role("Admin")  # uppercase

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await admin_role_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireAnyRole:
    """Tests for require_any_role() factory function."""

    @pytest.mark.asyncio
    async def test_require_any_role_with_first_role_grants_access(self):
        """Test require_any_role grants access when user has first required role."""
        token_data = TokenData(
            sub="user123",
            username="recruiteruser",
            roles=["Recruiter"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        multi_role_dep = require_any_role("Admin", "Recruiter", "Viewer")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await multi_role_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_any_role_with_second_role_grants_access(self):
        """Test require_any_role grants access when user has second required role."""
        token_data = TokenData(
            sub="user123",
            username="vieweruser",
            roles=["Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        multi_role_dep = require_any_role("Admin", "Recruiter", "Viewer")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await multi_role_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_any_role_with_no_matching_role_raises_403(self):
        """Test require_any_role raises 403 when user has none of the required roles."""
        token_data = TokenData(
            sub="user123",
            username="guestuser",
            roles=["Guest"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        multi_role_dep = require_any_role("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await multi_role_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail
        assert "Admin, Recruiter" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_any_role_with_multiple_matching_roles(self):
        """Test require_any_role works when user has multiple matching roles."""
        token_data = TokenData(
            sub="user123",
            username="superuser",
            roles=["Admin", "Recruiter", "Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        multi_role_dep = require_any_role("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await multi_role_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_any_role_with_empty_roles_raises_403(self):
        """Test require_any_role raises 403 when user has no roles."""
        token_data = TokenData(
            sub="user123",
            username="norolesuser",
            roles=[],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        multi_role_dep = require_any_role("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await multi_role_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireAllRoles:
    """Tests for require_all_roles() factory function."""

    @pytest.mark.asyncio
    async def test_require_all_roles_with_all_roles_grants_access(self):
        """Test require_all_roles grants access when user has all required roles."""
        token_data = TokenData(
            sub="user123",
            username="superuser",
            roles=["Admin", "Recruiter", "Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        all_roles_dep = require_all_roles("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await all_roles_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_all_roles_missing_one_role_raises_403(self):
        """Test require_all_roles raises 403 when user is missing one required role."""
        token_data = TokenData(
            sub="user123",
            username="recruiteruser",
            roles=["Recruiter", "Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        all_roles_dep = require_all_roles("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await all_roles_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient permissions" in exc_info.value.detail
        assert "Admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_all_roles_with_single_role(self):
        """Test require_all_roles works with a single required role."""
        token_data = TokenData(
            sub="user123",
            username="adminuser",
            roles=["Admin"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        single_role_dep = require_all_roles("Admin")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await single_role_dep(token_data)

        assert result == token_data

    @pytest.mark.asyncio
    async def test_require_all_roles_with_no_roles_raises_403(self):
        """Test require_all_roles raises 403 when user has no roles."""
        token_data = TokenData(
            sub="user123",
            username="norolesuser",
            roles=[],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        all_roles_dep = require_all_roles("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            with pytest.raises(HTTPException) as exc_info:
                await all_roles_dep(token_data)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        # Should mention both missing roles
        assert "Admin" in exc_info.value.detail
        assert "Recruiter" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_all_roles_with_extra_roles_grants_access(self):
        """Test require_all_roles grants access when user has extra roles beyond required."""
        token_data = TokenData(
            sub="user123",
            username="superuser",
            roles=["Admin", "Recruiter", "Viewer", "SuperUser"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        all_roles_dep = require_all_roles("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=token_data):
            result = await all_roles_dep(token_data)

        assert result == token_data


class TestIntegrationScenarios:
    """Integration test scenarios for authentication and authorization."""

    @pytest.mark.asyncio
    async def test_admin_access_to_admin_endpoint(self):
        """Test Admin user can access admin-only endpoint."""
        admin_token = TokenData(
            sub="admin123",
            username="admin",
            roles=["Admin"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        admin_dep = require_role("Admin")

        with patch("middleware.auth.get_current_token", return_value=admin_token):
            result = await admin_dep(admin_token)

        assert result.sub == "admin123"

    @pytest.mark.asyncio
    async def test_recruiter_denied_access_to_admin_endpoint(self):
        """Test Recruiter user cannot access admin-only endpoint."""
        recruiter_token = TokenData(
            sub="recruiter123",
            username="recruiter",
            roles=["Recruiter"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        admin_dep = require_role("Admin")

        with patch("middleware.auth.get_current_token", return_value=recruiter_token):
            with pytest.raises(HTTPException) as exc_info:
                await admin_dep(recruiter_token)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_recruiter_can_access_recruiter_endpoints(self):
        """Test Recruiter user can access recruiter endpoints."""
        recruiter_token = TokenData(
            sub="recruiter123",
            username="recruiter",
            roles=["Recruiter"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        recruiter_dep = require_any_role("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=recruiter_token):
            result = await recruiter_dep(recruiter_token)

        assert result.username == "recruiter"

    @pytest.mark.asyncio
    async def test_viewer_read_only_access(self):
        """Test Viewer can access read-only but not write endpoints."""
        viewer_token = TokenData(
            sub="viewer123",
            username="viewer",
            roles=["Viewer"],
            exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
        )

        # Viewer should be able to access read endpoints (any authenticated user)
        read_dep = get_current_token
        mock_request = Mock()
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)

        exp_time = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": "viewer123",
            "preferred_username": "viewer",
            "realm_access": {"roles": ["Viewer"]},
            "exp": int(exp_time.timestamp()),
        }
        mock_credentials.credentials = jwt.encode(payload, "secret", algorithm="HS256")

        result = await read_dep(mock_request, mock_credentials)
        assert result.roles == ["Viewer"]

        # But should not be able to access admin write endpoints
        admin_write_dep = require_any_role("Admin", "Recruiter")

        with patch("middleware.auth.get_current_token", return_value=viewer_token):
            with pytest.raises(HTTPException) as exc_info:
                await admin_write_dep(viewer_token)

        assert exc_info.value.status_code == 403
