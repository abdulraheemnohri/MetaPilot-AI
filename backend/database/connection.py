"""
Database Connection Management for MetaPilot AI

Provides SQLAlchemy engine, session management, and connection utilities.
Supports both synchronous and asynchronous operations.
"""

import os
import logging
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from ..config import settings

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = settings.DATABASE_URL

# Check if database is SQLite
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Synchronous engine
if IS_SQLITE:
    # SQLite doesn't support async well, use sync engine
    engine: Engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG,
    )

# Async engine
async_engine: AsyncEngine = create_async_engine(
    DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///") if IS_SQLITE else DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Session factories
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Base class for models
Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """
    Get a synchronous database session.
    
    Usage:
        async with get_db_session() as session:
            # Use session
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an asynchronous database session.
    
    Usage:
        async with get_async_db_session() as session:
            # Use session
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()


def init_db():
    """Initialize the database by creating all tables."""
    logger.info("Initializing database")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


async def async_init_db():
    """Asynchronously initialize the database."""
    logger.info("Asynchronously initializing database")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database asynchronously initialized")


def drop_all():
    """Drop all tables (for testing only)."""
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


async def async_drop_all():
    """Asynchronously drop all tables (for testing only)."""
    logger.warning("Asynchronously dropping all database tables")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("All database tables asynchronously dropped")
