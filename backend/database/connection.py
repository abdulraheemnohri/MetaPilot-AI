"""
Database Connection for MetaPilot AI

Handles SQLAlchemy database connection and session management.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_scoped_session
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

DATABASE_URL = settings.DATABASE_URL

if DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///"), echo=settings.DEBUG, future=True)
else:
    engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG, pool_size=settings.DATABASE_POOL_SIZE, max_overflow=settings.DATABASE_MAX_OVERFLOW, pool_pre_ping=True)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False)

async_scoped = async_scoped_session(async_session_maker, scopefunc=asynccontextmanager)


async def get_db() -> AsyncSession:
    async with async_scoped() as session:
        yield session


async def init_db():
    try:
        if DATABASE_URL.startswith("sqlite"):
            import os
            db_path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db():
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


@asynccontextmanager
async def get_db_context():
    async with async_scoped() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()