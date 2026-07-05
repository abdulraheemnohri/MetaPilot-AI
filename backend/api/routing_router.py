"""
Routing Rules Router for MetaPilot AI
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from ..api.auth_router import get_current_user
from ..database.models import SystemConfig
from ..database.connection import get_async_db_session

router = APIRouter(prefix="/routing", tags=["Routing"])

class RoutingRule(BaseModel):
    intent: str
    provider_id: str

@router.get("/rules")
async def get_routing_rules(current_user: dict = Depends(get_current_user)):
    async with get_async_db_session() as session:
        from sqlalchemy import select
        stmt = select(SystemConfig).where(SystemConfig.key == "routing_rules")
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()
        return config.value if config else {}

@router.post("/rules")
async def update_routing_rules(rules: Dict[str, str], current_user: dict = Depends(get_current_user)):
    async with get_async_db_session() as session:
        from sqlalchemy import select
        stmt = select(SystemConfig).where(SystemConfig.key == "routing_rules")
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            config.value = rules
        else:
            config = SystemConfig(key="routing_rules", value=rules)
            session.add(config)

        await session.commit()
        return {"success": True}
