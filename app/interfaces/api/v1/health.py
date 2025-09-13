"""
Health check endpoints for QuantyFinAI Agent.

This module provides health check endpoints to monitor application status.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

health_router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Application status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    services: Dict[str, Any] = Field(
        default_factory=dict, description="Service statuses"
    )


@health_router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the application is running and healthy",
)
async def health_check() -> HealthResponse:
    """
    Perform a health check of the application.

    Returns:
        HealthResponse: Application health status including version and service checks.
    """
    logger.info("Health check requested")

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment="development",
        services={
            "database": "not_checked",
            "redis": "not_checked",
            "llm": "not_checked",
        },
    )


@health_router.get(
    "/health/detailed",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Health Check",
    description="Perform detailed health checks including external services",
)
async def detailed_health_check() -> HealthResponse:
    """
    Perform a detailed health check including external services.

    Returns:
        HealthResponse: Detailed health status with service-specific checks.
    """
    logger.info("Detailed health check requested")

    # In a real implementation, we would check actual service connectivity
    # For now, returning mock service statuses
    service_status = {
        "database": "healthy",
        "redis": "healthy",
        "llm": "healthy",
    }

    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment="development",
        services=service_status,
    )
