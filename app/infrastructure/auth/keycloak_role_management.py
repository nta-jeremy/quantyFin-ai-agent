"""
Keycloak role management module for QuantyFinAI Agent.

This module provides role-related functionality including:
- Role assignment and removal
- Role retrieval and validation
- Permission management
- Role-based access control
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KeycloakRoleManager:
    """Manages Keycloak role operations."""

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

    async def assign_role(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name to assign

        Returns:
            True if role assignment successful

        Raises:
            Exception: If role assignment fails
        """
        try:
            # Get role representation
            role = await self._get_role_by_name(role_name)
            if not role:
                raise Exception(f"Role not found: {role_name}")

            admin_url = urljoin(
                self.base_url, f"users/{user_id}/role-mappings/realm"
            )

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(
                admin_url, json=[role], headers=headers
            )
            response.raise_for_status()

            logger.info(f"Role {role_name} assigned to user {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to assign role: {error_detail}")
            raise Exception(f"Role assignment failed: {error_detail}")

    async def remove_role(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: Keycloak user ID
            role_name: Role name to remove

        Returns:
            True if role removal successful

        Raises:
            Exception: If role removal fails
        """
        try:
            # Get role representation
            role = await self._get_role_by_name(role_name)
            if not role:
                raise Exception(f"Role not found: {role_name}")

            admin_url = urljoin(
                self.base_url, f"users/{user_id}/role-mappings/realm"
            )

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.delete(
                admin_url, json=[role], headers=headers
            )
            response.raise_for_status()

            logger.info(f"Role {role_name} removed from user {user_id}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to remove role: {error_detail}")
            raise Exception(f"Role removal failed: {error_detail}")

    async def create_role(
        self, role_name: str, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new role in Keycloak.

        Args:
            role_name: Role name
            description: Role description

        Returns:
            Created role information

        Raises:
            Exception: If role creation fails
        """
        try:
            admin_url = urljoin(self.base_url, "roles")

            role_data = {
                "name": role_name,
            }

            if description:
                role_data["description"] = description

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(
                admin_url, json=role_data, headers=headers
            )
            response.raise_for_status()

            created_role = response.json()
            logger.info(f"Role created successfully: {role_name}")
            return created_role

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to create role: {error_detail}")
            raise Exception(f"Role creation failed: {error_detail}")

    async def delete_role(self, role_name: str) -> bool:
        """
        Delete a role from Keycloak.

        Args:
            role_name: Role name to delete

        Returns:
            True if role deletion successful

        Raises:
            Exception: If role deletion fails
        """
        try:
            # Get role representation
            role = await self._get_role_by_name(role_name)
            if not role:
                raise Exception(f"Role not found: {role_name}")

            admin_url = urljoin(self.base_url, f"roles-by-id/{role['id']}")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.delete(
                admin_url, headers=headers
            )
            response.raise_for_status()

            logger.info(f"Role deleted successfully: {role_name}")
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to delete role: {error_detail}")
            raise Exception(f"Role deletion failed: {error_detail}")

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Get all roles from Keycloak.

        Returns:
            List of roles

        Raises:
            Exception: If role retrieval fails
        """
        try:
            admin_url = urljoin(self.base_url, "roles")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get roles: {error_detail}")
            raise Exception(f"Role retrieval failed: {error_detail}")

    async def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all roles for a specific user.

        Args:
            user_id: Keycloak user ID

        Returns:
            List of user roles

        Raises:
            Exception: If role retrieval fails
        """
        try:
            admin_url = urljoin(
                self.base_url, f"users/{user_id}/role-mappings/realm"
            )

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get user roles: {error_detail}")
            raise Exception(f"User role retrieval failed: {error_detail}")

    async def check_user_role(self, user_id: str, role_name: str) -> bool:
        """
        Check if a user has a specific role.

        Args:
            user_id: Keycloak user ID
            role_name: Role name to check

        Returns:
            True if user has the role, False otherwise
        """
        try:
            user_roles = await self.get_user_roles(user_id)
            return any(role["name"] == role_name for role in user_roles)

        except Exception:
            return False

    async def get_role_by_name(
        self, role_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get role information by name.

        Args:
            role_name: Role name

        Returns:
            Role information or None if not found
        """
        try:
            admin_url = urljoin(self.base_url, "roles")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            roles = response.json()
            for role in roles:
                if role["name"] == role_name:
                    return role
            return None

        except httpx.HTTPError:
            return None

    async def get_composite_roles(
        self, role_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get composite roles for a specific role.

        Args:
            role_name: Role name

        Returns:
            List of composite roles

        Raises:
            Exception: If composite role retrieval fails
        """
        try:
            # Get role representation
            role = await self._get_role_by_name(role_name)
            if not role:
                raise Exception(f"Role not found: {role_name}")

            admin_url = urljoin(
                self.base_url, f"roles-by-id/{role['id']}/composites"
            )

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get composite roles: {error_detail}")
            raise Exception(f"Composite role retrieval failed: {error_detail}")

    async def add_composite_role(
        self, parent_role_name: str, child_role_name: str
    ) -> bool:
        """
        Add a composite role to a parent role.

        Args:
            parent_role_name: Parent role name
            child_role_name: Child role name to add as composite

        Returns:
            True if composite role addition successful

        Raises:
            Exception: If composite role addition fails
        """
        try:
            # Get role representations
            parent_role = await self._get_role_by_name(parent_role_name)
            child_role = await self._get_role_by_name(child_role_name)

            if not parent_role:
                raise Exception(f"Parent role not found: {parent_role_name}")
            if not child_role:
                raise Exception(f"Child role not found: {child_role_name}")

            admin_url = urljoin(
                self.base_url, f"roles-by-id/{parent_role['id']}/composites"
            )

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.post(
                admin_url, json=[child_role], headers=headers
            )
            response.raise_for_status()

            logger.info(
                f"Composite role {child_role_name} added to {parent_role_name}"
            )
            return True

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to add composite role: {error_detail}")
            raise Exception(f"Composite role addition failed: {error_detail}")

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

    async def _get_role_by_name(
        self, role_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get role representation by name.

        Args:
            role_name: Role name

        Returns:
            Role representation if found, None otherwise
        """
        try:
            admin_url = urljoin(self.base_url, "roles")

            headers = {
                "Authorization": f"Bearer {await self._get_admin_token()}",
                "Content-Type": "application/json",
            }

            response = await self.http_client.get(admin_url, headers=headers)
            response.raise_for_status()

            roles = response.json()
            for role in roles:
                if role["name"] == role_name:
                    return role
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
        Check Keycloak health by trying to get roles.

        Returns:
            True if Keycloak is healthy, False otherwise
        """
        try:
            await self.get_all_roles()
            return True
        except Exception:
            return False
