"""
Keycloak authentication module for QuantyFinAI Agent.

This module provides authentication-related functionality including:
- JWT token validation
- Access token management
- Token refresh
- User authentication
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KeycloakAuthManager:
    """Manages Keycloak authentication operations."""

    def __init__(self, config: dict):
        self.server_url = config.get(
            "server_url", settings.keycloak.server_url
        )
        self.realm = config.get("realm", settings.keycloak.realm)
        self.client_id = config.get("client_id", settings.keycloak.client_id)
        self.client_secret = config.get(
            "client_secret", settings.keycloak.client_secret.get_secret_value()
        )
        self.algorithm = config.get("algorithm", settings.keycloak.algorithm)

        # Build Keycloak URLs
        self.base_url = urljoin(self.server_url, f"/auth/realms/{self.realm}/")
        self.token_url = urljoin(
            self.base_url, "protocol/openid-connect/token"
        )
        self.user_info_url = urljoin(
            self.base_url, "protocol/openid-connect/userinfo"
        )
        self.certs_url = urljoin(
            self.base_url, "protocol/openid-connect/certs"
        )
        self.logout_url = urljoin(
            self.base_url, "protocol/openid-connect/logout"
        )

        # JWT public key cache
        self.public_key: Optional[str] = None
        self.public_key_cache_time: Optional[datetime] = None
        self.key_cache_ttl = timedelta(hours=1)

        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.http_client.aclose()

    async def get_public_key(self) -> str:
        """
        Get Keycloak public key for JWT validation.

        Returns:
            Public key in PEM format
        """
        # Check cache first
        if (
            self.public_key
            and self.public_key_cache_time
            and datetime.now(timezone.utc) - self.public_key_cache_time
            < self.key_cache_ttl
        ):
            return self.public_key

        try:
            # Fetch JWKS (JSON Web Key Set)
            response = await self.http_client.get(self.certs_url)
            response.raise_for_status()

            jwks = response.json()
            if not jwks.get("keys"):
                raise Exception("No keys found in Keycloak JWKS")

            # Extract the first key (Keycloak typically uses one key)
            key_data = jwks["keys"][0]

            # Convert to PEM format
            self.public_key = self._convert_jwk_to_pem(key_data)
            self.public_key_cache_time = datetime.now(timezone.utc)

            logger.debug("Fetched and cached Keycloak public key")
            return self.public_key

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch Keycloak public key: {e}")
            raise Exception(f"Failed to fetch Keycloak public key: {e}")

    def _convert_jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        """
        Convert JWK to PEM format.

        Args:
            jwk: JSON Web Key

        Returns:
            Public key in PEM format
        """
        # This is a simplified conversion. In production, use a proper JWK library
        # like python-jose or cryptography
        if jwk.get("kty") != "RSA":
            raise Exception("Only RSA keys are supported")

        n = int.from_bytes(jwk["n"], "big")
        e = int.from_bytes(jwk["e"], "big")

        # Create PEM format (simplified)
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Create RSA public key
        public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())

        # Serialize to PEM
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return pem.decode("utf-8")

    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and return claims.

        Args:
            token: JWT token string

        Returns:
            Token claims dictionary

        Raises:
            Exception: If token is invalid
        """
        try:
            # Get public key
            public_key = await self.get_public_key()

            # Decode and validate token
            claims = jwt.decode(
                token,
                public_key,
                algorithms=[self.algorithm],
                audience=self.client_id,
                issuer=self.base_url.rstrip("/"),
            )

            # Check required claims
            if "sub" not in claims:
                raise Exception("Token missing subject claim")

            if "exp" not in claims:
                raise Exception("Token missing expiration claim")

            # Check if token is expired
            if claims["exp"] < datetime.now(timezone.utc).timestamp():
                raise Exception("Token has expired")

            logger.debug(
                f"Token validated successfully for user {claims.get('sub')}"
            )
            return claims

        except ExpiredSignatureError:
            raise Exception("Token has expired")
        except JWTClaimsError as e:
            raise Exception(f"Invalid token claims: {e}")
        except JWTError as e:
            raise Exception(f"Invalid token: {e}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from Keycloak.

        Args:
            token: Access token

        Returns:
            User information dictionary
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.http_client.get(
                self.user_info_url, headers=headers
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get user info: {e}")
            raise Exception(f"Failed to get user info: {e}")

    async def get_access_token(
        self, username: str, password: str, grant_type: str = "password"
    ) -> Dict[str, Any]:
        """
        Get access token using username/password.

        Args:
            username: User username
            password: User password
            grant_type: OAuth2 grant type

        Returns:
            Token response dictionary
        """
        try:
            data = {
                "grant_type": grant_type,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": username,
                "password": password,
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await self.http_client.post(
                self.token_url, data=data, headers=headers
            )
            response.raise_for_status()

            token_data = response.json()

            # Validate token response
            if "access_token" not in token_data:
                raise Exception("No access token in response")

            logger.debug(f"Access token obtained for user {username}")
            return token_data

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to get access token: {error_detail}")
            raise Exception(f"Authentication failed: {error_detail}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response dictionary
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await self.http_client.post(
                self.token_url, data=data, headers=headers
            )
            response.raise_for_status()

            token_data = response.json()

            if "access_token" not in token_data:
                raise Exception("No access token in refresh response")

            logger.debug("Access token refreshed successfully")
            return token_data

        except httpx.HTTPError as e:
            error_detail = self._extract_keycloak_error(e)
            logger.error(f"Failed to refresh access token: {error_detail}")
            raise Exception(f"Token refresh failed: {error_detail}")

    async def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating refresh token.

        Args:
            refresh_token: Refresh token to invalidate

        Returns:
            True if logout successful
        """
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await self.http_client.post(
                self.logout_url, data=data, headers=headers
            )
            response.raise_for_status()

            logger.debug("User logged out successfully")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to logout: {e}")
            return False

    async def get_user_roles(self, token: str) -> list[str]:
        """
        Get user roles from Keycloak token.

        Args:
            token: Access token

        Returns:
            List of user roles
        """
        try:
            claims = await self.validate_token(token)

            # Extract roles from token claims
            # Keycloak typically includes roles in the 'realm_access' or 'resource_access' claims
            roles = []

            # Realm roles
            if "realm_access" in claims and "roles" in claims["realm_access"]:
                roles.extend(claims["realm_access"]["roles"])

            # Client roles
            if (
                "resource_access" in claims
                and self.client_id in claims["resource_access"]
            ):
                client_access = claims["resource_access"][self.client_id]
                if "roles" in client_access:
                    roles.extend(client_access["roles"])

            logger.debug(f"User roles: {roles}")
            return roles

        except Exception:
            return []

    async def check_role(self, token: str, required_role: str) -> bool:
        """
        Check if user has required role.

        Args:
            token: Access token
            required_role: Role to check

        Returns:
            True if user has role, False otherwise
        """
        user_roles = await self.get_user_roles(token)
        return required_role in user_roles

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
        Check Keycloak health by trying to fetch public key.

        Returns:
            True if Keycloak is healthy, False otherwise
        """
        try:
            await self.get_public_key()
            return True
        except Exception:
            return False
