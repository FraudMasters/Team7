"""
Middleware modules for the backend API.

This package contains various middleware components used across
the backend application for request processing, monitoring,
and cross-cutting concerns.

Authentication middleware exports:
- get_current_user: Extract user from JWT access token
- get_current_active_user: Verify user is active
- get_current_verified_user: Verify user is active and email verified
- get_current_superuser: Verify user is admin/superuser
- require_role: Dependency factory for role-based access control
- require_admin: Convenience dependency for admin-only access
"""

from .auth import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_current_superuser,
    require_role,
    require_admin,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_current_superuser",
    "require_role",
    "require_admin",
]
