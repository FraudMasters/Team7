"""
OAuth 2.0 provider service for social authentication.

This module provides OAuth 2.0 authentication functionality for
social login integration with providers such as Google, LinkedIn, and GitHub.

The OAuth service supports:
- OAuth 2.0 authorization code flow
- Integration with major providers (Google, LinkedIn, GitHub)
- State parameter validation for CSRF protection
- PKCE (Proof Key for Code Exchange) support
- Token exchange and validation
- User profile fetching and attribute mapping
- Configurable scopes and redirect URIs
- Graceful error handling and security validation

OAuth Flow:
1. User initiates login -> Service generates authorization URL with state
2. User redirected to provider -> User authorizes application
3. Provider returns authorization code -> Service exchanges code for access token
4. Service fetches user profile -> User logged in with OAuth attributes

Reference: RFC 6749 - The OAuth 2.0 Authorization Framework
"""
import hashlib
import logging
import secrets
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Base exception for OAuth errors."""

    def __init__(self, message: str, error_code: Optional[str] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.response_data = response_data
        super().__init__(self.message)


class OAuthAuthorizationError(OAuthError):
    """Exception raised for authorization errors."""

    pass


class OAuthTokenError(OAuthError):
    """Exception raised for token exchange errors."""

    pass


class OAuthProfileError(OAuthError):
    """Exception raised for profile fetching errors."""

    pass


class OAuthStateError(OAuthError):
    """Exception raised for state validation errors."""

    pass


class BaseOAuthProvider(ABC):
    """
    Base class for OAuth 2.0 providers.

    This abstract class defines the interface for OAuth providers and
    provides common functionality for the OAuth authorization flow.

    Attributes:
        provider_name: Name of the OAuth provider
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: OAuth redirect URI
        scopes: List of OAuth scopes to request
        timeout: HTTP request timeout in seconds
    """

    # Provider-specific endpoints (must be overridden by subclasses)
    AUTHORIZATION_URL: str = ""
    TOKEN_URL: str = ""
    PROFILE_URL: str = ""

    # Default scopes (can be overridden by subclasses)
    DEFAULT_SCOPES: List[str] = []

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> None:
        """
        Initialize OAuth provider.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes: List of OAuth scopes to request (defaults to DEFAULT_SCOPES)
            timeout: HTTP request timeout in seconds

        Raises:
            ValueError: If required parameters are missing
        """
        if not client_id or not isinstance(client_id, str):
            raise ValueError("client_id must be a non-empty string")
        if not client_secret or not isinstance(client_secret, str):
            raise ValueError("client_secret must be a non-empty string")
        if not redirect_uri or not isinstance(redirect_uri, str):
            raise ValueError("redirect_uri must be a non-empty string")

        self.provider_name = self.__class__.__name__.replace("Provider", "")
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.timeout = timeout

        logger.info(
            f"{self.provider_name}Provider initialized (client_id={client_id[:8]}..., "
            f"scopes={','.join(self.scopes)})"
        )

    def generate_state(self) -> str:
        """
        Generate a secure random state parameter for CSRF protection.

        Returns:
            Random state string (32 bytes, hex-encoded)
        """
        return secrets.token_hex(32)

    def generate_pkce_pair(self) -> Dict[str, str]:
        """
        Generate PKCE code verifier and challenge for enhanced security.

        PKCE (Proof Key for Code Exchange) adds an extra layer of security
        to the authorization code flow by requiring a code challenge.

        Returns:
            Dictionary with 'code_verifier' and 'code_challenge' keys

        Reference: RFC 7636 - Proof Key for Code Exchange by OAuth Public Clients
        """
        # Generate code verifier (43-128 characters)
        code_verifier = secrets.token_urlsafe(32)

        # Generate code challenge (SHA256 hash of verifier, base64url-encoded)
        code_challenge = (
            hashlib.sha256(code_verifier.encode("ascii"))
            .digest()
            .hex()
        )

        return {
            "code_verifier": code_verifier,
            "code_challenge": code_challenge,
        }

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        use_pkce: bool = False,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL for user redirection.

        Args:
            state: Optional state parameter (generated if not provided)
            use_pkce: Whether to use PKCE for enhanced security
            extra_params: Additional query parameters for the authorization URL

        Returns:
            Dictionary with 'url', 'state', and optionally 'code_verifier' keys

        Example:
            >>> provider = GoogleProvider(client_id, client_secret, redirect_uri)
            >>> auth_data = provider.get_authorization_url()
            >>> # Redirect user to auth_data['url']
            >>> # Store auth_data['state'] in session for validation
        """
        if not state:
            state = self.generate_state()

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }

        result = {
            "url": f"{self.AUTHORIZATION_URL}?{urlencode(params)}",
            "state": state,
        }

        # Add PKCE if requested
        if use_pkce:
            pkce_pair = self.generate_pkce_pair()
            params["code_challenge"] = pkce_pair["code_challenge"]
            params["code_challenge_method"] = "S256"
            result["code_verifier"] = pkce_pair["code_verifier"]
            result["url"] = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

        # Add extra parameters
        if extra_params:
            params.update(extra_params)
            result["url"] = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

        logger.debug(
            f"Generated {self.provider_name} authorization URL with state={state[:8]}..."
        )

        return result

    def validate_state(self, received_state: str, expected_state: str) -> None:
        """
        Validate state parameter to prevent CSRF attacks.

        Args:
            received_state: State parameter received from OAuth callback
            expected_state: Expected state parameter from session

        Raises:
            OAuthStateError: If state validation fails
        """
        if not received_state or not expected_state:
            raise OAuthStateError("Missing state parameter")

        if received_state != expected_state:
            logger.warning(
                f"OAuth state mismatch: received={received_state[:8]}..., "
                f"expected={expected_state[:8]}..."
            )
            raise OAuthStateError("State parameter mismatch (possible CSRF attack)")

        logger.debug("OAuth state validation successful")

    def exchange_code_for_token(
        self,
        code: str,
        code_verifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            code_verifier: Optional PKCE code verifier

        Returns:
            Dictionary with token response (access_token, token_type, expires_in, etc.)

        Raises:
            OAuthTokenError: If token exchange fails
        """
        if not code:
            raise OAuthTokenError("Missing authorization code")

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        # Add PKCE code verifier if provided
        if code_verifier:
            data["code_verifier"] = code_verifier

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.TOKEN_URL,
                    data=data,
                    headers={"Accept": "application/json"},
                )

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    error_code = error_data.get("error", "unknown_error")
                    error_description = error_data.get(
                        "error_description", "Token exchange failed"
                    )
                    logger.error(
                        f"{self.provider_name} token exchange failed: "
                        f"{error_code} - {error_description}"
                    )
                    raise OAuthTokenError(
                        error_description,
                        error_code=error_code,
                        response_data=error_data,
                    )

                token_data = response.json()
                logger.info(
                    f"{self.provider_name} token exchange successful "
                    f"(expires_in={token_data.get('expires_in', 'N/A')})"
                )
                return token_data

        except httpx.RequestError as e:
            logger.error(f"{self.provider_name} token exchange request failed: {e}")
            raise OAuthTokenError(f"Token exchange request failed: {e}")

    @abstractmethod
    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from OAuth provider.

        This method must be implemented by subclasses to handle
        provider-specific profile API endpoints and response formats.

        Args:
            access_token: OAuth access token

        Returns:
            Dictionary with user profile data (normalized format)

        Raises:
            OAuthProfileError: If profile fetching fails
        """
        pass

    def _fetch_profile(self, access_token: str, url: str) -> Dict[str, Any]:
        """
        Helper method to fetch profile data from provider API.

        Args:
            access_token: OAuth access token
            url: Profile API endpoint URL

        Returns:
            Raw profile data from provider

        Raises:
            OAuthProfileError: If profile fetch fails
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                )

                if response.status_code != 200:
                    error_data = response.json() if response.text else {}
                    logger.error(
                        f"{self.provider_name} profile fetch failed: "
                        f"status={response.status_code}"
                    )
                    raise OAuthProfileError(
                        f"Profile fetch failed with status {response.status_code}",
                        response_data=error_data,
                    )

                profile_data = response.json()
                logger.info(f"{self.provider_name} profile fetch successful")
                return profile_data

        except httpx.RequestError as e:
            logger.error(f"{self.provider_name} profile fetch request failed: {e}")
            raise OAuthProfileError(f"Profile fetch request failed: {e}")


class GoogleProvider(BaseOAuthProvider):
    """
    Google OAuth 2.0 provider.

    Supports Google Sign-In for authentication and profile data fetching.

    Default scopes:
    - openid: OpenID Connect authentication
    - email: Access to user's email address
    - profile: Access to user's basic profile info

    Reference: https://developers.google.com/identity/protocols/oauth2
    """

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    PROFILE_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

    DEFAULT_SCOPES = [
        "openid",
        "email",
        "profile",
    ]

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from Google.

        Args:
            access_token: OAuth access token

        Returns:
            Normalized user profile with keys:
            - id: Unique user ID
            - email: User email address
            - name: Full name
            - first_name: First name
            - last_name: Last name
            - picture: Profile picture URL
            - email_verified: Whether email is verified

        Raises:
            OAuthProfileError: If profile fetching fails
        """
        raw_profile = self._fetch_profile(access_token, self.PROFILE_URL)

        # Normalize profile data to common format
        return {
            "id": raw_profile.get("id"),
            "email": raw_profile.get("email"),
            "name": raw_profile.get("name"),
            "first_name": raw_profile.get("given_name"),
            "last_name": raw_profile.get("family_name"),
            "picture": raw_profile.get("picture"),
            "email_verified": raw_profile.get("verified_email", False),
            "provider": "google",
            "raw": raw_profile,
        }


class LinkedInProvider(BaseOAuthProvider):
    """
    LinkedIn OAuth 2.0 provider.

    Supports LinkedIn Sign-In for authentication and profile data fetching.

    Default scopes:
    - r_liteprofile: Access to user's basic profile
    - r_emailaddress: Access to user's email address

    Note: LinkedIn deprecated v1 API. This uses v2 API endpoints.

    Reference: https://docs.microsoft.com/en-us/linkedin/shared/authentication/authentication
    """

    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    PROFILE_URL = "https://api.linkedin.com/v2/me"
    EMAIL_URL = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"

    DEFAULT_SCOPES = [
        "r_liteprofile",
        "r_emailaddress",
    ]

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from LinkedIn.

        LinkedIn requires separate API calls for profile and email.

        Args:
            access_token: OAuth access token

        Returns:
            Normalized user profile with keys:
            - id: Unique user ID
            - email: User email address
            - name: Full name
            - first_name: First name (localized)
            - last_name: Last name (localized)
            - picture: Profile picture URL

        Raises:
            OAuthProfileError: If profile fetching fails
        """
        # Fetch basic profile
        raw_profile = self._fetch_profile(access_token, self.PROFILE_URL)

        # Fetch email (separate endpoint)
        email_data = self._fetch_profile(access_token, self.EMAIL_URL)

        # Extract email from response
        email = None
        if "elements" in email_data and len(email_data["elements"]) > 0:
            email_element = email_data["elements"][0]
            if "handle~" in email_element:
                email = email_element["handle~"].get("emailAddress")

        # Extract localized name (prefer English, fallback to first available)
        first_name = None
        last_name = None

        if "firstName" in raw_profile and "localized" in raw_profile["firstName"]:
            first_name_data = raw_profile["firstName"]["localized"]
            first_name = first_name_data.get("en_US") or next(iter(first_name_data.values()), None)

        if "lastName" in raw_profile and "localized" in raw_profile["lastName"]:
            last_name_data = raw_profile["lastName"]["localized"]
            last_name = last_name_data.get("en_US") or next(iter(last_name_data.values()), None)

        # Construct full name
        name_parts = [p for p in [first_name, last_name] if p]
        name = " ".join(name_parts) if name_parts else None

        # Extract profile picture
        picture = None
        if "profilePicture" in raw_profile:
            display_image = raw_profile["profilePicture"].get("displayImage~")
            if display_image and "elements" in display_image and display_image["elements"]:
                # Get largest image
                images = display_image["elements"]
                largest = max(images, key=lambda x: x.get("data", {}).get("com.linkedin.digitalmedia.mediaartifact.StillImage", {}).get("storageSize", 0))
                picture = largest.get("identifiers", [{}])[0].get("identifier")

        # Normalize profile data to common format
        return {
            "id": raw_profile.get("id"),
            "email": email,
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "picture": picture,
            "email_verified": True if email else False,
            "provider": "linkedin",
            "raw": raw_profile,
        }


class GitHubProvider(BaseOAuthProvider):
    """
    GitHub OAuth 2.0 provider.

    Supports GitHub Sign-In for authentication and profile data fetching.

    Default scopes:
    - user:email: Access to user's email addresses

    Note: GitHub returns basic profile info without any scope, but
    email access requires the user:email scope.

    Reference: https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps
    """

    AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    PROFILE_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    DEFAULT_SCOPES = [
        "user:email",
    ]

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from GitHub.

        GitHub requires separate API calls for profile and verified email.

        Args:
            access_token: OAuth access token

        Returns:
            Normalized user profile with keys:
            - id: Unique user ID
            - email: Primary verified email address
            - name: Full name
            - first_name: First name (parsed from full name)
            - last_name: Last name (parsed from full name)
            - picture: Profile picture URL (avatar)
            - username: GitHub username
            - email_verified: Whether email is verified

        Raises:
            OAuthProfileError: If profile fetching fails
        """
        # Fetch basic profile
        raw_profile = self._fetch_profile(access_token, self.PROFILE_URL)

        # Fetch emails to get verified primary email
        email = raw_profile.get("email")
        email_verified = False

        try:
            emails_data = self._fetch_profile(access_token, self.EMAILS_URL)
            # Find primary verified email
            for email_obj in emails_data:
                if email_obj.get("primary") and email_obj.get("verified"):
                    email = email_obj.get("email")
                    email_verified = True
                    break
            # Fallback to first verified email if no primary
            if not email_verified:
                for email_obj in emails_data:
                    if email_obj.get("verified"):
                        email = email_obj.get("email")
                        email_verified = True
                        break
        except OAuthProfileError:
            logger.warning("Failed to fetch GitHub email addresses")

        # Parse name into first/last name
        name = raw_profile.get("name")
        first_name = None
        last_name = None

        if name:
            name_parts = name.split(maxsplit=1)
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name = name_parts[1] if len(name_parts) > 1 else None

        # Normalize profile data to common format
        return {
            "id": str(raw_profile.get("id")),
            "email": email,
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "picture": raw_profile.get("avatar_url"),
            "username": raw_profile.get("login"),
            "email_verified": email_verified,
            "provider": "github",
            "raw": raw_profile,
        }


class OAuthService:
    """
    OAuth 2.0 service for managing multiple providers.

    This service provides a unified interface for OAuth authentication
    across multiple providers (Google, LinkedIn, GitHub).

    Attributes:
        providers: Dictionary of initialized OAuth providers by name

    Example:
        >>> oauth = OAuthService()
        >>> # Initialize Google provider
        >>> oauth.add_provider('google', GoogleProvider(
        ...     client_id='...', client_secret='...', redirect_uri='...'
        ... ))
        >>> # Start OAuth flow
        >>> auth_data = oauth.get_authorization_url('google')
        >>> # Exchange code for token
        >>> token = oauth.exchange_code('google', code, state, auth_data['state'])
        >>> # Get user profile
        >>> profile = oauth.get_user_profile('google', token['access_token'])
    """

    def __init__(self) -> None:
        """Initialize OAuth service with empty provider registry."""
        self.providers: Dict[str, BaseOAuthProvider] = {}
        logger.info("OAuthService initialized")

    def add_provider(self, name: str, provider: BaseOAuthProvider) -> None:
        """
        Register an OAuth provider.

        Args:
            name: Provider name (e.g., 'google', 'linkedin', 'github')
            provider: Initialized OAuth provider instance

        Raises:
            ValueError: If provider is not a BaseOAuthProvider instance
        """
        if not isinstance(provider, BaseOAuthProvider):
            raise ValueError("Provider must be an instance of BaseOAuthProvider")

        self.providers[name.lower()] = provider
        logger.info(f"Registered OAuth provider: {name}")

    def get_provider(self, name: str) -> BaseOAuthProvider:
        """
        Get OAuth provider by name.

        Args:
            name: Provider name (e.g., 'google', 'linkedin', 'github')

        Returns:
            OAuth provider instance

        Raises:
            ValueError: If provider is not registered
        """
        provider = self.providers.get(name.lower())
        if not provider:
            raise ValueError(
                f"OAuth provider '{name}' not registered. "
                f"Available providers: {', '.join(self.providers.keys())}"
            )
        return provider

    def get_authorization_url(
        self,
        provider_name: str,
        state: Optional[str] = None,
        use_pkce: bool = False,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL for a provider.

        Args:
            provider_name: Provider name (e.g., 'google', 'linkedin', 'github')
            state: Optional state parameter (generated if not provided)
            use_pkce: Whether to use PKCE for enhanced security
            extra_params: Additional query parameters

        Returns:
            Dictionary with 'url', 'state', and optionally 'code_verifier'

        Raises:
            ValueError: If provider is not registered
        """
        provider = self.get_provider(provider_name)
        return provider.get_authorization_url(state, use_pkce, extra_params)

    def exchange_code(
        self,
        provider_name: str,
        code: str,
        received_state: str,
        expected_state: str,
        code_verifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token with state validation.

        Args:
            provider_name: Provider name (e.g., 'google', 'linkedin', 'github')
            code: Authorization code from OAuth callback
            received_state: State parameter received from OAuth callback
            expected_state: Expected state parameter from session
            code_verifier: Optional PKCE code verifier

        Returns:
            Token response dictionary

        Raises:
            ValueError: If provider is not registered
            OAuthStateError: If state validation fails
            OAuthTokenError: If token exchange fails
        """
        provider = self.get_provider(provider_name)
        provider.validate_state(received_state, expected_state)
        return provider.exchange_code_for_token(code, code_verifier)

    def get_user_profile(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """
        Fetch user profile from OAuth provider.

        Args:
            provider_name: Provider name (e.g., 'google', 'linkedin', 'github')
            access_token: OAuth access token

        Returns:
            Normalized user profile dictionary

        Raises:
            ValueError: If provider is not registered
            OAuthProfileError: If profile fetching fails
        """
        provider = self.get_provider(provider_name)
        return provider.get_user_profile(access_token)


# Global OAuth service instance
_oauth_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
    """
    Get or create global OAuth service instance.

    Returns:
        Global OAuthService instance

    Example:
        >>> oauth = get_oauth_service()
        >>> oauth.add_provider('google', GoogleProvider(...))
    """
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService()
    return _oauth_service
