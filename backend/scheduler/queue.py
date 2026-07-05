"""
Priority Queue for MetaPilot AI
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass(order=True)
class QueuedTask:
    priority: int
    task_id: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)
    timestamp: float = field(compare=False)

class TaskQueue:
    def __init__(self):
        self._queue = asyncio.PriorityQueue()
        self._all_tasks = {}

    async def put(self, task_id: str, payload: Dict[str, Any], priority: int = 10):
        import time
        item = QueuedTask(priority=priority, task_id=task_id, payload=payload, timestamp=time.time())
        self._all_tasks[task_id] = item
        await self._queue.put(item)

    async def get(self) -> QueuedTask:
        item = await self._queue.get()
        return item

    def size(self) -> int:
        return self._queue.qsize()

task_queue = TaskQueue()
