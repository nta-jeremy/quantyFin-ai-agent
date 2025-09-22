"""
FastAPI application entry point for QuantyFinAI Agent.

This module provides the main FastAPI application instance and includes
authentication, health check, and API endpoints with middleware.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.core.application.auth_service import AuthService
from app.infrastructure.auth.keycloak_adapter import KeycloakAuthManager
from app.infrastructure.cache.redis_adapter import RedisCacheManager
from app.interfaces.api.auth_routes import auth_router
from app.interfaces.api.middleware import (
    create_auth_middleware,
    create_rate_limit_middleware,
    create_request_logging_middleware,
    create_security_headers_middleware,
)
from app.interfaces.api.v1 import (
    agent_router,
    health_router,
    hello_router,
    historical_router,
    international_router,
    listing_router,
)
from config.settings import get_settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
settings = get_settings()
auth_manager: KeycloakAuthManager = None
auth_service: AuthService = None
cache_manager: RedisCacheManager = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager with authentication setup."""
    global auth_manager, auth_service, cache_manager

    logger.info("Starting QuantyFinAI Agent application")

    try:
        # Initialize cache manager
        cache_manager = RedisCacheManager(redis_url=settings.redis.url)
        await cache_manager.initialize()

        # Initialize Keycloak auth manager
        auth_manager = KeycloakAuthManager()
        await auth_manager.initialize()

        # Initialize authentication service
        auth_service = AuthService(auth_manager, cache_manager)
        await auth_service.initialize()

        logger.info("Authentication services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize authentication services: {e}")
        # Continue startup but auth will be unavailable

    yield

    logger.info("Shutting down QuantyFinAI Agent application")

    # Cleanup authentication services
    try:
        if auth_service:
            await auth_service.close()
        if auth_manager:
            await auth_manager.close()
        if cache_manager:
            await cache_manager.close()
        logger.info("Authentication services closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="QuantyFinAI Agent",
        description="AI-powered financial analysis and stock prediction system",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add middleware
    # Note: These need to be added after auth_service is initialized in lifespan
    # We'll add them dynamically in the lifespan function

    # Include API routers
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(hello_router, prefix="/api/v1", tags=["general"])
    app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
    app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
    app.include_router(listing_router, prefix="/api/v1", tags=["listing"])
    app.include_router(historical_router, prefix="/api/v1")
    app.include_router(international_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        logger.error(f"HTTP Exception: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Health check endpoint with authentication status
    @app.get("/auth-health")
    async def auth_health_check():
        """Check authentication system health."""
        if not auth_service:
            return {
                "status": "unavailable",
                "message": "Authentication service not initialized",
            }

        try:
            health_result = await auth_service.health_check()
            return {
                "status": (
                    "healthy" if health_result["healthy"] else "unhealthy"
                ),
                "details": health_result,
            }
        except Exception as e:
            logger.error(f"Authentication health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    # Public endpoint for testing authentication setup
    @app.get("/auth-test")
    async def auth_test():
        """Test authentication setup."""
        return {
            "message": "Authentication system is available",
            "keycloak_configured": bool(settings.keycloak.server_url),
            "redis_configured": bool(settings.redis.url),
        }

    return app


# Create the FastAPI application instance
app = create_app()


async def setup_middleware():
    """Setup middleware after authentication services are initialized."""
    global app, auth_service, cache_manager

    if auth_service and cache_manager:
        # Add authentication middleware
        auth_middleware = await create_auth_middleware(app, auth_service)
        app.add_middleware(
            auth_middleware.__class__, app=app, auth_service=auth_service
        )

        # Add security headers middleware
        security_middleware = await create_security_headers_middleware(app)
        app.add_middleware(security_middleware.__class__, app=app)

        # Add request logging middleware
        logging_middleware = await create_request_logging_middleware(app)
        app.add_middleware(logging_middleware.__class__, app=app)

        # Add rate limiting middleware
        rate_limit_middleware = await create_rate_limit_middleware(
            app, auth_service
        )
        app.add_middleware(
            rate_limit_middleware.__class__, app=app, auth_service=auth_service
        )

        # Configure CORS
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.app.cors_origins,
            allow_credentials=settings.app.cors_allow_credentials,
            allow_methods=settings.app.cors_allow_methods,
            allow_headers=settings.app.cors_allow_headers,
        )

        logger.info("Authentication middleware configured successfully")


def main() -> None:
    """Main entry point for running the application."""
    import asyncio

    import uvicorn

    async def run_app():
        # Setup middleware before starting the server
        await setup_middleware()

        # Run the application
        config = uvicorn.Config(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.is_development,
            log_level="info",
        )
        server = uvicorn.Server(config)
        await server.serve()

    if settings.is_development:
        # For development, run with asyncio
        asyncio.run(run_app())
    else:
        # For production, use standard uvicorn run
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
        )


if __name__ == "__main__":
    main()
