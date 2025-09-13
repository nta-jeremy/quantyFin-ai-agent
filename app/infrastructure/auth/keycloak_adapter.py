"""
Keycloak authentication adapter implementation for QuantyFinAI Agent.

This module provides the main Keycloak adapter interface that coordinates
between the specialized authentication, user management, role management,
and session management modules.
"""

import logging
from typing import Any, Dict, Optional

from config.settings import get_settings

from .keycloak_auth import KeycloakAuthManager as KeycloakAuthModule
from .keycloak_role_management import KeycloakRoleManager
from .keycloak_session import KeycloakSessionManager
from .keycloak_user_management import KeycloakUserManager

logger = logging.getLogger(__name__)
settings = get_settings()


class KeycloakError(Exception):
    """Keycloak-related errors."""

    pass


class KeycloakAuthenticationError(KeycloakError):
    """Authentication-related errors."""

    pass


class KeycloakAuthorizationError(KeycloakError):
    """Authorization-related errors."""

    pass


class KeycloakAdapter:
    """Keycloak adapter for authentication and authorization."""

    def __init__(self, config: dict):
        self.config = config

        # Initialize specialized managers
        self.auth_manager = KeycloakAuthModule(config)
        self.user_manager = KeycloakUserManager(config)
        self.role_manager = KeycloakRoleManager(config)
        self.session_manager = KeycloakSessionManager(config)

    async def close(self) -> None:
        """Close all managers."""
        await self.auth_manager.close()
        await self.user_manager.close()
        await self.role_manager.close()
        await self.session_manager.close()

    # Authentication methods
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        return await self.auth_manager.validate_token(token)

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get user information from Keycloak."""
        return await self.auth_manager.get_user_info(token)

    async def get_access_token(
        self, username: str, password: str, grant_type: str = "password"
    ) -> Dict[str, Any]:
        """Get access token using username/password."""
        return await self.auth_manager.get_access_token(
            username, password, grant_type
        )

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        return await self.auth_manager.refresh_access_token(refresh_token)

    async def logout(self, refresh_token: str) -> bool:
        """Logout user by invalidating refresh token."""
        return await self.auth_manager.logout(refresh_token)

    async def get_user_roles(self, token: str) -> list[str]:
        """Get user roles from Keycloak token."""
        return await self.auth_manager.get_user_roles(token)

    async def check_role(self, token: str, required_role: str) -> bool:
        """Check if user has required role."""
        return await self.auth_manager.check_role(token, required_role)

    async def get_public_key(self) -> str:
        """Get Keycloak public key for JWT validation."""
        return await self.auth_manager.get_public_key()

    # User management methods
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: bool = True,
        email_verified: bool = False,
    ) -> Dict[str, Any]:
        """Create a new user in Keycloak."""
        return await self.user_manager.create_user(
            username,
            email,
            password,
            first_name,
            last_name,
            enabled,
            email_verified,
        )

    async def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update user information in Keycloak."""
        return await self.user_manager.update_user(
            user_id, email, first_name, last_name, enabled
        )

    async def delete_user(self, user_id: str) -> bool:
        """Delete user from Keycloak."""
        return await self.user_manager.delete_user(user_id)

    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email to user."""
        return await self.user_manager.send_password_reset_email(email)

    async def reset_password_with_token(
        self, user_id: str, new_password: str, token: str
    ) -> bool:
        """Reset user password using reset token."""
        return await self.user_manager.reset_password_with_token(
            user_id, new_password, token
        )

    # Role management methods
    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign a role to a user."""
        return await self.role_manager.assign_role(user_id, role_name)

    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """Remove a role from a user."""
        return await self.role_manager.remove_role(user_id, role_name)

    # Session management methods
    async def revoke_token(
        self, token: str, token_type_hint: Optional[str] = None
    ) -> bool:
        """Revoke a token."""
        return await self.session_manager.revoke_token(token, token_type_hint)

    async def logout_all_sessions(self, user_id: str) -> bool:
        """Logout all sessions for a user."""
        return await self.session_manager.logout_all_sessions(user_id)

    async def get_active_sessions(self, user_id: str) -> list[Dict[str, Any]]:
        """Get active sessions for a user."""
        return await self.session_manager.get_active_sessions(user_id)

    # Health check
    async def health_check(self) -> bool:
        """Check Keycloak health by trying to fetch public key."""
        return await self.auth_manager.health_check()


class KeycloakAuthManager:
    """Manages Keycloak authentication operations using specialized modules."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if config is None:
            config = {
                "server_url": settings.keycloak.server_url,
                "realm": settings.keycloak.realm,
                "client_id": settings.keycloak.client_id,
                "client_secret": settings.keycloak.client_secret.get_secret_value(),
                "algorithm": settings.keycloak.algorithm,
            }

        self.adapter = KeycloakAdapter(config)

    async def initialize(self) -> None:
        """Initialize Keycloak adapter."""
        # Pre-fetch public key to ensure connectivity
        await self.adapter.get_public_key()

    async def close(self) -> None:
        """Close Keycloak adapter."""
        await self.adapter.close()

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
        """
        # Get access token
        token_response = await self.adapter.get_access_token(
            username, password
        )

        # Get user info
        user_info = await self.adapter.get_user_info(
            token_response["access_token"]
        )

        # Get user roles
        roles = await self.adapter.get_user_roles(
            token_response["access_token"]
        )

        return {
            "access_token": token_response["access_token"],
            "refresh_token": token_response.get("refresh_token"),
            "expires_in": token_response.get("expires_in"),
            "refresh_expires_in": token_response.get("refresh_expires_in"),
            "token_type": token_response.get("token_type"),
            "user_info": user_info,
            "roles": roles,
        }

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Token claims
        """
        return await self.adapter.validate_token(token)

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response
        """
        return await self.adapter.refresh_access_token(refresh_token)

    async def logout_user(self, refresh_token: str) -> bool:
        """
        Logout user.

        Args:
            refresh_token: Refresh token

        Returns:
            True if logout successful
        """
        return await self.adapter.logout(refresh_token)

    async def health_check(self) -> bool:
        """
        Check Keycloak health.

        Returns:
            True if healthy, False otherwise
        """
        return await self.adapter.health_check()

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user in Keycloak.

        Args:
            username: User username
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name

        Returns:
            Registration result
        """
        # Create user in Keycloak
        created_user = await self.adapter.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        # Assign default role
        user_id = created_user.get("id")
        if user_id:
            await self.adapter.assign_role(user_id, "user")

        # Authenticate user to get tokens
        auth_result = await self.authenticate_user(username, password)
        return auth_result

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
            email: New email
            first_name: New first name
            last_name: New last name

        Returns:
            Update result
        """
        return await self.adapter.update_user(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

    async def delete_user_account(self, user_id: str) -> bool:
        """
        Delete user account.

        Args:
            user_id: Keycloak user ID

        Returns:
            True if deletion successful
        """
        return await self.adapter.delete_user(user_id)

    async def initiate_password_reset(self, email: str) -> bool:
        """
        Initiate password reset process.

        Args:
            email: User email address

        Returns:
            True if reset initiated successfully
        """
        return await self.adapter.send_password_reset_email(email)

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
        return await self.adapter.reset_password_with_token(
            user_id=user_id, new_password=new_password, token=token
        )

    async def assign_user_role(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name

        Returns:
            True if role assignment successful
        """
        return await self.adapter.assign_role(user_id, role_name)

    async def remove_user_role(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name

        Returns:
            True if role removal successful
        """
        return await self.adapter.remove_role(user_id, role_name)
