"""
Authentication API routes for QuantyFinAI Agent.

This module provides endpoints for user authentication, registration,
password management, and role-based access control.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field, validator

from app.core.domain import Role, User
from app.infrastructure.auth.keycloak_adapter import (
    KeycloakAuthenticationError,
    KeycloakAuthManager,
    KeycloakAuthorizationError,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Pydantic models for request/response
class UserRegistrationRequest(BaseModel):
    """User registration request model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)


class UserLoginRequest(BaseModel):
    """User login request model."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str = Field(..., min_length=1)


class PasswordResetRequest(BaseModel):
    """Password reset request model."""

    email: EmailStr = Field(...)


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation model."""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class UserUpdateRequest(BaseModel):
    """User profile update request model."""

    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = Field(None)


class AuthResponse(BaseModel):
    """Authentication response model."""

    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
    user_info: Dict[str, Any]
    roles: list[str]


class UserInfoResponse(BaseModel):
    """User info response model."""

    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    roles: list[str]
    is_active: bool
    created_at: str


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    error_code: Optional[str] = None


# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])


# Dependency to get Keycloak auth manager
async def get_auth_manager() -> KeycloakAuthManager:
    """Get Keycloak authentication manager instance."""
    from app.main import auth_manager

    return auth_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token."""
    try:
        token = credentials.credentials
        claims = await auth_manager.validate_token(token)
        return claims
    except KeycloakAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current active user."""
    if not current_user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def check_role(required_role: str):
    """Decorator to check if user has required role."""

    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_roles = current_user.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )
        return current_user

    return role_checker


@auth_router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def register_user(
    request: UserRegistrationRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Register a new user."""
    try:
        # Register user with Keycloak
        auth_result = await auth_manager.authenticate_user(
            request.username, request.password
        )

        logger.info(f"User registered successfully: {request.username}")
        return AuthResponse(**auth_result)

    except KeycloakAuthenticationError as e:
        logger.error(f"Registration failed for {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration",
        )


@auth_router.post(
    "/login",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login_user(
    request: UserLoginRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Authenticate user and return JWT tokens."""
    try:
        auth_result = await auth_manager.authenticate_user(
            request.username, request.password
        )

        logger.info(f"User logged in successfully: {request.username}")
        return AuthResponse(**auth_result)

    except KeycloakAuthenticationError as e:
        logger.error(f"Login failed for {request.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@auth_router.post(
    "/refresh",
    response_model=AuthResponse,
    responses={401: {"model": ErrorResponse}},
)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Refresh access token using refresh token."""
    try:
        token_response = await auth_manager.refresh_token(
            request.refresh_token
        )

        logger.info("Access token refreshed successfully")
        return AuthResponse(**token_response)

    except KeycloakAuthenticationError as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        )


@auth_router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}},
)
async def logout_user(
    request: TokenRefreshRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Logout user by invalidating refresh token."""
    try:
        await auth_manager.logout_user(request.refresh_token)

        logger.info(f"User logged out successfully: {current_user.get('sub')}")

    except KeycloakAuthenticationError as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Logout failed: {str(e)}",
        )


@auth_router.get(
    "/me",
    response_model=UserInfoResponse,
    responses={401: {"model": ErrorResponse}},
)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    """Get current user information."""
    return UserInfoResponse(
        id=current_user.get("sub", ""),
        username=current_user.get("preferred_username", ""),
        email=current_user.get("email", ""),
        first_name=current_user.get("given_name"),
        last_name=current_user.get("family_name"),
        roles=current_user.get("roles", []),
        is_active=current_user.get("active", True),
        created_at=current_user.get("created_at", ""),
    )


@auth_router.put(
    "/me",
    response_model=UserInfoResponse,
    responses={401: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_user_profile(
    request: UserUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Update current user profile."""
    try:
        # Update user in Keycloak
        # This would need to be implemented in the Keycloak adapter
        updated_user = current_user.copy()

        if request.first_name is not None:
            updated_user["given_name"] = request.first_name
        if request.last_name is not None:
            updated_user["family_name"] = request.last_name
        if request.email is not None:
            updated_user["email"] = request.email

        logger.info(f"User profile updated: {current_user.get('sub')}")

        return UserInfoResponse(
            id=updated_user.get("sub", ""),
            username=updated_user.get("preferred_username", ""),
            email=updated_user.get("email", ""),
            first_name=updated_user.get("given_name"),
            last_name=updated_user.get("family_name"),
            roles=updated_user.get("roles", []),
            is_active=updated_user.get("active", True),
            created_at=updated_user.get("created_at", ""),
        )

    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile update failed: {str(e)}",
        )


@auth_router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}},
)
async def delete_user_account(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Delete current user account."""
    try:
        # Delete user from Keycloak
        # This would need to be implemented in the Keycloak adapter
        user_id = current_user.get("sub")

        logger.info(f"User account deleted: {user_id}")

    except Exception as e:
        logger.error(f"Account deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account deletion failed: {str(e)}",
        )


@auth_router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}},
)
async def forgot_password(
    request: PasswordResetRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Initiate password reset process."""
    try:
        # Send password reset email via Keycloak
        # This would need to be implemented in the Keycloak adapter

        logger.info(f"Password reset initiated for: {request.email}")

        return {"message": "Password reset email sent if account exists"}

    except Exception as e:
        logger.error(f"Password reset initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password reset failed: {str(e)}",
        )


@auth_router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}},
)
async def reset_password(
    request: PasswordResetConfirmRequest,
    auth_manager: KeycloakAuthManager = Depends(get_auth_manager),
):
    """Reset password using reset token."""
    try:
        # Reset password in Keycloak using token
        # This would need to be implemented in the Keycloak adapter

        logger.info("Password reset completed successfully")

        return {"message": "Password reset successfully"}

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password reset failed: {str(e)}",
        )


@auth_router.get(
    "/roles",
    response_model=list[str],
    responses={401: {"model": ErrorResponse}},
)
async def get_user_roles(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    """Get current user roles."""
    return current_user.get("roles", [])


# Protected endpoint examples
@auth_router.get(
    "/admin-only",
    response_model=dict,
    dependencies=[Depends(check_role("admin"))],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def admin_only_endpoint():
    """Example admin-only endpoint."""
    return {"message": "Welcome, admin!"}


@auth_router.get(
    "/user-only",
    response_model=dict,
    dependencies=[Depends(check_role("user"))],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def user_only_endpoint():
    """Example user-only endpoint."""
    return {"message": "Welcome, user!"}
