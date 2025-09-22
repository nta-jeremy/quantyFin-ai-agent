"""
Test authentication utilities for development and testing.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_test_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    Get current test user for development/testing.

    This bypasses Keycloak authentication and returns a test user.
    """
    # For testing, accept any token or use default test token
    if credentials:
        token = credentials.credentials
        logger.debug(
            f"Using provided token for test authentication: {token[:10]}..."
        )
    else:
        logger.debug("No token provided, using default test user")

    # Return a test user with appropriate roles
    test_user = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user", "api"],  # Has API access role
        "active": True,
        "iat": 1634567890,
        "exp": 1734567890,
    }

    # Add user info to request state
    request.state.user = test_user

    return test_user


async def get_current_active_test_user(
    current_user: Dict[str, Any] = Depends(get_current_test_user),
) -> Dict[str, Any]:
    """
    Get current active test user.
    """
    if not current_user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def require_test_role(required_role: str):
    """
    Test dependency to check if user has required role.
    """

    async def role_dependency(
        current_user: Dict[str, Any] = Depends(get_current_active_test_user),
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])

        if required_role not in user_roles:
            logger.warning(
                f"Access denied for test user {current_user.get('sub')}. "
                f"Required role: {required_role}, User roles: {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return current_user

    return role_dependency


async def test_rate_limit_dependency(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_test_user),
):
    """
    Test rate limiting dependency - disabled for testing.
    """
    # In testing, we don't enforce rate limits
    pass


# Test authentication dependencies
get_current_user = get_current_test_user
get_current_active_user = get_current_active_test_user
rate_limit_dependency = test_rate_limit_dependency

# Test role dependencies
require_user_role = require_test_role("user")
require_api_role = require_test_role("api")
