"""
API Routers for MetaPilot AI

Contains all FastAPI routers for the application.
"""

from .ai_router import router as ai_router
from .auth_router import router as auth_router

__all__ = ["ai_router", "auth_router"]