"""
MetaPilot AI - Authentication Manager

Handles user authentication, sessions, and tokens.
"""

import logging
import os
import json
import hashlib
import hmac
import secrets
import base64
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class User:
    """Represents a user account."""
    user_id: str
    username: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_login: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.created_at, str) and not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if isinstance(self.updated_at, str) and not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (password hash is included)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "metadata": self.metadata
        }
    
    def to_public_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for public use (no sensitive data)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at,
            "last_login": self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Create a User from a dictionary."""
        return cls(
            user_id=data.get("user_id", ""),
            username=data.get("username", ""),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            display_name=data.get("display_name"),
            is_active=data.get("is_active", True),
            is_superuser=data.get("is_superuser", False),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            last_login=data.get("last_login"),
            metadata=data.get("metadata", {})
        )


@dataclass
class Session:
    """Represents a user session."""
    session_id: str
    user_id: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = field(default_factory=lambda: (datetime.utcnow() + timedelta(days=30)).isoformat())
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_valid: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.created_at, str) and not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if isinstance(self.expires_at, str) and not self.expires_at:
            self.expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except ValueError:
            return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "is_valid": self.is_valid,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data.get("session_id", ""),
            user_id=data.get("user_id", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            expires_at=data.get("expires_at", (datetime.utcnow() + timedelta(days=30)).isoformat()),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            is_valid=data.get("is_valid", True),
            metadata=data.get("metadata", {})
        )


@dataclass
class Token:
    """Represents an authentication token."""
    token: str
    token_hash: str
    user_id: str
    token_type: str = "access"  # access, refresh, api
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    is_valid: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.created_at, str) and not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.token_hash:
            self.token_hash = self._hash_token(self.token)
    
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expires
        except ValueError:
            return True
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Create a hash of a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def verify(self, token: str) -> bool:
        """Verify if a token matches."""
        # Use constant-time comparison
        return hmac.compare_digest(self._hash_token(token), self.token_hash)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_hash": self.token_hash,
            "user_id": self.user_id,
            "token_type": self.token_type,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_valid": self.is_valid,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], token: str = "") -> "Token":
        token_obj = cls(
            token=token,
            token_hash=data.get("token_hash", ""),
            user_id=data.get("user_id", ""),
            token_type=data.get("token_type", "access"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            expires_at=data.get("expires_at"),
            is_valid=data.get("is_valid", True),
            metadata=data.get("metadata", {})
        )
        return token_obj


class UserStorageBackend:
    """Abstract base class for user storage backends."""
    
    def store_user(self, user: User) -> bool:
        raise NotImplementedError
    
    def retrieve_user(self, user_id: str) -> Optional[User]:
        raise NotImplementedError
    
    def retrieve_user_by_username(self, username: str) -> Optional[User]:
        raise NotImplementedError
    
    def retrieve_user_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError
    
    def update_user(self, user: User) -> bool:
        raise NotImplementedError
    
    def delete_user(self, user_id: str) -> bool:
        raise NotImplementedError
    
    def list_users(self) -> List[User]:
        raise NotImplementedError
    
    def user_exists(self, user_id: str) -> bool:
        raise NotImplementedError


class FileUserStorage(UserStorageBackend):
    """Store users in JSON files."""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_path(self, user_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in ".-_" else "_" for c in user_id)
        return self.storage_dir / f"{safe_id}.user.json"
    
    def store_user(self, user: User) -> bool:
        try:
            user_path = self._get_user_path(user.user_id)
            with open(user_path, 'w') as f:
                json.dump(user.to_dict(), f, indent=2)
            os.chmod(user_path, 0o600)
            return True
        except Exception as e:
            logger.error(f"Error storing user {user.user_id}: {e}")
            return False
    
    def retrieve_user(self, user_id: str) -> Optional[User]:
        try:
            user_path = self._get_user_path(user_id)
            if not user_path.exists():
                return None
            with open(user_path, 'r') as f:
                data = json.load(f)
            return User.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None
    
    def retrieve_user_by_username(self, username: str) -> Optional[User]:
        users = self.list_users()
        for user in users:
            if user.username == username:
                return user
        return None
    
    def retrieve_user_by_email(self, email: str) -> Optional[User]:
        users = self.list_users()
        for user in users:
            if user.email == email:
                return user
        return None
    
    def update_user(self, user: User) -> bool:
        return self.store_user(user)
    
    def delete_user(self, user_id: str) -> bool:
        try:
            user_path = self._get_user_path(user_id)
            if user_path.exists():
                user_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def list_users(self) -> List[User]:
        users = []
        for user_file in self.storage_dir.glob("*.user.json"):
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)
                user = User.from_dict(data)
                users.append(user)
            except Exception as e:
                logger.error(f"Error loading user from {user_file}: {e}")
        return users
    
    def user_exists(self, user_id: str) -> bool:
        user_path = self._get_user_path(user_id)
        return user_path.exists()


class SessionStorageBackend:
    """Abstract base class for session storage backends."""
    
    def store_session(self, session: Session) -> bool:
        raise NotImplementedError
    
    def retrieve_session(self, session_id: str) -> Optional[Session]:
        raise NotImplementedError
    
    def update_session(self, session: Session) -> bool:
        raise NotImplementedError
    
    def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        raise NotImplementedError
    
    def session_exists(self, session_id: str) -> bool:
        raise NotImplementedError


class FileSessionStorage(SessionStorageBackend):
    """Store sessions in JSON files."""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in ".-_" else "_" for c in session_id)
        return self.storage_dir / f"{safe_id}.session.json"
    
    def store_session(self, session: Session) -> bool:
        try:
            session_path = self._get_session_path(session.session_id)
            with open(session_path, 'w') as f:
                json.dump(session.to_dict(), f, indent=2)
            os.chmod(session_path, 0o600)
            return True
        except Exception as e:
            logger.error(f"Error storing session {session.session_id}: {e}")
            return False
    
    def retrieve_session(self, session_id: str) -> Optional[Session]:
        try:
            session_path = self._get_session_path(session_id)
            if not session_path.exists():
                return None
            with open(session_path, 'r') as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def update_session(self, session: Session) -> bool:
        return self.store_session(session)
    
    def delete_session(self, session_id: str) -> bool:
        try:
            session_path = self._get_session_path(session_id)
            if session_path.exists():
                session_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Session]:
        sessions = []
        for session_file in self.storage_dir.glob("*.session.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                session = Session.from_dict(data)
                if user_id is None or session.user_id == user_id:
                    sessions.append(session)
            except Exception as e:
                logger.error(f"Error loading session from {session_file}: {e}")
        return sessions
    
    def session_exists(self, session_id: str) -> bool:
        session_path = self._get_session_path(session_id)
        return session_path.exists()


class TokenStorageBackend:
    """Abstract base class for token storage backends."""
    
    def store_token(self, token: Token) -> bool:
        raise NotImplementedError
    
    def retrieve_token(self, token_hash: str) -> Optional[Token]:
        raise NotImplementedError
    
    def retrieve_tokens_by_user(self, user_id: str) -> List[Token]:
        raise NotImplementedError
    
    def update_token(self, token: Token) -> bool:
        raise NotImplementedError
    
    def delete_token(self, token_hash: str) -> bool:
        raise NotImplementedError
    
    def list_tokens(self) -> List[Token]:
        raise NotImplementedError
    
    def token_exists(self, token_hash: str) -> bool:
        raise NotImplementedError


class FileTokenStorage(TokenStorageBackend):
    """Store tokens in JSON files."""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_token_path(self, token_hash: str) -> Path:
        safe_hash = token_hash[:2] + "_" + token_hash[2:]
        return self.storage_dir / f"{safe_hash}.token.json"
    
    def store_token(self, token: Token) -> bool:
        try:
            token_path = self._get_token_path(token.token_hash)
            with open(token_path, 'w') as f:
                json.dump(token.to_dict(), f, indent=2)
            os.chmod(token_path, 0o600)
            return True
        except Exception as e:
            logger.error(f"Error storing token {token.token_hash[:8]}: {e}")
            return False
    
    def retrieve_token(self, token_hash: str) -> Optional[Token]:
        try:
            token_path = self._get_token_path(token_hash)
            if not token_path.exists():
                return None
            with open(token_path, 'r') as f:
                data = json.load(f)
            # We can't recover the original token, but we can create a placeholder
            return Token.from_dict(data, token="")
        except Exception as e:
            logger.error(f"Error retrieving token {token_hash[:8]}: {e}")
            return None
    
    def retrieve_tokens_by_user(self, user_id: str) -> List[Token]:
        tokens = self.list_tokens()
        return [t for t in tokens if t.user_id == user_id]
    
    def update_token(self, token: Token) -> bool:
        return self.store_token(token)
    
    def delete_token(self, token_hash: str) -> bool:
        try:
            token_path = self._get_token_path(token_hash)
            if token_path.exists():
                token_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting token {token_hash[:8]}: {e}")
            return False
    
    def list_tokens(self) -> List[Token]:
        tokens = []
        for token_file in self.storage_dir.glob("*.token.json"):
            try:
                with open(token_file, 'r') as f:
                    data = json.load(f)
                token = Token.from_dict(data, token="")
                tokens.append(token)
            except Exception as e:
                logger.error(f"Error loading token from {token_file}: {e}")
        return tokens
    
    def token_exists(self, token_hash: str) -> bool:
        token_path = self._get_token_path(token_hash)
        return token_path.exists()


class AuthManager:
    """
    Main authentication manager class.
    
    Handles user authentication, session management, and token generation.
    """
    
    def __init__(self, 
                 user_storage: Optional[UserStorageBackend] = None,
                 session_storage: Optional[SessionStorageBackend] = None,
                 token_storage: Optional[TokenStorageBackend] = None,
                 secret_key: Optional[str] = None):
        """
        Initialize the authentication manager.
        
        Args:
            user_storage: Backend for storing users
            session_storage: Backend for storing sessions
            token_storage: Backend for storing tokens
            secret_key: Secret key for signing tokens
        """
        self.user_storage = user_storage or FileUserStorage(
            os.path.join(os.path.expanduser("~"), ".metapilot", "users")
        )
        self.session_storage = session_storage or FileSessionStorage(
            os.path.join(os.path.expanduser("~"), ".metapilot", "sessions")
        )
        self.token_storage = token_storage or FileTokenStorage(
            os.path.join(os.path.expanduser("~"), ".metapilot", "tokens")
        )
        
        if secret_key is None:
            # Generate a secret key if not provided
            secret_key_path = os.path.join(os.path.expanduser("~"), ".metapilot", "auth_secret.key")
            if os.path.exists(secret_key_path):
                with open(secret_key_path, 'r') as f:
                    secret_key = f.read().strip()
            else:
                secret_key = secrets.token_hex(32)
                os.makedirs(os.path.dirname(secret_key_path), exist_ok=True)
                with open(secret_key_path, 'w') as f:
                    f.write(secret_key)
                os.chmod(secret_key_path, 0o600)
        
        self.secret_key = secret_key
        self._lock = threading.Lock()
        
        logger.info("Authentication manager initialized")
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with a salt.
        
        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        import hashlib
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        )
        
        return base64.b64encode(hashed).decode('utf-8'), salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify a password against a hash.
        
        Args:
            password: Password to verify
            hashed_password: Stored hashed password
            salt: Salt used for hashing
        
        Returns:
            True if password matches
        """
        import hashlib
        
        try:
            # Recreate the hash
            hashed = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            
            # Compare with stored hash
            return hmac.compare_digest(
                base64.b64encode(hashed).decode('utf-8'),
                hashed_password
            )
        except Exception:
            return False
    
    def create_user(self, username: str, password: Optional[str] = None,
                    email: Optional[str] = None, display_name: Optional[str] = None,
                    is_superuser: bool = False, metadata: Optional[Dict[str, Any]] = None) -> User:
        """
        Create a new user.
        
        Args:
            username: Username
            password: Password (optional, if not provided, user cannot log in with password)
            email: Email address
            display_name: Display name
            is_superuser: Whether user has superuser privileges
            metadata: Additional metadata
        
        Returns:
            Created user
        """
        user_id = str(secrets.token_hex(8))
        
        # Hash password if provided
        password_hash = None
        salt = None
        if password:
            password_hash, salt = self.hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            is_superuser=is_superuser,
            metadata=metadata or {}
        )
        
        # Store salt in metadata if password was set
        if salt:
            user.metadata["password_salt"] = salt
        
        if self.user_storage.store_user(user):
            logger.info(f"Created new user: {username} ({user_id})")
            return user
        else:
            raise Exception("Failed to store user")
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.user_storage.retrieve_user(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return self.user_storage.retrieve_user_by_username(username)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.user_storage.retrieve_user_by_email(email)
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user properties."""
        user = self.get_user(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow().isoformat()
        
        if self.user_storage.update_user(user):
            logger.info(f"Updated user: {user.username} ({user_id})")
            return user
        
        return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        # First, delete all sessions for this user
        sessions = self.session_storage.list_sessions(user_id)
        for session in sessions:
            self.session_storage.delete_session(session.session_id)
        
        # Delete all tokens for this user
        tokens = self.token_storage.retrieve_tokens_by_user(user_id)
        for token in tokens:
            self.token_storage.delete_token(token.token_hash)
        
        # Finally, delete the user
        return self.user_storage.delete_user(user_id)
    
    def list_users(self) -> List[User]:
        """List all users."""
        return self.user_storage.list_users()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User if authentication succeeds, None otherwise
        """
        user = self.get_user_by_username(username)
        if not user:
            logger.warning(f"Authentication failed: user not found - {username}")
            return None
        
        if not user.password_hash:
            logger.warning(f"Authentication failed: no password set for user - {username}")
            return None
        
        salt = user.metadata.get("password_salt", "")
        if not salt:
            logger.warning(f"Authentication failed: no salt for user - {username}")
            return None
        
        if not self.verify_password(password, user.password_hash, salt):
            logger.warning(f"Authentication failed: invalid password for user - {username}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user is inactive - {username}")
            return None
        
        # Update last login
        user.last_login = datetime.utcnow().isoformat()
        self.user_storage.update_user(user)
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def create_session(self, user_id: str, ip_address: Optional[str] = None, 
                       user_agent: Optional[str] = None, expires_in: Optional[timedelta] = None) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent
            expires_in: Session expiration time
        
        Returns:
            Created session
        """
        session_id = secrets.token_urlsafe(32)
        
        expires_at = None
        if expires_in:
            expires_at = (datetime.utcnow() + expires_in).isoformat()
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if self.session_storage.store_session(session):
            logger.info(f"Created session for user {user_id}: {session_id[:8]}...")
            return session
        else:
            raise Exception("Failed to store session")
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.session_storage.retrieve_session(session_id)
    
    def validate_session(self, session_id: str) -> Optional[Session]:
        """
        Validate a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Session if valid, None otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        if not session.is_valid:
            return None
        
        if session.is_expired():
            # Mark as invalid
            session.is_valid = False
            self.session_storage.update_session(session)
            return None
        
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        session = self.get_session(session_id)
        if session:
            session.is_valid = False
            return self.session_storage.update_session(session)
        return False
    
    def invalidate_all_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User ID
            except_session: Session to keep valid
        
        Returns:
            Number of sessions invalidated
        """
        sessions = self.session_storage.list_sessions(user_id)
        count = 0
        
        for session in sessions:
            if session.session_id != except_session:
                session.is_valid = False
                self.session_storage.update_session(session)
                count += 1
        
        logger.info(f"Invalidated {count} sessions for user {user_id}")
        return count
    
    def generate_token(self, user_id: str, token_type: str = "access",
                       expires_in: Optional[timedelta] = None, metadata: Optional[Dict[str, Any]] = None) -> Token:
        """
        Generate a new authentication token.
        
        Args:
            user_id: User ID
            token_type: Token type (access, refresh, api)
            expires_in: Token expiration time
            metadata: Additional metadata
        
        Returns:
            Generated token
        """
        # Generate a random token
        token_value = secrets.token_urlsafe(32)
        
        expires_at = None
        if expires_in:
            expires_at = (datetime.utcnow() + expires_in).isoformat()
        
        token = Token(
            token=token_value,
            token_hash="",  # Will be set in __post_init__
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        if self.token_storage.store_token(token):
            logger.info(f"Generated {token_type} token for user {user_id}: {token.token[:8]}...")
            return token
        else:
            raise Exception("Failed to store token")
    
    def validate_token(self, token_value: str) -> Optional[Token]:
        """
        Validate an authentication token.
        
        Args:
            token_value: Token value to validate
        
        Returns:
            Token if valid, None otherwise
        """
        # Get all tokens and check each one
        tokens = self.token_storage.list_tokens()
        
        for token in tokens:
            if token.verify(token_value):
                if not token.is_valid:
                    return None
                if token.is_expired():
                    token.is_valid = False
                    self.token_storage.update_token(token)
                    return None
                return token
        
        return None
    
    def invalidate_token(self, token_value: str) -> bool:
        """Invalidate a token."""
        token = self.validate_token(token_value)
        if token:
            token.is_valid = False
            return self.token_storage.update_token(token)
        return False
    
    def invalidate_tokens_by_user(self, user_id: str, token_type: Optional[str] = None) -> int:
        """
        Invalidate all tokens for a user.
        
        Args:
            user_id: User ID
            token_type: Optional token type to filter by
        
        Returns:
            Number of tokens invalidated
        """
        tokens = self.token_storage.retrieve_tokens_by_user(user_id)
        count = 0
        
        for token in tokens:
            if token_type is None or token.token_type == token_type:
                token.is_valid = False
                self.token_storage.update_token(token)
                count += 1
        
        logger.info(f"Invalidated {count} tokens for user {user_id}")
        return count
    
    def refresh_token(self, refresh_token_value: str) -> Optional[Tuple[str, Token]]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token_value: Refresh token value
        
        Returns:
            Tuple of (new_access_token, new_access_token_object) or None
        """
        refresh_token = self.validate_token(refresh_token_value)
        if not refresh_token or refresh_token.token_type != "refresh":
            return None
        
        # Generate new access token
        new_token = self.generate_token(
            user_id=refresh_token.user_id,
            token_type="access",
            expires_in=timedelta(hours=1)
        )
        
        return new_token.token, new_token
    
    def generate_api_key(self, user_id: str, name: str = "", 
                         expires_in: Optional[timedelta] = None) -> str:
        """
        Generate a new API key for a user.
        
        Args:
            user_id: User ID
            name: Name for the API key
            expires_in: Expiration time
        
        Returns:
            Generated API key
        """
        token = self.generate_token(
            user_id=user_id,
            token_type="api",
            expires_in=expires_in,
            metadata={"name": name, "generated_by": "api_key_endpoint"}
        )
        return token.token
    
    def validate_api_key(self, api_key: str) -> Optional[User]:
        """
        Validate an API key and return the associated user.
        
        Args:
            api_key: API key to validate
        
        Returns:
            User if API key is valid, None otherwise
        """
        token = self.validate_token(api_key)
        if token and token.token_type == "api":
            return self.get_user(token.user_id)
        return None
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
        
        Returns:
            True if password was changed successfully
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Verify old password
        salt = user.metadata.get("password_salt", "")
        if not self.verify_password(old_password, user.password_hash or "", salt):
            return False
        
        # Hash new password
        new_hash, new_salt = self.hash_password(new_password)
        
        # Update user
        user.password_hash = new_hash
        user.metadata["password_salt"] = new_salt
        user.updated_at = datetime.utcnow().isoformat()
        
        return self.user_storage.update_user(user)
    
    def set_password(self, user_id: str, new_password: str) -> bool:
        """
        Set a user's password (without verifying old password).
        
        Args:
            user_id: User ID
            new_password: New password
        
        Returns:
            True if password was set successfully
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Hash new password
        new_hash, new_salt = self.hash_password(new_password)
        
        # Update user
        user.password_hash = new_hash
        user.metadata["password_salt"] = new_salt
        user.updated_at = datetime.utcnow().isoformat()
        
        return self.user_storage.update_user(user)


# Global auth manager instance
auth_manager = None


def get_auth_manager(user_storage: Optional[UserStorageBackend] = None,
                      session_storage: Optional[SessionStorageBackend] = None,
                      token_storage: Optional[TokenStorageBackend] = None,
                      secret_key: Optional[str] = None) -> AuthManager:
    """Get or create the global authentication manager."""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager(user_storage, session_storage, token_storage, secret_key)
    return auth_manager
