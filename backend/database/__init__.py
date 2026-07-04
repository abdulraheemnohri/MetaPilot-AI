"""
Database Module for MetaPilot AI

Provides database connection, models, and utilities.
"""

from .connection import get_db, init_db, close_db
from .models import *

__all__ = [
    "get_db",
    "init_db", 
    "close_db",
    "User",
    "Session",
    "UserSession",
    "Conversation",
    "Message",
    "Document",
    "DocumentChunk",
    "AIProvider",
    "Task",
    "Plugin",
    "AuditLog",
    "SystemConfig",
]