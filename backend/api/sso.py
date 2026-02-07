"""
SSO endpoints for SAML Single Sign-On authentication.

This module provides endpoints for SAML 2.0 SSO integration with identity
providers such as Okta, Azure AD, and Google Workspace. It handles SAML
authentication flow, SSO provider configuration, and SP metadata generation.
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
from models.sso_config import SSOConfig
from services.saml_service import get_saml_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SSOProviderItem(BaseModel):
    """Single SSO provider configuration item."""

    id: str = Field(..., description="SSO provider ID")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(..., description="Provider type (okta, azure_ad, google_workspace, generic_saml)")
    entity_id: str = Field(..., description="SAML Entity ID from IdP")
    sso_url: str = Field(..., description="SAML SSO URL")
    sls_url: Optional[str] = Field(None, description="SAML Single Logout Service URL")
    metadata_url: Optional[str] = Field(None, description="SAML metadata URL")
    attribute_mapping_email: str = Field(..., description="SAML attribute for email")
    attribute_mapping_name: str = Field(..., description="SAML attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(None, description="SAML attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(None, description="SAML attribute for last name")
    attribute_mapping_department: Optional[str] = Field(None, description="SAML attribute for department")
    is_enabled: bool = Field(..., description="Whether this SSO configuration is active")
    is_default: bool = Field(..., description="Whether this is the default SSO provider")
    created_at: str = Field(..., description="When the configuration was created")
    updated_at: str = Field(..., description="When the configuration was last updated")


class SSOProvidersResponse(BaseModel):
    """Response model for SSO providers list."""

    providers: List[SSOProviderItem] = Field(..., description="List of SSO providers")
    total_count: int = Field(..., description="Total number of providers")


class SSOLoginRequest(BaseModel):
    """Request model for initiating SAML login."""

    provider_id: str = Field(..., description="SSO provider ID to use for login")
    relay_state: Optional[str] = Field(None, description="Optional relay state for maintaining application state")


class SSOLoginResponse(BaseModel):
    """Response model for SAML login initiation."""

    redirect_url: str = Field(..., description="URL to redirect user to IdP for authentication")
    provider_id: str = Field(..., description="SSO provider ID being used")


class SAMLACSRequest(BaseModel):
    """Request model for SAML ACS callback."""

    saml_response: str = Field(..., description="Base64-encoded SAML response from IdP")
    provider_id: str = Field(..., description="SSO provider ID to validate response against")
    relay_state: Optional[str] = Field(None, description="Optional relay state from login request")


class SAMLACSResponse(BaseModel):
    """Response model for successful SAML authentication."""

    email: str = Field(..., description="User email from SAML response")
    name: Optional[str] = Field(None, description="User display name")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    department: Optional[str] = Field(None, description="User department")
    name_id: str = Field(..., description="SAML Name ID (persistent identifier)")
    session_index: Optional[str] = Field(None, description="SAML session index for logout")
    provider_id: str = Field(..., description="SSO provider ID used for authentication")


class SSOProviderCreate(BaseModel):
    """Request model for creating SSO provider configuration."""

    organization_id: Optional[str] = Field(None, description="Organization ID (null for system-wide)")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: str = Field(..., description="Provider type (okta, azure_ad, google_workspace, generic_saml)")
    entity_id: str = Field(..., description="SAML Entity ID from IdP")
    sso_url: str = Field(..., description="SAML SSO URL where authentication requests are sent")
    sls_url: Optional[str] = Field(None, description="SAML Single Logout Service URL")
    x509_certificate: str = Field(..., description="X.509 certificate from IdP (PEM format)")
    metadata_url: Optional[str] = Field(None, description="SAML metadata URL for automatic configuration")
    attribute_mapping_email: str = Field(default="email", description="SAML attribute for email")
    attribute_mapping_name: str = Field(default="displayName", description="SAML attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(default="firstName", description="SAML attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(default="lastName", description="SAML attribute for last name")
    attribute_mapping_department: Optional[str] = Field(default="department", description="SAML attribute for department")
    is_enabled: bool = Field(default=True, description="Whether this SSO configuration is active")
    is_default: bool = Field(default=False, description="Whether this is the default SSO provider")


class SSOProviderUpdate(BaseModel):
    """Request model for updating SSO provider configuration."""

    provider_name: Optional[str] = Field(None, description="Human-readable provider name")
    entity_id: Optional[str] = Field(None, description="SAML Entity ID from IdP")
    sso_url: Optional[str] = Field(None, description="SAML SSO URL")
    sls_url: Optional[str] = Field(None, description="SAML Single Logout Service URL")
    x509_certificate: Optional[str] = Field(None, description="X.509 certificate from IdP (PEM format)")
    metadata_url: Optional[str] = Field(None, description="SAML metadata URL")
    attribute_mapping_email: Optional[str] = Field(None, description="SAML attribute for email")
    attribute_mapping_name: Optional[str] = Field(None, description="SAML attribute for display name")
    attribute_mapping_first_name: Optional[str] = Field(None, description="SAML attribute for first name")
    attribute_mapping_last_name: Optional[str] = Field(None, description="SAML attribute for last name")
    attribute_mapping_department: Optional[str] = Field(None, description="SAML attribute for department")
    is_enabled: Optional[bool] = Field(None, description="Whether this SSO configuration is active")
    is_default: Optional[bool] = Field(None, description="Whether this is the default SSO provider")


class MetadataResponse(BaseModel):
    """Response model for SAML SP metadata."""

    metadata: str = Field(..., description="XML metadata document for import into IdP")


@router.get(
    "/providers",
    response_model=SSOProvidersResponse,
    tags=["SSO"],
)
async def get_sso_providers(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of providers to return"),
    offset: int = Query(0, ge=0, description="Number of providers to skip for pagination"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get SSO providers with filtering options.

    This endpoint retrieves configured SAML SSO providers. Providers can be filtered
    by organization, provider type, or enabled status. Only enabled providers should
    be used for authentication.

    Args:
        organization_id: Optional filter for specific organization
        provider_type: Optional filter for provider type (okta, azure_ad, google_workspace, generic_saml)
        is_enabled: Optional filter for enabled status
        limit: Maximum number of providers to return (default: 100, max: 1000)
        offset: Number of providers to skip for pagination (default: 0)
        db: Database session

    Returns:
        JSON response with list of SSO providers and total count

    Raises:
        HTTPException(400): If provider_type is invalid
        HTTPException(400): If organization_id format is invalid
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/sso/providers")
        >>> response.json()
        {
            "providers": [
                {
                    "id": "sso-1",
                    "organization_id": "org-1",
                    "provider_name": "Company Okta",
                    "provider_type": "okta",
                    "entity_id": "https://okta.com/entityid",
                    "sso_url": "https://okta.com/sso",
                    "sls_url": "https://okta.com/slo",
                    "metadata_url": null,
                    "attribute_mapping_email": "email",
                    "attribute_mapping_name": "displayName",
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
            f"Fetching SSO providers - organization_id: {organization_id}, "
            f"provider_type: {provider_type}, is_enabled: {is_enabled}"
        )

        # Build base query
        query = select(SSOConfig)

        # Apply filters
        if organization_id:
            try:
                org_uuid = UUID(organization_id)
                query = query.where(SSOConfig.organization_id == org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {organization_id}",
                )

        if provider_type:
            valid_types = ["okta", "azure_ad", "google_workspace", "generic_saml"]
            if provider_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid provider_type: {provider_type}. "
                           f"Valid types are: {', '.join(valid_types)}",
                )
            query = query.where(SSOConfig.provider_type == provider_type)

        if is_enabled is not None:
            query = query.where(SSOConfig.is_enabled == is_enabled)

        # Order by created_at descending and apply pagination
        query = query.order_by(SSOConfig.created_at.desc()).limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        providers = result.scalars().all()

        # Build response data
        providers_data = []
        for provider in providers:
            providers_data.append({
                "id": str(provider.id),
                "organization_id": str(provider.organization_id) if provider.organization_id else None,
                "provider_name": provider.provider_name,
                "provider_type": provider.provider_type,
                "entity_id": provider.entity_id,
                "sso_url": provider.sso_url,
                "sls_url": provider.sls_url,
                "metadata_url": provider.metadata_url,
                "attribute_mapping_email": provider.attribute_mapping_email,
                "attribute_mapping_name": provider.attribute_mapping_name,
                "attribute_mapping_first_name": provider.attribute_mapping_first_name,
                "attribute_mapping_last_name": provider.attribute_mapping_last_name,
                "attribute_mapping_department": provider.attribute_mapping_department,
                "is_enabled": provider.is_enabled,
                "is_default": provider.is_default,
                "created_at": provider.created_at.isoformat(),
                "updated_at": provider.updated_at.isoformat(),
            })

        response_data = {
            "providers": providers_data,
            "total_count": len(providers_data),
        }

        logger.info(f"Retrieved {len(providers_data)} SSO providers")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving SSO providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SSO providers: {str(e)}",
        ) from e


@router.post(
    "/login",
    response_model=SSOLoginResponse,
    tags=["SSO"],
)
async def initiate_saml_login(
    request: SSOLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Initiate SAML SSO login.

    This endpoint generates a SAML authentication request and returns the IdP redirect URL.
    The user should be redirected to this URL to complete authentication with their
    identity provider. After authentication, the IdP will redirect back to the ACS endpoint.

    Args:
        request: Login request with provider_id and optional relay_state
        db: Database session

    Returns:
        JSON response with redirect URL to IdP

    Raises:
        HTTPException(400): If provider_id is invalid
        HTTPException(404): If provider is not found
        HTTPException(400): If SAML is not configured or provider is disabled
        HTTPException(500): If login initiation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/sso/login",
        ...     json={"provider_id": "sso-1", "relay_state": "/dashboard"}
        ... )
        >>> response.json()
        {
            "redirect_url": "https://okta.com/sso?SAMLRequest=...",
            "provider_id": "sso-1"
        }
    """
    try:
        logger.info(f"Initiating SAML login for provider: {request.provider_id}")

        # Get SSO provider configuration
        try:
            provider_uuid = UUID(request.provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_id format: {request.provider_id}",
            )

        provider_result = await db.execute(
            select(SSOConfig).where(SSOConfig.id == provider_uuid)
        )
        provider = provider_result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SSO provider not found: {request.provider_id}",
            )

        if not provider.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO provider is not enabled: {provider.provider_name}",
            )

        # Get SAML service
        saml_service = get_saml_service()

        if not saml_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML SSO is not configured on the server",
            )

        # Generate login redirect URL
        redirect_url = saml_service.get_login_redirect_url(
            idp_entity_id=provider.entity_id,
            idp_sso_url=provider.sso_url,
            idp_certificate=provider.x509_certificate,
            relay_state=request.relay_state,
            idp_sls_url=provider.sls_url,
        )

        logger.info(f"Generated SAML login redirect for provider: {provider.provider_name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "redirect_url": redirect_url,
                "provider_id": str(provider.id),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating SAML login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate SAML login: {str(e)}",
        ) from e


@router.post(
    "/acs",
    response_model=SAMLACSResponse,
    tags=["SSO"],
)
async def handle_saml_acs(
    request: SAMLACSRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Handle SAML ACS (Assertion Consumer Service) callback.

    This endpoint processes the SAML response from the identity provider after
    user authentication. It validates the response, extracts user attributes,
    and returns the user information for session creation.

    Args:
        request: ACS request with SAML response and provider_id
        db: Database session

    Returns:
        JSON response with extracted user attributes

    Raises:
        HTTPException(400): If provider_id is invalid
        HTTPException(404): If provider is not found
        HTTPException(400): If SAML response is invalid or authentication failed
        HTTPException(500): If response processing fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/sso/acs",
        ...     json={
        ...         "saml_response": "base64_encoded_saml_response",
        ...         "provider_id": "sso-1"
        ...     }
        ... )
        >>> response.json()
        {
            "email": "user@example.com",
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "department": "Engineering",
            "name_id": "john.doe@example.com",
            "session_index": "session123",
            "provider_id": "sso-1"
        }
    """
    try:
        logger.info(f"Processing SAML ACS response for provider: {request.provider_id}")

        # Get SSO provider configuration
        try:
            provider_uuid = UUID(request.provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_id format: {request.provider_id}",
            )

        provider_result = await db.execute(
            select(SSOConfig).where(SSOConfig.id == provider_uuid)
        )
        provider = provider_result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SSO provider not found: {request.provider_id}",
            )

        if not provider.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSO provider is not enabled: {provider.provider_name}",
            )

        # Get SAML service
        saml_service = get_saml_service()

        if not saml_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML SSO is not configured on the server",
            )

        # Build attribute mapping
        attribute_mapping = {
            "email": provider.attribute_mapping_email,
            "name": provider.attribute_mapping_name,
            "first_name": provider.attribute_mapping_first_name,
            "last_name": provider.attribute_mapping_last_name,
            "department": provider.attribute_mapping_department,
        }

        # Process SAML response
        user_attrs = saml_service.process_saml_response(
            saml_response=request.saml_response,
            idp_entity_id=provider.entity_id,
            idp_sso_url=provider.sso_url,
            idp_certificate=provider.x509_certificate,
            idp_sls_url=provider.sls_url,
            attribute_mapping=attribute_mapping,
        )

        logger.info(f"Successfully processed SAML response for user: {user_attrs.get('email')}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "email": user_attrs["email"],
                "name": user_attrs.get("name"),
                "first_name": user_attrs.get("first_name"),
                "last_name": user_attrs.get("last_name"),
                "department": user_attrs.get("department"),
                "name_id": user_attrs["name_id"],
                "session_index": user_attrs.get("session_index"),
                "provider_id": str(provider.id),
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"SAML authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Error processing SAML ACS: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process SAML response: {str(e)}",
        ) from e


@router.post(
    "/providers",
    response_model=SSOProviderItem,
    tags=["SSO"],
)
async def create_sso_provider(
    provider: SSOProviderCreate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create SSO provider configuration.

    This endpoint creates a new SAML SSO provider configuration. The provider
    can be organization-specific or system-wide (organization_id=null).

    Args:
        provider: SSO provider configuration details
        db: Database session

    Returns:
        JSON response with created provider details

    Raises:
        HTTPException(400): If organization_id format is invalid
        HTTPException(400): If X.509 certificate format is invalid
        HTTPException(400): If provider type is invalid
        HTTPException(500): If provider creation fails

    Examples:
        >>> import requests
        >>> response = requests.post(
        ...     "http://localhost:8000/api/sso/providers",
        ...     json={
        ...         "provider_name": "Company Okta",
        ...         "provider_type": "okta",
        ...         "entity_id": "https://okta.com/entityid",
        ...         "sso_url": "https://okta.com/sso",
        ...         "x509_certificate": "-----BEGIN CERTIFICATE-----...",
        ...         "organization_id": "org-1"
        ...     }
        ... )
    """
    try:
        logger.info(f"Creating SSO provider: {provider.provider_name}")

        # Validate organization_id if provided
        if provider.organization_id:
            try:
                org_uuid = UUID(provider.organization_id)
                provider.organization_id = str(org_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid organization_id format: {provider.organization_id}",
                )

        # Validate provider type
        valid_types = ["okta", "azure_ad", "google_workspace", "generic_saml"]
        if provider.provider_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_type: {provider.provider_type}. "
                       f"Valid types are: {', '.join(valid_types)}",
            )

        # Validate X.509 certificate
        saml_service = get_saml_service()
        if not saml_service.validate_certificate(provider.x509_certificate):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X.509 certificate format. Certificate must be in PEM format.",
            )

        # Create SSO config
        sso_config = SSOConfig(
            organization_id=UUID(provider.organization_id) if provider.organization_id else None,
            provider_name=provider.provider_name,
            provider_type=provider.provider_type,
            entity_id=provider.entity_id,
            sso_url=provider.sso_url,
            sls_url=provider.sls_url,
            x509_certificate=provider.x509_certificate,
            metadata_url=provider.metadata_url,
            attribute_mapping_email=provider.attribute_mapping_email,
            attribute_mapping_name=provider.attribute_mapping_name,
            attribute_mapping_first_name=provider.attribute_mapping_first_name,
            attribute_mapping_last_name=provider.attribute_mapping_last_name,
            attribute_mapping_department=provider.attribute_mapping_department,
            is_enabled=provider.is_enabled,
            is_default=provider.is_default,
        )

        db.add(sso_config)
        await db.commit()
        await db.refresh(sso_config)

        logger.info(f"Created SSO provider: {sso_config.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(sso_config.id),
                "organization_id": str(sso_config.organization_id) if sso_config.organization_id else None,
                "provider_name": sso_config.provider_name,
                "provider_type": sso_config.provider_type,
                "entity_id": sso_config.entity_id,
                "sso_url": sso_config.sso_url,
                "sls_url": sso_config.sls_url,
                "metadata_url": sso_config.metadata_url,
                "attribute_mapping_email": sso_config.attribute_mapping_email,
                "attribute_mapping_name": sso_config.attribute_mapping_name,
                "attribute_mapping_first_name": sso_config.attribute_mapping_first_name,
                "attribute_mapping_last_name": sso_config.attribute_mapping_last_name,
                "attribute_mapping_department": sso_config.attribute_mapping_department,
                "is_enabled": sso_config.is_enabled,
                "is_default": sso_config.is_default,
                "created_at": sso_config.created_at.isoformat(),
                "updated_at": sso_config.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SSO provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SSO provider: {str(e)}",
        ) from e


@router.put(
    "/providers/{provider_id}",
    response_model=SSOProviderItem,
    tags=["SSO"],
)
async def update_sso_provider(
    provider_id: str,
    provider_update: SSOProviderUpdate,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update SSO provider configuration.

    This endpoint updates an existing SAML SSO provider configuration.

    Args:
        provider_id: SSO provider ID
        provider_update: Fields to update
        db: Database session

    Returns:
        JSON response with updated provider details

    Raises:
        HTTPException(400): If provider_id format is invalid
        HTTPException(404): If provider is not found
        HTTPException(400): If X.509 certificate format is invalid
        HTTPException(500): If provider update fails

    Examples:
        >>> import requests
        >>> response = requests.put(
        ...     "http://localhost:8000/api/sso/providers/sso-1",
        ...     json={"provider_name": "Updated Name", "is_enabled": false}
        ... )
    """
    try:
        logger.info(f"Updating SSO provider: {provider_id}")

        # Get provider
        try:
            provider_uuid = UUID(provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_id format: {provider_id}",
            )

        provider_result = await db.execute(
            select(SSOConfig).where(SSOConfig.id == provider_uuid)
        )
        provider = provider_result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SSO provider not found: {provider_id}",
            )

        # Update fields
        update_data = provider_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "x509_certificate" and value:
                # Validate certificate
                saml_service = get_saml_service()
                if not saml_service.validate_certificate(value):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid X.509 certificate format. Certificate must be in PEM format.",
                    )
            setattr(provider, field, value)

        await db.commit()
        await db.refresh(provider)

        logger.info(f"Updated SSO provider: {provider.id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(provider.id),
                "organization_id": str(provider.organization_id) if provider.organization_id else None,
                "provider_name": provider.provider_name,
                "provider_type": provider.provider_type,
                "entity_id": provider.entity_id,
                "sso_url": provider.sso_url,
                "sls_url": provider.sls_url,
                "metadata_url": provider.metadata_url,
                "attribute_mapping_email": provider.attribute_mapping_email,
                "attribute_mapping_name": provider.attribute_mapping_name,
                "attribute_mapping_first_name": provider.attribute_mapping_first_name,
                "attribute_mapping_last_name": provider.attribute_mapping_last_name,
                "attribute_mapping_department": provider.attribute_mapping_department,
                "is_enabled": provider.is_enabled,
                "is_default": provider.is_default,
                "created_at": provider.created_at.isoformat(),
                "updated_at": provider.updated_at.isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating SSO provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SSO provider: {str(e)}",
        ) from e


@router.delete(
    "/providers/{provider_id}",
    tags=["SSO"],
)
async def delete_sso_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete SSO provider configuration.

    This endpoint deletes a SAML SSO provider configuration.

    Args:
        provider_id: SSO provider ID
        db: Database session

    Returns:
        JSON response confirming deletion

    Raises:
        HTTPException(400): If provider_id format is invalid
        HTTPException(404): If provider is not found
        HTTPException(500): If provider deletion fails

    Examples:
        >>> import requests
        >>> response = requests.delete("http://localhost:8000/api/sso/providers/sso-1")
        >>> response.json()
        {"message": "SSO provider deleted successfully"}
    """
    try:
        logger.info(f"Deleting SSO provider: {provider_id}")

        # Get provider
        try:
            provider_uuid = UUID(provider_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider_id format: {provider_id}",
            )

        provider_result = await db.execute(
            select(SSOConfig).where(SSOConfig.id == provider_uuid)
        )
        provider = provider_result.scalar_one_or_none()

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SSO provider not found: {provider_id}",
            )

        await db.delete(provider)
        await db.commit()

        logger.info(f"Deleted SSO provider: {provider_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "SSO provider deleted successfully"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SSO provider: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete SSO provider: {str(e)}",
        ) from e


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    tags=["SSO"],
)
async def get_sp_metadata() -> JSONResponse:
    """
    Get SAML SP metadata.

    This endpoint generates and returns the SAML 2.0 Service Provider metadata
    XML document. This metadata can be imported into identity providers (Okta,
    Azure AD, Google Workspace) to configure the SSO integration.

    Returns:
        JSON response with XML metadata document

    Raises:
        HTTPException(400): If SAML is not configured
        HTTPException(500): If metadata generation fails

    Examples:
        >>> import requests
        >>> response = requests.get("http://localhost:8000/api/sso/metadata")
        >>> response.json()
        {
            "metadata": "<?xml version=\"1.0\"?>..."
        }
    """
    try:
        logger.info("Generating SAML SP metadata")

        saml_service = get_saml_service()

        if not saml_service.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML SSO is not configured on the server",
            )

        metadata = saml_service.generate_metadata()

        logger.info("Generated SAML SP metadata successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"metadata": metadata},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SP metadata: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate SP metadata: {str(e)}",
        ) from e
