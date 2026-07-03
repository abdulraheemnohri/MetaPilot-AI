"""
MetaPilot AI - Backend Package

This package contains all backend modules for the MetaPilot AI application.
Includes FastAPI routes, database models, AI providers, security, and utilities.
"""

__version__ = "1.0.0"
__author__ = "Abdulraheem Nohari"
__description__ = "MetaPilot AI Backend - FastAPI-based AI orchestration system"

# Import all modules for easy access
from .config import settings
from .main import app
from .orchestrator import AIOrchestrator
from .local_ai import LocalAIManager

# Database
from .database import connection, models

# Knowledge
from .knowledge import knowledge_base

# Memory
from .memory import memory_system

# Providers
from .providers import (
    base,
    registry,
    openai_provider,
    anthropic_provider,
    mistral_provider,
    google_provider,
    perplexity_provider,
    local_gguf,
)

# Security
from .security import (
    auth,
    permission_manager,
    sandbox,
    secrets_manager,
    audit_logger,
)

# Scheduler
from .scheduler import (
    scheduler,
    worker,
    queue,
)

# Browser
from .browser import browser_manager

# Export
from .export import (
    export_manager,
    markdown_exporter,
    json_exporter,
    html_exporter,
)

# Merge
from .merge import (
    conflict_resolver,
    duplicate_remover,
    result_fuser,
    similarity_detector,
)

# Ranking
from .ranking import (
    confidence_calculator,
    quality_scorer,
    ranker,
    relevance_scorer,
)

# Validator
from .validator import (
    completeness_checker,
    content_filter,
    format_validator,
    safety_checker,
)

__all__ = [
    "settings",
    "app",
    "AIOrchestrator",
    "LocalAIManager",
    "connection",
    "models",
    "knowledge_base",
    "memory_system",
    "base",
    "registry",
    "openai_provider",
    "anthropic_provider",
    "mistral_provider",
    "google_provider",
    "perplexity_provider",
    "local_gguf",
    "auth",
    "permission_manager",
    "sandbox",
    "secrets_manager",
    "audit_logger",
    "scheduler",
    "worker",
    "queue",
    "browser_manager",
    "export_manager",
    "markdown_exporter",
    "json_exporter",
    "html_exporter",
    "conflict_resolver",
    "duplicate_remover",
    "result_fuser",
    "similarity_detector",
    "confidence_calculator",
    "quality_scorer",
    "ranker",
    "relevance_scorer",
    "completeness_checker",
    "content_filter",
    "format_validator",
    "safety_checker",
]
