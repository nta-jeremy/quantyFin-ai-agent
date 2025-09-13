"""
Session service for QuantyFinAI Agent.

This module provides session management functionality including:
- Session caching and retrieval
- Session validation and cleanup
- Session lifecycle management
"""

import logging
from typing import Any, Dict, Optional

from app.infrastructure.cache.redis_adapter import RedisCacheManager

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions."""

    def __init__(
        self,
        cache_manager: RedisCacheManager,
        session_ttl: int = 3600,
    ):
        self.cache_manager = cache_manager
        self.session_ttl = session_ttl

    async def cache_user_session(self, auth_result: Dict[str, Any]) -> None:
        """
        Cache user session data.

        Args:
            auth_result: Authentication result with tokens
        """
        try:
            access_token = auth_result.get("access_token")
            if access_token:
                session_key = f"session:{access_token}"
                await self.cache_manager.cache_adapter.set(
                    session_key, auth_result, expire_seconds=self.session_ttl
                )
                logger.debug(
                    f"Session cached for token: {access_token[:20]}..."
                )
        except Exception as e:
            logger.warning(f"Failed to cache user session: {e}")

    async def get_cached_user_session(
        self, token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached user session.

        Args:
            token: Access token

        Returns:
            Cached session data if found, None otherwise
        """
        try:
            session_key = f"session:{token}"
            cached_data = await self.cache_manager.cache_adapter.get(
                session_key
            )
            if cached_data:
                logger.debug(f"Session retrieved for token: {token[:20]}...")
            return cached_data
        except Exception as e:
            logger.warning(f"Failed to get cached session: {e}")
            return None

    async def clear_user_session(self, token: str) -> None:
        """
        Clear cached user session.

        Args:
            token: Access token
        """
        try:
            session_key = f"session:{token}"
            await self.cache_manager.cache_adapter.delete(session_key)
            logger.debug(f"Session cleared for token: {token[:20]}...")
        except Exception as e:
            logger.warning(f"Failed to clear user session: {e}")

    async def update_session_ttl(self, token: str, new_ttl: int) -> None:
        """
        Update session TTL.

        Args:
            token: Access token
            new_ttl: New TTL in seconds
        """
        try:
            session_key = f"session:{token}"
            session_data = await self.get_cached_user_session(token)
            if session_data:
                await self.cache_manager.cache_adapter.set(
                    session_key, session_data, expire_seconds=new_ttl
                )
                logger.debug(f"Session TTL updated for token: {token[:20]}...")
        except Exception as e:
            logger.warning(f"Failed to update session TTL: {e}")

    async def validate_session(self, token: str) -> bool:
        """
        Validate session exists and is active.

        Args:
            token: Access token

        Returns:
            True if session is valid, False otherwise
        """
        try:
            session_data = await self.get_cached_user_session(token)
            return session_data is not None
        except Exception as e:
            logger.warning(f"Failed to validate session: {e}")
            return False

    async def get_session_user_info(
        self, token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user info from cached session.

        Args:
            token: Access token

        Returns:
            User info if session exists, None otherwise
        """
        try:
            session_data = await self.get_cached_user_session(token)
            if session_data:
                return session_data.get("user_info")
            return None
        except Exception as e:
            logger.warning(f"Failed to get session user info: {e}")
            return None

    async def get_session_roles(self, token: str) -> Optional[list[str]]:
        """
        Get user roles from cached session.

        Args:
            token: Access token

        Returns:
            List of roles if session exists, None otherwise
        """
        try:
            session_data = await self.get_cached_user_session(token)
            if session_data:
                return session_data.get("roles")
            return None
        except Exception as e:
            logger.warning(f"Failed to get session roles: {e}")
            return None

    async def clear_all_user_sessions(self, user_id: str) -> None:
        """
        Clear all sessions for a specific user.

        Note: This is a simplified implementation. In a production environment,
        you would need to track all session keys for a user or use Redis patterns
        to find and delete all sessions for a user.

        Args:
            user_id: User ID
        """
        try:
            # This is a simplified implementation
            # In production, you would maintain an index of user sessions
            # or use Redis SCAN with pattern matching
            logger.warning(
                f"Clear all user sessions called for user {user_id} - this is a placeholder implementation"
            )
        except Exception as e:
            logger.warning(f"Failed to clear all user sessions: {e}")

    async def health_check(self) -> bool:
        """
        Check session service health.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple cache operation to verify Redis is working
            test_key = "health_check:session_service"
            await self.cache_manager.cache_adapter.set(
                test_key, "test", expire_seconds=5
            )
            result = await self.cache_manager.cache_adapter.get(test_key)
            await self.cache_manager.cache_adapter.delete(test_key)

            return result == "test"
        except Exception as e:
            logger.error(f"Session service health check failed: {e}")
            return False

    async def get_session_stats(self) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Session statistics
        """
        try:
            # This is a simplified implementation
            # In production, you would track actual session metrics
            return {
                "total_sessions": "unknown",  # Would need Redis keyspace scanning
                "session_service_healthy": await self.health_check(),
                "cache_healthy": await self.cache_manager.health_check(),
            }
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {
                "total_sessions": "unknown",
                "session_service_healthy": False,
                "cache_healthy": False,
                "error": str(e),
            }
