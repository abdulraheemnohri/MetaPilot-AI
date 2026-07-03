"""
API Routers for MetaPilot AI

Contains all FastAPI routers for the application.
"""

from .ai_router import router as ai_router
from .knowledge_router import router as knowledge_router
from .memory_router import router as memory_router
from .tasks_router import router as tasks_router
from .auth_router import router as auth_router
from .models_router import router as models_router
from .providers_router import router as providers_router
from .plugins_router import router as plugins_router
from .projects_router import router as projects_router
from .export_router import router as export_router
from .merge_router import router as merge_router
from .ranking_router import router as ranking_router
from .validator_router import router as validator_router

__all__ = [
    "ai_router",
    "knowledge_router",
    "memory_router",
    "tasks_router",
    "auth_router",
    "models_router",
    "providers_router",
    "plugins_router",
    "projects_router",
    "export_router",
    "merge_router",
    "ranking_router",
    "validator_router",
]
