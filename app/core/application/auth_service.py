"""
Authentication service for QuantyFinAI Agent.

This module provides core authentication business logic, coordinating with
specialized services for session management and permission handling.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.application.permission_service import PermissionService
from app.core.application.session_service import SessionService
from app.core.domain.models import Role, User
from app.infrastructure.auth.keycloak_adapter import (
    KeycloakAuthenticationError,
    KeycloakAuthManager,
    KeycloakAuthorizationError,
)
from app.infrastructure.cache.redis_adapter import RedisCacheManager

logger = logging.getLogger(__name__)


class AuthService:
    """Service for core authentication and authorization business logic."""

    def __init__(
        self,
        auth_manager: KeycloakAuthManager,
        cache_manager: RedisCacheManager,
        session_service: Optional[SessionService] = None,
        permission_service: Optional[PermissionService] = None,
    ):
        self.auth_manager = auth_manager
        self.cache_manager = cache_manager

        # Initialize session service
        if session_service is None:
            self.session_service = SessionService(cache_manager)
        else:
            self.session_service = session_service

        # Initialize permission service
        if permission_service is None:
            self.permission_service = PermissionService()
        else:
            self.permission_service = permission_service

    async def initialize(self) -> None:
        """Initialize the authentication service."""
        await self.auth_manager.initialize()
        logger.info("Authentication service initialized")

    async def close(self) -> None:
        """Close the authentication service."""
        await self.auth_manager.close()
        logger.info("Authentication service closed")

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            username: User username
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name

        Returns:
            Authentication result with tokens and user info

        Raises:
            KeycloakAuthenticationError: If registration fails
        """
        logger.info(f"Attempting to register user: {username}")

        # Register user in Keycloak
        auth_result = await self.auth_manager.register_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Cache user session
        await self.session_service.cache_user_session(auth_result)

        logger.info(f"User registered successfully: {username}")
        return auth_result

    async def authenticate_user(
        self, username: str, password: str
    ) -> Dict[str, Any]:
        """
        Authenticate user with username and password.

        Args:
            username: User username
            password: User password

        Returns:
            Authentication result with tokens and user info

        Raises:
            KeycloakAuthenticationError: If authentication fails
        """
        logger.info(f"Attempting to authenticate user: {username}")

        # Authenticate with Keycloak
        auth_result = await self.auth_manager.authenticate_user(
            username, password
        )

        # Cache user session
        await self.session_service.cache_user_session(auth_result)

        logger.info(f"User authenticated successfully: {username}")
        return auth_result

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New authentication result

        Raises:
            KeycloakAuthenticationError: If token refresh fails
        """
        logger.info("Attempting to refresh access token")

        # Refresh token with Keycloak
        new_auth_result = await self.auth_manager.refresh_token(refresh_token)

        # Cache new session
        await self._cache_user_session(new_auth_result)

        logger.info("Access token refreshed successfully")
        return new_auth_result

    async def logout_user(self, refresh_token: str, access_token: str) -> bool:
        """
        Logout user and invalidate sessions.

        Args:
            refresh_token: Refresh token to invalidate
            access_token: Access token for session cleanup

        Returns:
            True if logout successful

        Raises:
            KeycloakAuthenticationError: If logout fails
        """
        logger.info("Attempting to logout user")

        # Logout from Keycloak
        logout_success = await self.auth_manager.logout_user(refresh_token)

        # Clear cached session
        if logout_success:
            await self.session_service.clear_user_session(access_token)

        logger.info("User logged out successfully")
        return logout_success

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.

        Args:
            token: JWT token string

        Returns:
            Token claims dictionary

        Raises:
            KeycloakAuthenticationError: If token is invalid
        """
        logger.debug("Validating JWT token")

        claims = await self.auth_manager.validate_token(token)

        # Check if user is active
        if not claims.get("active", True):
            raise KeycloakAuthenticationError("User account is inactive")

        logger.debug(
            f"Token validated successfully for user {claims.get('sub')}"
        )
        return claims

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from token.

        Args:
            token: Access token

        Returns:
            User information dictionary
        """
        logger.debug("Getting user information")

        # Try to get from cache first
        cached_user = await self.session_service.get_cached_user_session(token)
        if cached_user:
            return cached_user.get("user_info", {})

        # Get from Keycloak
        user_info = await self.auth_manager.adapter.get_user_info(token)

        logger.debug("User information retrieved successfully")
        return user_info

    async def update_user_profile(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update user profile.

        Args:
            user_id: Keycloak user ID
            email: New email address
            first_name: New first name
            last_name: New last name

        Returns:
            Update result

        Raises:
            KeycloakAuthenticationError: If update fails
        """
        logger.info(f"Attempting to update user profile: {user_id}")

        result = await self.auth_manager.update_user_profile(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        logger.info(f"User profile updated successfully: {user_id}")
        return result

    async def delete_user_account(
        self, user_id: str, access_token: str
    ) -> bool:
        """
        Delete user account.

        Args:
            user_id: Keycloak user ID
            access_token: Access token for session cleanup

        Returns:
            True if deletion successful

        Raises:
            KeycloakAuthenticationError: If deletion fails
        """
        logger.info(f"Attempting to delete user account: {user_id}")

        # Delete user from Keycloak
        success = await self.auth_manager.delete_user_account(user_id)

        # Clear cached sessions
        if success:
            await self._clear_user_session(access_token)

        logger.info(f"User account deleted successfully: {user_id}")
        return success

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Initiate password reset process.

        Args:
            email: User email address

        Returns:
            True if reset initiated successfully
        """
        logger.info(f"Attempting to initiate password reset for: {email}")

        success = await self.auth_manager.initiate_password_reset(email)

        if success:
            logger.info(f"Password reset initiated successfully for: {email}")
        else:
            logger.warning(f"Password reset initiation failed for: {email}")

        return success

    async def complete_password_reset(
        self, user_id: str, new_password: str, token: str
    ) -> bool:
        """
        Complete password reset.

        Args:
            user_id: Keycloak user ID
            new_password: New password
            token: Reset token

        Returns:
            True if password reset successful
        """
        logger.info(
            f"Attempting to complete password reset for user: {user_id}"
        )

        success = await self.auth_manager.complete_password_reset(
            user_id=user_id, new_password=new_password, token=token
        )

        if success:
            logger.info(
                f"Password reset completed successfully for user: {user_id}"
            )
        else:
            logger.warning(f"Password reset failed for user: {user_id}")

        return success

    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name to assign

        Returns:
            True if role assignment successful
        """
        logger.info(f"Attempting to assign role {role_name} to user {user_id}")

        success = await self.auth_manager.assign_user_role(user_id, role_name)

        if success:
            logger.info(
                f"Role {role_name} assigned successfully to user {user_id}"
            )
        else:
            logger.warning(
                f"Failed to assign role {role_name} to user {user_id}"
            )

        return success

    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name to remove

        Returns:
            True if role removal successful
        """
        logger.info(
            f"Attempting to remove role {role_name} from user {user_id}"
        )

        success = await self.auth_manager.remove_user_role(user_id, role_name)

        if success:
            logger.info(
                f"Role {role_name} removed successfully from user {user_id}"
            )
        else:
            logger.warning(
                f"Failed to remove role {role_name} from user {user_id}"
            )

        return success

    async def check_permission(
        self, token: str, required_permission: str
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            token: Access token
            required_permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get user roles
            roles = await self.auth_manager.adapter.get_user_roles(token)

            # Use permission service to check permissions
            return self.permission_service.check_permission(
                roles, required_permission
            )

        except KeycloakAuthenticationError:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check authentication system health.

        Returns:
            Health check result
        """
        try:
            keycloak_healthy = await self.auth_manager.health_check()
            redis_healthy = await self.cache_manager.health_check()

            return {
                "healthy": keycloak_healthy and redis_healthy,
                "keycloak": keycloak_healthy,
                "redis": redis_healthy,
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "keycloak": False,
                "redis": False,
                "error": str(e),
            }

    def get_required_roles(self, endpoint: str) -> List[str]:
        """
        Get required roles for an endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            List of required roles
        """
        # Use permission service to get required roles
        return self.permission_service.get_required_roles(endpoint)
