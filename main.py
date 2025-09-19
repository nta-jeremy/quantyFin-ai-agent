"""
Main entry point for QuantyFinAI Agent ASGI application.

This module provides the ASGI application instance for deployment.
"""

from app.main import app

# Export the ASGI application
__all__ = ["app"]
