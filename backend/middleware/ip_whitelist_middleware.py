"""
IP Whitelist Middleware Module

This module provides middleware for validating incoming requests against
organization IP whitelist configurations. It enforces IP-based access control
to protect sensitive resources.

Features:
- Validates client IP against organization IP whitelist
- Supports CIDR notation and IP range matching
- Per-organization and system-wide whitelist rules
- Configurable strict mode (block all when no whitelist configured)
- Integration with SecurityConfig for enable/disable
- Automatic logging of blocked access attempts

Example:
    >>> from fastapi import FastAPI
    >>> from middleware.ip_whitelist_middleware import IPWhitelistMiddleware
    >>> app = FastAPI()
    >>> app.add_middleware(IPWhitelistMiddleware)
"""
import logging
from typing import Callable, List, Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from database import async_session_maker
from models.ip_whitelist import IPWhitelist
from models.security_config import SecurityConfig

logger = logging.getLogger(__name__)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce IP whitelist restrictions for HTTP requests.

    This middleware validates incoming requests against configured IP whitelist rules:
    1. Checks if IP whitelist is enabled for the organization
    2. Retrieves active IP whitelist entries (organization-specific and system-wide)
    3. Validates client IP against whitelist rules (CIDR notation, IP ranges)
    4. Blocks access from unauthorized IPs with 403 Forbidden
    5. Logs all blocked access attempts for security monitoring

    Supports flexible IP matching:
    - CIDR notation (e.g., "192.168.1.0/24", "10.0.0.0/8")
    - Start/end IP ranges (supports both IPv4 and IPv6)
    - Organization-specific and system-wide rules

    Attributes:
        exclude_paths: List of path patterns to exclude from IP checking (e.g., health endpoints)

    Example:
        The middleware is automatically applied to all requests.
        Health endpoints are excluded by default to allow monitoring.
        >>> @app.get("/api/test")
        >>> async def test_endpoint(request: Request):
        ...     return {"message": "Access granted"}
    """

    # Paths excluded from IP whitelist checking
    EXCLUDE_PATHS = [
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    def __init__(self, app, exclude_paths: Optional[List[str]] = None):
        """
        Initialize the IP whitelist middleware.

        Args:
            app: The FastAPI application instance
            exclude_paths: List of path patterns to exclude from IP checking

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> middleware = IPWhitelistMiddleware(app, exclude_paths=["/health"])
            >>> app.add_middleware(IPWhitelistMiddleware)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or self.EXCLUDE_PATHS
        logger.info(
            f"IP whitelist middleware initialized with {len(self.exclude_paths)} excluded paths"
        )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and validate client IP against whitelist.

        This method:
        1. Checks if request path is excluded from IP checking
        2. Extracts client IP address from request
        3. Retrieves security config for IP whitelist settings
        4. Loads active IP whitelist entries
        5. Validates client IP against whitelist rules
        6. Blocks unauthorized access with 403 Forbidden
        7. Processes allowed requests normally

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler in the chain

        Returns:
            Response from the route handler or 403 Forbidden if IP blocked

        Example:
            The middleware automatically processes all requests.
            No manual intervention required.
        """
        # Check if path is excluded from IP whitelist checking
        if self._is_excluded_path(request.url.path):
            logger.debug(
                f"Path {request.url.path} is excluded from IP whitelist checking"
            )
            return await call_next(request)

        # Extract client IP address
        client_ip = self._get_client_ip(request)
        if not client_ip:
            logger.warning(
                f"Unable to extract client IP for {request.method} {request.url.path}, "
                "allowing request"
            )
            return await call_next(request)

        # Validate IP against whitelist
        is_allowed, reason = await self._validate_ip_against_whitelist(
            request, client_ip
        )

        if not is_allowed:
            # Log blocked access attempt
            logger.warning(
                f"IP blocked: {client_ip} - {request.method} {request.url.path} - {reason}"
            )

            # Return 403 Forbidden
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Access denied",
                    "detail": reason,
                    "type": "ip_not_allowed",
                },
            )

        # IP is allowed, process request normally
        logger.debug(
            f"IP allowed: {client_ip} - {request.method} {request.url.path}"
        )
        return await call_next(request)

    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if path should be excluded from IP whitelist checking.

        Args:
            path: Request path

        Returns:
            True if path is excluded, False otherwise

        Example:
            >>> middleware._is_excluded_path("/health")
            True
            >>> middleware._is_excluded_path("/api/resumes")
            False
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Checks multiple headers for the real client IP:
        - X-Forwarded-For (proxy/load balancer)
        - X-Real-IP (nginx)
        - CF-Connecting-IP (Cloudflare)
        - Falls back to request.client.host

        Args:
            request: The FastAPI request object

        Returns:
            Client IP address or None if not found

        Example:
            >>> client_ip = middleware._get_client_ip(request)
            >>> print(f"Client IP: {client_ip}")
        """
        # Check X-Forwarded-For header (from proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one (original client)
            ip = forwarded_for.split(",")[0].strip()
            if ip:
                return ip

        # Check X-Real-IP header (common with nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Check CF-Connecting-IP header (Cloudflare)
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip.strip()

        # Fall back to direct connection IP
        if request.client and request.client.host:
            return request.client.host

        return None

    async def _validate_ip_against_whitelist(
        self, request: Request, client_ip: str
    ) -> tuple[bool, str]:
        """
        Validate client IP against organization IP whitelist.

        Args:
            request: The FastAPI request object
            client_ip: Client IP address to validate

        Returns:
            Tuple of (is_allowed, reason)
            - is_allowed: True if IP is allowed, False otherwise
            - reason: Human-readable reason for allow/deny

        Example:
            >>> is_allowed, reason = await middleware._validate_ip_against_whitelist(
            ...     request, "192.168.1.100"
            ... )
            >>> print(f"Allowed: {is_allowed}, Reason: {reason}")
        """
        try:
            async with async_session_maker() as db:
                # Get security config (check system default and organization-specific)
                # For now, just check if IP whitelist is enabled at system level
                # TODO: Get organization_id from authenticated user context
                from sqlalchemy import select

                # Get system default security config
                config_result = await db.execute(
                    select(SecurityConfig).where(
                        SecurityConfig.organization_id.is_(None)
                    )
                )
                security_config = config_result.scalar_one_or_none()

                # If no config exists, allow all access (default open)
                if not security_config:
                    logger.debug("No security config found, allowing all IP access")
                    return True, "No security configuration"

                # Check if IP whitelist is enabled
                if not security_config.ip_whitelist_enabled:
                    logger.debug("IP whitelist is disabled, allowing all IP access")
                    return True, "IP whitelist disabled"

                # Get active IP whitelist entries
                whitelist_result = await db.execute(
                    select(IPWhitelist).where(
                        IPWhitelist.is_active == True,
                        IPWhitelist.organization_id.is_(None),  # System-wide rules
                    )
                )
                whitelist_entries = whitelist_result.scalars().all()

                # Check if any whitelist entries exist
                if not whitelist_entries:
                    if security_config.ip_whitelist_strict:
                        return (
                            False,
                            "No IP whitelist configured and strict mode is enabled",
                        )
                    else:
                        logger.debug(
                            "No whitelist entries but strict mode disabled, allowing access"
                        )
                        return True, "No whitelist configured, strict mode disabled"

                # Validate client IP against whitelist entries
                for entry in whitelist_entries:
                    if self._ip_matches_rule(client_ip, entry):
                        logger.debug(
                            f"IP {client_ip} matched whitelist rule: {entry.name}"
                        )
                        return True, f"Allowed by whitelist rule: {entry.name}"

                # IP didn't match any whitelist rules
                return (
                    False,
                    f"IP address {client_ip} is not in the allowed whitelist",
                )

        except Exception as e:
            # Log error but allow request (fail open for security config issues)
            logger.error(
                f"Error validating IP against whitelist: {e}",
                exc_info=True,
            )
            return True, f"Error during validation: {str(e)}"

    def _ip_matches_rule(self, client_ip: str, whitelist_entry: IPWhitelist) -> bool:
        """
        Check if client IP matches a whitelist rule.

        Supports:
        - CIDR notation (e.g., "192.168.1.0/24")
        - Start/end IP ranges

        Args:
            client_ip: Client IP address to check
            whitelist_entry: IP whitelist entry with matching rules

        Returns:
            True if IP matches the rule, False otherwise

        Example:
            >>> entry = IPWhitelist(cidr_notation="192.168.1.0/24", ...)
            >>> middleware._ip_matches_rule("192.168.1.100", entry)
            True
        """
        try:
            # Try CIDR notation matching
            if whitelist_entry.cidr_notation:
                if self._ip_in_cidr(client_ip, whitelist_entry.cidr_notation):
                    return True

            # Try IP range matching (start/end)
            if whitelist_entry.start_ip and whitelist_entry.end_ip:
                if self._ip_in_range(
                    client_ip, whitelist_entry.start_ip, whitelist_entry.end_ip
                ):
                    return True

            return False

        except Exception as e:
            logger.warning(
                f"Error matching IP {client_ip} against rule {whitelist_entry.name}: {e}"
            )
            return False

    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """
        Check if IP address is within a CIDR range.

        Args:
            ip: IP address to check
            cidr: CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            True if IP is in CIDR range, False otherwise

        Example:
            >>> middleware._ip_in_cidr("192.168.1.100", "192.168.1.0/24")
            True
            >>> middleware._ip_in_cidr("10.0.0.1", "192.168.1.0/24")
            False
        """
        try:
            import ipaddress

            client_ip_obj = ipaddress.ip_address(ip)
            network = ipaddress.ip_network(cidr, strict=False)

            return client_ip_obj in network

        except ValueError as e:
            logger.warning(f"Invalid IP or CIDR notation: {e}")
            return False

    def _ip_in_range(self, ip: str, start_ip: str, end_ip: str) -> bool:
        """
        Check if IP address is within a range (inclusive).

        Args:
            ip: IP address to check
            start_ip: Start of IP range
            end_ip: End of IP range

        Returns:
            True if IP is in range, False otherwise

        Example:
            >>> middleware._ip_in_range(
            ...     "192.168.1.100", "192.168.1.1", "192.168.1.255"
            ... )
            True
        """
        try:
            import ipaddress

            client_ip_obj = ipaddress.ip_address(ip)
            start_ip_obj = ipaddress.ip_address(start_ip)
            end_ip_obj = ipaddress.ip_address(end_ip)

            return start_ip_obj <= client_ip_obj <= end_ip_obj

        except ValueError as e:
            logger.warning(f"Invalid IP address in range: {e}")
            return False
