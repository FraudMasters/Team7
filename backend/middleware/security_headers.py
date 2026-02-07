"""
Security Headers Middleware Module

This module provides middleware for automatic security header management
across HTTP responses. It adds OWASP-recommended security headers to
protect against common web vulnerabilities.

Features:
- Content-Security-Policy (CSP) to restrict resource sources
- Strict-Transport-Security (HSTS) to enforce HTTPS connections
- X-Frame-Options to prevent clickjacking attacks
- X-Content-Type-Options to prevent MIME-sniffing
- Referrer-Policy to control referrer information leakage
- Permissions-Policy to control browser features

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.security_headers import SecurityHeadersMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(SecurityHeadersMiddleware)
"""
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to HTTP responses.

    This middleware automatically adds OWASP-recommended security headers
    to all responses for defense-in-depth against common web attacks:

    1. Content-Security-Policy (CSP): Restricts sources of scripts, styles,
       images, etc. to prevent XSS attacks
    2. Strict-Transport-Security (HSTS): Forces browser to use HTTPS,
       preventing SSL stripping attacks
    3. X-Frame-Options: Prevents clickjacking by blocking framing
    4. X-Content-Type-Options: Prevents MIME-sniffing attacks
    5. Referrer-Policy: Controls referrer information in links
    6. Permissions-Policy: Restricts browser features and APIs

    These headers are required by security standards including SOC2,
    PCI-DSS, and are OWASP best practices.

    Attributes:
        hsts_enabled: Whether to enable HSTS header (HTTPS only)
        hsts_max_age: Max age in seconds for HSTS (default: 31536000 = 1 year)
        hsts_include_subdomains: Include subdomains in HSTS
        csp_enabled: Whether to enable CSP header
        csp_directives: Custom CSP directives string
        frame_options: X-Frame-Options value (DENY, SAMEORIGIN, or ALLOW-FROM)
        referrer_policy: Referrer-Policy value
        permissions_policy: Permissions-Policy value

    Example:
        The middleware is automatically applied to all responses.
        Default configuration provides strong security:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> app.add_middleware(SecurityHeadersMiddleware)

        Custom CSP configuration:
        >>> app.add_middleware(
        ...     SecurityHeadersMiddleware,
        ...     csp_directives="default-src 'self'; script-src 'self' https://cdn.example.com"
        ... )
    """

    def __init__(
        self,
        app,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        csp_enabled: bool = True,
        csp_directives: Optional[str] = None,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = "geolocation=(), microphone=(), camera=()",
    ):
        """
        Initialize the security headers middleware.

        Args:
            app: The FastAPI application instance
            hsts_enabled: Enable HSTS header (default: True, only applied to HTTPS)
            hsts_max_age: HSTS max-age in seconds (default: 31536000 = 1 year)
            hsts_include_subdomains: Include subdomains in HSTS (default: True)
            csp_enabled: Enable CSP header (default: True)
            csp_directives: Custom CSP directives (default: restrictive policy)
            frame_options: X-Frame-Options value (default: "DENY")
            referrer_policy: Referrer-Policy value (default: "strict-origin-when-cross-origin")
            permissions_policy: Permissions-Policy value (default: restrictive for geo/mic/cam)

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> # Use defaults (recommended)
            >>> app.add_middleware(SecurityHeadersMiddleware)
            >>>
            >>> # Or customize for specific needs
            >>> app.add_middleware(
            ...     SecurityHeadersMiddleware,
            ...     csp_directives="default-src 'self' https://cdn.trusted.com",
            ...     frame_options="SAMEORIGIN"
            ... )
        """
        super().__init__(app)

        # HSTS Configuration
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains

        # CSP Configuration
        self.csp_enabled = csp_enabled
        self.csp_directives = csp_directives or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # Other Security Headers
        self.frame_options = frame_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy

        logger.info(
            f"Security headers middleware initialized "
            f"(HSTS={hsts_enabled}, CSP={csp_enabled}, X-Frame-Options={frame_options})"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and add security headers to response.

        This method:
        1. Processes the request through the middleware chain
        2. Adds security headers to the response
        3. Logs the security headers being applied

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler with security headers

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        logger.debug(
            f"Request {request.method} {request.url.path} - "
            f"Applying security headers"
        )

        try:
            # Process request
            response = await call_next(request)

            # Add X-Content-Type-Options: prevents MIME-sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"

            # Add X-Frame-Options: prevents clickjacking
            response.headers["X-Frame-Options"] = self.frame_options

            # Add Referrer-Policy: controls referrer information
            response.headers["Referrer-Policy"] = self.referrer_policy

            # Add Permissions-Policy: restricts browser features
            response.headers["Permissions-Policy"] = self.permissions_policy

            # Add Content-Security-Policy: restricts resource sources
            if self.csp_enabled:
                response.headers["Content-Security-Policy"] = self.csp_directives

            # Add Strict-Transport-Security: enforce HTTPS (only on HTTPS requests)
            if self.hsts_enabled:
                # Only add HSTS header if the request is over HTTPS
                if request.url.scheme == "https":
                    hsts_value = f"max-age={self.hsts_max_age}"
                    if self.hsts_include_subdomains:
                        hsts_value += "; includeSubDomains"
                    response.headers["Strict-Transport-Security"] = hsts_value
                    logger.debug(
                        f"Added HSTS header to {request.method} {request.url.path}"
                    )
                else:
                    logger.debug(
                        f"Skipping HSTS for HTTP request {request.method} {request.url.path} "
                        "(HSTS only applies to HTTPS)"
                    )

            logger.debug(
                f"Response {request.method} {request.url.path} "
                f"[status={response.status_code}] - Security headers applied"
            )

            return response

        except Exception as e:
            # Log error with context
            logger.error(
                f"Request error: {request.method} {request.url.path} - {e}",
                exc_info=True,
            )
            raise
