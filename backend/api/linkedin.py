"""
LinkedIn integration endpoints.

This module provides endpoints for:
- OAuth 2.0 authentication with LinkedIn
- Importing LinkedIn profiles
- Searching LinkedIn candidates
- Viewing LinkedIn import history

Supports seamless integration with LinkedIn for candidate sourcing.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.linkedin_import import LinkedInImport, LinkedInImportStatus
from models.linkedin_profile import LinkedInProfile, LinkedInProfileStatus
from models.linkedin_token import LinkedInToken
from models.recruiter import Recruiter
from models.resume import Resume, ResumeStatus
from utils.linkedin_oauth import generate_auth_url, generate_state, verify_state
from utils.redis_client import store_oauth_state, verify_oauth_state
from utils.token_encryption import encrypt_token

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class AuthUrlRequest(BaseModel):
    """Request model for generating LinkedIn authorization URL."""

    scopes: Optional[List[str]] = Field(
        None,
        description="List of OAuth scopes to request. If not provided, uses default scopes.",
    )
    force_login: bool = Field(
        False,
        description="Force user to re-login even if already authenticated with LinkedIn",
    )


class AuthUrlResponse(BaseModel):
    """Response model for LinkedIn authorization URL."""

    auth_url: str = Field(..., description="Complete LinkedIn authorization URL")
    state: str = Field(..., description="OAuth state parameter for CSRF protection")
    message: str = Field(..., description="Info message about next steps")


class CallbackRequest(BaseModel):
    """Request model for OAuth callback processing."""

    code: str = Field(..., description="Authorization code from LinkedIn")
    state: str = Field(..., description="State parameter for CSRF protection")


class CallbackResponse(BaseModel):
    """Response model for OAuth callback processing."""

    success: bool = Field(..., description="Whether the callback was processed successfully")
    message: str = Field(..., description="Status message")
    access_token: Optional[str] = Field(None, description="Access token (if successful)")
    expires_in: Optional[int] = Field(None, description="Token lifetime in seconds")


class ProfileImportRequest(BaseModel):
    """Request model for importing a LinkedIn profile."""

    linkedin_url: str = Field(
        ...,
        description="LinkedIn profile URL (e.g., https://www.linkedin.com/in/username)",
    )
    profile_id: Optional[str] = Field(
        None,
        description="LinkedIn profile ID (alternative to URL)",
    )


class ProfileImportResponse(BaseModel):
    """Response model for profile import."""

    success: bool = Field(..., description="Whether the import was successful")
    message: str = Field(..., description="Status message")
    profile_id: Optional[str] = Field(None, description="Imported profile ID")
    resume_id: Optional[str] = Field(None, description="Associated resume ID")


class LinkedInSearchRequest(BaseModel):
    """Request model for LinkedIn candidate search."""

    keywords: Optional[str] = Field(None, description="Search keywords")
    skills: Optional[List[str]] = Field(None, description="Required skills")
    location: Optional[str] = Field(None, description="Location filter")
    industry: Optional[str] = Field(None, description="Industry filter")
    experience_level: Optional[str] = Field(None, description="Experience level filter")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")


class LinkedInProfileSummary(BaseModel):
    """Summary of a LinkedIn profile from search results."""

    profile_id: str = Field(..., description="LinkedIn profile ID")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    headline: Optional[str] = Field(None, description="Profile headline")
    location: Optional[str] = Field(None, description="Location")
    industry: Optional[str] = Field(None, description="Industry")
    profile_url: str = Field(..., description="LinkedIn profile URL")


class LinkedInSearchResponse(BaseModel):
    """Response model for LinkedIn search results."""

    total_results: int = Field(..., description="Total number of results")
    results: List[LinkedInProfileSummary] = Field(..., description="Search results")


class ImportHistoryItem(BaseModel):
    """Single item in LinkedIn import history."""

    import_id: str = Field(..., description="Import record ID")
    profile_id: str = Field(..., description="LinkedIn profile ID")
    profile_name: str = Field(..., description="Profile name")
    imported_at: str = Field(..., description="Import timestamp")
    status: str = Field(..., description="Import status (success/failed)")
    resume_id: Optional[str] = Field(None, description="Associated resume ID")


class ImportHistoryResponse(BaseModel):
    """Response model for import history."""

    total_imports: int = Field(..., description="Total number of imports")
    imports: List[ImportHistoryItem] = Field(..., description="Import history records")


@router.get(
    "/auth/url",
    response_model=AuthUrlResponse,
    tags=["LinkedIn"],
)
async def get_auth_url(
    request: Request,
    scopes: Optional[str] = Query(None, description="Comma-separated list of OAuth scopes"),
    force_login: bool = Query(False, description="Force re-login"),
) -> JSONResponse:
    """
    Generate LinkedIn OAuth 2.0 authorization URL.

    This endpoint generates a LinkedIn authorization URL that users should be
    redirected to for granting permission to access their LinkedIn profile.

    The authorization URL includes:
    - Client ID
    - Redirect URI
    - Requested OAuth scopes
    - State parameter for CSRF protection

    Args:
        request: FastAPI request object
        scopes: Optional comma-separated list of OAuth scopes
        force_login: Force user to re-login even if already authenticated

    Returns:
        JSON response with authorization URL and state parameter

    Raises:
        HTTPException(500): If LinkedIn client configuration is missing

    Examples:
        >>> import requests
        >>> # Get default authorization URL
        >>> response = requests.get("http://localhost:8000/api/linkedin/auth/url")
        >>> data = response.json()
        >>> # Redirect user to data["auth_url"]
        >>> # Store data["state"] for callback verification
        >>>
        >>> # Get authorization URL with custom scopes
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/auth/url",
        ...     params={"scopes": "r_liteprofile,r_emailaddress"}
        ... )
    """
    try:
        logger.info(
            f"Generating LinkedIn authorization URL - scopes: {scopes}, force_login: {force_login}"
        )

        # Parse scopes from comma-separated string to list
        scopes_list = None
        if scopes:
            scopes_list = [s.strip() for s in scopes.split(",")]
            logger.debug(f"Parsed scopes: {scopes_list}")

        # Generate state parameter for CSRF protection
        state = generate_state()

        # Store state in Redis with 10-minute TTL
        state_stored = await store_oauth_state(state, ttl_seconds=600)
        if not state_stored:
            logger.error("Failed to store OAuth state in Redis")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize OAuth flow. Please try again.",
            )

        # Generate authorization URL
        auth_url = generate_auth_url(
            state=state,
            scopes=scopes_list,
            force_login=force_login,
        )

        logger.info(
            "Successfully generated LinkedIn authorization URL",
            state=state[:10] + "...",  # Log only partial state for security
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "auth_url": auth_url,
                "state": state,
                "message": "Redirect user to the authorization URL to grant LinkedIn access",
            },
        )

    except ValueError as e:
        # Configuration error (missing client ID, redirect URI, etc.)
        logger.error(f"Configuration error generating auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LinkedIn configuration error: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Error generating LinkedIn authorization URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}",
        ) from e


@router.post(
    "/auth/callback",
    response_model=CallbackResponse,
    tags=["LinkedIn"],
)
async def process_callback(
    request: Request,
    callback_data: CallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Process LinkedIn OAuth callback and exchange code for access token.

    This endpoint handles the callback from LinkedIn after user authorization.
    It exchanges the authorization code for an access token that can be used
    to make authenticated API requests to LinkedIn.

    Args:
        request: FastAPI request object
        callback_data: Callback data including code and state parameters
        db: Database session

    Returns:
        JSON response with access token info

    Raises:
        HTTPException(400): Invalid callback data
        HTTPException(401): State verification failed
        HTTPException(500): Token exchange failed

    Examples:
        >>> import requests
        >>> data = {
        ...     "code": "authorization-code-from-linkedin",
        ...     "state": "state-from-auth-url-step"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/linkedin/auth/callback",
        ...     json=data
        ... )
        >>> token_data = response.json()
        >>> access_token = token_data["access_token"]
    """
    try:
        logger.info("Processing LinkedIn OAuth callback")

        if not callback_data.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required",
            )

        if not callback_data.state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="State parameter is required",
            )

        # Verify state parameter to prevent CSRF attacks
        state_valid = await verify_oauth_state(callback_data.state)
        if not state_valid:
            logger.warning(
                "OAuth state verification failed",
                state=callback_data.state[:10] + "...",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="State verification failed. Please try the OAuth flow again.",
            )

        logger.debug("State verified successfully")

        # Exchange authorization code for access token
        from utils.linkedin_oauth import exchange_code_for_token

        token_data = exchange_code_for_token(callback_data.code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")  # Seconds until expiration

        logger.info("Successfully exchanged authorization code for access token")

        # Calculate token expiration timestamp
        from datetime import datetime, timedelta
        token_expires_at = None
        if expires_in:
            token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Encrypt tokens for storage
        access_token_encrypted = encrypt_token(access_token)
        refresh_token_encrypted = encrypt_token(refresh_token) if refresh_token else None

        # For this implementation, we'll use the first recruiter we find
        # In production, you would get the current user from the session/JWT token
        result = await db.execute(select(Recruiter).limit(1))
        recruiter = result.scalar_one_or_none()

        if not recruiter:
            # Create a default recruiter if none exists
            recruiter = Recruiter(
                name="Default Recruiter",
                email="recruiter@example.com",
                is_active=True,
            )
            db.add(recruiter)
            await db.flush()
            logger.info(f"Created default recruiter: {recruiter.id}")

        # Store encrypted token in database
        linkedin_token = LinkedInToken(
            recruiter_id=recruiter.id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expires_at=token_expires_at,
        )
        db.add(linkedin_token)
        await db.commit()

        logger.info(
            "LinkedIn token stored successfully",
            token_id=str(linkedin_token.id),
            recruiter_id=str(recruiter.id),
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Successfully connected to LinkedIn",
                "redirect_to": "/dashboard",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Configuration error during token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LinkedIn configuration error: {str(e)}",
        ) from e
    except RuntimeError as e:
        logger.error(f"Token exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to exchange authorization code: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Error processing LinkedIn callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process callback: {str(e)}",
        ) from e


@router.post(
    "/import",
    response_model=ProfileImportResponse,
    tags=["LinkedIn"],
)
async def import_profile(
    request: Request,
    import_data: ProfileImportRequest,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Import a LinkedIn profile into AgentHR.

    This endpoint fetches profile data from LinkedIn and creates a resume record
    with the imported information. The profile is automatically analyzed and scored.

    Args:
        request: FastAPI request object
        import_data: Profile import data (URL or profile ID)
        db: Database session

    Returns:
        JSON response with import status and profile/resume IDs

    Raises:
        HTTPException(401): No valid LinkedIn access token
        HTTPException(400): Invalid profile URL or ID
        HTTPException(500): Import failed

    Examples:
        >>> import requests
        >>> data = {
        ...     "linkedin_url": "https://www.linkedin.com/in/johndoe"
        ... }
        >>> response = requests.post(
        ...     "http://localhost:8000/api/linkedin/import",
        ...     json=data,
        ...     headers={"Authorization": "Bearer your-token"}
        ... )
    """
    # Extract locale from Accept-Language header
    locale = _extract_locale(request)

    try:
        # Validate LinkedIn URL format
        if not import_data.linkedin_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn URL is required",
            )

        # Basic URL validation
        if "linkedin.com/in/" not in import_data.linkedin_url and "linkedin.com/" not in import_data.linkedin_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid LinkedIn profile URL. Expected format: https://www.linkedin.com/in/username",
            )

        logger.info(f"Importing LinkedIn profile: {import_data.linkedin_url}")

        # Get recruiter and their LinkedIn token
        # For this implementation, use the first recruiter
        result = await db.execute(
            select(Recruiter)
            .order_by(desc(Recruiter.created_at))
            .limit(1)
        )
        recruiter = result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No recruiter found. Please complete OAuth authentication first.",
            )

        # Get LinkedIn token for this recruiter
        token_result = await db.execute(
            select(LinkedInToken).where(LinkedInToken.recruiter_id == recruiter.id)
        )
        linkedin_token = token_result.scalar_one_or_none()

        if not linkedin_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="LinkedIn authentication required. Please connect your LinkedIn account first.",
            )

        # Decrypt access token
        from utils.token_encryption import decrypt_token
        try:
            access_token = decrypt_token(linkedin_token.access_token_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired LinkedIn access token. Please re-authenticate.",
            )

        # Fetch profile data from LinkedIn
        from services.linkedin_service import LinkedInService
        linkedin_service = LinkedInService(access_token)

        try:
            # Extract LinkedIn member ID from URL
            linkedin_id = import_data.linkedin_url.strip("/").split("/")[-1]

            # Fetch profile data
            profile_data = await linkedin_service.get_profile(linkedin_id)

            logger.info(
                "Fetched LinkedIn profile data",
                linkedin_id=linkedin_id,
                profile_name=f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip(),
            )

        except Exception as e:
            logger.error(f"Failed to fetch LinkedIn profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch LinkedIn profile: {str(e)}",
            )

        # Create or update LinkedInProfile record
        # Check if profile already exists
        existing_profile = await db.execute(
            select(LinkedInProfile).where(
                LinkedInProfile.linkedin_id == profile_data.get("id")
            )
        )
        existing = existing_profile.scalar_one_or_none()

        if existing:
            # Update existing profile
            for key, value in profile_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.status = LinkedInProfileStatus.COMPLETED
            linkedin_profile = existing
            logger.info(f"Updated existing LinkedIn profile: {existing.id}")
        else:
            # Create new profile
            linkedin_profile = LinkedInProfile(
                linkedin_id=profile_data.get("id"),
                linkedin_url=import_data.linkedin_url,
                first_name=profile_data.get("first_name"),
                last_name=profile_data.get("last_name"),
                headline=profile_data.get("headline"),
                location=profile_data.get("location"),
                email=profile_data.get("email"),
                phone=profile_data.get("phone"),
                profile_picture_url=profile_data.get("profile_picture_url"),
                skills=profile_data.get("skills"),
                experience=profile_data.get("experience"),
                education=profile_data.get("education"),
                raw_profile_data=profile_data,
                status=LinkedInProfileStatus.COMPLETED,
            )
            db.add(linkedin_profile)
            logger.info(f"Created new LinkedIn profile: {linkedin_profile.id}")

        await db.flush()  # Get the profile ID

        # Create Resume record with LinkedIn source attribution
        try:
            # Generate filename from profile name
            profile_name = f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip()
            if not profile_name:
                profile_name = f"linkedin_profile_{linkedin_profile.linkedin_id}"

            # Generate virtual file path for LinkedIn import
            # LinkedIn profiles don't have physical files, so we use a virtual path
            virtual_file_path = f"linkedin/{linkedin_profile.linkedin_id}.json"

            # Extract text content from LinkedIn profile for raw_text field
            raw_text_parts = []
            if profile_data.get('first_name'):
                raw_text_parts.append(f"Name: {profile_data.get('first_name')} {profile_data.get('last_name', '')}")
            if profile_data.get('headline'):
                raw_text_parts.append(f"Headline: {profile_data.get('headline')}")
            if profile_data.get('location'):
                raw_text_parts.append(f"Location: {profile_data.get('location')}")
            if profile_data.get('skills'):
                skills = profile_data.get('skills')
                if isinstance(skills, list):
                    raw_text_parts.append(f"Skills: {', '.join(str(s) for s in skills)}")
            if profile_data.get('experience'):
                raw_text_parts.append("Experience: (see structured data)")
            if profile_data.get('education'):
                raw_text_parts.append("Education: (see structured data)")

            raw_text = "\n".join(raw_text_parts)

            # Create Resume record
            resume = Resume(
                filename=f"{profile_name}_linkedin.json",
                file_path=virtual_file_path,
                content_type="application/json",
                status=ResumeStatus.COMPLETED,  # LinkedIn profiles are already "complete"
                source="linkedin",
                raw_text=raw_text,
                language="en",  # Default to English, can be enhanced with language detection
            )
            db.add(resume)
            await db.flush()  # Get the resume ID

            logger.info(
                f"Created Resume record for LinkedIn profile",
                resume_id=str(resume.id),
                profile_id=str(linkedin_profile.id),
            )

            resume_id = str(resume.id)

        except Exception as e:
            logger.error(f"Failed to create Resume record: {e}")
            # Don't fail the entire import if Resume creation fails
            resume_id = None

        # Trigger background task for skill extraction and taxonomy mapping
        try:
            from tasks.linkedin_sync import sync_linkedin_profile, map_linkedin_skills_to_taxonomy

            # Trigger sync task (runs asynchronously)
            sync_linkedin_profile.delay(str(linkedin_profile.id), str(recruiter.id))

            # Trigger skill mapping task
            map_linkedin_skills_to_taxonomy.delay(str(linkedin_profile.id))

            logger.info("Background tasks triggered for profile processing")

        except ImportError:
            logger.warning("Celery tasks not available, skipping background processing")
        except Exception as e:
            logger.error(f"Failed to trigger background tasks: {e}")

        await db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "LinkedIn profile imported successfully",
                "profile_id": str(linkedin_profile.id),
                "resume_id": resume_id,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation and auth errors)
        raise
    except Exception as e:
        logger.error(f"Error importing LinkedIn profile: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import profile: {str(e)}",
        ) from e


def _extract_locale(request: Optional[Request]) -> str:
    """
    Extract Accept-Language header from request.

    Args:
        request: The incoming FastAPI request (optional)

    Returns:
        Language code (e.g., 'en', 'ru')
    """
    if request is None:
        return "en"
    accept_language = request.headers.get("Accept-Language", "en")
    lang_code = accept_language.split("-")[0].split(",")[0].strip().lower()
    return lang_code


@router.get(
    "/search",
    response_model=LinkedInSearchResponse,
    tags=["LinkedIn"],
)
async def search_profiles(
    request: Request,
    keywords: Optional[str] = Query(None, description="Search keywords"),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
    location: Optional[str] = Query(None, description="Location filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Search for candidates on LinkedIn.

    This endpoint searches LinkedIn for candidates matching the specified criteria.
    Results can be imported directly into AgentHR.

    Args:
        request: FastAPI request object
        keywords: Search keywords
        skills: Comma-separated list of required skills
        location: Location filter
        industry: Industry filter
        limit: Maximum number of results (1-50)
        db: Database session

    Returns:
        JSON response with search results

    Raises:
        HTTPException(401): No valid LinkedIn access token
        HTTPException(500): Search failed

    Examples:
        >>> import requests
        >>> params = {
        ...     "skills": "python,react",
        ...     "location": "San Francisco",
        ...     "limit": 20
        ... }
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/search",
        ...     params=params,
        ...     headers={"Authorization": "Bearer your-token"}
        ... )
    """
    try:
        logger.info(
            f"Searching LinkedIn profiles - keywords: {keywords}, skills: {skills}, "
            f"location: {location}, industry: {industry}, limit: {limit}"
        )

        # Get recruiter and their LinkedIn token
        result = await db.execute(
            select(Recruiter)
            .order_by(desc(Recruiter.created_at))
            .limit(1)
        )
        recruiter = result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No recruiter found. Please complete OAuth authentication first.",
            )

        # Get LinkedIn token for this recruiter
        token_result = await db.execute(
            select(LinkedInToken).where(LinkedInToken.recruiter_id == recruiter.id)
        )
        linkedin_token = token_result.scalar_one_or_none()

        if not linkedin_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="LinkedIn authentication required. Please connect your LinkedIn account first.",
            )

        # Decrypt access token
        from utils.token_encryption import decrypt_token
        try:
            access_token = decrypt_token(linkedin_token.access_token_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired LinkedIn access token. Please re-authenticate.",
            )

        # Parse skills from comma-separated string
        skills_list = None
        if skills:
            skills_list = [s.strip() for s in skills.split(",") if s.strip()]

        # Search LinkedIn using the service
        from services.linkedin_service import LinkedInService
        linkedin_service = LinkedInService(access_token)

        try:
            # Perform search
            search_response = await linkedin_service.search_candidates(
                keywords=keywords,
                skills=skills_list,
                location=location,
                industry=industry,
                limit=limit,
            )

            logger.info(
                "LinkedIn search completed",
                results_count=search_response.get("total", 0),
            )

        except Exception as e:
            logger.error(f"LinkedIn search failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LinkedIn search failed: {str(e)}",
            )

        # Extract results from search response
        search_results = search_response.get("results", [])

        # Format results as LinkedInSearchResponse
        results = [
            LinkedInProfileSummary(
                profile_id=result.get("id", ""),
                first_name=result.get("first_name", ""),
                last_name=result.get("last_name", ""),
                headline=result.get("headline"),
                location=result.get("location"),
                industry=result.get("industry"),
                profile_url=result.get("profile_url", ""),
            )
            for result in search_results
        ]

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "total_results": search_response.get("total", 0),
                "results": [r.model_dump() for r in results],
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (auth and validation errors)
        raise
    except Exception as e:
        logger.error(f"Error searching LinkedIn profiles: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search profiles: {str(e)}",
        ) from e


@router.get(
    "/history",
    response_model=ImportHistoryResponse,
    tags=["LinkedIn"],
)
async def get_import_history(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get LinkedIn import history.

    Returns a paginated list of all LinkedIn profiles that have been imported,
    including timestamps and status information. This endpoint allows recruiters
    to track their LinkedIn sourcing activity and review past imports.

    The import history includes:
    - Import record ID
    - LinkedIn profile ID
    - Profile name
    - Import timestamp
    - Import status (success/failed)
    - Associated resume ID (if successful)

    Args:
        request: FastAPI request object
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session

    Returns:
        JSON response with import history including total count and paginated results

    Raises:
        HTTPException(500): History retrieval failed

    Examples:
        >>> import requests
        >>> # Get first 50 import records
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/history",
        ...     params={"limit": 50}
        ... )
        >>> history = response.json()
        >>> total = history["total_imports"]
        >>> imports = history["imports"]
        >>>
        >>> # Get next page with pagination
        >>> response = requests.get(
        ...     "http://localhost:8000/api/linkedin/history",
        ...     params={"skip": 50, "limit": 50}
        ... )
    """
    try:
        logger.info(f"Fetching LinkedIn import history - skip: {skip}, limit: {limit}")

        # Query total count of imports
        count_query = select(func.count(LinkedInImport.id))
        total_result = await db.execute(count_query)
        total_imports = total_result.scalar() or 0

        # Query import history with pagination
        # Note: LinkedInImport tracks bulk import operations, not individual profiles
        # Each import operation can include multiple candidates (tracked via total_candidates,
        # successful_imports, failed_imports counters)
        query = (
            select(LinkedInImport)
            .order_by(desc(LinkedInImport.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        imports = result.scalars().all()

        # Format results as ImportHistoryItem
        import_items = []
        for imp in imports:
            # Since LinkedInImport tracks bulk operations, we use the import_id
            # For profile_name, we construct a descriptive name from the import metadata
            profile_name = f"Import Operation ({imp.total_candidates or 0} candidates)"

            # Format timestamp
            imported_at = imp.created_at.isoformat() if imp.created_at else ""

            # Map status to string
            status_str = imp.status.value if isinstance(imp.status, LinkedInImportStatus) else str(imp.status)

            import_item = ImportHistoryItem(
                import_id=str(imp.id),
                profile_id=str(imp.id),  # Using import_id as profile_id for bulk operations
                profile_name=profile_name,
                imported_at=imported_at,
                status=status_str,
                resume_id=None,  # Resume tracking not implemented for bulk imports
            )
            import_items.append(import_item)

        response_data = {
            "total_imports": total_imports,
            "imports": import_items,
        }

        logger.info(
            f"Import history retrieved successfully - total: {total_imports}, "
            f"returned: {len(import_items)} records"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data,
        )

    except Exception as e:
        logger.error(f"Error fetching import history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch import history: {str(e)}",
        ) from e
