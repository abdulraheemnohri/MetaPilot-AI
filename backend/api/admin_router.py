"""
Admin Router for MetaPilot AI
"""

import logging
import psutil
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from ..api.auth_router import get_current_user
from ..security.permission_manager import check_permission
from ..providers.registry import provider_registry
from ..scheduler.queue import task_queue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
async def get_system_stats(current_user: dict = Depends(get_current_user)):
    check_permission(current_user, "admin:read")

    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()

    return {
        "cpu": cpu_usage,
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        },
        "active_providers": len(provider_registry.providers),
        "queue_size": task_queue.size()
    }

@router.get("/providers/health")
async def get_providers_health(current_user: dict = Depends(get_current_user)):
    check_permission(current_user, "admin:read")

    health = {}
    for pid, registered in provider_registry.providers.items():
        # Simple health check placeholder
        health[pid] = "healthy"

    return health
