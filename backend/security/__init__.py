"""
MetaPilot AI - Security Module

Provides security-related functionality including:
- Authentication and authorization
- Permission management
- Secrets management
- Sandboxed execution
- Audit logging
- Encryption
"""

from .encryption import EncryptionManager, get_encryption_manager
from .permission_manager import (
    PermissionManager, 
    Permission, 
    Role, 
    UserPermissions,
    PermissionLevel,
    ResourceType,
    get_permission_manager
)
from .sandbox import (
    SandboxManager,
    SandboxConfig,
    SandboxResult,
    SandboxType,
    SandboxStatus,
    get_sandbox_manager
)
from .secrets_manager import (
    SecretsManager,
    Secret,
    SecretReference,
    SecretStorageBackend,
    FileSecretStorage,
    EnvironmentSecretStorage,
    get_secrets_manager
)
from .auth import (
    AuthManager,
    User,
    Session,
    Token,
    UserStorageBackend,
    FileUserStorage,
    SessionStorageBackend,
    FileSessionStorage,
    TokenStorageBackend,
    FileTokenStorage,
    get_auth_manager
)
from .audit_logger import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditEventSeverity,
    AuditLogStorageBackend,
    FileAuditLogStorage,
    DatabaseAuditLogStorage,
    get_audit_logger
)

__all__ = [
    # Encryption
    "EncryptionManager",
    "get_encryption_manager",
    
    # Permission Management
    "PermissionManager",
    "Permission",
    "Role",
    "UserPermissions",
    "PermissionLevel",
    "ResourceType",
    "get_permission_manager",
    
    # Sandbox
    "SandboxManager",
    "SandboxConfig",
    "SandboxResult",
    "SandboxType",
    "SandboxStatus",
    "get_sandbox_manager",
    
    # Secrets Management
    "SecretsManager",
    "Secret",
    "SecretReference",
    "SecretStorageBackend",
    "FileSecretStorage",
    "EnvironmentSecretStorage",
    "get_secrets_manager",
    
    # Authentication
    "AuthManager",
    "User",
    "Session",
    "Token",
    "UserStorageBackend",
    "FileUserStorage",
    "SessionStorageBackend",
    "FileSessionStorage",
    "TokenStorageBackend",
    "FileTokenStorage",
    "get_auth_manager",
    
    # Audit Logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditEventSeverity",
    "AuditLogStorageBackend",
    "FileAuditLogStorage",
    "DatabaseAuditLogStorage",
    "get_audit_logger"
]
