"""
Rate Limit Middleware Module

This module provides middleware for automatic rate limiting of HTTP requests
to protect the API from abuse and DoS attacks. It implements tiered rate limiting
with different limits for different endpoint types.

Features:
- Extract client IP from request
- Categorize endpoints by path patterns (standard, expensive, upload)
- Apply appropriate rate limit per tier
- Add rate limit headers to response (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- Return 429 Too Many Requests with JSONResponse when limit exceeded
- Use i18n for error messages
- Bypass rate limiting for health/check endpoints

Tiered Limits:
- Standard endpoints: 60 requests/minute
- Expensive operations (analyze, ATS): 10 requests/minute
- File uploads: 5 requests/minute

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.rate_limit_middleware import RateLimitMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(RateLimitMiddleware)
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings
from utils.rate_limiter import RateLimiter
from i18n.backend_translations import get_error_message

logger = logging.getLogger(__name__)

# Rate limit header names
RATE_LIMIT_LIMIT_HEADER = "X-RateLimit-Limit"
RATE_LIMIT_REMAINING_HEADER = "X-RateLimit-Remaining"
RATE_LIMIT_RESET_HEADER = "X-RateLimit-Reset"
RATE_LIMIT_RETRY_AFTER_HEADER = "Retry-After"

# Endpoint categories
CATEGORY_STANDARD = "standard"
CATEGORY_EXPENSIVE = "expensive"
CATEGORY_UPLOAD = "upload"
CATEGORY_BYPASS = "bypass"

# Endpoint path patterns for categorization
UPLOAD_PATTERNS = ["/api/resumes/upload"]
EXPENSIVE_PATTERNS = ["/api/resumes/", "/api/ats/"]
BYPASS_PATTERNS = ["/health", "/api/health", "/readiness", "/api/readiness"]


def categorize_endpoint(path: str) -> str:
    """
    Categorize an endpoint path for rate limiting purposes.

    Determines which rate limit tier to apply based on the request path:
    - 'upload': File upload endpoints (5/min)
    - 'expensive': Computationally expensive operations (10/min)
    - 'standard': Regular endpoints (60/min)
    - 'bypass': Health check endpoints (no rate limiting)

    Args:
        path: The request path to categorize

    Returns:
        Category name: 'upload', 'expensive', 'standard', or 'bypass'

    Example:
        >>> categorize_endpoint('/api/resumes/upload')
        'upload'
        >>> categorize_endpoint('/api/resumes/123/analyze')
        'expensive'
        >>> categorize_endpoint('/api/candidates')
        'standard'
        >>> categorize_endpoint('/health')
        'bypass'
    """
    # Check for bypass endpoints first (health checks)
    for pattern in BYPASS_PATTERNS:
        if path.startswith(pattern):
            return CATEGORY_BYPASS

    # Check for upload endpoints
    for pattern in UPLOAD_PATTERNS:
        if path.startswith(pattern):
            return CATEGORY_UPLOAD

    # Check for expensive operations (analyze, ATS scoring, etc.)
    for pattern in EXPENSIVE_PATTERNS:
        if path.startswith(pattern):
            return CATEGORY_EXPENSIVE

    # Default to standard tier
    return CATEGORY_STANDARD


def get_rate_limit_for_category(category: str) -> int:
    """
    Get the rate limit for a specific endpoint category.

    Returns the configured rate limit (requests per minute) for the
    given category.

    Args:
        category: The endpoint category ('upload', 'expensive', 'standard', or 'bypass')

    Returns:
        Rate limit in requests per minute (or 0 for bypass category)

    Example:
        >>> get_rate_limit_for_category('upload')
        5
        >>> get_rate_limit_for_category('expensive')
        10
        >>> get_rate_limit_for_category('standard')
        60
        >>> get_rate_limit_for_category('bypass')
        0
    """
    settings = get_settings()

    if category == CATEGORY_UPLOAD:
        return settings.rate_limit_per_minute_upload
    elif category == CATEGORY_EXPENSIVE:
        return settings.rate_limit_per_minute_expensive
    elif category == CATEGORY_STANDARD:
        return settings.rate_limit_per_minute
    elif category == CATEGORY_BYPASS:
        return 0  # No rate limiting for bypass endpoints
    else:
        # Default to standard limit if category unknown
        logger.warning(f"Unknown category '{category}', defaulting to standard limit")
        return settings.rate_limit_per_minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on HTTP requests.

    This middleware implements tiered rate limiting to protect the API:
    1. Extracts client IP address from request
    2. Categorizes the endpoint by path pattern
    3. Checks rate limit for that IP and category
    4. Allows request if under limit, denies if exceeded
    5. Adds rate limit headers to all responses
    6. Returns 429 with retry-after header when limit exceeded

    Rate limiting is applied per IP address per endpoint category.

    Attributes:
        limiter: RateLimiter instance for checking limits
        enabled: Whether rate limiting is enabled

    Example:
        The middleware is automatically applied to all requests.
        Rate limit headers are added to responses:
        >>> response.headers["X-RateLimit-Limit"]
        '60'
        >>> response.headers["X-RateLimit-Remaining"]
        '59'
        >>> response.headers["X-RateLimit-Reset"]
        '1735862400'
    """

    def __init__(self, app):
        """
        Initialize the rate limit middleware.

        Args:
            app: The FastAPI application instance

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = RateLimitMiddleware(app)
            >>> app.add_middleware(RateLimitMiddleware)
        """
        super().__init__(app)
        settings = get_settings()
        self.enabled = settings.rate_limit_enabled

        # Initialize rate limiter with appropriate storage
        # Note: rate_limit_storage might be missing from config, default to 'memory'
        storage = getattr(settings, 'rate_limit_storage', 'memory')
        self.limiter = RateLimiter(storage=storage)

        logger.info(
            f"Rate limit middleware initialized (enabled={self.enabled}, storage={storage})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and enforce rate limiting.

        This method:
        1. Extracts client IP address
        2. Categorizes the endpoint
        3. Checks rate limit for that IP and category
        4. Allows request if under limit, returns 429 if exceeded
        5. Adds rate limit headers to response
        6. Processes the request if allowed

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from route handler with rate limit headers,
            or 429 response if rate limit exceeded

        Example:
            The middleware automatically processes all requests.
            Rate limit headers are added to responses.
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)

        # Extract client IP
        client_ip = self._get_client_ip(request)
        path = request.url.path

        # Categorize endpoint
        category = categorize_endpoint(path)

        # Bypass rate limiting for health checks
        if category == CATEGORY_BYPASS:
            logger.debug(f"Bypassing rate limit for health check: {path}")
            return await call_next(request)

        # Get rate limit for this category
        limit = get_rate_limit_for_category(category)
        window_seconds = 60  # 1 minute window

        # Create rate limit key: ip:category
        rate_limit_key = f"{client_ip}:{category}"

        # Check rate limit
        allowed, info = self.limiter.is_allowed(
            key=rate_limit_key,
            limit=limit,
            window=window_seconds,
        )

        logger.debug(
            f"Rate limit check: {request.method} {path} "
            f"[ip={client_ip}, category={category}, allowed={allowed}]"
        )

        if not allowed:
            # Rate limit exceeded - return 429
            retry_after = info.get('retry-after', window_seconds)

            logger.warning(
                f"Rate limit exceeded: {request.method} {path} "
                f"[ip={client_ip}, category={category}, retry_after={retry_after}s]"
            )

            # Get localized error message
            error_message = get_error_message(
                "rate_limit_exceeded",
                locale="en"  # TODO: Extract from Accept-Language header
            )

            # Add context about retry time
            error_message = f"{error_message}. Retry after {retry_after} seconds."

            return JSONResponse(
                status_code=429,
                content={
                    "detail": error_message,
                    "retry_after": retry_after,
                },
                headers={
                    RATE_LIMIT_RETRY_AFTER_HEADER: str(retry_after),
                    RATE_LIMIT_LIMIT_HEADER: str(limit),
                    RATE_LIMIT_RESET_HEADER: str(info.get('reset', 0)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        response.headers[RATE_LIMIT_LIMIT_HEADER] = str(limit)
        response.headers[RATE_LIMIT_REMAINING_HEADER] = str(info.get('remaining', 0))
        response.headers[RATE_LIMIT_RESET_HEADER] = str(info.get('reset', 0))

        logger.debug(
            f"Rate limit headers added: {request.method} {path} "
            f"[limit={limit}, remaining={info.get('remaining', 0)}]"
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Attempts to get the real client IP, checking for forwarded headers
        in case the request passes through a proxy or load balancer.

        Args:
            request: The FastAPI request object

        Returns:
            Client IP address as string

        Example:
            >>> ip = middleware._get_client_ip(request)
            >>> print(ip)
            '192.168.1.100'
        """
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection IP
        if request.client and request.client.host:
            return request.client.host

        # Default fallback
        return "unknown"


def get_rate_limit_status(request: Request) -> dict:
    """
    Helper function to get current rate limit status for a request.

    This is a convenience function to retrieve rate limit information
    for the current request. Useful for endpoints that want to return
    rate limit information in the response body.

    Args:
        request: The FastAPI request object

    Returns:
        Dictionary with rate limit status:
            - limit: Rate limit for this endpoint category
            - remaining: Remaining requests in current window
            - reset: Unix timestamp when window resets
            - category: Endpoint category

    Example:
        >>> from fastapi import Request
        >>> from middleware.rate_limit_middleware import get_rate_limit_status
        >>> @app.get("/api/rate-limit")
        >>> async def rate_limit_info(request: Request):
        ...     return get_rate_limit_status(request)
    """
    settings = get_settings()
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    path = request.url.path
    category = categorize_endpoint(path)
    limit = get_rate_limit_for_category(category)

    return {
        "limit": limit,
        "remaining": "N/A",  # Would need access to limiter to get actual value
        "reset": "N/A",  # Would need access to limiter to get actual value
        "category": category,
        "ip": client_ip,
    }
