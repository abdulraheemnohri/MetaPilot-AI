"""
Database Seed Data for MetaPilot AI

Provides initial data for the database including roles, permissions, and admin user.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, UserRole, UserStatus
from .connection import get_db_context
from ..security.auth import get_password_hash

logger = logging.getLogger(__name__)


class SeedData:
    @staticmethod
    async def seed_admin_user(email: str = "admin@metapilot.ai", username: str = "admin", password: str = "admin123", full_name: str = "Admin User") -> Optional[User]:
        async with get_db_context() as db:
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                logger.info(f"Admin user already exists: {username}")
                return existing_user
            hashed_password = get_password_hash(password)
            admin_user = User(email=email, username=username, hashed_password=hashed_password, full_name=full_name, role=UserRole.ADMIN, status=UserStatus.ACTIVE, is_verified=True, created_at=datetime.utcnow())
            db.add(admin_user)
            await db.flush()
            await db.refresh(admin_user)
            logger.info(f"Created admin user: {username} ({email})")
            return admin_user

    @staticmethod
    async def seed_test_user(email: str = "test@example.com", username: str = "testuser", password: str = "test123", full_name: str = "Test User") -> Optional[User]:
        async with get_db_context() as db:
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalar_one_or_none()
            if existing_user:
                logger.info(f"Test user already exists: {username}")
                return existing_user
            hashed_password = get_password_hash(password)
            test_user = User(email=email, username=username, hashed_password=hashed_password, full_name=full_name, role=UserRole.USER, status=UserStatus.ACTIVE, is_verified=True, created_at=datetime.utcnow())
            db.add(test_user)
            await db.flush()
            await db.refresh(test_user)
            logger.info(f"Created test user: {username} ({email})")
            return test_user

    @staticmethod
    async def seed_all():
        logger.info("Starting database seeding...")
        await SeedData.seed_admin_user()
        await SeedData.seed_test_user()
        logger.info("Database seeding completed")


async def seed_database():
    await SeedData.seed_all()


def sync_seed_database():
    asyncio.run(seed_database())


if __name__ == "__main__":
    asyncio.run(seed_database())