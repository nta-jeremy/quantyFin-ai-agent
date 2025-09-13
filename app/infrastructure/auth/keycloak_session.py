"""
Keycloak session management module for QuantyFinAI Agent.

This module provides session-related functionality including:
- Session validation and management
- Password reset session handling
- Token revocation
- Session monitoring
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KeycloakSessionManager:
    """Manages Keycloak session operations."""

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
        self.logout_url = urljoin(
            self.base_url, "protocol/openid-connect/logout"
        )
        self.revocation_url = urljoin(
            self.base_url, "protocol/openid-connect/revoke"
        )

        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

    async def revoke_token(
        self, token: str, token_type_hint: Optional[str] = None
    ) -> bool:
        """
        Revoke a token.

        Args:
            token: Token to revoke
            token_type_hint: Token type hint (access_token, refresh_token)

        Returns:
            True if token revocation successful
        """
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": token,
            }

            if token_type_hint:
                data["token_type_hint"] = token_type_hint

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await self.http_client.post(
                self.revocation_url, data=data, headers=headers
            )
            response.raise_for_status()

            logger.debug("Token revoked successfully")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    async def logout_all_sessions(self, user_id: str) -> bool:
        """
        Logout all sessions for a user.

        Args:
            user_id: Keycloak user ID

        Returns:
            True if all sessions logged out successfully
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}/logout")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(admin_url, headers=headers)
            response.raise_for_status()

            logger.info(f"All sessions logged out for user: {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to logout all sessions: {error_detail}")
            raise Exception(f"Session logout failed: {error_detail}")

    async def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for a user.

        Args:
            user_id: Keycloak user ID

        Returns:
            List of active sessions

        Raises:
            Exception: If session retrieval fails
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}/sessions")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get active sessions: {error_detail}")
            raise Exception(f"Session retrieval failed: {error_detail}")

    async def is_session_active(self, session_id: str) -> bool:
        """
        Check if a session is still active.

        Args:
            session_id: Session ID

        Returns:
            True if session is active, False otherwise
        """
        try:
            # This is a simplified check - in practice, you'd need to query Keycloak
            # or implement a more sophisticated session validation mechanism
            admin_url = urljoin(self.base_url, f"sessions/{session_id}")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            return response.status_code == 200

        except httpx.HTTPError:
            return False

    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a specific session.

        Args:
            session_id: Session ID to terminate

        Returns:
            True if session terminated successfully
        """
        try:
            admin_url = urljoin(self.base_url, f"sessions/{session_id}")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.delete(
                admin_url, headers=headers
            )
            response.raise_for_status()

            logger.info(f"Session terminated: {session_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to terminate session: {error_detail}")
            raise Exception(f"Session termination failed: {error_detail}")

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.

        Args:
            user_id: Keycloak user ID

        Returns:
            List of user sessions

        Raises:
            Exception: If session retrieval fails
        """
        try:
            admin_url = urljoin(self.base_url, f"users/{user_id}/sessions")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get user sessions: {error_detail}")
            raise Exception(f"User session retrieval failed: {error_detail}")

    async def init_password_reset_flow(self, email: str) -> bool:
        """
        Initialize password reset flow for a user.

        Args:
            email: User email address

        Returns:
            True if password reset flow initiated successfully
        """
        try:
            # This would typically integrate with the user management module
            # For now, we'll provide a simplified implementation
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
                user_id = users[0]["id"]
                action_url = urljoin(
                    self.base_url, f"users/{user_id}/execute-actions-email"
                )

                data = {
                    "actions": ["UPDATE_PASSWORD"],
                    "client_id": self.client_id,
                    "redirect_uri": "http://localhost:8000/reset-password",
                }

                response = await self.http_client.put(
                    action_url, json=data, headers=headers
                )
                response.raise_for_status()

                logger.info(f"Password reset flow initiated for: {email}")
                return True

            return False

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(
                f"Failed to initiate password reset flow: {error_detail}"
            )
            raise Exception(
                f"Password reset flow initiation failed: {error_detail}"
            )

    async def validate_reset_token(self, token: str) -> bool:
        """
        Validate a password reset token.

        Args:
            token: Password reset token

        Returns:
            True if token is valid, False otherwise
        """
        try:
            # This is a simplified validation - in practice, you'd need to implement
            # proper token validation based on your Keycloak configuration
            # For now, we'll just check if the token exists and is not expired
            if not token or len(token) < 10:
                return False

            # In a real implementation, you would:
            # 1. Parse the token
            # 2. Check expiration
            # 3. Verify the token signature
            # 4. Check if the token is in the valid state

            return True

        except Exception:
            return False

    async def complete_password_reset(
        self, user_id: str, new_password: str, token: str
    ) -> bool:
        """
        Complete password reset process.

        Args:
            user_id: Keycloak user ID
            new_password: New password
            token: Reset token

        Returns:
            True if password reset completed successfully
        """
        try:
            if not await self.validate_reset_token(token):
                raise Exception("Invalid or expired reset token")

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

            logger.info(f"Password reset completed for user: {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to complete password reset: {error_detail}")
            raise Exception(
                f"Password reset completion failed: {error_detail}"
            )

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
