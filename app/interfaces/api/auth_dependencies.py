"""
Authentication dependencies for FastAPI routes.

This module provides dependency functions for authentication and authorization
in FastAPI routes, including JWT validation and role-based access control.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.application.auth_service import AuthService
from app.infrastructure.auth.keycloak_adapter import (
    KeycloakAuthenticationError,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_auth_service() -> Optional[AuthService]:
    """Get authentication service instance."""
    from app.main import auth_service
    from config.settings import get_settings

    settings = get_settings()

    # In development mode, return None if auth service failed to initialize
    if settings.is_development:
        return auth_service

    # In production, require auth service
    if auth_service is None:
        raise RuntimeError("Authentication service not available")

    return auth_service


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: Optional[AuthService] = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.

    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials
        auth_service: Authentication service

    Returns:
        User claims dictionary

    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials

        # Handle development mode with test authentication
        if auth_service is None:
            from config.settings import get_settings

            settings = get_settings()

            if settings.is_development:
                # Use test authentication for development
                if token == "dev_test_token":
                    user_claims = {
                        "sub": "dev-user-id",
                        "email": "dev@example.com",
                        "name": "Development User",
                        "roles": ["user", "api"],
                        "active": True,
                        "iat": 1634567890,
                        "exp": 1734567890,
                    }
                    request.state.user = user_claims
                    return user_claims
                else:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid development token. Use 'dev_test_token'",
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service unavailable",
                )

        user_claims = await auth_service.validate_token(token)

        # Add user info to request state for middleware access
        request.state.user = user_claims

        return user_claims

    except KeycloakAuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current active user.

    Args:
        current_user: Current user claims

    Returns:
        User claims dictionary

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """
    Dependency to check if user has required role.

    Args:
        required_role: Role name required for access

    Returns:
        Dependency function that validates user role
    """

    async def role_dependency(
        current_user: Dict[str, Any] = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])

        if required_role not in user_roles:
            logger.warning(
                f"Access denied for user {current_user.get('sub')}. "
                f"Required role: {required_role}, User roles: {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        logger.debug(
            f"Access granted for user {current_user.get('sub')} with role {required_role}"
        )
        return current_user

    return role_dependency


def require_any_role(required_roles: List[str]):
    """
    Dependency to check if user has any of the required roles.

    Args:
        required_roles: List of role names, any of which grants access

    Returns:
        Dependency function that validates user roles
    """

    async def roles_dependency(
        current_user: Dict[str, Any] = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])

        # Check if user has any of the required roles
        has_required_role = any(role in user_roles for role in required_roles)

        if not has_required_role:
            logger.warning(
                f"Access denied for user {current_user.get('sub')}. "
                f"Required any of: {required_roles}, User roles: {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required one of: {', '.join(required_roles)}",
            )

        logger.debug(
            f"Access granted for user {current_user.get('sub')} with roles {user_roles}"
        )
        return current_user

    return roles_dependency


def require_permission(required_permission: str):
    """
    Dependency to check if user has required permission.

    Args:
        required_permission: Permission string required for access

    Returns:
        Dependency function that validates user permission
    """

    async def permission_dependency(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_active_user),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> Dict[str, Any]:
        token = request.headers.get("authorization", "").replace("Bearer ", "")

        has_permission = await auth_service.check_permission(
            token, required_permission
        )

        if not has_permission:
            logger.warning(
                f"Access denied for user {current_user.get('sub')}. "
                f"Required permission: {required_permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required permission: {required_permission}",
            )

        logger.debug(
            f"Permission granted for user {current_user.get('sub')}: {required_permission}"
        )
        return current_user

    return permission_dependency


async def optional_auth(
    request: Request,
    auth_service: Optional[AuthService] = Depends(get_auth_service),
) -> Optional[Dict[str, Any]]:
    """
    Optional authentication dependency.

    Returns user claims if token is provided and valid,
    otherwise returns None.

    Args:
        request: FastAPI request object
        auth_service: Authentication service

    Returns:
        User claims dictionary if authenticated, None otherwise
    """
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header[7:]  # Remove "Bearer " prefix

        # Handle development mode with test authentication
        if auth_service is None:
            from config.settings import get_settings

            settings = get_settings()

            if settings.is_development:
                # Use test authentication for development
                if token == "dev_test_token":
                    user_claims = {
                        "sub": "dev-user-id",
                        "email": "dev@example.com",
                        "name": "Development User",
                        "roles": ["user", "api"],
                        "active": True,
                        "iat": 1634567890,
                        "exp": 1734567890,
                    }
                    request.state.user = user_claims
                    return user_claims
                else:
                    # Invalid token in development, return None for optional auth
                    logger.debug(
                        "Invalid development token provided for optional authentication"
                    )
                    return None
            else:
                # Production mode without auth service
                logger.debug(
                    "Authentication service unavailable for optional authentication"
                )
                return None

        user_claims = await auth_service.validate_token(token)
        request.state.user = user_claims
        return user_claims

    except KeycloakAuthenticationError:
        logger.debug("Invalid token provided for optional authentication")
        return None


async def rate_limit_dependency(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth),
):
    """
    Rate limiting dependency.

    Applies rate limiting based on user ID or IP address.

    Args:
        request: FastAPI request object
        auth_service: Authentication service
        current_user: Current user if authenticated

    Raises:
        HTTPException: If rate limit exceeded
    """
    try:
        # Get identifier for rate limiting
        if current_user:
            identifier = current_user.get("sub", "anonymous")
        else:
            identifier = request.client.host if request.client else "anonymous"

        # Check rate limit (100 requests per hour)
        is_limited = (
            await auth_service.cache_manager.rate_limiter.check_rate_limit(
                identifier, 100, 3600
            )
        )

        if is_limited["is_limited"]:
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

    except Exception as e:
        logger.error(f"Rate limiting error: {e}")
        # Don't fail the request if rate limiting fails
        pass


# Common role dependencies
require_system_role = require_role("system")
require_super_admin_role = require_role("super_admin")
require_admin_role = require_role("admin")
require_user_role = require_role("user")
require_api_role = require_role("api")

# Common role combinations
require_admin_or_higher = require_any_role(["admin", "super_admin", "system"])
require_user_or_higher = require_any_role(
    ["user", "admin", "super_admin", "system"]
)
require_api_or_higher = require_any_role(
    ["api", "user", "admin", "super_admin", "system"]
)

# Common permission dependencies
require_read_permission = require_permission("read")
require_write_permission = require_permission("write")
require_delete_permission = require_permission("delete")
require_manage_users_permission = require_permission("manage_users")
