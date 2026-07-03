"""
Database Module for MetaPilot AI

Provides database connection management, models, and migrations.
"""

from .connection import (
    engine,
    async_engine,
    SessionLocal,
    AsyncSessionLocal,
    get_db_session,
    get_async_db_session,
    Base,
)
from .models import (
    User,
    UserRole,
    Permission,
    RolePermission,
    UserPermission,
    Conversation,
    Message,
    KnowledgeDocument,
    KnowledgeChunk,
    Embedding,
    Task,
    TaskResult,
    ProviderConfig,
    ModelConfig,
    Plugin,
    Project,
    AuditLog,
    Session,
)

__all__ = [
    # Connection
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db_session",
    "get_async_db_session",
    "Base",
    # Models
    "User",
    "UserRole",
    "Permission",
    "RolePermission",
    "UserPermission",
    "Conversation",
    "Message",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "Embedding",
    "Task",
    "TaskResult",
    "ProviderConfig",
    "ModelConfig",
    "Plugin",
    "Project",
    "AuditLog",
    "Session",
]
