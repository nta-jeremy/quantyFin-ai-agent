"""
Integration tests for authentication system.

This module provides comprehensive tests for the authentication and authorization
system including user registration, login, token management, and role-based access.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.application.auth_service import AuthService
from app.infrastructure.auth.keycloak_adapter import KeycloakAuthManager
from app.infrastructure.cache.redis_adapter import RedisCacheManager
from app.main import app


class TestAuthentication:
    """Test class for authentication system."""

    @pytest.fixture
    def mock_auth_manager(self):
        """Mock Keycloak authentication manager."""
        mock = AsyncMock(spec=KeycloakAuthManager)
        mock.initialize.return_value = None
        mock.close.return_value = None
        mock.health_check.return_value = True

        # Mock authentication response
        mock.authenticate_user.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "refresh_expires_in": 604800,
            "token_type": "Bearer",
            "user_info": {
                "sub": "12345",
                "username": "testuser",
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User",
            },
            "roles": ["user"],
        }

        # Mock token validation
        mock.validate_token.return_value = {
            "sub": "12345",
            "username": "testuser",
            "email": "test@example.com",
            "roles": ["user"],
            "active": True,
            "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        }

        # Mock user registration
        mock.register_user.return_value = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "refresh_expires_in": 604800,
            "token_type": "Bearer",
            "user_info": {
                "sub": "12345",
                "username": "newuser",
                "email": "newuser@example.com",
                "given_name": "New",
                "family_name": "User",
            },
            "roles": ["user"],
        }

        # Mock token refresh
        mock.refresh_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "refresh_expires_in": 604800,
            "token_type": "Bearer",
        }

        # Mock logout
        mock.logout_user.return_value = True

        # Mock user operations
        mock.update_user_profile.return_value = {
            "user_id": "12345",
            "updated": True,
        }
        mock.delete_user_account.return_value = True
        mock.initiate_password_reset.return_value = True
        mock.complete_password_reset.return_value = True

        return mock

    @pytest.fixture
    def mock_cache_manager(self):
        """Mock Redis cache manager."""
        mock = AsyncMock(spec=RedisCacheManager)
        mock.initialize.return_value = None
        mock.close.return_value = None
        mock.health_check.return_value = True

        # Mock rate limiter
        mock.rate_limiter = AsyncMock()
        mock.rate_limiter.check_rate_limit.return_value = {
            "is_limited": False,
            "remaining": 95,
            "reset_time": int(
                (datetime.now() + timedelta(hours=1)).timestamp()
            ),
        }

        # Mock cache operations
        mock.cache_adapter = AsyncMock()
        mock.cache_adapter.set.return_value = True
        mock.cache_adapter.get.return_value = None
        mock.cache_adapter.delete.return_value = True

        return mock

    @pytest.fixture
    def mock_auth_service(self, mock_auth_manager, mock_cache_manager):
        """Mock authentication service."""
        with patch("app.main.auth_service") as mock_service:
            service = AuthService(mock_auth_manager, mock_cache_manager)
            mock_service.return_value = service
            yield service

    @pytest.fixture
    def client(self, mock_auth_service, mock_auth_manager, mock_cache_manager):
        """Test client with mocked authentication."""
        with (
            patch("app.main.auth_manager", mock_auth_manager),
            patch("app.main.cache_manager", mock_cache_manager),
        ):
            with TestClient(app) as test_client:
                yield test_client

    def test_auth_health_check(self, client):
        """Test authentication health check endpoint."""
        response = client.get("/auth-health")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "status" in data
        assert "details" in data
        assert data["status"] == "healthy"

    def test_auth_test_endpoint(self, client):
        """Test authentication test endpoint."""
        response = client.get("/auth-test")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert data["message"] == "Authentication system is available"
        assert "keycloak_configured" in data
        assert "redis_configured" in data

    def test_user_registration_success(self, client):
        """Test successful user registration."""
        registration_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "first_name": "New",
            "last_name": "User",
        }

        response = client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert "token_type" in data
        assert "user_info" in data
        assert "roles" in data
        assert data["token_type"] == "Bearer"
        assert "user" in data["roles"]

    def test_user_registration_invalid_data(self, client):
        """Test user registration with invalid data."""
        # Missing required fields
        invalid_data = {"username": "test", "email": "invalid-email"}

        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_user_login_success(self, client):
        """Test successful user login."""
        login_data = {"username": "testuser", "password": "SecurePassword123!"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"

    def test_user_login_invalid_credentials(self, client, mock_auth_manager):
        """Test user login with invalid credentials."""
        mock_auth_manager.authenticate_user.side_effect = Exception(
            "Invalid credentials"
        )

        login_data = {"username": "testuser", "password": "wrongpassword"}

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh_success(self, client):
        """Test successful token refresh."""
        refresh_data = {"refresh_token": "mock_refresh_token"}

        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] == "new_access_token"

    def test_token_refresh_invalid_token(self, client, mock_auth_manager):
        """Test token refresh with invalid refresh token."""
        mock_auth_manager.refresh_token.side_effect = Exception(
            "Invalid refresh token"
        )

        refresh_data = {"refresh_token": "invalid_token"}

        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_logout_success(self, client):
        """Test successful user logout."""
        logout_data = {"refresh_token": "mock_refresh_token"}

        # Add authorization header
        headers = {"Authorization": "Bearer mock_access_token"}

        response = client.post(
            "/api/v1/auth/logout", json=logout_data, headers=headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_current_user_info(self, client):
        """Test getting current user information."""
        headers = {"Authorization": "Bearer mock_access_token"}

        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "roles" in data
        assert "is_active" in data
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthorized(self, client):
        """Test getting user info without authorization."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_profile(self, client):
        """Test updating user profile."""
        update_data = {"first_name": "Updated", "last_name": "User"}

        headers = {"Authorization": "Bearer mock_access_token"}

        response = client.put(
            "/api/v1/auth/me", json=update_data, headers=headers
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "first_name" in data
        assert "last_name" in data

    def test_forgot_password(self, client):
        """Test forgot password functionality."""
        forgot_data = {"email": "test@example.com"}

        response = client.post(
            "/api/v1/auth/forgot-password", json=forgot_data
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "Password reset email sent" in data["message"]

    def test_reset_password(self, client):
        """Test password reset functionality."""
        reset_data = {
            "token": "reset_token",
            "new_password": "NewSecurePassword123!",
        }

        response = client.post("/api/v1/auth/reset-password", json=reset_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "Password reset successfully" in data["message"]

    def test_get_user_roles(self, client):
        """Test getting user roles."""
        headers = {"Authorization": "Bearer mock_access_token"}

        response = client.get("/api/v1/auth/roles", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert "user" in data

    def test_admin_only_endpoint_access(self, client):
        """Test admin-only endpoint access."""
        headers = {"Authorization": "Bearer mock_access_token"}

        # Should fail for regular user
        response = client.get("/api/v1/auth/admin-only", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_only_endpoint_access(self, client):
        """Test user-only endpoint access."""
        headers = {"Authorization": "Bearer mock_access_token"}

        # Should succeed for regular user
        response = client.get("/api/v1/auth/user-only", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "message" in data
        assert "Welcome, user!" in data["message"]

    def test_rate_limiting(self, client, mock_cache_manager):
        """Test rate limiting functionality."""
        login_data = {"username": "testuser", "password": "SecurePassword123!"}

        # Mock rate limit exceeded
        mock_cache_manager.rate_limiter.check_rate_limit.return_value = {
            "is_limited": True,
            "remaining": 0,
            "reset_time": int(
                (datetime.now() + timedelta(hours=1)).timestamp()
            ),
        }

        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/api/v1/auth/login")
        assert response.status_code == status.HTTP_200_OK

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    @pytest.mark.asyncio
    async def test_auth_service_initialization(
        self, mock_auth_manager, mock_cache_manager
    ):
        """Test authentication service initialization."""
        auth_service = AuthService(mock_auth_manager, mock_cache_manager)

        await auth_service.initialize()

        mock_auth_manager.initialize.assert_called_once()
        mock_cache_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_service_health_check(
        self, mock_auth_manager, mock_cache_manager
    ):
        """Test authentication service health check."""
        auth_service = AuthService(mock_auth_manager, mock_cache_manager)

        health_result = await auth_service.health_check()

        assert "healthy" in health_result
        assert "keycloak" in health_result
        assert "redis" in health_result
        assert health_result["healthy"] is True

    @pytest.mark.asyncio
    async def test_permission_checking(
        self, mock_auth_manager, mock_cache_manager
    ):
        """Test permission checking functionality."""
        auth_service = AuthService(mock_auth_manager, mock_cache_manager)

        # Mock user roles
        mock_auth_manager.adapter.get_user_roles.return_value = ["user"]

        # Test read permission
        has_read_permission = await auth_service.check_permission(
            "mock_token", "read"
        )
        assert has_read_permission is True

        # Test admin permission (should fail for regular user)
        has_admin_permission = await auth_service.check_permission(
            "mock_token", "manage_users"
        )
        assert has_admin_permission is False

    def test_middleware_error_handling(self, client, mock_auth_manager):
        """Test middleware error handling."""
        # Mock authentication failure
        mock_auth_manager.validate_token.side_effect = Exception(
            "Token validation failed"
        )

        headers = {"Authorization": "Bearer invalid_token"}

        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_security_headers(self, client):
        """Test security headers are present."""
        response = client.get("/auth-test")

        # Check security headers
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
