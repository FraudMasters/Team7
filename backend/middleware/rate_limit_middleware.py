"""
Rate Limit Middleware Module

This module provides middleware for automatic rate limiting of HTTP requests.
It uses a Redis-backed token bucket algorithm to enforce rate limits and adds
rate limit information to response headers.

Features:
- Token bucket algorithm for smooth rate limiting
- IP-based rate limiting (by default)
- Support for different rate limit tiers (anonymous, user, org_admin, admin)
- Automatic rate limit headers in responses (X-RateLimit-*)
- IP-based blocking for DDoS protection
- Graceful fallback when Redis is unavailable

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.rate_limit_middleware import RateLimitMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(RateLimitMiddleware)
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from services.rate_limit_service import (
    RateLimitService,
    RateLimitTier,
    get_rate_limit_service,
)

logger = logging.getLogger(__name__)

# Rate limit response headers
HEADER_LIMIT = "X-RateLimit-Limit"
HEADER_REMAINING = "X-RateLimit-Remaining"
HEADER_RESET = "X-RateLimit-Reset"
HEADER_RETRY_AFTER = "Retry-After"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting for HTTP requests.

    This middleware automatically applies rate limiting to all requests:
    1. Extracts client IP address from request
    2. Checks if IP is blocked (DDoS protection)
    3. Checks rate limit using token bucket algorithm
    4. Adds rate limit headers to response
    5. Returns 429 Too Many Requests if limit exceeded

    The middleware supports different rate limit tiers based on user roles:
    - ANONYMOUS: 20 requests/minute (default for unauthenticated users)
    - USER: 100 requests/minute
    - ORG_ADMIN: 300 requests/minute
    - ADMIN: 1000 requests/minute

    This protects the API from abuse while ensuring fair resource allocation.

    Attributes:
        rate_limit_service: The RateLimitService instance for checking limits
        default_tier: Default rate limit tier to apply

    Example:
        The middleware is automatically applied to all requests.
        Rate limit headers are added to responses:
        >>> X-RateLimit-Limit: 100
        >>> X-RateLimit-Remaining: 95
        >>> X-RateLimit-Reset: 1738569600

        When rate limited:
        >>> HTTP/1.1 429 Too Many Requests
        >>> Retry-After: 60
        >>> X-RateLimit-Limit: 100
        >>> X-RateLimit-Remaining: 0
        >>> X-RateLimit-Reset: 1738569600
    """

    def __init__(
        self,
        app,
        rate_limit_service: Optional[RateLimitService] = None,
        default_tier: RateLimitTier = RateLimitTier.ANONYMOUS,
        enabled: bool = True,
    ):
        """
        Initialize the rate limit middleware.

        Args:
            app: The FastAPI application instance
            rate_limit_service: RateLimitService instance (defaults to global instance)
            default_tier: Default rate limit tier (default: ANONYMOUS)
            enabled: Whether rate limiting is enabled (default: True)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = RateLimitMiddleware(app)
            >>> app.add_middleware(RateLimitMiddleware)
        """
        super().__init__(app)
        self.rate_limit_service = rate_limit_service or get_rate_limit_service()
        self.default_tier = default_tier
        self.enabled = enabled and self.rate_limit_service.enabled

        logger.info(
            f"Rate limit middleware initialized (enabled={self.enabled}, "
            f"default_tier={default_tier.value})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and enforce rate limiting.

        This method:
        1. Extracts client IP address
            2. Checks if IP is blocked
            3. Determines rate limit tier based on user role
            4. Checks rate limit for the request
            5. Adds rate limit headers to response
            6. Returns 429 if rate limit exceeded

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler with rate limit headers,
            or 429 Too Many Requests if rate limit exceeded

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Extract client IP address early for logging
        client_ip = self._get_client_ip(request)

        # If rate limiting is disabled, pass through with default headers
        if not self.enabled:
            response = await call_next(request)
            self._add_default_rate_limit_headers(response)
            return response

        # Check if IP is blocked (DDoS protection)
        if self.rate_limit_service.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted request: {client_ip}")
            return self._create_blocked_response(client_ip)

        # Determine rate limit tier based on user role
        tier = self._get_rate_limit_tier(request)

        # Determine identifier for rate limiting
        # Use user ID if authenticated, otherwise IP address
        identifier = self._get_rate_limit_identifier(request, client_ip)

        logger.debug(
            f"Rate limit check: {request.method} {request.url.path} "
            f"[ip={client_ip}, tier={tier.value}, identifier={identifier}]"
        )

        try:
            # Check rate limit
            result = self.rate_limit_service.check_rate_limit(
                namespace="user" if tier != RateLimitTier.ANONYMOUS else "ip",
                identifier=identifier,
                tier=tier,
            )

            # If rate limit exceeded, return 429
            if not result.allowed:
                logger.warning(
                    f"Rate limit exceeded: {request.method} {request.url.path} "
                    f"[ip={client_ip}, tier={tier.value}, retry_after={result.retry_after}]"
                )
                return self._create_rate_limit_response(result)

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            self._add_rate_limit_headers(response, result)

            logger.debug(
                f"Request allowed: {request.method} {request.url.path} "
                f"[status={response.status_code}, remaining={result.remaining}]"
            )

            return response

        except Exception as e:
            # Log error but allow request (fail open)
            logger.error(
                f"Rate limit check error: {request.method} {request.url.path} "
                f"[ip={client_ip}] - {e}",
                exc_info=True,
            )
            # Allow request to proceed if rate limiting fails
            # Add default headers to indicate rate limit status is unknown
            response = await call_next(request)
            self._add_default_rate_limit_headers(response)
            return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Checks multiple headers for the real IP address, accounting for
        proxies and load balancers.

        Args:
            request: The FastAPI request object

        Returns:
            Client IP address as string

        Example:
            >>> ip = middleware._get_client_ip(request)
            >>> print(ip)
            '192.168.1.1'
        """
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        # Default if no IP found
        return "unknown"

    def _get_rate_limit_tier(self, request: Request) -> RateLimitTier:
        """
        Determine rate limit tier based on user role.

        Checks if user is authenticated and determines their role
        to apply the appropriate rate limit tier.

        Args:
            request: The FastAPI request object

        Returns:
            RateLimitTier based on user role

        Example:
            >>> tier = middleware._get_rate_limit_tier(request)
            >>> print(tier)
            <RateLimitTier.USER: 'user'>
        """
        # Check if user is authenticated and has role info
        # This will be populated by authentication middleware when added
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user

            # Check for admin role
            if hasattr(user, "role"):
                role = user.role
                if role == "admin":
                    return RateLimitTier.ADMIN
                elif role == "org_admin":
                    return RateLimitTier.ORG_ADMIN
                else:
                    return RateLimitTier.USER

            # If user object exists but no role field, assume regular user
            return RateLimitTier.USER

        # Default to anonymous tier
        return self.default_tier

    def _get_rate_limit_identifier(self, request: Request, client_ip: str) -> str:
        """
        Get identifier for rate limiting.

        Uses user ID if authenticated, otherwise IP address.
        This ensures rate limits are applied per user or per IP.

        Args:
            request: The FastAPI request object
            client_ip: Client IP address

        Returns:
            Identifier string for rate limiting

        Example:
            >>> identifier = middleware._get_rate_limit_identifier(request, "192.168.1.1")
            >>> print(identifier)
            'user_123'
        """
        # Check if user is authenticated
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user

            # Use user ID if available
            if hasattr(user, "id"):
                return f"user_{user.id}"

            # Use username if ID not available
            if hasattr(user, "username"):
                return f"user_{user.username}"

        # Fall back to IP address
        return client_ip

    def _add_rate_limit_headers(
        self, response: Response, result
    ) -> None:
        """
        Add rate limit headers to response.

        Adds standard rate limit headers to inform clients of their
        current rate limit status.

        Args:
            response: The HTTP response object
            result: RateLimitResult from rate limit check

        Example:
            >>> middleware._add_rate_limit_headers(response, result)
            >>> # Headers added: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        """
        response.headers[HEADER_LIMIT] = str(result.limit)
        response.headers[HEADER_REMAINING] = str(result.remaining)
        response.headers[HEADER_RESET] = str(result.reset_at)

    def _add_default_rate_limit_headers(
        self, response: Response
    ) -> None:
        """
        Add default rate limit headers to response.

        Adds default headers when rate limiting is disabled or unavailable.
        This ensures all responses have consistent rate limit headers.

        Args:
            response: The HTTP response object

        Example:
            >>> middleware._add_default_rate_limit_headers(response)
            >>> # Headers added: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        """
        # Use a high limit value to indicate unrestricted access
        response.headers[HEADER_LIMIT] = "-1"
        response.headers[HEADER_REMAINING] = "-1"
        response.headers[HEADER_RESET] = "0"

    def _create_rate_limit_response(self, result) -> Response:
        """
        Create a 429 Too Many Requests response.

        Creates a standardized response when rate limit is exceeded,
        including retry information.

        Args:
            result: RateLimitResult from rate limit check

        Returns:
            JSONResponse with 429 status code and retry information

        Example:
            >>> response = middleware._create_rate_limit_response(result)
            >>> # Returns: HTTP/1.1 429 Too Many Requests
        """
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please slow down.",
                "retry_after": result.retry_after,
                "limit": result.limit,
                "tier": result.tier.value,
            },
            headers={
                HEADER_LIMIT: str(result.limit),
                HEADER_REMAINING: "0",
                HEADER_RESET: str(result.reset_at),
                HEADER_RETRY_AFTER: str(result.retry_after),
            },
        )

    def _create_blocked_response(self, client_ip: str) -> Response:
        """
        Create a 403 Forbidden response for blocked IPs.

        Creates a response when an IP is blocked due to abusive behavior.

        Args:
            client_ip: The blocked client IP address

        Returns:
            JSONResponse with 403 status code

        Example:
            >>> response = middleware._create_blocked_response("192.168.1.1")
            >>> # Returns: HTTP/1.1 403 Forbidden
        """
        from fastapi.responses import JSONResponse

        response = JSONResponse(
            status_code=403,
            content={
                "error": "Access denied",
                "message": "Your IP address has been blocked due to abusive behavior.",
            },
        )

        # Add rate limit headers to indicate blocked status
        self._add_default_rate_limit_headers(response)

        return response
