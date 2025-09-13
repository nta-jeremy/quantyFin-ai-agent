"""
Middleware for authentication and authorization.

This module provides middleware functions for handling authentication,
authorization, and security-related tasks in FastAPI applications.
"""

import logging
import time
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.application.auth_service import AuthService
from app.interfaces.api.auth_dependencies import get_auth_service

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication and authorization."""

    def __init__(self, app, auth_service: AuthService):
        super().__init__(app)
        self.auth_service = auth_service
        self.excluded_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/hello",
        }

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process the request through authentication middleware."""
        start_time = time.time()

        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        try:
            # Process request
            response = await self._process_authenticated_request(
                request, call_next
            )

            # Log request processing time
            process_time = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} "
                f"completed in {process_time:.3f}s"
            )

            return response

        except HTTPException:
            # Re-raise HTTP exceptions as they're already properly formatted
            raise
        except Exception as e:
            logger.error(f"Unexpected error in authentication middleware: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def _process_authenticated_request(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process request with authentication checks."""
        # Extract token from Authorization header
        token = self._extract_token(request)
        if not token:
            return await call_next(request)

        try:
            # Validate token and get user info
            user_claims = await self.auth_service.validate_token(token)

            # Add user info to request state
            request.state.user = user_claims

            # Check if user is active
            if not user_claims.get("active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                )

            # Log authenticated request
            logger.debug(
                f"Authenticated request: {request.method} {request.url.path} "
                f"by user {user_claims.get('sub')}"
            )

            # Process the request
            return await call_next(request)

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            # Continue without authentication for optional auth routes
            return await call_next(request)

    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers."""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
        return None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses."""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests."""

    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
        }

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Log HTTP requests and responses."""
        start_time = time.time()

        # Skip logging for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Log request
        logger.info(
            f"Incoming request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} for {request.method} {request.url.path} "
            f"in {process_time:.3f}s"
        )

        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with authentication support."""

    def __init__(self, app, allowed_origins: list[str]):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Handle CORS with authentication support."""
        origin = request.headers.get("origin")

        # Check if origin is allowed
        if origin and origin in self.allowed_origins:
            # Handle preflight requests
            if request.method == "OPTIONS":
                response = JSONResponse(content={"detail": "OK"})
            else:
                response = await call_next(request)

            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours

            return response
        elif not origin:
            # No origin header (e.g., same-origin or non-browser request)
            return await call_next(request)
        else:
            # Origin not allowed
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Origin not allowed"},
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, auth_service: AuthService):
        super().__init__(app)
        self.auth_service = auth_service
        self.rate_limits = {
            # path: (requests, window_seconds)
            "/api/v1/auth/login": (5, 300),  # 5 login attempts per 5 minutes
            "/api/v1/auth/register": (3, 300),  # 3 registrations per 5 minutes
            "/api/v1/auth/forgot-password": (
                3,
                300,
            ),  # 3 password resets per 5 minutes
        }

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Apply rate limiting to requests."""
        path = request.url.path

        # Check if this path has rate limiting
        if path in self.rate_limits:
            try:
                # Get identifier for rate limiting
                identifier = self._get_rate_limit_identifier(request)

                # Apply rate limit
                max_requests, window_seconds = self.rate_limits[path]
                is_limited = await self.auth_service.cache_manager.rate_limiter.check_rate_limit(
                    f"rate_limit:{path}:{identifier}",
                    max_requests,
                    window_seconds,
                )

                if is_limited["is_limited"]:
                    logger.warning(
                        f"Rate limit exceeded for {path} by {identifier}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later.",
                    )

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Don't fail the request if rate limiting fails

        return await call_next(request)

    def _get_rate_limit_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("sub")
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP address
        return f"ip:{request.client.host if request.client else 'unknown'}"


async def create_auth_middleware(
    app, auth_service: AuthService
) -> BaseHTTPMiddleware:
    """Factory function to create authentication middleware."""
    return AuthenticationMiddleware(app, auth_service)


async def create_security_headers_middleware(app) -> BaseHTTPMiddleware:
    """Factory function to create security headers middleware."""
    return SecurityHeadersMiddleware(app)


async def create_request_logging_middleware(app) -> BaseHTTPMiddleware:
    """Factory function to create request logging middleware."""
    return RequestLoggingMiddleware(app)


async def create_cors_middleware(
    app, allowed_origins: list[str]
) -> BaseHTTPMiddleware:
    """Factory function to create CORS middleware."""
    return CORSMiddleware(app, allowed_origins)


async def create_rate_limit_middleware(
    app, auth_service: AuthService
) -> BaseHTTPMiddleware:
    """Factory function to create rate limit middleware."""
    return RateLimitMiddleware(app, auth_service)
