"""
Database Models for MetaPilot AI

Defines all SQLAlchemy models for the application.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# Use the base from connection module
from .connection import Base


# If Base is not defined (import issue), define it here
if Base is None:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class UserRole(str, Enum):
    """User roles."""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task types."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    KNOWLEDGE_QUERY = "knowledge_query"
    DOCUMENT_PROCESSING = "document_processing"
    CODE_GENERATION = "code_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    ANALYSIS = "analysis"
    MULTI_PROVIDER = "multi_provider"
    BATCH = "batch"


class ProviderType(str, Enum):
    """AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    LOCAL_GGUF = "local_gguf"
    LOCAL_ONNX = "local_onnx"
    LOCAL_TRANSFORMERS = "local_transformers"


# User and Authentication Models
class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default=UserRole.USER.value)
    avatar_url = Column(String(500))
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    theme = Column(String(10), default="system")  # system, light, dark
    
    # API keys (encrypted)
    api_keys = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    sessions = relationship("Session", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
    )


class Permission(Base):
    """Permission model."""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))
    code = Column(String(50), unique=True, nullable=False)
    category = Column(String(50))
    
    # Relationships
    roles = relationship("UserRole", secondary="role_permission", back_populates="permissions")
    users = relationship("User", secondary="user_permission", back_populates="permissions")


class UserRole(Base):
    """User role model."""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    
    # Relationships
    permissions = relationship("Permission", secondary="role_permission", back_populates="roles")
    users = relationship("User", backref="role_obj")


class RolePermission(Base):
    """Role-Permission many-to-many relationship."""
    __tablename__ = "role_permission"
    
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)
    
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class UserPermission(Base):
    """User-Permission many-to-many relationship."""
    __tablename__ = "user_permission"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), primary_key=True)
    
    __table_args__ = (
        UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),
    )


# Conversation Models
class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(200), default="New Conversation")
    is_archived = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    
    __table_args__ = (
        Index("idx_conversation_user", "user_id"),
        Index("idx_conversation_created", "created_at"),
    )


class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Tokens
    tokens = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_created", "created_at"),
    )


# Knowledge Base Models
class KnowledgeDocument(Base):
    """Knowledge document model."""
    __tablename__ = "knowledge_documents"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    # File info
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    # Content
    content = Column(Text)
    content_hash = Column(String(64))
    
    # Processing
    is_processed = Column(Boolean, default=False)
    processing_error = Column(String(500))
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    project = relationship("Project", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document")
    
    __table_args__ = (
        Index("idx_knowledge_doc_user", "user_id"),
        Index("idx_knowledge_doc_project", "project_id"),
        Index("idx_knowledge_doc_created", "created_at"),
    )


class KnowledgeChunk(Base):
    """Knowledge chunk model (for vector search)."""
    __tablename__ = "knowledge_chunks"
    
    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("knowledge_documents.id"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    document = relationship("KnowledgeDocument", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk")
    
    __table_args__ = (
        Index("idx_knowledge_chunk_doc", "document_id"),
    )


class Embedding(Base):
    """Embedding model for vector search."""
    __tablename__ = "embeddings"
    
    id = Column(String(36), primary_key=True, index=True)
    chunk_id = Column(String(36), ForeignKey("knowledge_chunks.id"), nullable=False)
    
    # Vector
    vector = Column(ARRAY(Float), nullable=False)
    dimension = Column(Integer, default=384)
    
    # Metadata
    model_name = Column(String(100))
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    chunk = relationship("KnowledgeChunk", back_populates="embeddings")
    
    __table_args__ = (
        Index("idx_embedding_chunk", "chunk_id"),
    )


# Task Models
class Task(Base):
    """Task model."""
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    # Task info
    task_type = Column(String(50), default=TaskType.TEXT_GENERATION.value)
    status = Column(String(20), default=TaskStatus.PENDING.value)
    priority = Column(Integer, default=0)
    
    # Content
    prompt = Column(Text)
    system_prompt = Column(Text)
    result = Column(Text)
    
    # Provider
    provider = Column(String(50))
    model = Column(String(100))
    
    # Parameters
    parameters = Column(JSON, default={})
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Tokens
    tokens_prompt = Column(Integer, default=0)
    tokens_generated = Column(Integer, default=0)
    
    # Timing
    latency_ms = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    results = relationship("TaskResult", back_populates="task")
    
    __table_args__ = (
        Index("idx_task_user", "user_id"),
        Index("idx_task_project", "project_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_created", "created_at"),
        Index("idx_task_type", "task_type"),
    )


class TaskResult(Base):
    """Task result model (for multi-provider tasks)."""
    __tablename__ = "task_results"
    
    id = Column(String(36), primary_key=True, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    
    # Provider result
    provider = Column(String(50))
    text = Column(Text)
    confidence = Column(Float)
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="results")
    
    __table_args__ = (
        Index("idx_task_result_task", "task_id"),
    )


# Provider and Model Models
class ProviderConfig(Base):
    """Provider configuration model."""
    __tablename__ = "provider_configs"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Provider info
    provider_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Configuration
    config = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    models = relationship("ModelConfig", back_populates="provider")
    
    __table_args__ = (
        Index("idx_provider_user", "user_id"),
        Index("idx_provider_type", "provider_type"),
    )


class ModelConfig(Base):
    """Model configuration model."""
    __tablename__ = "model_configs"
    
    id = Column(String(36), primary_key=True, index=True)
    provider_id = Column(String(36), ForeignKey("provider_configs.id"), nullable=False)
    
    # Model info
    model_name = Column(String(100), nullable=False)
    display_name = Column(String(100))
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Parameters
    parameters = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    provider = relationship("ProviderConfig", back_populates="models")
    
    __table_args__ = (
        Index("idx_model_provider", "provider_id"),
    )


# Plugin Models
class Plugin(Base):
    """Plugin model."""
    __tablename__ = "plugins"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Plugin info
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    version = Column(String(20), default="1.0.0")
    
    # File info
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # Status
    is_enabled = Column(Boolean, default=True)
    is_installed = Column(Boolean, default=False)
    
    # Configuration
    config = Column(JSON, default={})
    
    # Metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_plugin_user", "user_id"),
        Index("idx_plugin_enabled", "is_enabled"),
    )


# Project Models
class Project(Base):
    """Project model."""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Project info
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    is_archived = Column(Boolean, default=False)
    
    # Settings
    settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    documents = relationship("KnowledgeDocument", back_populates="project")
    tasks = relationship("Task", back_populates="project")
    
    __table_args__ = (
        Index("idx_project_user", "user_id"),
        Index("idx_project_created", "created_at"),
    )


# Audit and Logging Models
class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Action info
    action = Column(String(100), nullable=False)
    category = Column(String(50))
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    
    # Details
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_category", "category"),
        Index("idx_audit_created", "created_at"),
    )


class Session(Base):
    """User session model."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session info
    token = Column(String(500), unique=True, nullable=False)
    token_hash = Column(String(64))
    expires_at = Column(DateTime, nullable=False)
    
    # Device info
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    device_info = Column(JSON, default={})
    
    # Status
    is_revoked = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("idx_session_user", "user_id"),
        Index("idx_session_token", "token_hash"),
        Index("idx_session_expires", "expires_at"),
    )
