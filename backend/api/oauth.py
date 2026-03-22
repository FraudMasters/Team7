"""
OAuth 2.0 endpoints for social authentication integration.

This module provides endpoints for OAuth 2.0 SSO integration with identity
providers such as Google, GitHub, LinkedIn, and Microsoft. It handles OAuth
authorization flow, provider configuration management, and callback handling.
"""
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from database import get_db
from models.oauth_provider import OAuthProvider
from services.oauth_service import get_oauth_service, GoogleProvider, LinkedInProvider, GitHubProvider

logger = logging.getLogger(__name__)

router = APIRouter()


class OAuthProviderItem(BaseModel):
    """Single OAuth provider configuration item."""

    id: str = Field(..., description="OAuth provider ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(..., description="Provider type (google, github, linkedin, microsoft, generic_oauth)")
    client_id: str = Field(..., description="OAuth client ID")
    authorization_url: str = Field(..., description="OAuth authorization endpoint URL")
    token_url: str = Field(..., description="OAuth token endpoint URL")
    userinfo_url: str = Field(..., description="OAuth userinfo endpoint URL")
    scopes: str = Field(..., description="Space-separated list of OAuth scopes")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    attribute_mapping_email: str = Field(..., description="User profile attribute for email")
    attribute_mapping_name: str = Field(..., description="User profile attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(None, description="User profile attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(None, description="User profile attribute for last name")
    attribute_mapping_picture: Optional[str] = Field(None, description="User profile attribute for picture")
    is_enabled: bool = Field(..., description="Whether this OAuth configuration is active")
    is_default: bool = Field(..., description="Whether this is the default OAuth provider")
    created_at: str = Field(..., description="When the configuration was created")
    updated_at: str = Field(..., description="When the configuration was last updated")


class OAuthProvidersResponse(BaseModel):
    """Response model for OAuth providers list."""

    providers: List[OAuthProviderItem] = Field(..., description="List of OAuth providers")
    total_count: int = Field(..., description="Total number of providers")


class OAuthAuthorizeRequest(BaseModel):
    """Request model for initiating OAuth login."""

    provider_id: Optional[str] = Field(None, description="OAuth provider ID to use (optional if using provider_type)")
    provider_type: Optional[str] = Field(None, description="Provider type shorthand (google, github, linkedin)")
    use_pkce: bool = Field(default=False, description="Whether to use PKCE for enhanced security")
    redirect_uri: Optional[str] = Field(None, description="Optional custom redirect URI")


class OAuthAuthorizeResponse(BaseModel):
    """Response model for OAuth authorization initiation."""

    authorization_url: str = Field(..., description="URL to redirect user to provider for authentication")
    state: str = Field(..., description="CSRF state token (must be validated in callback)")
    provider_id: str = Field(..., description="OAuth provider ID being used")
    provider_type: str = Field(..., description="Provider type being used")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier (if PKCE is enabled)")


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="CSRF state token from authorization request")
    expected_state: str = Field(..., description="Expected state token from session")
    provider_id: str = Field(..., description="OAuth provider ID to validate against")
    code_verifier: Optional[str] = Field(None, description="PKCE code verifier (if PKCE was used)")


class OAuthCallbackResponse(BaseModel):
    """Response model for successful OAuth authentication."""

    access_token: str = Field(..., description="OAuth access token")
    token_type: str = Field(..., description="Token type (usually Bearer)")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    scope: Optional[str] = Field(None, description="Granted OAuth scopes")
    user_profile: Dict = Field(..., description="User profile data from provider")
    provider_id: str = Field(..., description="OAuth provider ID used for authentication")


class OAuthProviderCreate(BaseModel):
    """Request model for creating OAuth provider configuration."""

    organization_id: Optional[str] = Field(None, description="Organization ID (null for system-wide)")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(..., description="Provider type (google, github, linkedin, microsoft, generic_oauth)")
    client_id: str = Field(..., description="OAuth client ID from the identity provider")
    client_secret: str = Field(..., description="OAuth client secret")
    authorization_url: str = Field(..., description="OAuth authorization endpoint URL")
    token_url: str = Field(..., description="OAuth token endpoint URL")
    userinfo_url: str = Field(..., description="OAuth userinfo endpoint URL")
    scopes: str = Field(default="openid profile email", description="Space-separated list of OAuth scopes")
    redirect_uri: str = Field(..., description="OAuth redirect URI configured in the provider")
    attribute_mapping_email: str = Field(default="email", description="User profile attribute for email")
    attribute_mapping_name: str = Field(default="name", description="User profile attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(default="given_name", description="User profile attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(default="family_name", description="User profile attribute for last name")
    attribute_mapping_picture: Optional[str] = Field(default="picture", description="User profile attribute for picture")
    is_enabled: bool = Field(default=True, description="Whether this OAuth configuration is active")
    is_default: bool = Field(default=False, description="Whether this is the default OAuth provider")


class OAuthProviderUpdate(BaseModel):
    """Request model for updating OAuth provider configuration."""

    provider_name: Optional[str] = Field(None, description="Human-readable provider name")
    client_id: Optional[str] = Field(None, description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")
    authorization_url: Optional[str] = Field(None, description="OAuth authorization endpoint URL")
    token_url: Optional[str] = Field(None, description="OAuth token endpoint URL")
    userinfo_url: Optional[str] = Field(None, description="OAuth userinfo endpoint URL")
    scopes: Optional[str] = Field(None, description="Space-separated list of OAuth scopes")
    redirect_uri: Optional[str] = Field(None, description="OAuth redirect URI")
    attribute_mapping_email: Optional[str] = Field(None, description="User profile attribute for email")
    attribute_mapping_name: Optional[str] = Field(None, description="User profile attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(None, description="User profile attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(None, description="User profile attribute for last name")
    attribute_mapping_picture: Optional[str] = Field(None, description="User profile attribute for picture")
    is_enabled: Optional[bool] = Field(None, description="Whether this OAuth configuration is active")
    is_default: Optional[bool] = Field(None, description="Whether this is the default OAuth provider")


@router.get(
    "/providers",
    response_model=OAuthProvidersResponse,
    tags=["OAuth"],
)
async def get_oauth_providers(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of providers to return"),
    offset: int = Query(0, ge=0, description="Number of providers to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get OAuth providers with filtering options.

    This endpoint retrieves configured OAuth 2.0 providers. Providers can be filtered
    by organization, provider type, or enabled status. Only enabled providers should
    be used for authentication.

    Args:
        organization_id: Optional filter for specific organization
        provider_type: Optional filter for provider type (google, github, linkedin, microsoft, generic_oauth)
        is_enabled: Optional filter for enabled status
        limit: Maximum number of providers to return (default: 100, max: 1000)
        offset: Number of providers to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of OAuth providers and total count

    Raises:
        HTTPException(400): If provider_type is invalid
        HTTPException(400): If organization_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/oauth/providers")
        >>> response.json()
        {
            "providers": [
                {
                    "id": "oauth-1",
                    "organization_id": "org-1",
                    "provider_name": "Google OAuth",
                    "provider_type": "google",
                    "client_id": "client-id",
                    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                    "scopes": "openid email profile",
                    "redirect_uri": "http://localhost:8000/api/oauth/callback",
                    "is_enabled": true,
                    "is_default": true,
                    "created_at": "2026-01-31T10:30:00Z",
                    "updated_at": "2026-01-31T10:30:00Z"
                }
            ],
            "total_count": 1
        }
    """
    try:
        logger.info(
            f"Fetching OAuth providers - organization_id: {organization_id}, "
            f"provider_type: {provider_type}, is_enabled: {is_enabled}"
        )

        # Validate provider_type
        valid_types = ["google", "github", "linkedin", "microsoft", "generic_oauth"]
        if provider_type and provider_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_type. Must be one of: {', '.join(valid_types)}"
            )

        # Build query
        query = select(OAuthProvider)

        # Apply filters
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.where(OAuthProvider.organization_id == org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid organization_id format (must be UUID)"
                )

        if provider_type:
            query = query.where(OAuthProvider.provider_type == provider_type)

        if is_enabled is not None:
            query = query.where(OAuthProvider.is_enabled == is_enabled)

        # Get total count
        count_query = query
        count_result = await db.execute(count_query)
        total_count = len(count_result.scalars().all())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        providers = result.scalars().all()

        # Format response
        provider_items = [
            OAuthProviderItem(
                id=str(provider.id),
                organization_id=str(provider.organization_id) if provider.organization_id else None,
                provider_name=provider.provider_name,
                provider_type=provider.provider_type,
                client_id=provider.client_id,
                authorization_url=provider.authorization_url,
                token_url=provider.token_url,
                userinfo_url=provider.userinfo_url,
                scopes=provider.scopes,
                redirect_uri=provider.redirect_uri,
                attribute_mapping_email=provider.attribute_mapping_email,
                attribute_mapping_name=provider.attribute_mapping_name,
                attribute_mapping_first_name=provider.attribute_mapping_first_name,
                attribute_mapping_last_name=provider.attribute_mapping_last_name,
                attribute_mapping_picture=provider.attribute_mapping_picture,
                is_enabled=provider.is_enabled,
                is_default=provider.is_default,
                created_at=provider.created_at.isoformat(),
                updated_at=provider.updated_at.isoformat(),
            )
            for provider in providers
        ]

        logger.info(f"Found {len(provider_items)} OAuth providers (total: {total_count})")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "providers": [item.model_dump() for item in provider_items],
                "total_count": total_count,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch OAuth providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch OAuth providers"
        )


@router.get(
    "/{provider}/authorize",
    response_model=OAuthAuthorizeResponse,
    tags=["OAuth"],
)
async def get_oauth_authorization_url(
    provider: str,
    redirect_uri: Optional[str] = Query(None, description="Optional custom redirect URI"),
    use_pkce: bool = Query(False, description="Whether to use PKCE for enhanced security"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Generate OAuth authorization URL for user redirection.

    This endpoint generates an authorization URL for the specified OAuth provider.
    The user should be redirected to this URL to authenticate with the provider.
    The provider will then redirect back to the callback endpoint with an authorization code.

    Args:
        provider: Provider type (google, github, linkedin, microsoft) or provider ID
        redirect_uri: Optional custom redirect URI (overrides provider config)
        use_pkce: Whether to use PKCE for enhanced security (recommended for public clients)
        db: Database session

    Returns:
        JSON response with authorization URL, state token, and provider details

    Raises:
        HTTPException(404): If provider is not found or not enabled
        HTTPException(500): If URL generation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/oauth/google/authorize")
        >>> response.json()
        {
            "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
            "state": "random-state-token",
            "provider_id": "oauth-1",
            "provider_type": "google",
            "code_verifier": null
        }
    """
    try:
        logger.info(f"Generating OAuth authorization URL for provider: {provider}")

        # Try to find provider by type first, then by ID
        query = select(OAuthProvider).where(OAuthProvider.is_enabled == True)

        # Check if provider is a known type
        if provider.lower() in ["google", "github", "linkedin", "microsoft"]:
            query = query.where(OAuthProvider.provider_type == provider.lower())
            query = query.where(OAuthProvider.is_default == True)
        else:
            # Try to find by ID
            try:
                provider_uuid = UUID(provider)
                query = query.where(OAuthProvider.id == provider_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Provider '{provider}' not found (must be a valid type or UUID)"
                )

        result = await db.execute(query)
        provider_config = result.scalar_one_or_none()

        if not provider_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider}' not found or not enabled"
            )

        # Get OAuth service
        oauth_service = get_oauth_service()

        # Initialize provider based on type
        provider_class = None
        if provider_config.provider_type == "google":
            provider_class = GoogleProvider
        elif provider_config.provider_type == "github":
            provider_class = GitHubProvider
        elif provider_config.provider_type == "linkedin":
            provider_class = LinkedInProvider
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Provider type '{provider_config.provider_type}' not yet implemented"
            )

        # Create provider instance
        provider_instance = provider_class(
            client_id=provider_config.client_id,
            client_secret=provider_config.client_secret,
            redirect_uri=redirect_uri or provider_config.redirect_uri,
            scopes=provider_config.scopes.split() if provider_config.scopes else None,
        )

        # Generate authorization URL
        auth_data = provider_instance.get_authorization_url(use_pkce=use_pkce)

        logger.info(
            f"Generated authorization URL for {provider_config.provider_type} "
            f"(provider_id={provider_config.id})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "authorization_url": auth_data["url"],
                "state": auth_data["state"],
                "provider_id": str(provider_config.id),
                "provider_type": provider_config.provider_type,
                "code_verifier": auth_data.get("code_verifier"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate OAuth authorization URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OAuth authorization URL"
        )


@router.post(
    "/callback",
    response_model=OAuthCallbackResponse,
    tags=["OAuth"],
)
async def handle_oauth_callback(
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Handle OAuth callback after user authorization.

    This endpoint processes the OAuth callback after the user has authenticated
    with the provider. It validates the state token, exchanges the authorization
    code for an access token, and fetches the user profile.

    Args:
        request: OAuth callback request with code, state, and provider info
        db: Database session

    Returns:
        JSON response with access token, user profile, and provider details

    Raises:
        HTTPException(400): If state validation fails or parameters are invalid
        HTTPException(404): If provider is not found
        HTTPException(401): If token exchange fails
        HTTPException(500): If processing fails

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/oauth/callback", json={
        ...     "code": "auth-code",
        ...     "state": "received-state",
        ...     "expected_state": "expected-state",
        ...     "provider_id": "oauth-1"
        ... })
        >>> response.json()
        {
            "access_token": "ya29...",
            "token_type": "Bearer",
            "expires_in": 3600,
            "user_profile": {
                "id": "123",
                "email": "user@example.com",
                "name": "John Doe"
            },
            "provider_id": "oauth-1"
        }
    """
    try:
        logger.info(f"Processing OAuth callback for provider: {request.provider_id}")

        # Validate required fields
        if not request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code"
            )

        if not request.state or not request.expected_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing state parameter"
            )

        # Validate state (CSRF protection)
        if request.state != request.expected_state:
            logger.warning(
                f"OAuth state mismatch - received: {request.state[:8]}..., "
                f"expected: {request.expected_state[:8]}..."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State parameter mismatch (possible CSRF attack)"
            )

        # Find provider by ID
        try:
            provider_uuid = UUID(request.provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid provider_id format (must be UUID)"
            )

        query = select(OAuthProvider).where(
            OAuthProvider.id == provider_uuid,
            OAuthProvider.is_enabled == True
        )
        result = await db.execute(query)
        provider_config = result.scalar_one_or_none()

        if not provider_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{request.provider_id}' not found or not enabled"
            )

        # Initialize provider based on type
        provider_class = None
        if provider_config.provider_type == "google":
            provider_class = GoogleProvider
        elif provider_config.provider_type == "github":
            provider_class = GitHubProvider
        elif provider_config.provider_type == "linkedin":
            provider_class = LinkedInProvider
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=f"Provider type '{provider_config.provider_type}' not yet implemented"
            )

        # Create provider instance
        provider_instance = provider_class(
            client_id=provider_config.client_id,
            client_secret=provider_config.client_secret,
            redirect_uri=provider_config.redirect_uri,
            scopes=provider_config.scopes.split() if provider_config.scopes else None,
        )

        # Exchange code for token
        try:
            token_data = provider_instance.exchange_code_for_token(
                code=request.code,
                code_verifier=request.code_verifier,
            )
        except Exception as e:
            logger.error(f"Token exchange failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token exchange failed: {str(e)}"
            )

        # Fetch user profile
        try:
            user_profile = provider_instance.get_user_profile(token_data["access_token"])
        except Exception as e:
            logger.error(f"Profile fetch failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Profile fetch failed: {str(e)}"
            )

        logger.info(
            f"OAuth callback successful for {provider_config.provider_type} "
            f"(user_email={user_profile.get('email')})"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": token_data["access_token"],
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in"),
                "refresh_token": token_data.get("refresh_token"),
                "scope": token_data.get("scope"),
                "user_profile": user_profile,
                "provider_id": str(provider_config.id),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process OAuth callback"
        )


@router.post(
    "/providers",
    response_model=OAuthProviderItem,
    tags=["OAuth"],
    status_code=status.HTTP_201_CREATED,
)
async def create_oauth_provider(
    provider: OAuthProviderCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new OAuth provider configuration.

    This endpoint creates a new OAuth 2.0 provider configuration for an organization
    or system-wide. Only one provider can be set as default per organization.

    Args:
        provider: OAuth provider configuration to create
        db: Database session

    Returns:
        JSON response with created provider configuration

    Raises:
        HTTPException(400): If validation fails or default conflict
        HTTPException(500): If creation fails

    Examples:
        >>> import requests
        >>> response = requests.post("http://localhost:8000/api/oauth/providers", json={
        ...     "provider_name": "Google OAuth",
        ...     "provider_type": "google",
        ...     "client_id": "client-id",
        ...     "client_secret": "client-secret",
        ...     "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
        ...     "token_url": "https://oauth2.googleapis.com/token",
        ...     "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        ...     "redirect_uri": "http://localhost:8000/api/oauth/callback",
        ...     "is_default": true
        ... })
    """
    try:
        logger.info(f"Creating OAuth provider: {provider.provider_name} ({provider.provider_type})")

        # Validate provider type
        valid_types = ["google", "github", "linkedin", "microsoft", "generic_oauth"]
        if provider.provider_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_type. Must be one of: {', '.join(valid_types)}"
            )

        # If setting as default, unset other defaults for this organization
        if provider.is_default:
            query = select(OAuthProvider).where(
                OAuthProvider.is_default == True,
                OAuthProvider.provider_type == provider.provider_type
            )
            if provider.organization_id:
                query = query.where(OAuthProvider.organization_id == UUID(provider.organization_id))
            else:
                query = query.where(OAuthProvider.organization_id.is_(None))

            result = await db.execute(query)
            existing_defaults = result.scalars().all()

            for existing in existing_defaults:
                existing.is_default = False
                db.add(existing)

        # Create new provider
        new_provider = OAuthProvider(
            organization_id=UUID(provider.organization_id) if provider.organization_id else None,
            provider_name=provider.provider_name,
            provider_type=provider.provider_type,
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            authorization_url=provider.authorization_url,
            token_url=provider.token_url,
            userinfo_url=provider.userinfo_url,
            scopes=provider.scopes,
            redirect_uri=provider.redirect_uri,
            attribute_mapping_email=provider.attribute_mapping_email,
            attribute_mapping_name=provider.attribute_mapping_name,
            attribute_mapping_first_name=provider.attribute_mapping_first_name,
            attribute_mapping_last_name=provider.attribute_mapping_last_name,
            attribute_mapping_picture=provider.attribute_mapping_picture,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
        )

        db.add(new_provider)
        await db.commit()
        await db.refresh(new_provider)

        logger.info(f"Created OAuth provider: {new_provider.id}")

        provider_item = OAuthProviderItem(
            id=str(new_provider.id),
            organization_id=str(new_provider.organization_id) if new_provider.organization_id else None,
            provider_name=new_provider.provider_name,
            provider_type=new_provider.provider_type,
            client_id=new_provider.client_id,
            authorization_url=new_provider.authorization_url,
            token_url=new_provider.token_url,
            userinfo_url=new_provider.userinfo_url,
            scopes=new_provider.scopes,
            redirect_uri=new_provider.redirect_uri,
            attribute_mapping_email=new_provider.attribute_mapping_email,
            attribute_mapping_name=new_provider.attribute_mapping_name,
            attribute_mapping_first_name=new_provider.attribute_mapping_first_name,
            attribute_mapping_last_name=new_provider.attribute_mapping_last_name,
            attribute_mapping_picture=new_provider.attribute_mapping_picture,
            is_enabled=new_provider.is_enabled,
            is_default=new_provider.is_default,
            created_at=new_provider.created_at.isoformat(),
            updated_at=new_provider.updated_at.isoformat(),
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=provider_item.model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create OAuth provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create OAuth provider"
        )


@router.put(
    "/providers/{provider_id}",
    response_model=OAuthProviderItem,
    tags=["OAuth"],
)
async def update_oauth_provider(
    provider_id: str,
    provider_update: OAuthProviderUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing OAuth provider configuration.

    This endpoint updates an OAuth 2.0 provider configuration.
    Only provided fields will be updated.

    Args:
        provider_id: OAuth provider ID to update
        provider_update: Fields to update
        db: Database session

    Returns:
        JSON response with updated provider configuration

    Raises:
        HTTPException(404): If provider is not found
        HTTPException(400): If validation fails
        HTTPException(500): If update fails
    """
    try:
        logger.info(f"Updating OAuth provider: {provider_id}")

        # Find provider
        try:
            provider_uuid = UUID(provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid provider_id format (must be UUID)"
            )

        query = select(OAuthProvider).where(OAuthProvider.id == provider_uuid)
        result = await db.execute(query)
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider_id}' not found"
            )

        # Update fields
        update_data = provider_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)

        # If setting as default, unset other defaults
        if provider_update.is_default:
            query = select(OAuthProvider).where(
                OAuthProvider.is_default == True,
                OAuthProvider.provider_type == provider.provider_type,
                OAuthProvider.id != provider_uuid
            )
            if provider.organization_id:
                query = query.where(OAuthProvider.organization_id == provider.organization_id)
            else:
                query = query.where(OAuthProvider.organization_id.is_(None))

            result = await db.execute(query)
            existing_defaults = result.scalars().all()

            for existing in existing_defaults:
                existing.is_default = False
                db.add(existing)

        await db.commit()
        await db.refresh(provider)

        logger.info(f"Updated OAuth provider: {provider.id}")

        provider_item = OAuthProviderItem(
            id=str(provider.id),
            organization_id=str(provider.organization_id) if provider.organization_id else None,
            provider_name=provider.provider_name,
            provider_type=provider.provider_type,
            client_id=provider.client_id,
            authorization_url=provider.authorization_url,
            token_url=provider.token_url,
            userinfo_url=provider.userinfo_url,
            scopes=provider.scopes,
            redirect_uri=provider.redirect_uri,
            attribute_mapping_email=provider.attribute_mapping_email,
            attribute_mapping_name=provider.attribute_mapping_name,
            attribute_mapping_first_name=provider.attribute_mapping_first_name,
            attribute_mapping_last_name=provider.attribute_mapping_last_name,
            attribute_mapping_picture=provider.attribute_mapping_picture,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
            created_at=provider.created_at.isoformat(),
            updated_at=provider.updated_at.isoformat(),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=provider_item.model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update OAuth provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update OAuth provider"
        )


@router.delete(
    "/providers/{provider_id}",
    tags=["OAuth"],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_oauth_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an OAuth provider configuration.

    This endpoint deletes an OAuth 2.0 provider configuration.

    Args:
        provider_id: OAuth provider ID to delete
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException(404): If provider is not found
        HTTPException(400): If provider_id format is invalid
        HTTPException(500): If deletion fails
    """
    try:
        logger.info(f"Deleting OAuth provider: {provider_id}")

        # Find provider
        try:
            provider_uuid = UUID(provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid provider_id format (must be UUID)"
            )

        query = select(OAuthProvider).where(OAuthProvider.id == provider_uuid)
        result = await db.execute(query)
        provider = result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"OAuth provider '{provider_id}' not found"
            )

        await db.delete(provider)
        await db.commit()

        logger.info(f"Deleted OAuth provider: {provider_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete OAuth provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete OAuth provider"
        )
