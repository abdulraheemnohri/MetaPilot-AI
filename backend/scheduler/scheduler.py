"""
Task Scheduler for MetaPilot AI
"""

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from .queue import task_queue
from .worker import get_worker_pool

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 30
    NORMAL = 20
    HIGH = 10

class Task:
    def __init__(self, task_id: str, name: str):
        self.task_id = task_id
        self.name = name
        self.status = TaskStatus.PENDING

class TaskResult:
    pass

class TaskScheduler:
    def __init__(self):
        self.worker_pool = get_worker_pool()
        self._running = False

    async def start(self):
        if self._running: return
        self._running = True
        logger.info("Task Scheduler started.")
        asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        while self._running:
            try:
                queued_task = await task_queue.get()
                # Execute via worker pool
                self.worker_pool.submit(
                    queued_task.payload["function"],
                    *queued_task.payload.get("args", ()),
                    **queued_task.payload.get("kwargs", {})
                )
            except Exception:
                await asyncio.sleep(1)

    async def schedule(self, function: Callable, name: str, priority: int = 10, *args, **kwargs):
        task_id = f"task_{datetime.utcnow().timestamp()}"
        payload = {"function": function, "name": name, "args": args, "kwargs": kwargs}
        await task_queue.put(task_id, payload, priority)
        return task_id

task_scheduler = TaskScheduler()

def get_task_scheduler():
    return task_scheduler
