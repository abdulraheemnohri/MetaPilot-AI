"""
Knowledge Base Module for MetaPilot AI

Provides document processing, embeddings, and semantic search capabilities.
"""

from .knowledge_base import KnowledgeBase
from .embeddings import EmbeddingManager
from .document_processor import DocumentProcessor

__all__ = [
    "KnowledgeBase",
    "EmbeddingManager",
    "DocumentProcessor",
]
