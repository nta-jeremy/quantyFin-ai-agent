"""
Hello endpoint for QuantyFinAI Agent.

This module provides a basic connectivity test endpoint.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

hello_router = APIRouter()


class HelloResponse(BaseModel):
    """Hello endpoint response model."""

    message: str = Field(..., description="Greeting message")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    user_name: Optional[str] = Field(None, description="User name if provided")


@hello_router.get(
    "/hello",
    response_model=HelloResponse,
    status_code=status.HTTP_200_OK,
    summary="Hello World",
    description="Basic connectivity test endpoint",
)
async def hello_world(
    name: Optional[str] = Query(
        None,
        description="Optional name to personalize the greeting",
        min_length=1,
        max_length=100,
    )
) -> HelloResponse:
    """
    Return a greeting message.

    Args:
        name: Optional name parameter for personalized greeting.

    Returns:
        HelloResponse: Greeting message with timestamp and version.
    """
    logger.info(f"Hello endpoint called with name: {name}")

    if name:
        message = f"Hello, {name}! Welcome to QuantyFinAI Agent."
    else:
        message = "Hello, World! Welcome to QuantyFinAI Agent."

    return HelloResponse(
        message=message,
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        user_name=name,
    )
