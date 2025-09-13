"""
Permission service for QuantyFinAI Agent.

This module provides role-based access control and permission management
functionality including:
- Role-based endpoint protection
- Permission validation
- Role hierarchy management
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing role-based access control."""

    def __init__(self):
        # Define role requirements for different endpoints
        self.endpoint_roles = {
            "/api/v1/auth/admin-only": ["admin", "super_admin", "system"],
            "/api/v1/users": ["admin", "super_admin", "system"],
            "/api/v1/users/delete": ["super_admin", "system"],
            "/api/v1/finance": ["user", "admin", "super_admin", "system"],
            "/api/v1/ai": ["user", "admin", "super_admin", "system", "api"],
            "/api/v1/admin": ["admin", "super_admin", "system"],
            "/api/v1/super-admin": ["super_admin", "system"],
            "/api/v1/system": ["system"],
        }

        # Define role hierarchy for inheritance
        self.role_hierarchy = {
            "user": [],
            "api": [],
            "admin": ["user"],
            "super_admin": ["admin", "user"],
            "system": ["super_admin", "admin", "user", "api"],
        }

        # Define role permissions mapping
        self.role_permissions = {
            "user": [
                "read:profile",
                "update:profile",
                "read:finance_data",
                "use:ai_features",
            ],
            "api": [
                "access:api_endpoints",
                "read:public_data",
            ],
            "admin": [
                "read:all_users",
                "create:users",
                "update:users",
                "delete:users",
                "manage:roles",
                "read:all_financial_data",
                "export:data",
            ],
            "super_admin": [
                "manage:system_settings",
                "create:admins",
                "delete:admins",
                "access:audit_logs",
                "manage:api_keys",
                "system:backup",
                "system:restore",
            ],
            "system": [
                "system:full_control",
                "system:manage_infrastructure",
                "system:security_management",
                "system:database_management",
                "system:monitoring",
            ],
        }

    def get_required_roles(self, endpoint: str) -> List[str]:
        """
        Get required roles for an endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            List of required roles
        """
        # Exact match first
        if endpoint in self.endpoint_roles:
            return self.endpoint_roles[endpoint]

        # Pattern matching for dynamic endpoints
        for pattern, roles in self.endpoint_roles.items():
            if pattern.endswith("*") and endpoint.startswith(pattern[:-1]):
                return roles

        # Default to no roles required
        return []

    def check_permission(
        self, user_roles: List[str], required_permission: str
    ) -> bool:
        """
        Check if user has required permission.

        Args:
            user_roles: List of user roles
            required_permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        try:
            # Get all effective roles including inherited ones
            effective_roles = self._get_effective_roles(user_roles)

            # Check if any role has the required permission
            for role in effective_roles:
                if required_permission in self.role_permissions.get(role, []):
                    return True

            return False

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    def check_endpoint_access(
        self, user_roles: List[str], endpoint: str
    ) -> bool:
        """
        Check if user has access to an endpoint.

        Args:
            user_roles: List of user roles
            endpoint: API endpoint path

        Returns:
            True if user has access, False otherwise
        """
        try:
            required_roles = self.get_required_roles(endpoint)
            if not required_roles:
                return True  # No roles required, allow access

            effective_roles = self._get_effective_roles(user_roles)

            # Check if user has any of the required roles
            for required_role in required_roles:
                if required_role in effective_roles:
                    return True

            return False

        except Exception as e:
            logger.error(f"Endpoint access check failed: {e}")
            return False

    def _get_effective_roles(self, user_roles: List[str]) -> List[str]:
        """
        Get all effective roles including inherited ones.

        Args:
            user_roles: List of user roles

        Returns:
            List of all effective roles
        """
        effective_roles = set(user_roles)

        for role in user_roles:
            # Add all inherited roles
            inherited_roles = self.role_hierarchy.get(role, [])
            effective_roles.update(inherited_roles)

            # Recursively add inherited roles from parent roles
            for inherited_role in inherited_roles:
                parent_inherited = self.role_hierarchy.get(inherited_role, [])
                effective_roles.update(parent_inherited)

        return list(effective_roles)

    def get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """
        Get all permissions for a user based on their roles.

        Args:
            user_roles: List of user roles

        Returns:
            List of all user permissions
        """
        try:
            effective_roles = self._get_effective_roles(user_roles)
            permissions = set()

            for role in effective_roles:
                role_permissions = self.role_permissions.get(role, [])
                permissions.update(role_permissions)

            return list(permissions)

        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []

    def validate_role_hierarchy(self) -> bool:
        """
        Validate that the role hierarchy is consistent.

        Returns:
            True if hierarchy is valid, False otherwise
        """
        try:
            # Check for circular dependencies
            visited = set()
            recursion_stack = set()

            def has_cycle(role: str) -> bool:
                if role in recursion_stack:
                    return True
                if role in visited:
                    return False

                visited.add(role)
                recursion_stack.add(role)

                for inherited_role in self.role_hierarchy.get(role, []):
                    if has_cycle(inherited_role):
                        return True

                recursion_stack.remove(role)
                return False

            for role in self.role_hierarchy:
                if has_cycle(role):
                    logger.error(
                        f"Circular dependency detected in role hierarchy for role: {role}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Role hierarchy validation failed: {e}")
            return False

    def add_role_permission(self, role: str, permission: str) -> bool:
        """
        Add a permission to a role.

        Args:
            role: Role name
            permission: Permission to add

        Returns:
            True if permission was added, False otherwise
        """
        try:
            if role not in self.role_permissions:
                self.role_permissions[role] = []

            if permission not in self.role_permissions[role]:
                self.role_permissions[role].append(permission)
                logger.info(
                    f"Added permission '{permission}' to role '{role}'"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to add role permission: {e}")
            return False

    def remove_role_permission(self, role: str, permission: str) -> bool:
        """
        Remove a permission from a role.

        Args:
            role: Role name
            permission: Permission to remove

        Returns:
            True if permission was removed, False otherwise
        """
        try:
            if (
                role in self.role_permissions
                and permission in self.role_permissions[role]
            ):
                self.role_permissions[role].remove(permission)
                logger.info(
                    f"Removed permission '{permission}' from role '{role}'"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to remove role permission: {e}")
            return False

    def get_role_info(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a role.

        Args:
            role: Role name

        Returns:
            Role information or None if role doesn't exist
        """
        try:
            if (
                role not in self.role_permissions
                and role not in self.role_hierarchy
            ):
                return None

            return {
                "name": role,
                "permissions": self.role_permissions.get(role, []),
                "inherits_from": self.role_hierarchy.get(role, []),
                "inherited_by": [
                    parent_role
                    for parent_role, inherited_roles in self.role_hierarchy.items()
                    if role in inherited_roles
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get role info: {e}")
            return None

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Get information about all roles.

        Returns:
            List of role information
        """
        try:
            all_roles = set(self.role_permissions.keys()).union(
                set(self.role_hierarchy.keys())
            )
            return [
                self.get_role_info(role)
                for role in all_roles
                if self.get_role_info(role)
            ]

        except Exception as e:
            logger.error(f"Failed to get all roles: {e}")
            return []

    def health_check(self) -> Dict[str, Any]:
        """
        Check permission service health.

        Returns:
            Health check result
        """
        try:
            hierarchy_valid = self.validate_role_hierarchy()
            total_roles = len(
                set(self.role_permissions.keys()).union(
                    set(self.role_hierarchy.keys())
                )
            )

            return {
                "healthy": hierarchy_valid,
                "total_roles": total_roles,
                "hierarchy_valid": hierarchy_valid,
                "role_permissions_count": len(self.role_permissions),
                "role_hierarchy_count": len(self.role_hierarchy),
            }

        except Exception as e:
            logger.error(f"Permission service health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
            }
