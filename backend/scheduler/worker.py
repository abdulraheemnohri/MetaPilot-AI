"""
MetaPilot AI - Worker Pool

Provides a pool of worker threads for parallel task execution.
"""

import logging
import threading
import queue
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Status of a worker."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class Worker:
    """Represents a worker thread."""
    worker_id: str
    name: str
    status: WorkerStatus = WorkerStatus.IDLE
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: str = field(default_factory=lambda: time.time())
    last_activity: float = field(default_factory=lambda: time.time())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "name": self.name,
            "status": self.status.value,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }


class WorkerPool:
    """
    Pool of worker threads for parallel execution.
    
    Provides a higher-level interface for managing workers and executing tasks.
    """
    
    def __init__(self, 
                 num_workers: int = 4,
                 max_queue_size: int = 1000,
                 worker_prefix: str = "Worker"):
        """
        Initialize the worker pool.
        
        Args:
            num_workers: Number of worker threads
            max_queue_size: Maximum size of the task queue
            worker_prefix: Prefix for worker names
        """
        self.num_workers = num_workers
        self.max_queue_size = max_queue_size
        self.worker_prefix = worker_prefix
        
        self._task_queue = queue.Queue(maxsize=max_queue_size)
        self._workers: List[Worker] = []
        self._worker_threads: List[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Dict[str, Future] = {}
    
    def start(self) -> None:
        """Start the worker pool."""
        if self._running:
            return
        
        self._running = True
        
        # Create workers
        for i in range(self.num_workers):
            worker = Worker(
                worker_id=f"{self.worker_prefix}-{i}",
                name=f"{self.worker_prefix}-{i}"
            )
            self._workers.append(worker)
        
        # Create thread pool executor
        self._executor = ThreadPoolExecutor(max_workers=self.num_workers)
        
        logger.info(f"Worker pool started with {self.num_workers} workers")
    
    def stop(self, wait: bool = True) -> None:
        """
        Stop the worker pool.
        
        Args:
            wait: Whether to wait for current tasks to complete
        """
        if not self._running:
            return
        
        self._running = False
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=wait)
        
        # Clear task queue
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
                self._task_queue.task_done()
            except queue.Empty:
                break
        
        logger.info("Worker pool stopped")
    
    def submit(self, 
              function: Callable,
              *args,
              task_id: Optional[str] = None,
              **kwargs) -> str:
        """
        Submit a task for execution.
        
        Args:
            function: Function to execute
            *args: Positional arguments
            task_id: Optional task ID
            **kwargs: Keyword arguments
        
        Returns:
            Task ID
        """
        if task_id is None:
            import uuid
            task_id = str(uuid.uuid4())
        
        # Submit to executor
        future = self._executor.submit(function, *args, **kwargs)
        
        with self._lock:
            self._futures[task_id] = future
        
        # Update worker status
        self._update_worker_status(task_id, WorkerStatus.RUNNING)
        
        # Add callback to update status when done
        future.add_done_callback(lambda f: self._task_done(task_id, f))
        
        logger.debug(f"Submitted task: {task_id}")
        return task_id
    
    def _task_done(self, task_id: str, future: Future) -> None:
        """Called when a task completes."""
        with self._lock:
            if task_id in self._futures:
                del self._futures[task_id]
        
        # Update worker status
        self._update_worker_status(task_id, WorkerStatus.IDLE)
        
        # Log result
        try:
            result = future.result()
            logger.debug(f"Task completed successfully: {task_id}")
        except Exception as e:
            logger.error(f"Task failed: {task_id}: {e}")
    
    def _update_worker_status(self, task_id: str, status: WorkerStatus) -> None:
        """Update the status of a worker."""
        # This is a simplified implementation
        # In a real implementation, we would track which worker is running which task
        for worker in self._workers:
            if worker.current_task == task_id:
                worker.status = status
                if status == WorkerStatus.IDLE:
                    worker.current_task = None
                break
    
    def execute(self, 
                function: Callable,
                *args,
                callback: Optional[Callable[[Any], None]] = None,
                error_callback: Optional[Callable[[Exception], None]] = None,
                **kwargs) -> str:
        """
        Execute a function in the worker pool.
        
        Args:
            function: Function to execute
            *args: Positional arguments
            callback: Function to call on success
            error_callback: Function to call on error
            **kwargs: Keyword arguments
        
        Returns:
            Task ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        def wrapper():
            try:
                result = function(*args, **kwargs)
                if callback:
                    callback(result)
                return result
            except Exception as e:
                if error_callback:
                    error_callback(e)
                raise
        
        self.submit(wrapper, task_id=task_id)
        return task_id
    
    def map(self, 
            function: Callable,
            iterable: List[Any],
            *args,
            **kwargs) -> List[str]:
        """
        Execute a function on each item in an iterable.
        
        Args:
            function: Function to execute
            iterable: List of items
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        
        Returns:
            List of task IDs
        """
        task_ids = []
        for item in iterable:
            task_id = self.submit(function, item, *args, **kwargs)
            task_ids.append(task_id)
        return task_ids
    
    def get_workers(self) -> List[Worker]:
        """Get list of workers."""
        return self._workers.copy()
    
    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Get a specific worker."""
        for worker in self._workers:
            if worker.worker_id == worker_id:
                return worker
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            completed = sum(1 for f in self._futures.values() if f.done())
            pending = len(self._futures) - completed
        
        return {
            "total_workers": self.num_workers,
            "active_workers": sum(1 for w in self._workers if w.status == WorkerStatus.RUNNING),
            "idle_workers": sum(1 for w in self._workers if w.status == WorkerStatus.IDLE),
            "tasks_submitted": len(self._futures),
            "tasks_completed": completed,
            "tasks_pending": pending,
            "queue_size": self._task_queue.qsize()
        }
    
    def wait_for_all(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all submitted tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            True if all tasks completed, False if timeout
        """
        if not self._futures:
            return True
        
        # Wait for all futures to complete
        import concurrent.futures
        
        with self._lock:
            futures = list(self._futures.values())
        
        if not futures:
            return True
        
        try:
            concurrent.futures.wait(futures, timeout=timeout, return_when=concurrent.futures.ALL_COMPLETED)
            return True
        except concurrent.futures.TimeoutError:
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task ID to cancel
        
        Returns:
            True if task was cancelled
        """
        with self._lock:
            future = self._futures.get(task_id)
        
        if future and not future.done():
            return future.cancel()
        return False
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Get the result of a task.
        
        Args:
            task_id: Task ID
            timeout: Maximum time to wait in seconds
        
        Returns:
            Task result
        
        Raises:
            TimeoutError: If timeout occurs
            Exception: If task failed
        """
        with self._lock:
            future = self._futures.get(task_id)
        
        if not future:
            raise ValueError(f"Task {task_id} not found")
        
        return future.result(timeout=timeout)
    
    def get_exception(self, task_id: str) -> Optional[Exception]:
        """
        Get the exception from a failed task.
        
        Args:
            task_id: Task ID
        
        Returns:
            Exception if task failed, None otherwise
        """
        with self._lock:
            future = self._futures.get(task_id)
        
        if future and future.done():
            try:
                future.result()
            except Exception as e:
                return e
        return None


class TaskWorker(Worker):
    """
    Enhanced worker that can execute tasks with additional features.
    """
    
    def __init__(self, worker_id: str, name: str, task_queue: queue.Queue):
        super().__init__(worker_id=worker_id, name=name)
        self.task_queue = task_queue
        self._running = False
        self._thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start the worker thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run,
            name=self.name,
            daemon=True
        )
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the worker thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def _run(self) -> None:
        """Worker thread main loop."""
        while self._running:
            try:
                # Get next task
                task = self.task_queue.get(timeout=0.1)
                
                if task is None:
                    # Poison pill
                    self.task_queue.task_done()
                    break
                
                # Update status
                self.status = WorkerStatus.RUNNING
                self.current_task = task.get("task_id", "unknown")
                self.last_activity = time.time()
                
                # Execute task
                try:
                    function = task.get("function")
                    args = task.get("args", ())
                    kwargs = task.get("kwargs", {})
                    
                    result = function(*args, **kwargs)
                    
                    # Task completed
                    self.tasks_completed += 1
                    
                except Exception as e:
                    # Task failed
                    self.tasks_failed += 1
                    logger.error(f"Task failed in worker {self.worker_id}: {e}")
                
                # Update status
                self.status = WorkerStatus.IDLE
                self.current_task = None
                self.last_activity = time.time()
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker {self.worker_id}: {e}")


# Global worker pool instance
worker_pool = None


def get_worker_pool(num_workers: int = 4, 
                    max_queue_size: int = 1000,
                    worker_prefix: str = "MetaPilot-Worker") -> WorkerPool:
    """Get or create the global worker pool."""
    global worker_pool
    if worker_pool is None:
        worker_pool = WorkerPool(num_workers, max_queue_size, worker_prefix)
    return worker_pool
