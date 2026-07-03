"""
MetaPilot AI - Task Scheduler

Manages scheduled tasks and their execution.
"""

import logging
import os
import json
import time
import threading
import queue
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path
import traceback

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Task:
    """Represents a scheduled task."""
    task_id: str
    name: str
    function: Callable
    args: Tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    scheduled_time: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout: Optional[float] = None  # seconds
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.priority, int):
            self.priority = TaskPriority(self.priority)
        if isinstance(self.status, str):
            try:
                self.status = TaskStatus(self.status)
            except ValueError:
                self.status = TaskStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        # Note: function is not serialized
        return {
            "task_id": self.task_id,
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "priority": self.priority.value,
            "status": self.status.value,
            "scheduled_time": self.scheduled_time,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], function: Callable) -> "Task":
        """Create a Task from a dictionary."""
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            function=function,
            args=tuple(data.get("args", [])),
            kwargs=data.get("kwargs", {}),
            priority=TaskPriority(data.get("priority", 1)),
            status=TaskStatus(data.get("status", "pending")),
            scheduled_time=data.get("scheduled_time"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 5.0),
            metadata=data.get("metadata", {})
        )
    
    def is_ready(self) -> bool:
        """Check if the task is ready to run."""
        if self.status != TaskStatus.PENDING and self.status != TaskStatus.SCHEDULED:
            return False
        
        if self.scheduled_time:
            try:
                scheduled = datetime.fromisoformat(self.scheduled_time)
                return datetime.utcnow() >= scheduled
            except ValueError:
                return True
        
        return True
    
    def is_finished(self) -> bool:
        """Check if the task has finished."""
        return self.status in [
            TaskStatus.COMPLETED, 
            TaskStatus.FAILED, 
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT
        ]


@dataclass
class TaskResult:
    """Represents the result of a task execution."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        return cls(
            task_id=data.get("task_id", ""),
            status=TaskStatus(data.get("status", "pending")),
            result=data.get("result"),
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            retry_count=data.get("retry_count", 0),
            metadata=data.get("metadata", {})
        )


class TaskStorageBackend:
    """Abstract base class for task storage backends."""
    
    def store_task(self, task: Task) -> bool:
        raise NotImplementedError
    
    def retrieve_task(self, task_id: str) -> Optional[Task]:
        raise NotImplementedError
    
    def update_task(self, task: Task) -> bool:
        raise NotImplementedError
    
    def delete_task(self, task_id: str) -> bool:
        raise NotImplementedError
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        raise NotImplementedError
    
    def list_ready_tasks(self) -> List[Task]:
        raise NotImplementedError


class MemoryTaskStorage(TaskStorageBackend):
    """Store tasks in memory."""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
    
    def store_task(self, task: Task) -> bool:
        with self._lock:
            self._tasks[task.task_id] = task
        return True
    
    def retrieve_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)
    
    def update_task(self, task: Task) -> bool:
        with self._lock:
            if task.task_id in self._tasks:
                self._tasks[task.task_id] = task
                return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                return True
        return False
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
        
        if status:
            return [t for t in tasks if t.status == status]
        return tasks
    
    def list_ready_tasks(self) -> List[Task]:
        with self._lock:
            tasks = list(self._tasks.values())
        return [t for t in tasks if t.is_ready()]


class FileTaskStorage(TaskStorageBackend):
    """Store tasks in JSON files."""
    
    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_task_path(self, task_id: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in ".-_" else "_" for c in task_id)
        return self.storage_dir / f"{safe_id}.task.json"
    
    def store_task(self, task: Task) -> bool:
        try:
            task_path = self._get_task_path(task.task_id)
            # Note: function is not serialized
            data = task.to_dict()
            with open(task_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error storing task {task.task_id}: {e}")
            return False
    
    def retrieve_task(self, task_id: str) -> Optional[Task]:
        try:
            task_path = self._get_task_path(task_id)
            if not task_path.exists():
                return None
            
            with open(task_path, 'r') as f:
                data = json.load(f)
            
            # We can't deserialize the function, so return None
            # This is a limitation of file storage
            logger.warning("Cannot deserialize task function from file storage")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving task {task_id}: {e}")
            return None
    
    def update_task(self, task: Task) -> bool:
        return self.store_task(task)
    
    def delete_task(self, task_id: str) -> bool:
        try:
            task_path = self._get_task_path(task_id)
            if task_path.exists():
                task_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False
    
    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        # File storage cannot properly deserialize tasks with functions
        logger.warning("Cannot list tasks with functions from file storage")
        return []
    
    def list_ready_tasks(self) -> List[Task]:
        return self.list_tasks()


class TaskScheduler:
    """
    Main task scheduler class.
    
    Manages scheduling and execution of tasks.
    """
    
    def __init__(self, 
                 storage_backend: Optional[TaskStorageBackend] = None,
                 num_workers: int = 4,
                 max_queue_size: int = 1000):
        """
        Initialize the task scheduler.
        
        Args:
            storage_backend: Backend for storing tasks
            num_workers: Number of worker threads
            max_queue_size: Maximum size of the task queue
        """
        self.storage_backend = storage_backend or MemoryTaskStorage()
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size
        
        self._task_queue = queue.PriorityQueue(maxsize=max_queue_size)
        self._running = False
        self._workers: List[threading.Thread] = []
        self._lock = threading.Lock()
        self._results: Dict[str, TaskResult] = {}
        self._callbacks: Dict[str, List[Callable[[TaskResult], None]]] = {}
        
        logger.info(f"Task scheduler initialized with {num_workers} workers")
    
    def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        
        # Start worker threads
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"Started {self.num_workers} worker threads")
    
    def stop(self, wait: bool = True, timeout: float = 5.0) -> None:
        """
        Stop the scheduler.
        
        Args:
            wait: Whether to wait for workers to finish
            timeout: Maximum time to wait for workers
        """
        if not self._running:
            return
        
        self._running = False
        
        # Add poison pills to stop workers
        for _ in range(self.num_workers):
            try:
                self._task_queue.put((0, None))  # None is the poison pill
            except queue.Full:
                pass
        
        if wait:
            for worker in self._workers:
                worker.join(timeout=timeout)
        
        logger.info("Task scheduler stopped")
    
    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while self._running:
            try:
                # Get next task with priority
                priority, task = self._task_queue.get(timeout=1.0)
                
                if task is None:
                    # Poison pill, exit
                    self._task_queue.task_done()
                    break
                
                # Execute the task
                self._execute_task(task)
                self._task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
    
    def _execute_task(self, task: Task) -> None:
        """Execute a single task."""
        start_time = time.time()
        
        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow().isoformat()
            self.storage_backend.update_task(task)
            
            # Execute the function
            result = task.function(*task.args, **task.kwargs)
            
            # Create result
            execution_time = time.time() - start_time
            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=execution_time,
                started_at=task.started_at,
                completed_at=datetime.utcnow().isoformat(),
                retry_count=task.retry_count,
                metadata=task.metadata
            )
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.completed_at = task_result.completed_at
            self.storage_backend.update_task(task)
            
            # Store result
            with self._lock:
                self._results[task.task_id] = task_result
            
            # Call callbacks
            self._call_callbacks(task.task_id, task_result)
            
            logger.info(f"Task completed: {task.name} ({task.task_id})")
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Check if we should retry
            should_retry = (
                task.retry_count < task.max_retries and
                task.status not in [TaskStatus.CANCELLED, TaskStatus.TIMEOUT]
            )
            
            if should_retry:
                new_status = TaskStatus.SCHEDULED
                task.retry_count += 1
                
                # Calculate delay (exponential backoff)
                delay = min(task.retry_delay * (2 ** task.retry_count), 300)  # Max 5 minutes
                task.scheduled_time = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
                
                # Re-queue the task
                self.storage_backend.update_task(task)
                self._task_queue.put((task.priority.value, task))
                
                task_result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.SCHEDULED,
                    error=str(e),
                    execution_time=execution_time,
                    started_at=task.started_at,
                    retry_count=task.retry_count,
                    metadata=task.metadata
                )
                
                logger.warning(f"Task failed, will retry ({task.retry_count}/{task.max_retries}): {task.name} ({task.task_id}): {e}")
                
            else:
                # Give up
                task_result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=str(e),
                    execution_time=execution_time,
                    started_at=task.started_at,
                    completed_at=datetime.utcnow().isoformat(),
                    retry_count=task.retry_count,
                    metadata=task.metadata
                )
                
                # Update task
                task.status = TaskStatus.FAILED
                task.completed_at = task_result.completed_at
                task.error = str(e)
                self.storage_backend.update_task(task)
                
                # Store result
                with self._lock:
                    self._results[task.task_id] = task_result
                
                # Call callbacks
                self._call_callbacks(task.task_id, task_result)
                
                logger.error(f"Task failed permanently: {task.name} ({task.task_id}): {e}")
    
    def _call_callbacks(self, task_id: str, result: TaskResult) -> None:
        """Call all callbacks for a task."""
        with self._lock:
            callbacks = self._callbacks.get(task_id, [])
        
        for callback in callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error in task callback: {e}")
    
    def schedule_task(self, 
                      function: Callable,
                      name: str = "",
                      args: Tuple = (),
                      kwargs: Optional[Dict[str, Any]] = None,
                      priority: TaskPriority = TaskPriority.NORMAL,
                      delay: Optional[float] = None,
                      scheduled_time: Optional[str] = None,
                      timeout: Optional[float] = None,
                      max_retries: int = 3,
                      retry_delay: float = 5.0,
                      metadata: Optional[Dict[str, Any]] = None,
                      callback: Optional[Callable[[TaskResult], None]] = None) -> str:
        """
        Schedule a new task.
        
        Args:
            function: Function to execute
            name: Task name
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            priority: Task priority
            delay: Delay in seconds before execution
            scheduled_time: Specific time to execute (ISO format)
            timeout: Timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            metadata: Additional metadata
            callback: Callback function to call when task completes
        
        Returns:
            Task ID
        """
        if kwargs is None:
            kwargs = {}
        if metadata is None:
            metadata = {}
        
        # Create task
        task = Task(
            task_id=str(uuid.uuid4()),
            name=name or function.__name__,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            metadata=metadata
        )
        
        # Set scheduled time
        if delay is not None:
            task.scheduled_time = (datetime.utcnow() + timedelta(seconds=delay)).isoformat()
        elif scheduled_time is not None:
            task.scheduled_time = scheduled_time
        else:
            # Execute immediately
            task.status = TaskStatus.PENDING
        
        # Store task
        self.storage_backend.store_task(task)
        
        # Add to queue
        try:
            self._task_queue.put((priority.value, task))
        except queue.Full:
            logger.error(f"Task queue is full, cannot schedule task: {name}")
            task.status = TaskStatus.FAILED
            task.error = "Queue is full"
            self.storage_backend.update_task(task)
            raise Exception("Task queue is full")
        
        # Register callback
        if callback:
            with self._lock:
                if task.task_id not in self._callbacks:
                    self._callbacks[task.task_id] = []
                self._callbacks[task.task_id].append(callback)
        
        logger.info(f"Scheduled task: {name} ({task.task_id})")
        return task.task_id
    
    def schedule_at(self, 
                    function: Callable,
                    scheduled_time: str,
                    name: str = "",
                    args: Tuple = (),
                    kwargs: Optional[Dict[str, Any]] = None,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    **extra_kwargs) -> str:
        """
        Schedule a task to run at a specific time.
        
        Args:
            function: Function to execute
            scheduled_time: Time to execute (ISO format)
            name: Task name
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority
            **extra_kwargs: Additional arguments for schedule_task
        
        Returns:
            Task ID
        """
        return self.schedule_task(
            function=function,
            name=name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            scheduled_time=scheduled_time,
            **extra_kwargs
        )
    
    def schedule_delayed(self, 
                         function: Callable,
                         delay: float,
                         name: str = "",
                         args: Tuple = (),
                         kwargs: Optional[Dict[str, Any]] = None,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         **extra_kwargs) -> str:
        """
        Schedule a task to run after a delay.
        
        Args:
            function: Function to execute
            delay: Delay in seconds
            name: Task name
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority
            **extra_kwargs: Additional arguments for schedule_task
        
        Returns:
            Task ID
        """
        return self.schedule_task(
            function=function,
            name=name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            delay=delay,
            **extra_kwargs
        )
    
    def schedule_recurring(self, 
                          function: Callable,
                          interval: float,
                          name: str = "",
                          args: Tuple = (),
                          kwargs: Optional[Dict[str, Any]] = None,
                          priority: TaskPriority = TaskPriority.NORMAL,
                          first_delay: Optional[float] = None,
                          max_runs: Optional[int] = None,
                          **extra_kwargs) -> str:
        """
        Schedule a recurring task.
        
        Args:
            function: Function to execute
            interval: Interval in seconds between runs
            name: Task name
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority
            first_delay: Delay before first run
            max_runs: Maximum number of runs (None for infinite)
            **extra_kwargs: Additional arguments for schedule_task
        
        Returns:
            Task ID (the first task in the sequence)
        """
        if kwargs is None:
            kwargs = {}
        
        # Track run count in metadata
        metadata = extra_kwargs.get("metadata", {})
        metadata["_recurring"] = True
        metadata["_interval"] = interval
        metadata["_max_runs"] = max_runs
        metadata["_run_count"] = 0
        extra_kwargs["metadata"] = metadata
        
        # Create the recurring function
        def recurring_wrapper(*w_args, **w_kwargs):
            # Get metadata from task
            task = self.storage_backend.retrieve_task(w_kwargs.get("task_id", ""))
            if not task:
                return
            
            run_count = task.metadata.get("_run_count", 0) + 1
            max_runs = task.metadata.get("_max_runs")
            
            # Update run count
            task.metadata["_run_count"] = run_count
            self.storage_backend.update_task(task)
            
            # Execute the actual function
            result = function(*w_args, **w_kwargs)
            
            # Schedule next run if needed
            if max_runs is None or run_count < max_runs:
                self.schedule_delayed(
                    function=recurring_wrapper,
                    delay=interval,
                    name=f"{name} (recurring)",
                    args=w_args,
                    kwargs=w_kwargs,
                    priority=priority,
                    metadata=task.metadata
                )
            
            return result
        
        # Schedule the first run
        if first_delay is not None:
            return self.schedule_delayed(
                function=recurring_wrapper,
                delay=first_delay,
                name=name,
                args=args,
                kwargs=kwargs,
                priority=priority,
                **extra_kwargs
            )
        else:
            return self.schedule_task(
                function=recurring_wrapper,
                name=name,
                args=args,
                kwargs=kwargs,
                priority=priority,
                **extra_kwargs
            )
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            True if task was cancelled
        """
        task = self.storage_backend.retrieve_task(task_id)
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow().isoformat()
        
        if self.storage_backend.update_task(task):
            logger.info(f"Cancelled task: {task.name} ({task_id})")
            return True
        
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.storage_backend.retrieve_task(task_id)
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a task."""
        with self._lock:
            return self._results.get(task_id)
    
    def get_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """Get all tasks with optional status filter."""
        return self.storage_backend.list_tasks(status)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get all ready tasks."""
        return self.storage_backend.list_ready_tasks()
    
    def clear_completed_tasks(self, older_than: Optional[str] = None) -> int:
        """
        Clear completed tasks.
        
        Args:
            older_than: Only clear tasks completed before this time (ISO format)
        
        Returns:
            Number of tasks cleared
        """
        count = 0
        tasks = self.get_tasks()
        
        for task in tasks:
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if older_than:
                    try:
                        cutoff = datetime.fromisoformat(older_than)
                        if task.completed_at and datetime.fromisoformat(task.completed_at) < cutoff:
                            if self.storage_backend.delete_task(task.task_id):
                                count += 1
                    except ValueError:
                        continue
                else:
                    if self.storage_backend.delete_task(task.task_id):
                        count += 1
        
        logger.info(f"Cleared {count} completed tasks")
        return count
    
    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """
        Wait for a task to complete.
        
        Args:
            task_id: Task ID to wait for
            timeout: Maximum time to wait in seconds
        
        Returns:
            TaskResult or None if timeout
        """
        start_time = time.time()
        
        while True:
            result = self.get_task_result(task_id)
            if result:
                return result
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None
            
            time.sleep(0.1)
    
    def wait_for_all(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all scheduled tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if all tasks completed, False if timeout
        """
        start_time = time.time()
        
        while True:
            # Get all non-completed tasks
            tasks = self.get_tasks()
            non_completed = [t for t in tasks if not t.is_finished()]
            
            if not non_completed:
                return True
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.1)


# Global task scheduler instance
task_scheduler = None


def get_task_scheduler(storage_backend: Optional[TaskStorageBackend] = None,
                       num_workers: int = 4,
                       max_queue_size: int = 1000) -> TaskScheduler:
    """Get or create the global task scheduler."""
    global task_scheduler
    if task_scheduler is None:
        task_scheduler = TaskScheduler(storage_backend, num_workers, max_queue_size)
    return task_scheduler
