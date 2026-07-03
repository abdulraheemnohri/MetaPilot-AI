"""
MetaPilot AI - Permission Manager

Role-based access control (RBAC) system for MetaPilot AI.
Manages user permissions, roles, and access control.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for different operations."""
    DENIED = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    SUPER_ADMIN = 4


class ResourceType(Enum):
    """Types of resources that can be protected."""
    USER = "user"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    KNOWLEDGE_BASE = "knowledge_base"
    MEMORY = "memory"
    TASK = "task"
    SETTINGS = "settings"
    SYSTEM = "system"
    DOCUMENT = "document"
    PROJECT = "project"
    MODEL = "model"
    ALL = "*"


@dataclass
class Permission:
    """Represents a permission for a specific resource."""
    resource_type: ResourceType
    resource_id: Optional[str] = None  # None means all resources of this type
    level: PermissionLevel = PermissionLevel.READ
    
    def __post_init__(self):
        if isinstance(self.resource_type, str):
            self.resource_type = ResourceType(self.resource_type)
        if isinstance(self.level, int):
            self.level = PermissionLevel(self.level)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "level": self.level.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Permission":
        return cls(
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id"),
            level=data.get("level", 1)
        )
    
    def __hash__(self):
        return hash((self.resource_type.value, self.resource_id or "*", self.level.value))
    
    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return (self.resource_type == other.resource_type and 
                self.resource_id == other.resource_id and 
                self.level == other.level)


@dataclass
class Role:
    """Represents a user role with a set of permissions."""
    name: str
    description: str = ""
    permissions: Set[Permission] = field(default_factory=set)
    is_default: bool = False
    is_system: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "is_default": self.is_default,
            "is_system": self.is_system
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Role":
        permissions = {Permission.from_dict(p) for p in data.get("permissions", [])}
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            permissions=permissions,
            is_default=data.get("is_default", False),
            is_system=data.get("is_system", False)
        )
    
    def add_permission(self, permission: Permission) -> None:
        """Add a permission to this role."""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove a permission from this role."""
        self.permissions.discard(permission)
    
    def has_permission(self, resource_type: ResourceType, resource_id: Optional[str] = None, level: PermissionLevel = PermissionLevel.READ) -> bool:
        """Check if this role has the specified permission."""
        # Check for wildcard permission
        wildcard_perm = Permission(resource_type=ResourceType.ALL, level=level)
        if wildcard_perm in self.permissions:
            return True
        
        # Check for resource type wildcard
        type_wildcard = Permission(resource_type=resource_type, resource_id=None, level=level)
        if type_wildcard in self.permissions:
            return True
        
        # Check for specific resource
        specific_perm = Permission(resource_type=resource_type, resource_id=resource_id, level=level)
        if specific_perm in self.permissions:
            return True
        
        # Check if we have higher level permission
        for perm in self.permissions:
            if perm.resource_type == resource_type and (perm.resource_id is None or perm.resource_id == resource_id):
                if perm.level.value >= level.value:
                    return True
        
        return False


@dataclass
class UserPermissions:
    """Manages permissions for a specific user."""
    user_id: str
    roles: Set[str] = field(default_factory=set)
    direct_permissions: Set[Permission] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "roles": list(self.roles),
            "direct_permissions": [p.to_dict() for p in self.direct_permissions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPermissions":
        direct_permissions = {Permission.from_dict(p) for p in data.get("direct_permissions", [])}
        return cls(
            user_id=data.get("user_id", ""),
            roles=set(data.get("roles", [])),
            direct_permissions=direct_permissions
        )
    
    def add_role(self, role_name: str) -> None:
        """Add a role to this user."""
        self.roles.add(role_name)
    
    def remove_role(self, role_name: str) -> None:
        """Remove a role from this user."""
        self.roles.discard(role_name)
    
    def add_permission(self, permission: Permission) -> None:
        """Add a direct permission to this user."""
        self.direct_permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove a direct permission from this user."""
        self.direct_permissions.discard(permission)


class PermissionManager:
    """
    Main permission manager class.
    
    Manages roles, permissions, and user access control for MetaPilot AI.
    """
    
    # Default roles
    DEFAULT_ROLES = {
        "guest": {
            "description": "Guest user with minimal access",
            "permissions": [],
            "is_default": False,
            "is_system": True
        },
        "user": {
            "description": "Regular user with basic access",
            "permissions": [
                {"resource_type": "user", "level": 2},  # WRITE access to own user data
                {"resource_type": "provider", "level": 1},  # READ access to providers
                {"resource_type": "plugin", "level": 1},  # READ access to plugins
                {"resource_type": "knowledge_base", "level": 1},  # READ access to knowledge
                {"resource_type": "task", "level": 2},  # WRITE access to tasks
                {"resource_type": "settings", "level": 1},  # READ access to settings
            ],
            "is_default": True,
            "is_system": True
        },
        "power_user": {
            "description": "Power user with elevated access",
            "permissions": [
                {"resource_type": "*", "level": 2},  # WRITE access to all
            ],
            "is_default": False,
            "is_system": True
        },
        "admin": {
            "description": "Administrator with full access",
            "permissions": [
                {"resource_type": "*", "level": 3},  # ADMIN access to all
            ],
            "is_default": False,
            "is_system": True
        },
        "super_admin": {
            "description": "Super administrator with all permissions",
            "permissions": [
                {"resource_type": "*", "level": 4},  # SUPER_ADMIN access to all
            ],
            "is_default": False,
            "is_system": True
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the permission manager.
        
        Args:
            config_file: Path to JSON file containing roles and permissions configuration
        """
        self.roles: Dict[str, Role] = {}
        self.user_permissions: Dict[str, UserPermissions] = {}
        self.config_file = config_file
        self._initialized = False
        
        # Initialize with default roles
        self._initialize_default_roles()
        
        # Load from config file if specified
        if config_file:
            self.load_config(config_file)
        
        self._initialized = True
        logger.info("Permission manager initialized")
    
    def _initialize_default_roles(self):
        """Initialize with default roles."""
        for role_name, role_data in self.DEFAULT_ROLES.items():
            permissions = {Permission.from_dict(p) for p in role_data.get("permissions", [])}
            role = Role(
                name=role_name,
                description=role_data.get("description", ""),
                permissions=permissions,
                is_default=role_data.get("is_default", False),
                is_system=role_data.get("is_system", False)
            )
            self.roles[role_name] = role
    
    def create_role(self, name: str, description: str = "", permissions: Optional[List[Permission]] = None, is_system: bool = False) -> Role:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            permissions: List of initial permissions
            is_system: Whether this is a system role
        
        Returns:
            The created role
        """
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")
        
        if permissions is None:
            permissions = []
        
        role = Role(
            name=name,
            description=description,
            permissions=set(permissions),
            is_system=is_system
        )
        
        self.roles[name] = role
        logger.info(f"Created new role: {name}")
        
        if self.config_file:
            self.save_config()
        
        return role
    
    def delete_role(self, name: str) -> bool:
        """
        Delete a role.
        
        Args:
            name: Role name to delete
        
        Returns:
            True if deleted successfully
        """
        if name not in self.roles:
            return False
        
        if self.roles[name].is_system:
            raise ValueError(f"Cannot delete system role: {name}")
        
        del self.roles[name]
        logger.info(f"Deleted role: {name}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.roles.get(name)
    
    def list_roles(self) -> List[Role]:
        """List all roles."""
        return list(self.roles.values())
    
    def add_permission_to_role(self, role_name: str, permission: Permission) -> bool:
        """
        Add a permission to a role.
        
        Args:
            role_name: Name of the role
            permission: Permission to add
        
        Returns:
            True if added successfully
        """
        role = self.roles.get(role_name)
        if not role:
            return False
        
        role.add_permission(permission)
        logger.info(f"Added permission to role {role_name}: {permission.resource_type.value}/{permission.resource_id or '*'}/{permission.level.name}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def remove_permission_from_role(self, role_name: str, permission: Permission) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            role_name: Name of the role
            permission: Permission to remove
        
        Returns:
            True if removed successfully
        """
        role = self.roles.get(role_name)
        if not role:
            return False
        
        role.remove_permission(permission)
        logger.info(f"Removed permission from role {role_name}: {permission.resource_type.value}/{permission.resource_id or '*'}/{permission.level.name}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role_name: Role name to assign
        
        Returns:
            True if assigned successfully
        """
        if role_name not in self.roles:
            return False
        
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = UserPermissions(user_id=user_id)
        
        self.user_permissions[user_id].add_role(role_name)
        logger.info(f"Assigned role {role_name} to user {user_id}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: User ID
            role_name: Role name to remove
        
        Returns:
            True if removed successfully
        """
        if user_id not in self.user_permissions:
            return False
        
        self.user_permissions[user_id].remove_role(role_name)
        logger.info(f"Removed role {role_name} from user {user_id}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def assign_permission_to_user(self, user_id: str, permission: Permission) -> bool:
        """
        Assign a direct permission to a user.
        
        Args:
            user_id: User ID
            permission: Permission to assign
        
        Returns:
            True if assigned successfully
        """
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = UserPermissions(user_id=user_id)
        
        self.user_permissions[user_id].add_permission(permission)
        logger.info(f"Assigned permission to user {user_id}: {permission.resource_type.value}/{permission.resource_id or '*'}/{permission.level.name}")
        
        if self.config_file:
            self.save_config()
        
        return True
    
    def check_permission(self, user_id: str, resource_type: Union[ResourceType, str], resource_id: Optional[str] = None, level: Union[PermissionLevel, int] = PermissionLevel.READ) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            resource_type: Resource type to check
            resource_id: Specific resource ID (None for all resources of type)
            level: Required permission level
        
        Returns:
            True if user has the permission
        """
        if isinstance(resource_type, str):
            resource_type = ResourceType(resource_type)
        if isinstance(level, int):
            level = PermissionLevel(level)
        
        # Get user permissions
        user_perms = self.user_permissions.get(user_id)
        if not user_perms:
            # If user has no specific permissions, check default role
            default_role = self.get_default_role()
            if default_role:
                return default_role.has_permission(resource_type, resource_id, level)
            return False
        
        # Check direct permissions first
        for perm in user_perms.direct_permissions:
            if perm.resource_type == resource_type and (perm.resource_id is None or perm.resource_id == resource_id):
                if perm.level.value >= level.value:
                    return True
        
        # Check role permissions
        for role_name in user_perms.roles:
            role = self.roles.get(role_name)
            if role and role.has_permission(resource_type, resource_id, level):
                return True
        
        return False
    
    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user (from roles and direct permissions).
        
        Args:
            user_id: User ID
        
        Returns:
            Set of all permissions
        """
        all_permissions: Set[Permission] = set()
        
        user_perms = self.user_permissions.get(user_id)
        if not user_perms:
            default_role = self.get_default_role()
            if default_role:
                return default_role.permissions.copy()
            return set()
        
        # Add direct permissions
        all_permissions.update(user_perms.direct_permissions)
        
        # Add role permissions
        for role_name in user_perms.roles:
            role = self.roles.get(role_name)
            if role:
                all_permissions.update(role.permissions)
        
        return all_permissions
    
    def get_default_role(self) -> Optional[Role]:
        """Get the default role."""
        for role in self.roles.values():
            if role.is_default:
                return role
        return None
    
    def save_config(self, path: Optional[str] = None) -> bool:
        """
        Save the current configuration to a file.
        
        Args:
            path: Path to save (uses config_file if not specified)
        
        Returns:
            True if saved successfully
        """
        save_path = path or self.config_file
        if not save_path:
            return False
        
        try:
            config = {
                "roles": {name: role.to_dict() for name, role in self.roles.items() if not role.is_system},
                "user_permissions": {user_id: up.to_dict() for user_id, up in self.user_permissions.items()}
            }
            
            with open(save_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved permission configuration to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def load_config(self, path: Optional[str] = None) -> bool:
        """
        Load configuration from a file.
        
        Args:
            path: Path to load (uses config_file if not specified)
        
        Returns:
            True if loaded successfully
        """
        load_path = path or self.config_file
        if not load_path:
            return False
        
        try:
            with open(load_path, 'r') as f:
                config = json.load(f)
            
            # Load roles
            for role_name, role_data in config.get("roles", {}).items():
                role = Role.from_dict(role_data)
                self.roles[role_name] = role
            
            # Load user permissions
            for user_id, user_data in config.get("user_permissions", {}).items():
                user_perms = UserPermissions.from_dict(user_data)
                self.user_permissions[user_id] = user_perms
            
            logger.info(f"Loaded permission configuration from {load_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False


# Global permission manager instance
permission_manager = None


def get_permission_manager(config_file: Optional[str] = None) -> PermissionManager:
    """Get or create the global permission manager."""
    global permission_manager
    if permission_manager is None:
        permission_manager = PermissionManager(config_file)
    return permission_manager
