"""
MetaPilot AI - Audit Logger

Logs security-relevant events for auditing and compliance.
"""

import logging
import os
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import threading
import traceback

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"
    
    # Authorization events
    PERMISSION_GRANTED = "authz.permission.granted"
    PERMISSION_REVOKED = "authz.permission.revoked"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REMOVED = "authz.role.removed"
    ACCESS_DENIED = "authz.access.denied"
    
    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    
    # Secret management
    SECRET_CREATED = "secret.created"
    SECRET_RETRIEVED = "secret.retrieved"
    SECRET_UPDATED = "secret.updated"
    SECRET_DELETED = "secret.deleted"
    
    # Plugin/sandbox events
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_UNINSTALLED = "plugin.uninstalled"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    SANDBOX_CREATED = "sandbox.created"
    SANDBOX_DESTROYED = "sandbox.destroyed"
    CODE_EXECUTED = "code.executed"
    
    # Provider events
    PROVIDER_ADDED = "provider.added"
    PROVIDER_REMOVED = "provider.removed"
    PROVIDER_CONFIGURED = "provider.configured"
    API_CALL = "api.call"
    
    # Knowledge base events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    KNOWLEDGE_QUERIED = "knowledge.queried"
    
    # System events
    CONFIG_CHANGED = "config.changed"
    BACKUP_CREATED = "backup.created"
    BACKUP_RESTORED = "backup.restored"
    SYSTEM_STARTED = "system.started"
    SYSTEM_SHUTDOWN = "system.shutdown"
    ERROR = "system.error"
    
    # General
    CUSTOM = "custom"


class AuditEventSeverity(Enum):
    """Severity levels for audit events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_type: AuditEventType
    severity: AuditEventSeverity = AuditEventSeverity.INFO
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None
    username: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.event_type, str):
            try:
                self.event_type = AuditEventType(self.event_type)
            except ValueError:
                self.event_type = AuditEventType.CUSTOM
        
        if isinstance(self.severity, str):
            try:
                self.severity = AuditEventSeverity(self.severity)
            except ValueError:
                self.severity = AuditEventSeverity.INFO
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create an AuditEvent from a dictionary."""
        return cls(
            event_type=data.get("event_type", AuditEventType.CUSTOM.value),
            severity=data.get("severity", AuditEventSeverity.INFO.value),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            user_id=data.get("user_id"),
            username=data.get("username"),
            session_id=data.get("session_id"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            action=data.get("action"),
            details=data.get("details", {}),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            stack_trace=data.get("stack_trace"),
            metadata=data.get("metadata", {})
        )
    
    def get_event_id(self) -> str:
        """Generate a unique event ID."""
        event_str = f"{self.timestamp}:{self.event_type.value}:{self.user_id or ''}:{self.resource_id or ''}"
        return hashlib.sha256(event_str.encode()).hexdigest()[:16]


class AuditLogStorageBackend:
    """Abstract base class for audit log storage backends."""
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store an audit event."""
        raise NotImplementedError
    
    def retrieve_event(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event."""
        raise NotImplementedError
    
    def query_events(self, 
                    event_types: Optional[List[AuditEventType]] = None,
                    user_id: Optional[str] = None,
                    resource_type: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    severity: Optional[AuditEventSeverity] = None,
                    limit: int = 100) -> List[AuditEvent]:
        """Query audit events with filters."""
        raise NotImplementedError
    
    def delete_events(self, older_than: Optional[str] = None) -> int:
        """Delete old audit events."""
        raise NotImplementedError


class FileAuditLogStorage(AuditLogStorageBackend):
    """Store audit logs in JSON files."""
    
    def __init__(self, storage_dir: str, max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize file-based audit log storage.
        
        Args:
            storage_dir: Directory to store log files
            max_file_size: Maximum size of each log file in bytes
        """
        self.storage_dir = Path(storage_dir)
        self.max_file_size = max_file_size
        self._current_file: Optional[Path] = None
        self._current_file_size = 0
        self._lock = threading.Lock()
        
        # Initialize storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Find or create current file
        self._initialize_current_file()
    
    def _initialize_current_file(self):
        """Initialize the current log file."""
        # Find the latest file
        log_files = sorted(self.storage_dir.glob("audit_*.json"))
        
        if log_files:
            # Use the last file
            self._current_file = log_files[-1]
            self._current_file_size = self._current_file.stat().st_size
        else:
            # Create new file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self._current_file = self.storage_dir / f"audit_{timestamp}.json"
            self._current_file_size = 0
    
    def _rotate_file_if_needed(self):
        """Rotate to a new file if current file is too large."""
        if self._current_file is None or self._current_file_size >= self.max_file_size:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self._current_file = self.storage_dir / f"audit_{timestamp}.json"
            self._current_file_size = 0
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store an audit event in a JSON file."""
        with self._lock:
            try:
                self._rotate_file_if_needed()
                
                # Convert to JSON and append to file
                event_dict = event.to_dict()
                json_str = json.dumps(event_dict, ensure_ascii=False) + "\n"
                
                with open(self._current_file, 'a', encoding='utf-8') as f:
                    f.write(json_str)
                
                self._current_file_size += len(json_str.encode('utf-8'))
                return True
                
            except Exception as e:
                logger.error(f"Error storing audit event: {e}")
                return False
    
    def retrieve_event(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event by ID."""
        # This is inefficient for file storage, but works
        events = self.query_events()
        for event in events:
            if event.get_event_id() == event_id:
                return event
        return None
    
    def query_events(self, 
                    event_types: Optional[List[AuditEventType]] = None,
                    user_id: Optional[str] = None,
                    resource_type: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    severity: Optional[AuditEventSeverity] = None,
                    limit: int = 100) -> List[AuditEvent]:
        """Query audit events from files."""
        events = []
        
        # Read all log files
        log_files = sorted(self.storage_dir.glob("audit_*.json"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            event = AuditEvent.from_dict(data)
                            
                            # Apply filters
                            if event_types and event.event_type not in event_types:
                                continue
                            if user_id and event.user_id != user_id:
                                continue
                            if resource_type and event.resource_type != resource_type:
                                continue
                            if resource_id and event.resource_id != resource_id:
                                continue
                            if start_time and event.timestamp < start_time:
                                continue
                            if end_time and event.timestamp > end_time:
                                continue
                            if severity and event.severity != severity:
                                continue
                            
                            events.append(event)
                            
                            if len(events) >= limit:
                                return events
                            
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"Error parsing audit event: {e}")
                            continue
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {e}")
                continue
        
        return events
    
    def delete_events(self, older_than: Optional[str] = None) -> int:
        """Delete old audit events."""
        if not older_than:
            return 0
        
        try:
            cutoff = datetime.fromisoformat(older_than)
        except ValueError:
            return 0
        
        deleted_count = 0
        log_files = self.storage_dir.glob("audit_*.json")
        
        for log_file in log_files:
            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    log_file.unlink()
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting log file {log_file}: {e}")
        
        return deleted_count


class DatabaseAuditLogStorage(AuditLogStorageBackend):
    """Store audit logs in a database."""
    
    def __init__(self, connection):
        """
        Initialize database-based audit log storage.
        
        Args:
            connection: Database connection object
        """
        self.connection = connection
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store an audit event in the database."""
        try:
            cursor = self.connection.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    username TEXT,
                    session_id TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    action TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    success INTEGER,
                    error_message TEXT,
                    stack_trace TEXT,
                    metadata TEXT
                )
            """)
            
            # Insert event
            event_id = event.get_event_id()
            cursor.execute("""
                INSERT INTO audit_logs (
                    event_id, event_type, severity, timestamp, user_id, username,
                    session_id, resource_type, resource_id, action, details,
                    ip_address, user_agent, success, error_message, stack_trace, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                event.event_type.value,
                event.severity.value,
                event.timestamp,
                event.user_id,
                event.username,
                event.session_id,
                event.resource_type,
                event.resource_id,
                event.action,
                json.dumps(event.details),
                event.ip_address,
                event.user_agent,
                1 if event.success else 0,
                event.error_message,
                event.stack_trace,
                json.dumps(event.metadata)
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing audit event in database: {e}")
            self.connection.rollback()
            return False
    
    def retrieve_event(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve an audit event from the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM audit_logs WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Parse row into AuditEvent
            return AuditEvent(
                event_type=row[2],
                severity=row[3],
                timestamp=row[4],
                user_id=row[5],
                username=row[6],
                session_id=row[7],
                resource_type=row[8],
                resource_id=row[9],
                action=row[10],
                details=json.loads(row[11] or "{}"),
                ip_address=row[12],
                user_agent=row[13],
                success=bool(row[14]),
                error_message=row[15],
                stack_trace=row[16],
                metadata=json.loads(row[17] or "{}")
            )
            
        except Exception as e:
            logger.error(f"Error retrieving audit event from database: {e}")
            return None
    
    def query_events(self, 
                    event_types: Optional[List[AuditEventType]] = None,
                    user_id: Optional[str] = None,
                    resource_type: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    start_time: Optional[str] = None,
                    end_time: Optional[str] = None,
                    severity: Optional[AuditEventSeverity] = None,
                    limit: int = 100) -> List[AuditEvent]:
        """Query audit events from the database."""
        try:
            cursor = self.connection.cursor()
            
            # Build query
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if event_types:
                placeholders = ",".join("？" * len(event_types))
                query += f" AND event_type IN ({placeholders})"
                params.extend([et.value for et in event_types])
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type)
            
            if resource_id:
                query += " AND resource_id = ?"
                params.append(resource_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if severity:
                query += " AND severity = ?"
                params.append(severity.value)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = AuditEvent(
                    event_type=row[2],
                    severity=row[3],
                    timestamp=row[4],
                    user_id=row[5],
                    username=row[6],
                    session_id=row[7],
                    resource_type=row[8],
                    resource_id=row[9],
                    action=row[10],
                    details=json.loads(row[11] or "{}"),
                    ip_address=row[12],
                    user_agent=row[13],
                    success=bool(row[14]),
                    error_message=row[15],
                    stack_trace=row[16],
                    metadata=json.loads(row[17] or "{}")
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error querying audit events from database: {e}")
            return []
    
    def delete_events(self, older_than: Optional[str] = None) -> int:
        """Delete old audit events from the database."""
        if not older_than:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM audit_logs WHERE timestamp < ?", (older_than,))
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Error deleting audit events from database: {e}")
            self.connection.rollback()
            return 0


class AuditLogger:
    """
    Main audit logger class.
    
    Provides a convenient interface for logging audit events.
    """
    
    def __init__(self, storage_backend: Optional[AuditLogStorageBackend] = None):
        """
        Initialize the audit logger.
        
        Args:
            storage_backend: Backend for storing audit logs
        """
        self.storage_backend = storage_backend or FileAuditLogStorage(
            os.path.join(os.path.expanduser("~"), ".metapilot", "audit_logs")
        )
        self._context: Dict[str, Any] = {}
        self._enabled = True
    
    def enable(self) -> None:
        """Enable audit logging."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable audit logging."""
        self._enabled = False
    
    def set_context(self, **kwargs) -> None:
        """Set context values that will be included in all events."""
        self._context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear the context."""
        self._context.clear()
    
    def log(self, 
            event_type: Union[AuditEventType, str],
            severity: AuditEventSeverity = AuditEventSeverity.INFO,
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None,
            action: Optional[str] = None,
            success: bool = True,
            error_message: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None,
            **kwargs) -> Optional[AuditEvent]:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            severity: Severity level
            resource_type: Type of resource involved
            resource_id: ID of resource involved
            action: Action being performed
            success: Whether the action succeeded
            error_message: Error message if action failed
            details: Additional details
            **kwargs: Additional metadata
        
        Returns:
            The created AuditEvent or None if logging is disabled
        """
        if not self._enabled:
            return None
        
        # Create event
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            success=success,
            error_message=error_message,
            details=details or {},
            **self._context,
            **kwargs
        )
        
        # Add stack trace for errors
        if not success and error_message:
            event.stack_trace = traceback.format_exc()
        
        # Store the event
        self.storage_backend.store_event(event)
        
        return event
    
    def log_auth(self, 
                 event_type: AuditEventType,
                 username: str,
                 success: bool = True,
                 error_message: Optional[str] = None,
                 ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 **kwargs) -> Optional[AuditEvent]:
        """Log an authentication event."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.INFO if success else AuditEventSeverity.WARNING,
            resource_type="authentication",
            action=event_type.value.split(".")[-1],
            success=success,
            error_message=error_message,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    def log_authz(self, 
                  event_type: AuditEventType,
                  user_id: str,
                  resource_type: str,
                  resource_id: str,
                  action: str,
                  success: bool = True,
                  error_message: Optional[str] = None,
                  **kwargs) -> Optional[AuditEvent]:
        """Log an authorization event."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.INFO if success else AuditEventSeverity.WARNING,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            success=success,
            error_message=error_message,
            **kwargs
        )
    
    def log_user_event(self, 
                       event_type: AuditEventType,
                       user_id: str,
                       username: str,
                       success: bool = True,
                       error_message: Optional[str] = None,
                       **kwargs) -> Optional[AuditEvent]:
        """Log a user management event."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.INFO if success else AuditEventSeverity.WARNING,
            user_id=user_id,
            username=username,
            resource_type="user",
            resource_id=user_id,
            success=success,
            error_message=error_message,
            **kwargs
        )
    
    def log_secret_event(self, 
                         event_type: AuditEventType,
                         secret_name: str,
                         user_id: str,
                         success: bool = True,
                         error_message: Optional[str] = None,
                         **kwargs) -> Optional[AuditEvent]:
        """Log a secret management event."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.INFO if success else AuditEventSeverity.ERROR,
            user_id=user_id,
            resource_type="secret",
            resource_id=secret_name,
            action=event_type.value.split(".")[-1],
            success=success,
            error_message=error_message,
            **kwargs
        )
    
    def log_plugin_event(self, 
                         event_type: AuditEventType,
                         plugin_id: str,
                         user_id: str,
                         success: bool = True,
                         error_message: Optional[str] = None,
                         **kwargs) -> Optional[AuditEvent]:
        """Log a plugin-related event."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.INFO if success else AuditEventSeverity.WARNING,
            user_id=user_id,
            resource_type="plugin",
            resource_id=plugin_id,
            action=event_type.value.split(".")[-1],
            success=success,
            error_message=error_message,
            **kwargs
        )
    
    def log_api_call(self, 
                     provider: str,
                     endpoint: str,
                     user_id: str,
                     success: bool = True,
                     error_message: Optional[str] = None,
                     request_data: Optional[Dict[str, Any]] = None,
                     response_data: Optional[Dict[str, Any]] = None,
                     **kwargs) -> Optional[AuditEvent]:
        """Log an API call."""
        # Redact sensitive data from request/response
        safe_request = self._redact_sensitive_data(request_data or {})
        safe_response = self._redact_sensitive_data(response_data or {})
        
        return self.log(
            event_type=AuditEventType.API_CALL,
            severity=AuditEventSeverity.DEBUG,
            user_id=user_id,
            resource_type="api",
            resource_id=provider,
            action=endpoint,
            success=success,
            error_message=error_message,
            details={
                "provider": provider,
                "endpoint": endpoint,
                "request": safe_request,
                "response": safe_response
            },
            **kwargs
        )
    
    def log_system_event(self, 
                         event_type: AuditEventType,
                         message: str,
                         severity: AuditEventSeverity = AuditEventSeverity.INFO,
                         **kwargs) -> Optional[AuditEvent]:
        """Log a system event."""
        return self.log(
            event_type=event_type,
            severity=severity,
            action=message,
            details={"message": message},
            **kwargs
        )
    
    def log_error(self, 
                  error: Exception,
                  event_type: AuditEventType = AuditEventType.ERROR,
                  user_id: Optional[str] = None,
                  resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None,
                  **kwargs) -> Optional[AuditEvent]:
        """Log an error with full stack trace."""
        return self.log(
            event_type=event_type,
            severity=AuditEventSeverity.ERROR,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            success=False,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            **kwargs
        )
    
    @staticmethod
    def _redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive data from a dictionary."""
        sensitive_keys = {"password", "secret", "api_key", "token", "authorization", "auth", "credential"}
        
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = AuditLogger._redact_sensitive_data(value)
            elif isinstance(value, list):
                redacted[key] = [
                    AuditLogger._redact_sensitive_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        
        return redacted
    
    def query_events(self, **kwargs) -> List[AuditEvent]:
        """Query audit events."""
        return self.storage_backend.query_events(**kwargs)


# Global audit logger instance
audit_logger = None


def get_audit_logger(storage_backend: Optional[AuditLogStorageBackend] = None) -> AuditLogger:
    """Get or create the global audit logger."""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger(storage_backend)
    return audit_logger
