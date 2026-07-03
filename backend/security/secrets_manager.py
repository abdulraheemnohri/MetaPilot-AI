"""
MetaPilot AI - Secrets Manager

Secure storage and management of sensitive secrets (API keys, passwords, etc.).
"""

import logging
import os
import json
import base64
import hashlib
import secrets
import hmac
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union
from pathlib import Path
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


@dataclass
class Secret:
    """Represents a stored secret."""
    name: str
    value: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.created_at, str) and not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if isinstance(self.updated_at, str) and not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()
    
    def is_expired(self) -> bool:
        """Check if the secret has expired."""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except ValueError:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (value is masked)."""
        return {
            "name": self.name,
            "value": "***REDACTED***",
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_expired": self.is_expired()
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with actual value (use with caution)."""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Secret":
        """Create a Secret from a dictionary."""
        return cls(
            name=data.get("name", ""),
            value=data.get("value", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            expires_at=data.get("expires_at"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )


@dataclass
class SecretReference:
    """A reference to a secret without exposing its value."""
    name: str
    version: Optional[str] = None
    
    def __post_init__(self):
        if self.version is None:
            self.version = "latest"


class SecretStorageBackend:
    """Abstract base class for secret storage backends."""
    
    def store_secret(self, secret: Secret) -> bool:
        """Store a secret."""
        raise NotImplementedError
    
    def retrieve_secret(self, name: str, version: Optional[str] = None) -> Optional[Secret]:
        """Retrieve a secret."""
        raise NotImplementedError
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        raise NotImplementedError
    
    def list_secrets(self, tags: Optional[List[str]] = None) -> List[str]:
        """List secret names."""
        raise NotImplementedError
    
    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists."""
        raise NotImplementedError


class FileSecretStorage(SecretStorageBackend):
    """Store secrets in encrypted files."""
    
    def __init__(self, storage_dir: str, encryption_key: str):
        """
        Initialize file-based secret storage.
        
        Args:
            storage_dir: Directory to store secret files
            encryption_key: Key for encrypting secrets
        """
        self.storage_dir = Path(storage_dir)
        self.encryption_key = encryption_key
        self._encryption_manager = None
        
        # Initialize storage directory
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to import encryption
        try:
            from .encryption import EncryptionManager
            self._encryption_manager = EncryptionManager(encryption_key)
        except ImportError:
            logger.warning("Encryption module not available, secrets will be stored unencrypted")
    
    def _get_secret_path(self, name: str) -> Path:
        """Get the file path for a secret."""
        # Sanitize name to be filesystem-safe
        safe_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in name)
        return self.storage_dir / f"{safe_name}.secret"
    
    def store_secret(self, secret: Secret) -> bool:
        """Store a secret in an encrypted file."""
        try:
            secret_path = self._get_secret_path(secret.name)
            
            # Convert to dictionary
            data = secret.to_full_dict()
            
            # Encrypt if available
            if self._encryption_manager and self._encryption_manager.is_available():
                encrypted_data = self._encryption_manager.encrypt(data)
                with open(secret_path, 'w') as f:
                    f.write(encrypted_data)
            else:
                # Store as JSON (unencrypted)
                with open(secret_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(secret_path, 0o600)
            
            logger.info(f"Stored secret: {secret.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing secret {secret.name}: {e}")
            return False
    
    def retrieve_secret(self, name: str, version: Optional[str] = None) -> Optional[Secret]:
        """Retrieve a secret from storage."""
        try:
            secret_path = self._get_secret_path(name)
            
            if not secret_path.exists():
                return None
            
            with open(secret_path, 'r') as f:
                encrypted_data = f.read()
            
            # Try to decrypt
            if self._encryption_manager and self._encryption_manager.is_available():
                try:
                    decrypted_data = self._encryption_manager.decrypt(encrypted_data)
                    if isinstance(decrypted_data, dict):
                        data = decrypted_data
                    else:
                        data = json.loads(decrypted_data)
                except:
                    # Try as JSON
                    data = json.loads(encrypted_data)
            else:
                data = json.loads(encrypted_data)
            
            return Secret.from_dict(data)
            
        except Exception as e:
            logger.error(f"Error retrieving secret {name}: {e}")
            return None
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret."""
        try:
            secret_path = self._get_secret_path(name)
            if secret_path.exists():
                secret_path.unlink()
                logger.info(f"Deleted secret: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting secret {name}: {e}")
            return False
    
    def list_secrets(self, tags: Optional[List[str]] = None) -> List[str]:
        """List all secret names."""
        try:
            secret_files = list(self.storage_dir.glob("*.secret"))
            names = []
            
            for file in secret_files:
                # Extract name from filename
                name = file.stem.replace("_", " ")
                names.append(name)
            
            # Filter by tags if specified
            if tags:
                filtered_names = []
                for name in names:
                    secret = self.retrieve_secret(name)
                    if secret and any(tag in secret.tags for tag in tags):
                        filtered_names.append(name)
                return filtered_names
            
            return names
            
        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return []
    
    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists."""
        secret_path = self._get_secret_path(name)
        return secret_path.exists()


class EnvironmentSecretStorage(SecretStorageBackend):
    """Store secrets in environment variables."""
    
    def __init__(self, prefix: str = "METAPILOT_"):
        """
        Initialize environment-based secret storage.
        
        Args:
            prefix: Prefix for environment variable names
        """
        self.prefix = prefix
    
    def _get_env_name(self, name: str) -> str:
        """Get the environment variable name for a secret."""
        # Sanitize name
        safe_name = "".join(c if c.isalnum() else "_" for c in name.upper())
        return f"{self.prefix}{safe_name}"
    
    def store_secret(self, secret: Secret) -> bool:
        """Store a secret in environment variable."""
        try:
            env_name = self._get_env_name(secret.name)
            os.environ[env_name] = secret.value
            logger.info(f"Stored secret in environment: {env_name}")
            return True
        except Exception as e:
            logger.error(f"Error storing secret in environment: {e}")
            return False
    
    def retrieve_secret(self, name: str, version: Optional[str] = None) -> Optional[Secret]:
        """Retrieve a secret from environment."""
        try:
            env_name = self._get_env_name(name)
            if env_name in os.environ:
                return Secret(
                    name=name,
                    value=os.environ[env_name],
                    description=f"Environment variable: {env_name}"
                )
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret from environment: {e}")
            return None
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret from environment."""
        try:
            env_name = self._get_env_name(name)
            if env_name in os.environ:
                del os.environ[env_name]
                logger.info(f"Deleted secret from environment: {env_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting secret from environment: {e}")
            return False
    
    def list_secrets(self, tags: Optional[List[str]] = None) -> List[str]:
        """List secrets from environment."""
        try:
            names = []
            for key, value in os.environ.items():
                if key.startswith(self.prefix):
                    # Extract name from key
                    name = key[len(self.prefix):].lower().replace("_", " ")
                    names.append(name)
            return names
        except Exception as e:
            logger.error(f"Error listing environment secrets: {e}")
            return []
    
    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists in environment."""
        env_name = self._get_env_name(name)
        return env_name in os.environ


class SecretsManager:
    """
    Main secrets manager class.
    
    Manages storage, retrieval, and rotation of sensitive secrets.
    Supports multiple storage backends (file, environment, etc.).
    """
    
    def __init__(self, storage_backend: Optional[SecretStorageBackend] = None, master_key: Optional[str] = None):
        """
        Initialize the secrets manager.
        
        Args:
            storage_backend: Backend for storing secrets
            master_key: Master key for encryption
        """
        self.storage_backend = storage_backend
        self.master_key = master_key
        self._cache: Dict[str, Secret] = {}
        self._lock = threading.Lock()
        
        # Initialize default storage if not provided
        if self.storage_backend is None:
            temp_dir = os.path.join(os.path.expanduser("~"), ".metapilot", "secrets")
            os.makedirs(temp_dir, exist_ok=True)
            
            if master_key is None:
                master_key = self._generate_master_key(temp_dir)
            
            self.storage_backend = FileSecretStorage(temp_dir, master_key)
            self.master_key = master_key
        
        logger.info("Secrets manager initialized")
    
    def _generate_master_key(self, storage_dir: str) -> str:
        """Generate or load a master encryption key."""
        key_file = os.path.join(storage_dir, "master_key.key")
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error loading master key: {e}")
        
        # Generate new key
        key = secrets.token_hex(32)
        
        try:
            with open(key_file, 'w') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
            logger.info(f"Generated new master key: {key_file}")
        except Exception as e:
            logger.error(f"Error saving master key: {e}")
        
        return key
    
    def store_secret(self, name: str, value: str, description: str = "", 
                     expires_at: Optional[str] = None, tags: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a new secret.
        
        Args:
            name: Secret name
            value: Secret value
            description: Description of the secret
            expires_at: Expiration date (ISO format)
            tags: Tags for categorization
            metadata: Additional metadata
        
        Returns:
            True if stored successfully
        """
        secret = Secret(
            name=name,
            value=value,
            description=description,
            expires_at=expires_at,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        with self._lock:
            if self.storage_backend.store_secret(secret):
                # Update cache
                self._cache[name] = secret
                return True
        
        return False
    
    def retrieve_secret(self, name: str, version: Optional[str] = None) -> Optional[Secret]:
        """
        Retrieve a secret by name.
        
        Args:
            name: Secret name
            version: Specific version (not implemented yet)
        
        Returns:
            Secret object or None if not found
        """
        with self._lock:
            # Check cache first
            if name in self._cache:
                secret = self._cache[name]
                if not secret.is_expired():
                    return secret
                else:
                    # Remove expired from cache
                    del self._cache[name]
            
            # Retrieve from storage
            secret = self.storage_backend.retrieve_secret(name, version)
            if secret:
                if not secret.is_expired():
                    # Update cache
                    self._cache[name] = secret
                    return secret
                else:
                    # Delete expired secret
                    self.delete_secret(name)
            
            return None
    
    def get_secret_value(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get the value of a secret.
        
        Args:
            name: Secret name
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        secret = self.retrieve_secret(name)
        if secret:
            return secret.value
        return default
    
    def delete_secret(self, name: str) -> bool:
        """
        Delete a secret.
        
        Args:
            name: Secret name
        
        Returns:
            True if deleted successfully
        """
        with self._lock:
            if name in self._cache:
                del self._cache[name]
            return self.storage_backend.delete_secret(name)
    
    def update_secret(self, name: str, new_value: Optional[str] = None, 
                      description: Optional[str] = None, expires_at: Optional[str] = None,
                      tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing secret.
        
        Args:
            name: Secret name
            new_value: New value (if None, keeps existing)
            description: New description
            expires_at: New expiration date
            tags: New tags
            metadata: New metadata
        
        Returns:
            True if updated successfully
        """
        secret = self.retrieve_secret(name)
        if not secret:
            return False
        
        # Update fields
        if new_value is not None:
            secret.value = new_value
        if description is not None:
            secret.description = description
        if expires_at is not None:
            secret.expires_at = expires_at
        if tags is not None:
            secret.tags = tags
        if metadata is not None:
            secret.metadata = metadata
        
        secret.updated_at = datetime.utcnow().isoformat()
        
        with self._lock:
            if self.storage_backend.store_secret(secret):
                # Update cache
                self._cache[name] = secret
                return True
        
        return False
    
    def rotate_secret(self, name: str, new_value: str) -> bool:
        """
        Rotate a secret (update its value).
        
        Args:
            name: Secret name
            new_value: New value
        
        Returns:
            True if rotated successfully
        """
        return self.update_secret(name, new_value=new_value)
    
    def list_secrets(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all secrets (metadata only, values are redacted).
        
        Args:
            tags: Filter by tags
        
        Returns:
            List of secret metadata dictionaries
        """
        names = self.storage_backend.list_secrets(tags)
        secrets = []
        
        for name in names:
            secret = self.retrieve_secret(name)
            if secret:
                secrets.append(secret.to_dict())
        
        return secrets
    
    def secret_exists(self, name: str) -> bool:
        """Check if a secret exists."""
        return self.storage_backend.secret_exists(name)
    
    def generate_api_key(self, name: str = "api_key", length: int = 32, 
                        description: str = "", tags: Optional[List[str]] = None) -> str:
        """
        Generate and store a new API key.
        
        Args:
            name: Name for the API key
            length: Length of the key in bytes
            description: Description
            tags: Tags
        
        Returns:
            The generated API key
        """
        key = secrets.token_urlsafe(length)
        self.store_secret(
            name=name,
            value=key,
            description=description or f"API Key generated at {datetime.utcnow().isoformat()}",
            tags=tags or ["api_key", "generated"],
            metadata={"type": "api_key", "length": length}
        )
        return key
    
    def generate_password(self, name: str = "password", length: int = 16,
                         description: str = "", tags: Optional[List[str]] = None) -> str:
        """
        Generate and store a new password.
        
        Args:
            name: Name for the password
            length: Length of the password
            description: Description
            tags: Tags
        
        Returns:
            The generated password
        """
        # Generate a strong password
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        
        self.store_secret(
            name=name,
            value=password,
            description=description or f"Password generated at {datetime.utcnow().isoformat()}",
            tags=tags or ["password", "generated"],
            metadata={"type": "password", "length": length}
        )
        return password
    
    def generate_token(self, name: str = "token", length: int = 32,
                       expires_in: Optional[timedelta] = None,
                       description: str = "", tags: Optional[List[str]] = None) -> str:
        """
        Generate and store a new token.
        
        Args:
            name: Name for the token
            length: Length of the token
            expires_in: Expiration time from now
            description: Description
            tags: Tags
        
        Returns:
            The generated token
        """
        token = secrets.token_urlsafe(length)
        
        expires_at = None
        if expires_in:
            expires_at = (datetime.utcnow() + expires_in).isoformat()
        
        self.store_secret(
            name=name,
            value=token,
            description=description or f"Token generated at {datetime.utcnow().isoformat()}",
            expires_at=expires_at,
            tags=tags or ["token", "generated"],
            metadata={"type": "token", "length": length}
        )
        return token
    
    def verify_token(self, name: str, token: str) -> bool:
        """
        Verify if a token matches the stored value.
        
        Args:
            name: Token name
            token: Token value to verify
        
        Returns:
            True if token matches
        """
        secret = self.retrieve_secret(name)
        if not secret:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(secret.value, token)
    
    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Clean up all expired secrets.
        
        Returns:
            Number of secrets deleted
        """
        count = 0
        names = self.storage_backend.list_secrets()
        
        for name in names:
            secret = self.retrieve_secret(name)
            if secret and secret.is_expired():
                self.delete_secret(name)
                count += 1
        
        logger.info(f"Cleaned up {count} expired secrets")
        return count


# Global secrets manager instance
secrets_manager = None


def get_secrets_manager(storage_backend: Optional[SecretStorageBackend] = None, 
                         master_key: Optional[str] = None) -> SecretsManager:
    """Get or create the global secrets manager."""
    global secrets_manager
    if secrets_manager is None:
        secrets_manager = SecretsManager(storage_backend, master_key)
    return secrets_manager
