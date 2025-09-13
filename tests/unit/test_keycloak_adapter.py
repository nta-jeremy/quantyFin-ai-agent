"""
Unit tests for Keycloak adapter.

This module provides unit tests for the Keycloak authentication adapter,
testing individual methods and edge cases.
"""

import json
import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import httpx
from jose import JWTError

from app.infrastructure.auth.keycloak_adapter import (
    KeycloakAdapter,
    KeycloakAuthManager,
    KeycloakAuthenticationError,
    KeycloakAuthorizationError,
)


class TestKeycloakAdapter:
    """Test class for Keycloak adapter."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client."""
        mock = AsyncMock(spec=httpx.AsyncClient)
        mock.get.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={
                "keys": [{
                    "kty": "RSA",
                    "n": "mock_n",
                    "e": "mock_e"
                }]
            })
        )
        return mock

    @pytest.fixture
    def adapter_config(self):
        """Test configuration for Keycloak adapter."""
        return {
            "server_url": "http://localhost:8080",
            "realm": "test-realm",
            "client_id": "test-client",
            "client_secret": "test-secret",
            "algorithm": "RS256"
        }

    @pytest.fixture
    def keycloak_adapter(self, adapter_config, mock_http_client):
        """Keycloak adapter instance with mocked HTTP client."""
        adapter = KeycloakAdapter(adapter_config)
        adapter.http_client = mock_http_client
        return adapter

    @pytest.mark.asyncio
    async def test_get_public_key_cached(self, keycloak_adapter):
        """Test getting public key from cache."""
        # Set cached key
        keycloak_adapter.public_key = "cached_key"
        keycloak_adapter.public_key_cache_time = datetime.now(timezone.utc)

        result = await keycloak_adapter.get_public_key()

        assert result == "cached_key"
        # HTTP client should not be called when key is cached
        keycloak_adapter.http_client.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_public_key_fetches_new(self, keycloak_adapter):
        """Test getting public key fetches new key when not cached."""
        # Set expired cache
        keycloak_adapter.public_key_cache_time = datetime.now(timezone.utc) - timedelta(hours=2)

        result = await keycloak_adapter.get_public_key()

        assert result is not None
        keycloak_adapter.http_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_token_success(self, keycloak_adapter):
        """Test successful token validation."""
        mock_token = "valid_token"
        mock_claims = {
            "sub": "user123",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        }

        with patch('app.infrastructure.auth.keycloak_adapter.jwt.decode', return_value=mock_claims):
            result = await keycloak_adapter.validate_token(mock_token)

            assert result == mock_claims

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, keycloak_adapter):
        """Test token validation with expired token."""
        mock_token = "expired_token"
        mock_claims = {
            "sub": "user123",
            "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        }

        with patch('app.infrastructure.auth.keycloak_adapter.jwt.decode', return_value=mock_claims):
            with pytest.raises(KeycloakAuthenticationError, match="Token has expired"):
                await keycloak_adapter.validate_token(mock_token)

    @pytest.mark.asyncio
    async def test_validate_token_missing_claims(self, keycloak_adapter):
        """Test token validation with missing required claims."""
        mock_token = "invalid_token"
        mock_claims = {
            "sub": "user123"
            # Missing 'exp' claim
        }

        with patch('app.infrastructure.auth.keycloak_adapter.jwt.decode', return_value=mock_claims):
            with pytest.raises(KeycloakAuthenticationError, match="Token missing expiration claim"):
                await keycloak_adapter.validate_token(mock_token)

    @pytest.mark.asyncio
    async def test_get_access_token_success(self, keycloak_adapter):
        """Test successful access token retrieval."""
        username = "testuser"
        password = "testpass"
        mock_response = {
            "access_token": "new_token",
            "refresh_token": "refresh_token",
            "expires_in": 3600
        }

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()
        mock_response_obj.json = Mock(return_value=mock_response)
        keycloak_adapter.http_client.post.return_value = mock_response_obj

        result = await keycloak_adapter.get_access_token(username, password)

        assert result == mock_response
        keycloak_adapter.http_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, keycloak_adapter):
        """Test access token retrieval failure."""
        username = "testuser"
        password = "wrongpass"

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status.side_effect = httpx.HTTPError("Invalid credentials")
        keycloak_adapter.http_client.post.return_value = mock_response_obj

        with pytest.raises(KeycloakAuthenticationError, match="Authentication failed"):
            await keycloak_adapter.get_access_token(username, password)

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, keycloak_adapter):
        """Test successful token refresh."""
        refresh_token = "valid_refresh_token"
        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token"
        }

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()
        mock_response_obj.json = Mock(return_value=mock_response)
        keycloak_adapter.http_client.post.return_value = mock_response_obj

        result = await keycloak_adapter.refresh_access_token(refresh_token)

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_user_info_retrieval(self, keycloak_adapter):
        """Test user information retrieval."""
        token = "valid_token"
        mock_user_info = {
            "sub": "user123",
            "username": "testuser",
            "email": "test@example.com"
        }

        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()
        mock_response_obj.json = Mock(return_value=mock_user_info)
        keycloak_adapter.http_client.get.return_value = mock_response_obj

        result = await keycloak_adapter.get_user_info(token)

        assert result == mock_user_info

    @pytest.mark.asyncio
    async def test_get_user_roles(self, keycloak_adapter):
        """Test getting user roles from token."""
        token = "valid_token"
        mock_claims = {
            "realm_access": {"roles": ["user", "offline_access"]},
            "resource_access": {"test-client": {"roles": ["client-role"]}}
        }

        with patch.object(keycloak_adapter, 'validate_token', return_value=mock_claims):
            result = await keycloak_adapter.get_user_roles(token)

            expected_roles = ["user", "offline_access", "client-role"]
            assert sorted(result) == sorted(expected_roles)

    @pytest.mark.asyncio
    async def test_check_role_success(self, keycloak_adapter):
        """Test successful role check."""
        token = "valid_token"
        required_role = "user"

        with patch.object(keycloak_adapter, 'get_user_roles', return_value=["user", "offline_access"]):
            result = await keycloak_adapter.check_role(token, required_role)

            assert result is True

    @pytest.mark.asyncio
    async def test_check_role_failure(self, keycloak_adapter):
        """Test role check failure."""
        token = "valid_token"
        required_role = "admin"

        with patch.object(keycloak_adapter, 'get_user_roles', return_value=["user", "offline_access"]):
            result = await keycloak_adapter.check_role(token, required_role)

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_success(self, keycloak_adapter):
        """Test successful health check."""
        with patch.object(keycloak_adapter, 'get_public_key', return_value="valid_key"):
            result = await keycloak_adapter.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, keycloak_adapter):
        """Test health check failure."""
        with patch.object(keycloak_adapter, 'get_public_key', side_effect=KeycloakError("Connection failed")):
            result = await keycloak_adapter.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_create_user_success(self, keycloak_adapter):
        """Test successful user creation."""
        mock_response = {"id": "new_user_id"}
        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()
        mock_response_obj.json = Mock(return_value=mock_response)
        keycloak_adapter.http_client.post.return_value = mock_response_obj

        with patch.object(keycloak_adapter, '_get_admin_token', return_value="admin_token"):
            result = await keycloak_adapter.create_user(
                username="newuser",
                email="newuser@example.com",
                password="securepass",
                first_name="New",
                last_name="User"
            )

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_delete_user_success(self, keycloak_adapter):
        """Test successful user deletion."""
        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()
        keycloak_adapter.http_client.delete.return_value = mock_response_obj

        with patch.object(keycloak_adapter, '_get_admin_token', return_value="admin_token"):
            result = await keycloak_adapter.delete_user("user123")

            assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_success(self, keycloak_adapter):
        """Test successful role assignment."""
        mock_role = {"id": "role123", "name": "user"}
        mock_response_obj = Mock()
        mock_response_obj.raise_for_status = Mock()

        keycloak_adapter.http_client.post.return_value = mock_response_obj

        with patch.object(keycloak_adapter, '_get_role_by_name', return_value=mock_role), \
             patch.object(keycloak_adapter, '_get_admin_token', return_value="admin_token"):
            result = await keycloak_adapter.assign_role("user123", "user")

            assert result is True

    @pytest.mark.asyncio
    async def test_assign_role_not_found(self, keycloak_adapter):
        """Test role assignment when role doesn't exist."""
        with patch.object(keycloak_adapter, '_get_role_by_name', return_value=None):
            with pytest.raises(KeycloakAuthenticationError, match="Role not found"):
                await keycloak_adapter.assign_role("user123", "nonexistent_role")

    @pytest.mark.asyncio
    async def test_extract_keycloak_error(self, keycloak_adapter):
        """Test Keycloak error extraction."""
        # Test error with error_description
        mock_response = Mock()
        mock_response.json.return_value = {"error_description": "Test error message"}
        error = httpx.HTTPError("HTTP error", response=mock_response)

        result = await keycloak_adapter._extract_keycloak_error(error)

        assert result == "Test error message"

    def test_convert_jwk_to_pem(self, keycloak_adapter):
        """Test JWK to PEM conversion."""
        jwk = {
            "kty": "RSA",
            "n": "mock_n",
            "e": "mock_e"
        }

        with patch('app.infrastructure.auth.keycloak_adapter.default_backend'), \
             patch('app.infrastructure.auth.keycloak_adapter.rsa'), \
             patch('app.infrastructure.auth.keycloak_adapter.serialization') as mock_serialization:

            mock_key = Mock()
            mock_public_bytes = Mock(return_value=b"mock_pem")
            mock_key.public_bytes = mock_public_bytes

            mock_rsa_numbers = Mock()
            mock_rsa_numbers.public_key.return_value = mock_key
            mock_rsa.RSAPublicNumbers.return_value = mock_rsa_numbers

            result = keycloak_adapter._convert_jwk_to_pem(jwk)

            assert result == "mock_pem"

    def test_convert_jwk_to_pem_unsupported_type(self, keycloak_adapter):
        """Test JWK to PEM conversion with unsupported key type."""
        jwk = {
            "kty": "EC",  # Not RSA
            "n": "mock_n",
            "e": "mock_e"
        }

        with pytest.raises(KeycloakError, match="Only RSA keys are supported"):
            keycloak_adapter._convert_jwk_to_pem(jwk)


class TestKeycloakAuthManager:
    """Test class for Keycloak authentication manager."""

    @pytest.fixture
    def mock_adapter(self):
        """Mock Keycloak adapter."""
        mock = AsyncMock(spec=KeycloakAdapter)
        mock.initialize.return_value = None
        mock.close.return_value = None
        mock.health_check.return_value = True
        mock.authenticate_user.return_value = {"access_token": "token"}
        mock.validate_token.return_value = {"sub": "user123", "roles": ["user"]}
        mock.logout.return_value = True
        mock.refresh_access_token.return_value = {"access_token": "new_token"}
        return mock

    @pytest.fixture
    def auth_manager(self, mock_adapter):
        """Keycloak auth manager instance."""
        return KeycloakAuthManager()

    @pytest.mark.asyncio
    async def test_initialize(self, auth_manager, mock_adapter):
        """Test auth manager initialization."""
        auth_manager.adapter = mock_adapter

        await auth_manager.initialize()

        mock_adapter.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user(self, auth_manager, mock_adapter):
        """Test user authentication."""
        auth_manager.adapter = mock_adapter

        result = await auth_manager.authenticate_user("testuser", "testpass")

        assert result == {"access_token": "token"}
        mock_adapter.authenticate_user.assert_called_once_with("testuser", "testpass")

    @pytest.mark.asyncio
    async def test_validate_token(self, auth_manager, mock_adapter):
        """Test token validation."""
        auth_manager.adapter = mock_adapter

        result = await auth_manager.validate_token("test_token")

        assert result == {"sub": "user123", "roles": ["user"]}
        mock_adapter.validate_token.assert_called_once_with("test_token")

    @pytest.mark.asyncio
    async def test_health_check(self, auth_manager, mock_adapter):
        """Test health check."""
        auth_manager.adapter = mock_adapter

        result = await auth_manager.health_check()

        assert result is True
        mock_adapter.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user(self, auth_manager, mock_adapter):
        """Test user registration."""
        auth_manager.adapter = mock_adapter
        mock_adapter.create_user.return_value = {"id": "new_user_id"}
        mock_adapter.assign_role.return_value = True

        result = await auth_manager.register_user(
            "newuser", "newuser@example.com", "password", "New", "User"
        )

        assert result == {"access_token": "token"}
        mock_adapter.create_user.assert_called_once()
        mock_adapter.assign_role.assert_called_once()
        mock_adapter.authenticate_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile(self, auth_manager, mock_adapter):
        """Test user profile update."""
        auth_manager.adapter = mock_adapter
        mock_adapter.update_user.return_value = {"updated": True}

        result = await auth_manager.update_user_profile(
            "user123", "newemail@example.com", "New", "User"
        )

        assert result == {"updated": True}
        mock_adapter.update_user.assert_called_once_with(
            user_id="user123",
            email="newemail@example.com",
            first_name="New",
            last_name="User"
        )

    @pytest.mark.asyncio
    async def test_initiate_password_reset(self, auth_manager, mock_adapter):
        """Test password reset initiation."""
        auth_manager.adapter = mock_adapter
        mock_adapter.send_password_reset_email.return_value = True

        result = await auth_manager.initiate_password_reset("test@example.com")

        assert result is True
        mock_adapter.send_password_reset_email.assert_called_once_with("test@example.com")