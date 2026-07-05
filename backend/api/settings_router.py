"""
Settings Router for MetaPilot AI
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..api.auth_router import get_current_user
from ..database.models import SystemConfig
from ..database.connection import get_async_db_session

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdate(BaseModel):
    key: str
    value: Any

@router.get("/")
async def get_settings(current_user: dict = Depends(get_current_user)):
    async with get_async_db_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(SystemConfig))
        configs = result.scalars().all()
        return {c.key: c.value for c in configs}

@router.post("/")
async def update_setting(update: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    async with get_async_db_session() as session:
        from sqlalchemy import select
        stmt = select(SystemConfig).where(SystemConfig.key == update.key)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            config.value = update.value
        else:
            config = SystemConfig(key=update.key, value=update.value)
            session.add(config)

        await session.commit()
        return {"success": True, "key": update.key}

@router.get("/defaults")
async def get_default_settings():
    return {
        "parallel_execution": True,
        "max_parallel_tasks": 5,
        "browser_headless": True,
        "security_level": "normal",
        "auto_summarize": True,
        "routing_strategy": "consensus"
    }
