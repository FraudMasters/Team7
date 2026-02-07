"""
LinkedIn OAuth 2.0 Utility Module

This module provides utility functions for implementing LinkedIn OAuth 2.0 authentication.
It handles generating authorization URLs and exchanging authorization codes for access tokens.

Features:
- Generate LinkedIn OAuth 2.0 authorization URLs with state parameter for CSRF protection
- Exchange authorization codes for access tokens using LinkedIn's token endpoint
- Secure token handling with proper error handling
- Integration with application configuration for LinkedIn client credentials
- Logging for debugging and monitoring OAuth flows

Example:
    >>> from utils.linkedin_oauth import generate_auth_url, exchange_code_for_token
    >>> # Generate authorization URL
    >>> auth_url = generate_auth_url(state="random-state-123")
    >>> # User visits auth_url and authorizes, then LinkedIn redirects back with code
    >>> # Exchange the code for an access token
    >>> token_data = exchange_code_for_token("authorization-code-123")
    >>> print(token_data["access_token"])
    'AQXzV3...'
"""
import logging
import secrets
from typing import Dict, Optional
from urllib.parse import urlencode

import httpx
from config import get_settings

logger = logging.getLogger(__name__)

# LinkedIn OAuth 2.0 endpoints
LINKEDIN_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# Default OAuth scopes for LinkedIn profile access
DEFAULT_SCOPES = [
    "r_liteprofile",  # Basic profile data
    "r_emailaddress",  # Email address
]


def generate_auth_url(
    state: str | None = None,
    scopes: list[str] | None = None,
    force_login: bool = False,
) -> str:
    """
    Generate a LinkedIn OAuth 2.0 authorization URL.

    This function creates the URL that users should be redirected to for LinkedIn
    authorization. The URL includes the client ID, redirect URI, requested scopes,
    and a state parameter for CSRF protection.

    Args:
        state: Optional state parameter for CSRF protection. If None, generates
               a cryptographically secure random string. This state should be
               validated in the callback to prevent CSRF attacks.
        scopes: List of OAuth scopes to request. If None, uses DEFAULT_SCOPES.
                Common scopes include: r_liteprofile, r_emailaddress
        force_login: If True, forces the user to re-login even if already
                     authenticated with LinkedIn.

    Returns:
        The complete LinkedIn authorization URL to redirect the user to

    Raises:
        ValueError: If LinkedIn client ID or redirect URI is not configured

    Example:
        >>> # Generate URL with auto-generated state
        >>> auth_url = generate_auth_url()
        >>> # Generate URL with custom state
        >>> auth_url = generate_auth_url(state="my-custom-state-123")
        >>> # Generate URL with custom scopes
        >>> auth_url = generate_auth_url(scopes=["r_liteprofile", "r_emailaddress"])
        >>> # Redirect user to auth_url
        >>> # After authorization, LinkedIn redirects back with code and state
    """
    settings = get_settings()

    # Validate required configuration
    if not settings.linkedin_client_id:
        raise ValueError(
            "LinkedIn client ID is not configured. "
            "Please set LINKEDIN_CLIENT_ID environment variable."
        )

    if not settings.linkedin_redirect_uri:
        raise ValueError(
            "LinkedIn redirect URI is not configured. "
            "Please set LINKEDIN_REDIRECT_URI environment variable."
        )

    # Generate state if not provided
    if state is None:
        state = secrets.token_urlsafe(32)
        logger.debug("Generated OAuth state parameter")

    # Use default scopes if not provided
    if scopes is None:
        scopes = DEFAULT_SCOPES

    # Build query parameters
    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "state": state,
        "scope": " ".join(scopes),
    }

    # Add force_login parameter if requested
    if force_login:
        params["force_login"] = "true"

    # Construct the authorization URL
    auth_url = f"{LINKEDIN_AUTH_URL}?{urlencode(params)}"

    logger.info(
        "Generated LinkedIn authorization URL",
        state=state,
        scopes=scopes,
        force_login=force_login,
    )

    return auth_url


def exchange_code_for_token(
    code: str,
    redirect_uri: str | None = None,
) -> Dict[str, any]:
    """
    Exchange a LinkedIn authorization code for an access token.

    This function takes the authorization code received from the LinkedIn OAuth
    callback and exchanges it for an access token by making a POST request to
    LinkedIn's token endpoint.

    Args:
        code: The authorization code received from LinkedIn callback
        redirect_uri: Optional override for the redirect URI. If None, uses the
                      configured LINKEDIN_REDIRECT_URI. This must match the
                      redirect_uri used in the authorization request.

    Returns:
        A dictionary containing the token response with keys:
        - access_token: The OAuth access token
        - expires_in: Token lifetime in seconds (typically 3600)
        - refresh_token: Optional refresh token (if offline_access granted)

    Raises:
        ValueError: If LinkedIn client credentials are not configured
        httpx.HTTPError: If the HTTP request fails
        RuntimeError: If the token exchange fails (invalid code, etc.)

    Example:
        >>> # Exchange authorization code for access token
        >>> token_data = exchange_code_for_token("auth-code-from-callback")
        >>> access_token = token_data["access_token"]
        >>> # Use access_token to make API requests
        >>> headers = {"Authorization": f"Bearer {access_token}"}
        >>> response = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    """
    settings = get_settings()

    # Validate required configuration
    if not settings.linkedin_client_id:
        raise ValueError(
            "LinkedIn client ID is not configured. "
            "Please set LINKEDIN_CLIENT_ID environment variable."
        )

    if not settings.linkedin_client_secret:
        raise ValueError(
            "LinkedIn client secret is not configured. "
            "Please set LINKEDIN_CLIENT_SECRET environment variable."
        )

    # Use configured redirect URI if not provided
    if redirect_uri is None:
        redirect_uri = settings.linkedin_redirect_uri

    if not redirect_uri:
        raise ValueError(
            "LinkedIn redirect URI is not configured. "
            "Please set LINKEDIN_REDIRECT_URI environment variable."
        )

    # Prepare token request data
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.linkedin_client_id,
        "client_secret": settings.linkedin_client_secret,
    }

    logger.info(
        "Exchanging authorization code for access token",
        redirect_uri=redirect_uri,
    )

    try:
        # Make POST request to LinkedIn's token endpoint
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                LINKEDIN_TOKEN_URL,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            token_data = response.json()

            # Validate response contains access_token
            if "access_token" not in token_data:
                logger.error(
                    "Token response missing access_token",
                    response_keys=list(token_data.keys()),
                )
                raise RuntimeError(
                    "Token response does not contain access_token. "
                    f"Response keys: {list(token_data.keys())}"
                )

            logger.info(
                "Successfully exchanged authorization code for access token",
                expires_in=token_data.get("expires_in"),
                has_refresh_token="refresh_token" in token_data,
            )

            return token_data

    except httpx.HTTPStatusError as e:
        # Log detailed error information
        error_response = None
        try:
            error_response = e.response.json()
        except Exception:
            error_response = e.response.text

        logger.error(
            "HTTP error during token exchange",
            status_code=e.response.status_code,
            error_response=error_response,
        )

        raise RuntimeError(
            f"Failed to exchange authorization code: "
            f"HTTP {e.response.status_code} - {error_response}"
        ) from e

    except httpx.RequestError as e:
        logger.error(
            "Network error during token exchange",
            error=str(e),
        )
        raise RuntimeError(
            f"Network error during token exchange: {e}"
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error during token exchange",
            error_type=type(e).__name__,
            error=str(e),
        )
        raise RuntimeError(
            f"Unexpected error during token exchange: {e}"
        ) from e


def verify_state(state: str, expected_state: str) -> bool:
    """
    Verify the OAuth state parameter to prevent CSRF attacks.

    This function compares the state parameter received in the OAuth callback
    with the expected state that was generated during authorization URL creation.

    Args:
        state: The state parameter received from LinkedIn callback
        expected_state: The state parameter that was originally generated

    Returns:
        True if the state parameters match, False otherwise

    Example:
        >>> # During authorization, store the state
        >>> stored_state = "random-state-123"
        >>>
        >>> # In the callback, verify the state
        >>> callback_state = request.args.get("state")
        >>> if verify_state(callback_state, stored_state):
        ...     # State is valid, proceed with token exchange
        ...     token = exchange_code_for_token(code)
        ... else:
        ...     # State mismatch, possible CSRF attack
        ...     raise SecurityError("Invalid state parameter")
    """
    is_valid = secrets.compare_digest(state, expected_state)

    if not is_valid:
        logger.warning(
            "OAuth state verification failed",
            received_state=state[:10] + "..." if state else None,
            expected_state=expected_state[:10] + "...",
        )
    else:
        logger.debug("OAuth state verified successfully")

    return is_valid


def generate_state() -> str:
    """
    Generate a cryptographically secure random state parameter.

    State parameters are used in OAuth 2.0 to prevent CSRF attacks.
    This function generates a secure random string that should be stored
    and verified in the OAuth callback.

    Returns:
        A URL-safe random string suitable for use as OAuth state

    Example:
        >>> # Generate a state parameter
        >>> state = generate_state()
        >>> # Store it in session/database for later verification
        >>> session["oauth_state"] = state
        >>> # Generate auth URL with this state
        >>> auth_url = generate_auth_url(state=state)
    """
    state = secrets.token_urlsafe(32)
    logger.debug("Generated OAuth state parameter")
    return state
