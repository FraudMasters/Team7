"""
Plugin marketplace and installation management endpoints.

This module provides endpoints for:
- Listing available plugins in the marketplace
- Getting detailed plugin information
- Creating/updating/deleting plugins (marketplace management)
- Installing/uninstalling plugins for recruiters
- Managing plugin installations (enable, disable, configure)
- Validating plugin manifests

Supports both plugin discovery and lifecycle management.
"""
import json
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from packaging import version as pkg_version

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.plugin import Plugin, PluginInstallation, PluginCategory, PluginStatus
from models.recruiter import Recruiter
from schemas.plugin_manifest import (
    PluginManifest,
    PluginManifestResponse,
    PluginManifestCreate,
    PluginManifestValidate,
    PluginManifestValidateResponse,
    PluginPermission,
    PluginDependency,
    PluginEntryPoint,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class PluginListItem(BaseModel):
    """Response model for a plugin in list view."""

    id: str = Field(..., description="Plugin UUID")
    name: str = Field(..., description="Plugin name")
    slug: str = Field(..., description="URL-friendly slug")
    version: str = Field(..., description="Current version")
    author: str = Field(..., description="Plugin author")
    description: str = Field(..., description="Short description")
    category: str = Field(..., description="Plugin category")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    is_official: bool = Field(..., description="Whether this is an official plugin")
    status: str = Field(..., description="Approval status")
    is_active: bool = Field(..., description="Whether plugin is active")
    install_count: int = Field(..., description="Number of installations")
    rating_count: int = Field(..., description="Number of ratings")
    average_rating: Optional[float] = Field(None, description="Average rating (0-5)")
    is_installed: bool = Field(False, description="Whether plugin is installed by current user")
    is_enabled: bool = Field(False, description="Whether installed plugin is enabled")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class PluginDetail(PluginListItem):
    """Detailed response model for a plugin."""

    long_description: Optional[str] = Field(None, description="Long description")
    homepage_url: Optional[str] = Field(None, description="Homepage URL")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    manifest_url: str = Field(..., description="Manifest URL")
    download_url: str = Field(..., description="Download URL")
    latest_version: Optional[str] = Field(None, description="Latest available version")
    min_agenthr_version: Optional[str] = Field(None, description="Minimum AgentHR version")
    max_agenthr_version: Optional[str] = Field(None, description="Maximum AgentHR version")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Plugin dependencies")
    is_compatible: bool = Field(..., description="Whether plugin is compatible with current version")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    license: Optional[str] = Field(None, description="Plugin license")


class PluginCreateRequest(BaseModel):
    """Request model for creating a new plugin."""

    name: str = Field(..., min_length=1, max_length=255, description="Plugin name")
    slug: str = Field(..., min_length=1, max_length=255, description="URL-friendly slug")
    version: str = Field(..., min_length=1, max_length=50, description="Plugin version")
    author: str = Field(..., min_length=1, max_length=255, description="Plugin author")
    author_email: Optional[str] = Field(None, description="Author email")
    description: str = Field(..., min_length=1, max_length=500, description="Short description")
    long_description: Optional[str] = Field(None, description="Long description")
    category: PluginCategory = Field(..., description="Plugin category")
    tags: List[str] = Field(default_factory=list, description="Plugin tags")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    manifest_url: str = Field(..., description="Manifest URL")
    download_url: str = Field(..., description="Download URL")
    homepage_url: Optional[str] = Field(None, description="Homepage URL")
    repository_url: Optional[str] = Field(None, description="Repository URL")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")
    is_official: bool = Field(False, description="Whether this is an official plugin")
    min_agenthr_version: Optional[str] = Field(None, description="Minimum AgentHR version")
    max_agenthr_version: Optional[str] = Field(None, description="Maximum AgentHR version")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Plugin dependencies")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Configuration schema")
    license: Optional[str] = Field(None, description="Plugin license")

    @validator("slug")
    def validate_slug(cls, v):
        """Validate slug format."""
        import re
        if not re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must start with a letter, contain only lowercase letters, numbers, and hyphens"
            )
        return v


class PluginUpdateRequest(BaseModel):
    """Request model for updating a plugin."""

    version: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    long_description: Optional[str] = Field(None)
    tags: Optional[List[str]] = Field(None)
    logo_url: Optional[str] = Field(None)
    manifest_url: Optional[str] = Field(None)
    download_url: Optional[str] = Field(None)
    homepage_url: Optional[str] = Field(None)
    repository_url: Optional[str] = Field(None)
    documentation_url: Optional[str] = Field(None)
    latest_version: Optional[str] = Field(None)
    min_agenthr_version: Optional[str] = Field(None)
    max_agenthr_version: Optional[str] = Field(None)
    permissions: Optional[List[str]] = Field(None)
    dependencies: Optional[Dict[str, Any]] = Field(None)
    config_schema: Optional[Dict[str, Any]] = Field(None)
    license: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)
    status: Optional[PluginStatus] = Field(None)


class PluginInstallRequest(BaseModel):
    """Request model for installing a plugin."""

    version: Optional[str] = Field(None, description="Version to install (defaults to latest)")
    config: Optional[Dict[str, Any]] = Field(None, description="Plugin configuration")
    install_notes: Optional[str] = Field(None, description="Installation notes")


class PluginInstallResponse(BaseModel):
    """Response model for plugin installation."""

    id: str = Field(..., description="Installation ID")
    plugin_id: str = Field(..., description="Plugin ID")
    plugin_name: str = Field(..., description="Plugin name")
    version: str = Field(..., description="Installed version")
    is_enabled: bool = Field(..., description="Whether plugin is enabled")
    message: str = Field(..., description="Success message")


class PluginInstallationListItem(BaseModel):
    """Response model for a plugin installation in list view."""

    id: str = Field(..., description="Installation ID")
    plugin_id: str = Field(..., description="Plugin ID")
    plugin_name: str = Field(..., description="Plugin name")
    plugin_slug: str = Field(..., description="Plugin slug")
    plugin_version: str = Field(..., description="Plugin version")
    version: str = Field(..., description="Installed version")
    description: str = Field(..., description="Plugin description")
    category: str = Field(..., description="Plugin category")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    is_enabled: bool = Field(..., description="Whether plugin is enabled")
    config: Optional[Dict[str, Any]] = Field(None, description="Plugin configuration")
    install_notes: Optional[str] = Field(None, description="Installation notes")
    installed_at: str = Field(..., description="Installation timestamp")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class PluginInstallationUpdateRequest(BaseModel):
    """Request model for updating a plugin installation."""

    is_enabled: Optional[bool] = Field(None, description="Enable or disable the plugin")
    config: Optional[Dict[str, Any]] = Field(None, description="Update plugin configuration")
    install_notes: Optional[str] = Field(None, description="Update installation notes")


class PluginValidateRequest(BaseModel):
    """Request model for validating a plugin manifest."""

    manifest_url: str = Field(..., description="URL to the plugin manifest JSON")
    agenthr_version: Optional[str] = Field(
        None,
        description="AgentHR version to check compatibility against (defaults to current version)",
    )


class PluginSearchResponse(BaseModel):
    """Response model for plugin search results."""

    total: int = Field(..., description="Total number of plugins")
    plugins: List[PluginListItem] = Field(..., description="List of plugins")


class PluginStatsResponse(BaseModel):
    """Response model for plugin statistics."""

    total_plugins: int = Field(..., description="Total number of plugins")
    active_plugins: int = Field(..., description="Number of active plugins")
    official_plugins: int = Field(..., description="Number of official plugins")
    total_installations: int = Field(..., description="Total number of installations")
    by_category: Dict[str, int] = Field(..., description="Plugins by category")


def get_current_agenthr_version() -> str:
    """Get the current AgentHR version from config or settings."""
    # This would typically come from config or settings
    return "1.0.0"


@router.get(
    "/",
    response_model=PluginSearchResponse,
    tags=["Plugins"],
)
async def list_plugins(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term for name/description"),
    is_official: Optional[bool] = Query(None, description="Filter by official status"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by approval status"),
    recruiter_id: Optional[str] = Query(None, description="Recruiter ID to check installations"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all available plugins in the marketplace.

    Returns a paginated list of plugins with optional filtering by category,
    search term, official status, and approval status. Also includes installation
    status for a specific recruiter if provided.

    Args:
        request: FastAPI request object
        category: Optional filter by plugin category
        search: Optional search term for name/description
        is_official: Optional filter by official status
        is_active: Optional filter by active status (default: true)
        status_filter: Optional filter by approval status
        recruiter_id: Optional recruiter ID to check installation status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with list of plugins

    Raises:
        HTTPException(500): If data retrieval fails

    Examples:
        >>> import requests
        >>> # Get all active plugins
        >>> response = requests.get("http://localhost:8000/api/plugins/")
        >>> # Filter by category
        >>> response = requests.get("http://localhost:8000/api/plugins/?category=integration")
        >>> # Search plugins
        >>> response = requests.get("http://localhost:8000/api/plugins/?search=slack")
    """
    try:
        logger.info(
            f"Fetching plugins - category: {category}, search: {search}, "
            f"is_official: {is_official}, is_active: {is_active}, "
            f"status: {status_filter}, skip: {skip}, limit: {limit}"
        )

        # Build base query
        query = select(Plugin)

        # Apply filters
        if category:
            try:
                plugin_category = PluginCategory(category)
                query = query.where(Plugin.category == plugin_category)
            except ValueError:
                logger.warning(f"Invalid category: {category}")

        if search:
            query = query.where(
                or_(
                    Plugin.name.ilike(f"%{search}%"),
                    Plugin.description.ilike(f"%{search}%"),
                    Plugin.tags.any(search),  type: ignore
                )
            )

        if is_official is not None:
            query = query.where(Plugin.is_official == is_official)

        if is_active is not None:
            query = query.where(Plugin.is_active == is_active)

        if status_filter:
            try:
                plugin_status = PluginStatus(status_filter)
                query = query.where(Plugin.status == plugin_status)
            except ValueError:
                logger.warning(f"Invalid status: {status_filter}")

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Order by install count (popularity) and created date
        query = query.order_by(Plugin.install_count.desc(), Plugin.created_at.desc())
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        plugins = result.scalars().all()

        # Get installations for recruiter if provided
        installed_plugin_ids = set()
        enabled_plugin_ids = set()

        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                install_query = select(PluginInstallation).where(
                    and_(
                        PluginInstallation.recruiter_id == recruiter_uuid,
                        PluginInstallation.is_enabled == True,
                    )
                )
                install_result = await db.execute(install_query)
                installations = install_result.scalars().all()

                for inst in installations:
                    installed_plugin_ids.add(str(inst.plugin_id))
                    if inst.is_enabled:
                        enabled_plugin_ids.add(str(inst.plugin_id))
            except ValueError:
                logger.warning(f"Invalid recruiter_id format: {recruiter_id}")

        # Get current AgentHR version for compatibility check
        agenthr_version = get_current_agenthr_version()

        # Convert to response format
        plugins_list = []
        for plugin in plugins:
            plugin_dict = {
                "id": str(plugin.id),
                "name": plugin.name,
                "slug": plugin.slug,
                "version": plugin.version,
                "author": plugin.author,
                "description": plugin.description,
                "category": plugin.category.value,
                "tags": plugin.tags or [],
                "logo_url": plugin.logo_url,
                "is_official": plugin.is_official,
                "status": plugin.status.value,
                "is_active": plugin.is_active,
                "install_count": plugin.install_count,
                "rating_count": plugin.rating_count,
                "average_rating": plugin.average_rating,
                "is_installed": str(plugin.id) in installed_plugin_ids,
                "is_enabled": str(plugin.id) in enabled_plugin_ids,
                "created_at": plugin.created_at.isoformat() if plugin.created_at else None,
                "updated_at": plugin.updated_at.isoformat() if plugin.updated_at else None,
            }
            plugins_list.append(plugin_dict)

        logger.info(f"Retrieved {len(plugins_list)} plugins")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total": total,
                "plugins": plugins_list,
            },
        )

    except Exception as e:
        logger.error(f"Error listing plugins: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugins: {str(e)}",
        ) from e


@router.get(
    "/{plugin_id}",
    response_model=PluginDetail,
    tags=["Plugins"],
)
async def get_plugin(
    request: Request,
    plugin_id: str,
    recruiter_id: Optional[str] = Query(None, description="Recruiter ID to check installation"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get detailed information about a specific plugin.

    Args:
        request: FastAPI request object
        plugin_id: Plugin UUID or slug
        recruiter_id: Optional recruiter ID to check installation status
        db: Database session

    Returns:
        JSON response with plugin details

    Raises:
        HTTPException(404): If plugin not found
        HTTPException(500): If data retrieval fails
    """
    try:
        logger.info(f"Fetching plugin: {plugin_id}")

        # Try to parse as UUID first, otherwise treat as slug
        try:
            plugin_uuid = UUID(plugin_id)
            query = select(Plugin).where(Plugin.id == plugin_uuid)
        except ValueError:
            # Treat as slug
            query = select(Plugin).where(Plugin.slug == plugin_id)

        result = await db.execute(query)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not found: {plugin_id}",
            )

        # Check installation status for recruiter
        is_installed = False
        is_enabled = False
        installation_config = None

        if recruiter_id:
            try:
                recruiter_uuid = UUID(recruiter_id)
                install_query = select(PluginInstallation).where(
                    and_(
                        PluginInstallation.plugin_id == plugin.id,
                        PluginInstallation.recruiter_id == recruiter_uuid,
                    )
                )
                install_result = await db.execute(install_query)
                installation = install_result.scalar_one_or_none()

                if installation:
                    is_installed = True
                    is_enabled = installation.is_enabled
                    installation_config = installation.config
            except ValueError:
                logger.warning(f"Invalid recruiter_id format: {recruiter_id}")

        # Check compatibility
        agenthr_version = get_current_agenthr_version()
        is_compatible = plugin.is_compatible_with(agenthr_version)

        plugin_dict = {
            "id": str(plugin.id),
            "name": plugin.name,
            "slug": plugin.slug,
            "version": plugin.version,
            "author": plugin.author,
            "description": plugin.description,
            "long_description": plugin.long_description,
            "category": plugin.category.value,
            "tags": plugin.tags or [],
            "logo_url": plugin.logo_url,
            "is_official": plugin.is_official,
            "status": plugin.status.value,
            "is_active": plugin.is_active,
            "install_count": plugin.install_count,
            "rating_count": plugin.rating_count,
            "average_rating": plugin.average_rating,
            "is_installed": is_installed,
            "is_enabled": is_enabled,
            "homepage_url": plugin.homepage_url,
            "repository_url": plugin.repository_url,
            "documentation_url": plugin.documentation_url,
            "manifest_url": plugin.manifest_url,
            "download_url": plugin.download_url,
            "latest_version": plugin.latest_version,
            "min_agenthr_version": plugin.min_agenthr_version,
            "max_agenthr_version": plugin.max_agenthr_version,
            "permissions": plugin.permissions or [],
            "dependencies": plugin.dependencies,
            "is_compatible": is_compatible,
            "config_schema": installation_config or plugin.dependencies.get("config_schema") if plugin.dependencies else None,
            "license": plugin.dependencies.get("license") if plugin.dependencies else None,
            "created_at": plugin.created_at.isoformat() if plugin.created_at else None,
            "updated_at": plugin.updated_at.isoformat() if plugin.updated_at else None,
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=plugin_dict,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin {plugin_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plugin: {str(e)}",
        ) from e


@router.post(
    "/",
    response_model=PluginDetail,
    tags=["Plugins"],
)
async def create_plugin(
    request: Request,
    plugin_data: PluginCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new plugin in the marketplace.

    Args:
        request: FastAPI request object
        plugin_data: Plugin creation data
        db: Database session

    Returns:
        JSON response with created plugin details

    Raises:
        HTTPException(400): If validation fails
        HTTPException(409): If plugin with same name/slug exists
        HTTPException(500): If creation fails
    """
    try:
        logger.info(f"Creating plugin: {plugin_data.name}")

        # Check if plugin with same name or slug exists
        existing_query = select(Plugin).where(
            or_(Plugin.name == plugin_data.name, Plugin.slug == plugin_data.slug)
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Plugin with name '{plugin_data.name}' or slug '{plugin_data.slug}' already exists",
            )

        # Create plugin
        plugin = Plugin(
            name=plugin_data.name,
            slug=plugin_data.slug,
            version=plugin_data.version,
            author=plugin_data.author,
            author_email=plugin_data.author_email,
            description=plugin_data.description,
            long_description=plugin_data.long_description,
            category=plugin_data.category,
            tags=plugin_data.tags,
            logo_url=plugin_data.logo_url,
            manifest_url=plugin_data.manifest_url,
            download_url=plugin_data.download_url,
            homepage_url=plugin_data.homepage_url,
            repository_url=plugin_data.repository_url,
            documentation_url=plugin_data.documentation_url,
            is_official=plugin_data.is_official,
            min_agenthr_version=plugin_data.min_agenthr_version,
            max_agenthr_version=plugin_data.max_agenthr_version,
            permissions=plugin_data.permissions,
            dependencies=plugin_data.dependencies,
            status=PluginStatus.PENDING_REVIEW,
            is_active=True,
        )

        db.add(plugin)
        await db.commit()
        await db.refresh(plugin)

        logger.info(f"Plugin created: {plugin.id}")

        # Return the created plugin
        return await get_plugin(request, str(plugin.id), db=db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating plugin: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create plugin: {str(e)}",
        ) from e


@router.put(
    "/{plugin_id}",
    response_model=PluginDetail,
    tags=["Plugins"],
)
async def update_plugin(
    request: Request,
    plugin_id: str,
    plugin_data: PluginUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update an existing plugin in the marketplace.

    Args:
        request: FastAPI request object
        plugin_id: Plugin UUID or slug
        plugin_data: Plugin update data
        db: Database session

    Returns:
        JSON response with updated plugin details

    Raises:
        HTTPException(404): If plugin not found
        HTTPException(500): If update fails
    """
    try:
        logger.info(f"Updating plugin: {plugin_id}")

        # Get plugin
        try:
            plugin_uuid = UUID(plugin_id)
            query = select(Plugin).where(Plugin.id == plugin_uuid)
        except ValueError:
            query = select(Plugin).where(Plugin.slug == plugin_id)

        result = await db.execute(query)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not found: {plugin_id}",
            )

        # Update fields
        update_data = plugin_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plugin, field, value)

        await db.commit()
        await db.refresh(plugin)

        logger.info(f"Plugin updated: {plugin.id}")

        return await get_plugin(request, str(plugin.id), db=db)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plugin {plugin_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plugin: {str(e)}",
        ) from e


@router.delete(
    "/{plugin_id}",
    tags=["Plugins"],
)
async def delete_plugin(
    request: Request,
    plugin_id: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete a plugin from the marketplace.

    Args:
        request: FastAPI request object
        plugin_id: Plugin UUID or slug
        db: Database session

    Returns:
        JSON response with deletion confirmation

    Raises:
        HTTPException(404): If plugin not found
        HTTPException(500): If deletion fails
    """
    try:
        logger.info(f"Deleting plugin: {plugin_id}")

        # Get plugin
        try:
            plugin_uuid = UUID(plugin_id)
            query = select(Plugin).where(Plugin.id == plugin_uuid)
        except ValueError:
            query = select(Plugin).where(Plugin.slug == plugin_id)

        result = await db.execute(query)
        plugin = result.scalar_one_or_none()

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not found: {plugin_id}",
            )

        plugin_name = plugin.name
        await db.delete(plugin)
        await db.commit()

        logger.info(f"Plugin deleted: {plugin_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Plugin '{plugin_name}' deleted successfully",
                "plugin_id": plugin_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plugin {plugin_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete plugin: {str(e)}",
        ) from e


@router.post(
    "/{plugin_id}/install",
    response_model=PluginInstallResponse,
    tags=["Plugins"],
)
async def install_plugin(
    request: Request,
    plugin_id: str,
    install_data: PluginInstallRequest,
    recruiter_id: str = Query(..., description="Recruiter ID installing the plugin"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Install a plugin for a recruiter.

    Args:
        request: FastAPI request object
        plugin_id: Plugin UUID or slug
        install_data: Installation details
        recruiter_id: Recruiter ID installing the plugin
        db: Database session

    Returns:
        JSON response with installation details

    Raises:
        HTTPException(404): If plugin not found
        HTTPException(400): If plugin already installed
        HTTPException(500): If installation fails
    """
    try:
        logger.info(f"Installing plugin {plugin_id} for recruiter {recruiter_id}")

        # Parse recruiter ID
        try:
            recruiter_uuid = UUID(recruiter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recruiter ID format: {recruiter_id}",
            )

        # Get plugin
        try:
            plugin_uuid = UUID(plugin_id)
            plugin_query = select(Plugin).where(Plugin.id == plugin_uuid)
        except ValueError:
            plugin_query = select(Plugin).where(Plugin.slug == plugin_id)

        plugin_result = await db.execute(plugin_query)
        plugin = plugin_result.scalar_one_or_none()

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not found: {plugin_id}",
            )

        # Check if already installed
        existing_query = select(PluginInstallation).where(
            and_(
                PluginInstallation.plugin_id == plugin.id,
                PluginInstallation.recruiter_id == recruiter_uuid,
            )
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin already installed for this recruiter",
            )

        # Determine version to install
        version = install_data.version or plugin.version

        # Create installation
        installation = PluginInstallation(
            plugin_id=plugin.id,
            recruiter_id=recruiter_uuid,
            version=version,
            config=install_data.config,
            is_enabled=True,
            install_notes=install_data.install_notes,
        )

        db.add(installation)

        # Update install count
        plugin.install_count += 1

        await db.commit()
        await db.refresh(installation)

        logger.info(f"Plugin installed: {installation.id}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(installation.id),
                "plugin_id": str(plugin.id),
                "plugin_name": plugin.name,
                "version": installation.version,
                "is_enabled": installation.is_enabled,
                "message": f"Plugin '{plugin.name}' installed successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error installing plugin {plugin_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install plugin: {str(e)}",
        ) from e


@router.delete(
    "/{plugin_id}/install",
    tags=["Plugins"],
)
async def uninstall_plugin(
    request: Request,
    plugin_id: str,
    recruiter_id: str = Query(..., description="Recruiter ID uninstalling the plugin"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Uninstall a plugin for a recruiter.

    Args:
        request: FastAPI request object
        plugin_id: Plugin UUID or slug
        recruiter_id: Recruiter ID uninstalling the plugin
        db: Database session

    Returns:
        JSON response with uninstall confirmation

    Raises:
        HTTPException(404): If plugin or installation not found
        HTTPException(500): If uninstall fails
    """
    try:
        logger.info(f"Uninstalling plugin {plugin_id} for recruiter {recruiter_id}")

        # Parse recruiter ID
        try:
            recruiter_uuid = UUID(recruiter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recruiter ID format: {recruiter_id}",
            )

        # Get plugin
        try:
            plugin_uuid = UUID(plugin_id)
            plugin_query = select(Plugin).where(Plugin.id == plugin_uuid)
        except ValueError:
            plugin_query = select(Plugin).where(Plugin.slug == plugin_id)

        plugin_result = await db.execute(plugin_query)
        plugin = plugin_result.scalar_one_or_none()

        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not found: {plugin_id}",
            )

        # Get installation
        install_query = select(PluginInstallation).where(
            and_(
                PluginInstallation.plugin_id == plugin.id,
                PluginInstallation.recruiter_id == recruiter_uuid,
            )
        )
        install_result = await db.execute(install_query)
        installation = install_result.scalar_one_or_none()

        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin not installed for this recruiter",
            )

        plugin_name = plugin.name

        # Delete installation
        await db.delete(installation)

        # Update install count
        if plugin.install_count > 0:
            plugin.install_count -= 1

        await db.commit()

        logger.info(f"Plugin uninstalled: {plugin_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": f"Plugin '{plugin_name}' uninstalled successfully",
                "plugin_id": plugin_id,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uninstalling plugin {plugin_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall plugin: {str(e)}",
        ) from e


@router.get(
    "/installations/list",
    response_model=List[PluginInstallationListItem],
    tags=["Plugins"],
)
async def list_installed_plugins(
    request: Request,
    recruiter_id: str = Query(..., description="Recruiter ID"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    List all installed plugins for a recruiter.

    Args:
        request: FastAPI request object
        recruiter_id: Recruiter ID
        is_enabled: Optional filter by enabled status
        db: Database session

    Returns:
        JSON response with list of installed plugins

    Raises:
        HTTPException(400): If recruiter_id is invalid
        HTTPException(500): If retrieval fails
    """
    try:
        logger.info(f"Fetching installed plugins for recruiter: {recruiter_id}")

        # Parse recruiter ID
        try:
            recruiter_uuid = UUID(recruiter_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid recruiter ID format: {recruiter_id}",
            )

        # Build query with plugin join
        query = (
            select(PluginInstallation, Plugin)
            .join(Plugin, PluginInstallation.plugin_id == Plugin.id)
            .where(PluginInstallation.recruiter_id == recruiter_uuid)
        )

        if is_enabled is not None:
            query = query.where(PluginInstallation.is_enabled == is_enabled)

        query = query.order_by(PluginInstallation.created_at.desc())

        result = await db.execute(query)
        rows = result.all()

        installations_list = []
        for installation, plugin in rows:
            installations_list.append({
                "id": str(installation.id),
                "plugin_id": str(plugin.id),
                "plugin_name": plugin.name,
                "plugin_slug": plugin.slug,
                "plugin_version": plugin.version,
                "version": installation.version,
                "description": plugin.description,
                "category": plugin.category.value,
                "logo_url": plugin.logo_url,
                "is_enabled": installation.is_enabled,
                "config": installation.config,
                "install_notes": installation.install_notes,
                "installed_at": installation.installed_at,
                "last_used_at": installation.last_used_at,
                "created_at": installation.created_at.isoformat() if installation.created_at else None,
                "updated_at": installation.updated_at.isoformat() if installation.updated_at else None,
            })

        logger.info(f"Retrieved {len(installations_list)} installed plugins")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=installations_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing installed plugins: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list installed plugins: {str(e)}",
        ) from e


@router.put(
    "/installations/{installation_id}",
    tags=["Plugins"],
)
async def update_installation(
    request: Request,
    installation_id: str,
    update_data: PluginInstallationUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update a plugin installation (enable/disable, reconfigure).

    Args:
        request: FastAPI request object
        installation_id: Installation UUID
        update_data: Update data
        db: Database session

    Returns:
        JSON response with updated installation details

    Raises:
        HTTPException(404): If installation not found
        HTTPException(500): If update fails
    """
    try:
        logger.info(f"Updating installation: {installation_id}")

        # Parse installation ID
        try:
            installation_uuid = UUID(installation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid installation ID format: {installation_id}",
            )

        # Get installation
        query = select(PluginInstallation).where(PluginInstallation.id == installation_uuid)
        result = await db.execute(query)
        installation = result.scalar_one_or_none()

        if not installation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Installation not found: {installation_id}",
            )

        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(installation, field, value)

        await db.commit()
        await db.refresh(installation)

        logger.info(f"Installation updated: {installation_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": str(installation.id),
                "plugin_id": str(installation.plugin_id),
                "is_enabled": installation.is_enabled,
                "config": installation.config,
                "install_notes": installation.install_notes,
                "message": "Installation updated successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating installation {installation_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update installation: {str(e)}",
        ) from e


@router.post(
    "/validate",
    response_model=PluginManifestValidateResponse,
    tags=["Plugins"],
)
async def validate_plugin_manifest(
    request: Request,
    validate_data: PluginValidateRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Validate a plugin manifest from a URL.

    Fetches and validates a plugin manifest JSON from the given URL,
    checking its structure, required fields, and compatibility.

    Args:
        request: FastAPI request object
        validate_data: Validation request with manifest URL
        db: Database session

    Returns:
        JSON response with validation result

    Raises:
        HTTPException(500): If validation fails

    Examples:
        >>> import requests
        >>> data = {"manifest_url": "https://example.com/plugin/manifest.json"}
        >>> response = requests.post(
        ...     "http://localhost:8000/api/plugins/validate",
        ...     json=data
        ... )
    """
    try:
        logger.info(f"Validating plugin manifest: {validate_data.manifest_url}")

        import httpx

        # Fetch manifest from URL
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(validate_data.manifest_url)
            response.raise_for_status()
            manifest_data = response.json()

        # Validate manifest schema
        try:
            manifest = PluginManifest(**manifest_data)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "valid": False,
                    "errors": [f"Schema validation failed: {str(e)}"],
                    "warnings": [],
                    "manifest": None,
                },
            )

        # Check compatibility
        agenthr_version = validate_data.agenthr_version or get_current_agenthr_version()
        is_compatible = True
        compatibility_message = None

        if manifest.min_agenthr_version:
            try:
                if pkg_version.parse(agenthr_version) < pkg_version.parse(manifest.min_agenthr_version):
                    is_compatible = False
                    compatibility_message = (
                        f"Requires AgentHR version >= {manifest.min_agenthr_version}, "
                        f"current is {agenthr_version}"
                    )
            except Exception:
                pass

        if is_compatible and manifest.max_agenthr_version:
            try:
                if pkg_version.parse(agenthr_version) > pkg_version.parse(manifest.max_agenthr_version):
                    is_compatible = False
                    compatibility_message = (
                        f"Requires AgentHR version <= {manifest.max_agenthr_version}, "
                        f"current is {agenthr_version}"
                    )
            except Exception:
                pass

        # Build response
        manifest_response = PluginManifestResponse(
            name=manifest.name,
            slug=manifest.slug,
            version=manifest.version,
            author=manifest.author,
            description=manifest.description,
            long_description=manifest.long_description,
            category=manifest.category.value,
            tags=manifest.tags,
            logo_url=manifest.logo_url,
            homepage_url=manifest.homepage_url,
            repository_url=manifest.repository_url,
            documentation_url=manifest.documentation_url,
            min_agenthr_version=manifest.min_agenthr_version,
            max_agenthr_version=manifest.max_agenthr_version,
            permissions=manifest.permissions,
            dependencies=manifest.dependencies,
            python_dependencies=manifest.python_dependencies,
            entry_points=manifest.entry_points,
            config_schema=manifest.config_schema,
            license=manifest.license,
            keywords=manifest.keywords,
            is_compatible=is_compatible,
            compatibility_message=compatibility_message,
        )

        logger.info(f"Manifest validation result: valid={is_compatible}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "valid": is_compatible,
                "errors": [] if is_compatible else [compatibility_message or "Compatibility check failed"],
                "warnings": [],
                "manifest": manifest_response.dict() if is_compatible else None,
            },
        )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching manifest: {e}")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "valid": False,
                "errors": [f"Failed to fetch manifest: {str(e)}"],
                "warnings": [],
                "manifest": None,
            },
        )
    except Exception as e:
        logger.error(f"Error validating manifest: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate manifest: {str(e)}",
        ) from e


@router.get(
    "/stats/overview",
    response_model=PluginStatsResponse,
    tags=["Plugins"],
)
async def get_plugin_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get plugin marketplace statistics.

    Returns aggregate statistics about plugins including total count,
    active plugins, official plugins, total installations, and breakdown by category.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        JSON response with plugin statistics

    Raises:
        HTTPException(500): If retrieval fails
    """
    try:
        logger.info("Fetching plugin statistics")

        # Get total plugins
        total_query = select(func.count()).select_from(Plugin)
        total_result = await db.execute(total_query)
        total_plugins = total_result.scalar() or 0

        # Get active plugins
        active_query = select(func.count()).select_from(Plugin).where(Plugin.is_active == True)
        active_result = await db.execute(active_query)
        active_plugins = active_result.scalar() or 0

        # Get official plugins
        official_query = select(func.count()).select_from(Plugin).where(Plugin.is_official == True)
        official_result = await db.execute(official_query)
        official_plugins = official_result.scalar() or 0

        # Get total installations
        install_query = select(func.count()).select_from(PluginInstallation)
        install_result = await db.execute(install_query)
        total_installations = install_result.scalar() or 0

        # Get plugins by category
        category_query = (
            select(Plugin.category, func.count(Plugin.id))
            .group_by(Plugin.category)
        )
        category_result = await db.execute(category_query)
        by_category = {cat.value: count for cat, count in category_result.all()}

        logger.info("Plugin statistics retrieved successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_plugins": total_plugins,
                "active_plugins": active_plugins,
                "official_plugins": official_plugins,
                "total_installations": total_installations,
                "by_category": by_category,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching plugin statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch plugin statistics: {str(e)}",
        ) from e
