"""
Keycloak user management module for QuantyFinAI Agent.

This module provides user-related functionality including:
- User creation, update, and deletion
- User profile management
- Password reset functionality
- User search operations
"""

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KeycloakUserManager:
    """Manages Keycloak user operations."""

    def __init__(self, config: dict):
        self.server_url = config.get(
            "server_url", settings.keycloak.server_url
        )
        self.realm = config.get("realm", settings.keycloak.realm)
        self.client_id = config.get("client_id", settings.keycloak.client_id)
        self.client_secret = config.get(
            "client_secret", settings.keycloak.client_secret.get_secret_value()
        )

        # Build Keycloak URLs
        self.base_url = urljoin(self.server_url, f"/auth/realms/{self.realm}/")
        self.token_url = urljoin(
            self.base_url, "protocol/openid-connect/token"
        )

        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

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
        """
        Create a new user in Keycloak.

        Args:
            username: User username
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name
            enabled: Whether user is enabled
            email_verified: Whether email is verified

        Returns:
            Created user information

        Raises:
            Exception: If user creation fails
        """
        try:
            # Keycloak admin API endpoint for user creation
            admin_url = urljoin(self.base_url, "users/")

            user_data = {
                "username": username,
                "email": email,
                "enabled": enabled,
                "emailVerified": email_verified,
                "credentials": [
                    {"type": "password", "value": password, "temporary": False}
                ],
            }

            if first_name:
                user_data["firstName"] = first_name
            if last_name:
                user_data["lastName"] = last_name

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(
                admin_url, json=user_data, headers=headers
            )
            response.raise_for_status()

            created_user = response.json()
            logger.info(f"User created successfully: {username}")
            return created_user

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to create user: {error_detail}")
            raise Exception(f"User creation failed: {error_detail}")

    async def update_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update user information in Keycloak.

        Args:
            user_id: Keycloak user ID
            email: New email address
            first_name: New first name
            last_name: New last name
            enabled: Whether user is enabled

        Returns:
            Updated user information

        Raises:
            Exception: If user update fails
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}")

            update_data = {}
            if email is not None:
                update_data["email"] = email
            if first_name is not None:
                update_data["firstName"] = first_name
            if last_name is not None:
                update_data["lastName"] = last_name
            if enabled is not None:
                update_data["enabled"] = enabled

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.put(
                admin_url, json=update_data, headers=headers
            )
            response.raise_for_status()

            logger.info(f"User updated successfully: {user_id}")
            return {"user_id": user_id, "updated": True}

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to update user: {error_detail}")
            raise Exception(f"User update failed: {error_detail}")

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user from Keycloak.

        Args:
            user_id: Keycloak user ID

        Returns:
            True if deletion successful

        Raises:
            Exception: If user deletion fails
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.delete(
                admin_url, headers=headers
            )
            response.raise_for_status()

            logger.info(f"User deleted successfully: {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to delete user: {error_detail}")
            raise Exception(f"User deletion failed: {error_detail}")

    async def send_password_reset_email(self, email: str) -> bool:
        """
        Send password reset email to user.

        Args:
            email: User email address

        Returns:
            True if email sent successfully

        Raises:
            Exception: If email sending fails
        """
        try:
            # First, find user by email
            user_id = await self._get_user_id_by_email(email)
            if not user_id:
                return False  # Don't reveal if user exists

            admin_url = urljoin(
                self.base_url, f"users/{user_id}/execute-actions-email"
            )

            actions = ["UPDATE_PASSWORD"]
            data = {
                "actions": actions,
                "client_id": self.client_id,
                "redirect_uri": "http://localhost:8000/reset-password",  # Configure this
            }

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.put(
                admin_url, json=data, headers=headers
            )
            response.raise_for_status()

            logger.info(f"Password reset email sent to: {email}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(
                f"Failed to send password reset email: {error_detail}"
            )
            raise Exception(f"Password reset failed: {error_detail}")

    async def reset_password_with_token(
        self, user_id: str, new_password: str, token: str
    ) -> bool:
        """
        Reset user password using reset token.

        Args:
            user_id: Keycloak user ID
            new_password: New password
            token: Reset token

        Returns:
            True if password reset successful

        Raises:
            Exception: If password reset fails
        """
        try:
            admin_url = urljoin(
                self.base_url, f"users/{user_id}/reset-password"
            )

            data = {
                "type": "password",
                "value": new_password,
                "temporary": False,
            }

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.put(
                admin_url, json=data, headers=headers
            )
            response.raise_for_status()

            logger.info(f"Password reset successful for user: {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to reset password: {error_detail}")
            raise Exception(f"Password reset failed: {error_detail}")

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.

        Args:
            user_id: Keycloak user ID

        Returns:
            User information or None if not found
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError:
            return None

    async def get_user_by_username(
        self, username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user by username.

        Args:
            username: User username

        Returns:
            User information or None if not found
        """
        try:
            admin_url = urljoin(self.base_url, "users")
            params = {"username": username}

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(
                admin_url, params=params, headers=headers
            )
            response.raise_for_status()

            users = response.json()
            if users:
                return users[0]
            return None

        except httpx.HTTPError:
            return None

    async def _get_admin_token(self) -> str:
        """
        Get admin access token for Keycloak management API.

        Returns:
            Admin access token

        Raises:
            Exception: If token retrieval fails
        """
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await self.http_client.post(
                self.token_url, data=data, headers=headers
            )
            response.raise_for_status()

            token_data = response.json()
            return token_data["access_token"]

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            raise Exception(f"Failed to get admin token: {error_detail}")

    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """
        Get user ID by email address.

        Args:
            email: User email address

        Returns:
            User ID if found, None otherwise
        """
        try:
            admin_url = urljoin(self.base_url, "users")
            params = {"email": email}

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(
                admin_url, params=params, headers=headers
            )
            response.raise_for_status()

            users = response.json()
            if users:
                return users[0]["id"]
            return None

        except httpx.HTTPError:
            return None

    async def _extract_keycloak_error(self, error: httpx.HTTPError) -> str:
        """
        Extract error message from Keycloak response.

        Args:
            error: HTTP error

        Returns:
            Error message string
        """
        try:
            response = error.response
            error_data = response.json()

            if "error_description" in error_data:
                return error_data["error_description"]
            elif "error" in error_data:
                return error_data["error"]

            return response.text

        except Exception:
            return str(error)

    async def health_check(self) -> bool:
        """
        Check Keycloak health by trying to get admin token.

        Returns:
            True if Keycloak is healthy, False otherwise
        """
        try:
            await self._get_admin_token()
            return True
        except Exception:
            return False
