"""
MetaPilot AI - Task Queue

Provides a priority-based task queue for the scheduler.
"""

import logging
import threading
import queue
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from heapq import heappush, heappop

logger = logging.getLogger(__name__)


@dataclass
class QueueItem:
    """An item in the priority queue."""
    priority: int
    timestamp: float
    task: Any
    
    def __lt__(self, other):
        # Higher priority first, then older tasks first
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp


class TaskQueue:
    """
    Priority-based task queue.
    
    Tasks with higher priority are executed first.
    Within the same priority, older tasks are executed first (FIFO).
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize the task queue.
        
        Args:
            max_size: Maximum size of the queue
        """
        self.max_size = max_size
        self._queue: List[QueueItem] = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._not_full = threading.Condition(self._lock)
    
    def put(self, task: Any, priority: int = 0) -> bool:
        """
        Add a task to the queue.
        
        Args:
            task: Task to add
            priority: Priority (higher number = higher priority)
        
        Returns:
            True if task was added successfully
        """
        with self._not_full:
            while len(self._queue) >= self.max_size:
                # Wait until there's space
                self._not_full.wait()
            
            item = QueueItem(
                priority=priority,
                timestamp=time.time(),
                task=task
            )
            heappush(self._queue, item)
            
            # Notify that queue is not empty
            with self._not_empty:
                self._not_empty.notify()
        
        return True
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """
        Get the next task from the queue.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            Next task
        
        Raises:
            queue.Empty: If timeout occurs
        """
        with self._not_empty:
            if len(self._queue) == 0:
                if timeout is None:
                    # Wait indefinitely
                    self._not_empty.wait()
                else:
                    # Wait with timeout
                    end_time = time.time() + timeout
                    remaining = timeout
                    while len(self._queue) == 0 and remaining > 0:
                        self._not_empty.wait(remaining)
                        remaining = end_time - time.time()
                    
                    if len(self._queue) == 0:
                        raise queue.Empty("Task queue is empty")
            
            # Get the highest priority task
            item = heappop(self._queue)
            
            # Notify that queue is not full
            with self._not_full:
                self._not_full.notify()
            
            return item.task
    
    def get_nowait(self) -> Any:
        """
        Get the next task without waiting.
        
        Returns:
            Next task
        
        Raises:
            queue.Empty: If queue is empty
        """
        with self._lock:
            if len(self._queue) == 0:
                raise queue.Empty("Task queue is empty")
            
            item = heappop(self._queue)
            
            # Notify that queue is not full
            with self._not_full:
                self._not_full.notify()
            
            return item.task
    
    def qsize(self) -> int:
        """Get the current size of the queue."""
        with self._lock:
            return len(self._queue)
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        with self._lock:
            return len(self._queue) == 0
    
    def full(self) -> bool:
        """Check if the queue is full."""
        with self._lock:
            return len(self._queue) >= self.max_size
    
    def put_nowait(self, task: Any, priority: int = 0) -> bool:
        """
        Add a task to the queue without waiting.
        
        Args:
            task: Task to add
            priority: Priority
        
        Returns:
            True if task was added successfully
        
        Raises:
            queue.Full: If queue is full
        """
        with self._not_full:
            if len(self._queue) >= self.max_size:
                raise queue.Full("Task queue is full")
            
            item = QueueItem(
                priority=priority,
                timestamp=time.time(),
                task=task
            )
            heappush(self._queue, item)
            
            # Notify that queue is not empty
            with self._not_empty:
                self._not_empty.notify()
        
        return True
    
    def clear(self) -> int:
        """
        Clear all tasks from the queue.
        
        Returns:
            Number of tasks cleared
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            return count
    
    def peek(self) -> Any:
        """
        Peek at the next task without removing it.
        
        Returns:
            Next task or None if queue is empty
        """
        with self._lock:
            if len(self._queue) == 0:
                return None
            return self._queue[0].task
    
    def task_done(self) -> None:
        """
        Indicate that a task is done.
        
        This method is provided for compatibility with queue.Queue.
        In this implementation, it does nothing since we don't track
        unfinished tasks separately.
        """
        pass
    
    def join(self) -> None:
        """
        Wait for all tasks to be completed.
        
        This method is provided for compatibility with queue.Queue.
        In this implementation, it does nothing since we don't track
        unfinished tasks separately.
        """
        pass


class PriorityTaskQueue:
    """
    Extended task queue with additional features.
    
    Supports task prioritization, filtering, and batch operations.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize the priority task queue.
        
        Args:
            max_size: Maximum size of the queue
        """
        self._queue = TaskQueue(max_size)
        self._task_map: Dict[str, Any] = {}  # task_id -> task
        self._lock = threading.Lock()
    
    def put(self, task: Any, priority: int = 0, task_id: Optional[str] = None) -> str:
        """
        Add a task to the queue.
        
        Args:
            task: Task to add
            priority: Priority (higher number = higher priority)
            task_id: Optional task ID
        
        Returns:
            Task ID
        """
        if task_id is None:
            import uuid
            task_id = str(uuid.uuid4())
        
        # Store task in map
        with self._lock:
            self._task_map[task_id] = task
        
        # Add to queue
        self._queue.put(task, priority)
        
        return task_id
    
    def get(self, timeout: Optional[float] = None) -> Tuple[str, Any]:
        """
        Get the next task from the queue.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            Tuple of (task_id, task)
        
        Raises:
            queue.Empty: If timeout occurs
        """
        task = self._queue.get(timeout)
        
        # Find task ID
        with self._lock:
            for task_id, stored_task in self._task_map.items():
                if stored_task is task:
                    del self._task_map[task_id]
                    return task_id, task
        
        # Task not found in map, return with generated ID
        return "", task
    
    def remove(self, task_id: str) -> bool:
        """
        Remove a task from the queue.
        
        Args:
            task_id: Task ID to remove
        
        Returns:
            True if task was removed
        """
        with self._lock:
            if task_id in self._task_map:
                task = self._task_map[task_id]
                del self._task_map[task_id]
                
                # Remove from queue (inefficient but works)
                # We need to rebuild the queue without this task
                temp_queue = []
                while True:
                    try:
                        item = self._queue.get_nowait()
                        if item is not task:
                            temp_queue.append(item)
                    except queue.Empty:
                        break
                
                # Restore other tasks
                for item in temp_queue:
                    self._queue.put_nowait(item)
                
                return True
        
        return False
    
    def contains(self, task_id: str) -> bool:
        """Check if a task is in the queue."""
        with self._lock:
            return task_id in self._task_map
    
    def get_by_id(self, task_id: str) -> Optional[Any]:
        """Get a task by ID without removing it."""
        with self._lock:
            return self._task_map.get(task_id)
    
    def qsize(self) -> int:
        """Get the current size of the queue."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()
    
    def full(self) -> bool:
        """Check if the queue is full."""
        return self._queue.full()
    
    def clear(self) -> int:
        """Clear all tasks from the queue."""
        with self._lock:
            self._task_map.clear()
        return self._queue.clear()
