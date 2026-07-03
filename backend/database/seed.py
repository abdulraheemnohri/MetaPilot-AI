"""
Database Seed Data for MetaPilot AI

Provides initial data for the database including roles, permissions, and admin user.
"""

import logging
from typing import Optional
import bcrypt

from sqlalchemy.orm import Session

from .models import (
    User,
    UserRole,
    Permission,
    RolePermission,
    UserPermission,
)
from .connection import SessionLocal, engine

logger = logging.getLogger(__name__)


# Default permissions
DEFAULT_PERMISSIONS = [
    {
        "name": "Create User",
        "code": "user:create",
        "category": "User Management",
        "description": "Create new users",
    },
    {
        "name": "Read User",
        "code": "user:read",
        "category": "User Management",
        "description": "View user information",
    },
    {
        "name": "Update User",
        "code": "user:update",
        "category": "User Management",
        "description": "Update user information",
    },
    {
        "name": "Delete User",
        "code": "user:delete",
        "category": "User Management",
        "description": "Delete users",
    },
    {
        "name": "List Users",
        "code": "user:list",
        "category": "User Management",
        "description": "List all users",
    },
    {
        "name": "Create Role",
        "code": "role:create",
        "category": "Role Management",
        "description": "Create new roles",
    },
    {
        "name": "Read Role",
        "code": "role:read",
        "category": "Role Management",
        "description": "View role information",
    },
    {
        "name": "Update Role",
        "code": "role:update",
        "category": "Role Management",
        "description": "Update role information",
    },
    {
        "name": "Delete Role",
        "code": "role:delete",
        "category": "Role Management",
        "description": "Delete roles",
    },
    {
        "name": "List Roles",
        "code": "role:list",
        "category": "Role Management",
        "description": "List all roles",
    },
    {
        "name": "Create Permission",
        "code": "permission:create",
        "category": "Permission Management",
        "description": "Create new permissions",
    },
    {
        "name": "Read Permission",
        "code": "permission:read",
        "category": "Permission Management",
        "description": "View permission information",
    },
    {
        "name": "Update Permission",
        "code": "permission:update",
        "category": "Permission Management",
        "description": "Update permission information",
    },
    {
        "name": "Delete Permission",
        "code": "permission:delete",
        "category": "Permission Management",
        "description": "Delete permissions",
    },
    {
        "name": "List Permissions",
        "code": "permission:list",
        "category": "Permission Management",
        "description": "List all permissions",
    },
    {
        "name": "Manage Permissions",
        "code": "permission:manage",
        "category": "Permission Management",
        "description": "Assign permissions to roles and users",
    },
    {
        "name": "Create Conversation",
        "code": "conversation:create",
        "category": "Conversation",
        "description": "Create new conversations",
    },
    {
        "name": "Read Conversation",
        "code": "conversation:read",
        "category": "Conversation",
        "description": "View conversations",
    },
    {
        "name": "Update Conversation",
        "code": "conversation:update",
        "category": "Conversation",
        "description": "Update conversations",
    },
    {
        "name": "Delete Conversation",
        "code": "conversation:delete",
        "category": "Conversation",
        "description": "Delete conversations",
    },
    {
        "name": "List Conversations",
        "code": "conversation:list",
        "category": "Conversation",
        "description": "List all conversations",
    },
    {
        "name": "Use AI",
        "code": "ai:use",
        "category": "AI",
        "description": "Use AI for text generation and tasks",
    },
    {
        "name": "Manage Models",
        "code": "model:manage",
        "category": "AI",
        "description": "Manage AI models and providers",
    },
    {
        "name": "Manage Knowledge",
        "code": "knowledge:manage",
        "category": "Knowledge",
        "description": "Manage knowledge base documents",
    },
    {
        "name": "Manage Tasks",
        "code": "task:manage",
        "category": "Tasks",
        "description": "Create and manage scheduled tasks",
    },
    {
        "name": "Manage Plugins",
        "code": "plugin:manage",
        "category": "Plugins",
        "description": "Install and manage plugins",
    },
    {
        "name": "Manage Projects",
        "code": "project:manage",
        "category": "Projects",
        "description": "Create and manage projects",
    },
    {
        "name": "View Audit Logs",
        "code": "audit:view",
        "category": "Audit",
        "description": "View audit logs",
    },
    {
        "name": "Manage Settings",
        "code": "settings:manage",
        "category": "Settings",
        "description": "Manage application settings",
    },
    {
        "name": "Access Admin Panel",
        "code": "admin:access",
        "category": "Admin",
        "description": "Access admin panel and settings",
    },
]

# Default roles with their permissions
DEFAULT_ROLES = {
    "superadmin": {
        "name": "Super Admin",
        "description": "Full access to all features and settings",
        "is_default": False,
        "permissions": [p["code"] for p in DEFAULT_PERMISSIONS],
    },
    "admin": {
        "name": "Admin",
        "description": "Administrative access with most features",
        "is_default": False,
        "permissions": [
            "user:create",
            "user:read",
            "user:update",
            "user:list",
            "role:read",
            "role:list",
            "permission:read",
            "permission:list",
            "conversation:create",
            "conversation:read",
            "conversation:update",
            "conversation:delete",
            "conversation:list",
            "ai:use",
            "model:manage",
            "knowledge:manage",
            "task:manage",
            "plugin:manage",
            "project:manage",
            "audit:view",
            "settings:manage",
            "admin:access",
        ],
    },
    "user": {
        "name": "User",
        "description": "Regular user with basic access",
        "is_default": True,
        "permissions": [
            "user:read",
            "user:update",
            "conversation:create",
            "conversation:read",
            "conversation:update",
            "conversation:delete",
            "conversation:list",
            "ai:use",
            "knowledge:manage",
            "task:manage",
            "plugin:manage",
            "project:manage",
        ],
    },
    "guest": {
        "name": "Guest",
        "description": "Limited access for guests",
        "is_default": False,
        "permissions": [
            "ai:use",
        ],
    },
}


class DatabaseSeeder:
    """Handles database seeding."""
    
    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session or SessionLocal()
    
    def seed(self):
        """Seed the database with initial data."""
        logger.info("Starting database seeding")
        
        try:
            # Seed permissions
            self._seed_permissions()
            
            # Seed roles
            self._seed_roles()
            
            # Seed admin user
            self._seed_admin_user()
            
            logger.info("Database seeding completed successfully")
            return True
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            self.db_session.rollback()
            return False
        finally:
            if not self.db_session.info.get("external"):
                self.db_session.close()
    
    def _seed_permissions(self):
        """Seed permissions."""
        logger.info("Seeding permissions")
        
        existing_permissions = self.db_session.query(Permission).all()
        existing_codes = {p.code for p in existing_permissions}
        
        for perm_data in DEFAULT_PERMISSIONS:
            if perm_data["code"] not in existing_codes:
                permission = Permission(
                    name=perm_data["name"],
                    code=perm_data["code"],
                    description=perm_data["description"],
                    category=perm_data["category"],
                )
                self.db_session.add(permission)
                logger.debug(f"Added permission: {perm_data['code']}")
        
        self.db_session.commit()
    
    def _seed_roles(self):
        """Seed roles and their permissions."""
        logger.info("Seeding roles")
        
        # Get all permissions
        permissions = self.db_session.query(Permission).all()
        permission_map = {p.code: p for p in permissions}
        
        for role_name, role_data in DEFAULT_ROLES.items():
            # Check if role exists
            existing_role = self.db_session.query(UserRole).filter(
                UserRole.name == role_name
            ).first()
            
            if existing_role:
                logger.debug(f"Role '{role_name}' already exists")
                continue
            
            # Create role
            role = UserRole(
                name=role_name,
                description=role_data["description"],
                is_default=role_data["is_default"],
            )
            self.db_session.add(role)
            self.db_session.flush()
            
            # Assign permissions
            for perm_code in role_data["permissions"]:
                if perm_code in permission_map:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission_map[perm_code].id,
                    )
                    self.db_session.add(role_permission)
                    logger.debug(f"Assigned permission '{perm_code}' to role '{role_name}'")
            
            logger.info(f"Created role: {role_name}")
        
        self.db_session.commit()
    
    def _seed_admin_user(self):
        """Seed the admin user."""
        logger.info("Seeding admin user")
        
        # Check if admin user exists
        admin_user = self.db_session.query(User).filter(
            User.username == "admin"
        ).first()
        
        if admin_user:
            logger.debug("Admin user already exists")
            return
        
        # Get admin role
        admin_role = self.db_session.query(UserRole).filter(
            UserRole.name == "superadmin"
        ).first()
        
        if not admin_role:
            admin_role = self.db_session.query(UserRole).filter(
                UserRole.name == "admin"
            ).first()
        
        # Hash password
        password_hash = self._hash_password("admin123")
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@metapilot.ai",
            hashed_password=password_hash,
            full_name="Admin User",
            is_active=True,
            is_verified=True,
            role=UserRole.SUPERADMIN.value if admin_role and admin_role.name == "superadmin" else UserRole.ADMIN.value,
        )
        
        self.db_session.add(admin_user)
        self.db_session.commit()
        
        logger.info("Created admin user with username: admin and password: admin123")
        logger.warning("Please change the admin password immediately!")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    
    def clear(self):
        """Clear all seed data (for testing)."""
        logger.warning("Clearing all seed data")
        
        # Delete all data in reverse order to respect foreign keys
        self.db_session.query(UserPermission).delete()
        self.db_session.query(RolePermission).delete()
        self.db_session.query(User).delete()
        self.db_session.query(UserRole).delete()
        self.db_session.query(Permission).delete()
        
        self.db_session.commit()
        logger.info("All seed data cleared")


def seed_database():
    """Seed the database with initial data."""
    seeder = DatabaseSeeder()
    return seeder.seed()


def clear_seed_data():
    """Clear all seed data."""
    seeder = DatabaseSeeder()
    seeder.clear()


if __name__ == "__main__":
    seed_database()
