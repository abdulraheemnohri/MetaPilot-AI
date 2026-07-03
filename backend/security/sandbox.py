"""
MetaPilot AI - Sandbox Manager

Provides isolated execution environments for plugins and untrusted code.
"""

import logging
import os
import sys
import tempfile
import shutil
import subprocess
import time
import signal
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pathlib import Path
import hashlib
import json

logger = logging.getLogger(__name__)


class SandboxType(Enum):
    """Types of sandbox environments."""
    NONE = "none"  # No sandbox (run in main process)
    SUBPROCESS = "subprocess"  # Run in separate process
    CONTAINER = "container"  # Run in Docker container
    THREAD = "thread"  # Run in separate thread with restrictions


class SandboxStatus(Enum):
    """Status of a sandbox environment."""
    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class SandboxConfig:
    """Configuration for a sandbox environment."""
    sandbox_type: SandboxType = SandboxType.SUBPROCESS
    timeout: int = 30  # seconds
    memory_limit: int = 512  # MB
    cpu_limit: float = 1.0  # CPU cores
    network_access: bool = False
    filesystem_access: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=list)
    allowed_modules: List[str] = field(default_factory=list)
    blocked_modules: List[str] = field(default_factory=list)
    max_output_size: int = 1024 * 1024  # 1MB
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_type": self.sandbox_type.value,
            "timeout": self.timeout,
            "memory_limit": self.memory_limit,
            "cpu_limit": self.cpu_limit,
            "network_access": self.network_access,
            "filesystem_access": self.filesystem_access,
            "allowed_paths": self.allowed_paths,
            "blocked_paths": self.blocked_paths,
            "allowed_modules": self.allowed_modules,
            "blocked_modules": self.blocked_modules,
            "max_output_size": self.max_output_size,
            "environment": self.environment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SandboxConfig":
        return cls(
            sandbox_type=SandboxType(data.get("sandbox_type", "subprocess")),
            timeout=data.get("timeout", 30),
            memory_limit=data.get("memory_limit", 512),
            cpu_limit=data.get("cpu_limit", 1.0),
            network_access=data.get("network_access", False),
            filesystem_access=data.get("filesystem_access", False),
            allowed_paths=data.get("allowed_paths", []),
            blocked_paths=data.get("blocked_paths", []),
            allowed_modules=data.get("allowed_modules", []),
            blocked_modules=data.get("blocked_modules", []),
            max_output_size=data.get("max_output_size", 1024 * 1024),
            environment=data.get("environment", {})
        )


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_used: int = 0
    status: SandboxStatus = SandboxStatus.READY
    exit_code: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used,
            "status": self.status.value,
            "exit_code": self.exit_code
        }


class SandboxManager:
    """
    Manages sandboxed execution environments for plugins and untrusted code.
    
    Provides isolation to prevent malicious code from affecting the main system.
    """
    
    # Default sandbox configurations
    DEFAULT_CONFIGS = {
        "strict": SandboxConfig(
            sandbox_type=SandboxType.SUBPROCESS,
            timeout=10,
            memory_limit=256,
            network_access=False,
            filesystem_access=False,
            blocked_modules=["os", "sys", "subprocess", "socket", "http", "urllib", "requests", "ctypes", "pickle", "marshal", "importlib", "builtins"]
        ),
        "moderate": SandboxConfig(
            sandbox_type=SandboxType.SUBPROCESS,
            timeout=30,
            memory_limit=512,
            network_access=True,
            filesystem_access=True,
            allowed_paths=["/tmp/metapilot_sandbox"],
            blocked_modules=["os", "sys", "subprocess", "ctypes", "pickle", "marshal"]
        ),
        "trusted": SandboxConfig(
            sandbox_type=SandboxType.SUBPROCESS,
            timeout=60,
            memory_limit=1024,
            network_access=True,
            filesystem_access=True,
            allowed_paths=["/tmp/metapilot_sandbox", "/home/user/MetaPilotAI/plugins"]
        ),
        "none": SandboxConfig(
            sandbox_type=SandboxType.NONE,
            timeout=120,
            memory_limit=2048,
            network_access=True,
            filesystem_access=True
        )
    }
    
    def __init__(self, config: Optional[SandboxConfig] = None, temp_dir: Optional[str] = None):
        """
        Initialize the sandbox manager.
        
        Args:
            config: Default sandbox configuration
            temp_dir: Temporary directory for sandbox operations
        """
        self.config = config or self.DEFAULT_CONFIGS["moderate"]
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="metapilot_sandbox_")
        self._active_sandboxes: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        # Ensure temp directory exists
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Sandbox manager initialized with temp dir: {self.temp_dir}")
    
    def _generate_sandbox_id(self) -> str:
        """Generate a unique sandbox ID."""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    
    def _create_sandbox_environment(self, sandbox_id: str) -> Dict[str, str]:
        """Create environment variables for sandbox execution."""
        env = os.environ.copy()
        
        # Set sandbox-specific environment
        env["METAPILOT_SANDBOX_ID"] = sandbox_id
        env["METAPILOT_SANDBOX_TEMP"] = self.temp_dir
        env["METAPILOT_SANDBOX_TYPE"] = self.config.sandbox_type.value
        
        # Add custom environment variables
        env.update(self.config.environment)
        
        return env
    
    def _validate_code(self, code: str) -> Tuple[bool, str]:
        """
        Validate code for potentially dangerous operations.
        
        Args:
            code: Code to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for blocked modules
        for module in self.config.blocked_modules:
            if f"import {module}" in code or f"from {module} " in code:
                return False, f"Import of blocked module '{module}' detected"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "open(",
            "os.system",
            "os.popen",
            "subprocess.",
            "socket.",
            "pickle.loads",
            "marshal.loads",
            "ctypes.",
            ":= "  # Walrus operator (can be used for assignment expressions)
        ]
        
        for pattern in dangerous_patterns:
            if pattern in code:
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, ""
    
    def _execute_in_subprocess(self, code: str, context: Dict[str, Any], sandbox_id: str) -> SandboxResult:
        """
        Execute code in a separate subprocess.
        
        Args:
            code: Python code to execute
            context: Context variables to pass to the code
            sandbox_id: Sandbox ID
        
        Returns:
            SandboxResult with execution results
        """
        start_time = time.time()
        
        try:
            # Create a temporary file for the code
            code_file = Path(self.temp_dir) / f"{sandbox_id}.py"
            
            # Prepare the code with context
            context_str = json.dumps(context)
            wrapper_code = f"""
import json
import sys
import traceback

# Set up context
try:
    context = {context_str}
except:
    context = {{}}

# Execute the code
try:
    # Add context variables to globals
    globals().update(context)
    
    # Execute the user code
    exec({repr(code)}, globals())
    
    # Get the result (last expression or _ variable)
    if '_' in globals():
        result = _
    else:
        result = None
    
    # Output the result
    print(json.dumps({{"success": True, "output": result}}))
    sys.exit(0)
    
except Exception as e:
    error_info = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(error_info))
    sys.exit(1)
"""
            
            # Write the code to file
            with open(code_file, 'w') as f:
                f.write(wrapper_code)
            
            # Execute with timeout
            env = self._create_sandbox_environment(sandbox_id)
            
            process = subprocess.Popen(
                [sys.executable, str(code_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=self.temp_dir
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.config.timeout)
                execution_time = time.time() - start_time
                
                # Parse output
                if stdout:
                    try:
                        result = json.loads(stdout.decode('utf-8'))
                        if result.get("success"):
                            return SandboxResult(
                                success=True,
                                output=result.get("output"),
                                execution_time=execution_time,
                                status=SandboxStatus.READY,
                                exit_code=process.returncode or 0
                            )
                        else:
                            return SandboxResult(
                                success=False,
                                error=result.get("error", "Unknown error"),
                                execution_time=execution_time,
                                status=SandboxStatus.ERROR,
                                exit_code=process.returncode or 1
                            )
                    except json.JSONDecodeError:
                        return SandboxResult(
                            success=False,
                            error=stdout.decode('utf-8') or stderr.decode('utf-8'),
                            execution_time=execution_time,
                            status=SandboxStatus.ERROR,
                            exit_code=process.returncode or 1
                        )
                
                return SandboxResult(
                    success=False,
                    error=stderr.decode('utf-8') or "No output",
                    execution_time=execution_time,
                    status=SandboxStatus.ERROR,
                    exit_code=process.returncode or 1
                )
                
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=5)
                except:
                    process.kill()
                
                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {self.config.timeout} seconds",
                    execution_time=self.config.timeout,
                    status=SandboxStatus.TIMEOUT,
                    exit_code=-1
                )
            
        except Exception as e:
            logger.error(f"Error in subprocess execution: {e}")
            return SandboxResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                status=SandboxStatus.ERROR,
                exit_code=-1
            )
        
        finally:
            # Clean up the temporary file
            try:
                code_file.unlink()
            except:
                pass
    
    def _execute_in_thread(self, code: str, context: Dict[str, Any], sandbox_id: str) -> SandboxResult:
        """
        Execute code in a separate thread.
        
        Args:
            code: Python code to execute
            context: Context variables to pass to the code
            sandbox_id: Sandbox ID
        
        Returns:
            SandboxResult with execution results
        """
        start_time = time.time()
        result = {"success": False, "output": None, "error": ""}
        
        def run_code():
            try:
                # Create a restricted globals dictionary
                restricted_globals = {
                    "__builtins__": {}
                }
                
                # Add safe builtins
                safe_builtins = [
                    "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable",
                    "chr", "complex", "dict", "dir", "divmod", "enumerate", "filter",
                    "float", "format", "frozenset", "getattr", "hasattr", "hash",
                    "hex", "int", "isinstance", "issubclass", "iter", "len", "list",
                    "map", "max", "min", "next", "object", "oct", "open", "ord",
                    "pow", "print", "property", "range", "repr", "reversed", "round",
                    "set", "slice", "sorted", "str", "sum", "super", "tuple", "type",
                    "zip", "True", "False", "None"
                ]
                
                for name in safe_builtins:
                    if hasattr(__builtins__, name):
                        restricted_globals["__builtins__"][name] = getattr(__builtins__, name)
                
                # Add context variables
                restricted_globals.update(context)
                
                # Compile and execute
                compiled = compile(code, "<sandbox>", "exec")
                exec(compiled, restricted_globals)
                
                # Get result
                if "_" in restricted_globals:
                    result["output"] = restricted_globals["_"]
                result["success"] = True
                
            except Exception as e:
                result["error"] = str(e)
                result["success"] = False
        
        thread = threading.Thread(target=run_code, daemon=True)
        thread.start()
        thread.join(timeout=self.config.timeout)
        
        if thread.is_alive():
            # Thread is still running, mark as timeout
            return SandboxResult(
                success=False,
                error=f"Execution timed out after {self.config.timeout} seconds",
                execution_time=self.config.timeout,
                status=SandboxStatus.TIMEOUT,
                exit_code=-1
            )
        
        execution_time = time.time() - start_time
        
        if result["success"]:
            return SandboxResult(
                success=True,
                output=result["output"],
                execution_time=execution_time,
                status=SandboxStatus.READY,
                exit_code=0
            )
        else:
            return SandboxResult(
                success=False,
                error=result["error"],
                execution_time=execution_time,
                status=SandboxStatus.ERROR,
                exit_code=1
            )
    
    def execute(self, code: str, context: Optional[Dict[str, Any]] = None, config: Optional[SandboxConfig] = None) -> SandboxResult:
        """
        Execute code in a sandboxed environment.
        
        Args:
            code: Python code to execute
            context: Context variables to pass to the code
            config: Override sandbox configuration for this execution
        
        Returns:
            SandboxResult with execution results
        """
        if context is None:
            context = {}
        
        # Use provided config or default
        execution_config = config or self.config
        
        # Generate sandbox ID
        sandbox_id = self._generate_sandbox_id()
        
        # Validate code
        is_valid, error = self._validate_code(code)
        if not is_valid:
            logger.warning(f"Code validation failed: {error}")
            return SandboxResult(
                success=False,
                error=f"Code validation failed: {error}",
                status=SandboxStatus.ERROR,
                exit_code=-1
            )
        
        logger.info(f"Executing code in sandbox {sandbox_id} with type {execution_config.sandbox_type.value}")
        
        # Execute based on sandbox type
        if execution_config.sandbox_type == SandboxType.SUBPROCESS:
            return self._execute_in_subprocess(code, context, sandbox_id)
        elif execution_config.sandbox_type == SandboxType.THREAD:
            return self._execute_in_thread(code, context, sandbox_id)
        elif execution_config.sandbox_type == SandboxType.CONTAINER:
            return self._execute_in_container(code, context, sandbox_id)
        else:  # NONE
            return self._execute_direct(code, context, sandbox_id)
    
    def _execute_in_container(self, code: str, context: Dict[str, Any], sandbox_id: str) -> SandboxResult:
        """
        Execute code in a Docker container.
        
        Note: This requires Docker to be installed and running.
        """
        start_time = time.time()
        
        try:
            # Check if Docker is available
            try:
                subprocess.run(["docker", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return SandboxResult(
                    success=False,
                    error="Docker is not available",
                    execution_time=time.time() - start_time,
                    status=SandboxStatus.ERROR,
                    exit_code=-1
                )
            
            # Create a temporary Dockerfile
            dockerfile_content = """FROM python:3.9-slim
WORKDIR /sandbox
COPY code.py .
RUN pip install -q --no-cache-dir json
CMD ["python", "code.py"]
"""
            
            dockerfile = Path(self.temp_dir) / f"{sandbox_id}.Dockerfile"
            with open(dockerfile, 'w') as f:
                f.write(dockerfile_content)
            
            # Create the code file
            code_file = Path(self.temp_dir) / f"{sandbox_id}.py"
            context_str = json.dumps(context)
            wrapper_code = f"""
import json
import sys
import traceback

try:
    context = {context_str}
except:
    context = {{}}

try:
    globals().update(context)
    exec({repr(code)}, globals())
    if '_' in globals():
        result = _
    else:
        result = None
    print(json.dumps({{"success": True, "output": result}}))
    sys.exit(0)
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e), "traceback": traceback.format_exc()}}))
    sys.exit(1)
"""
            with open(code_file, 'w') as f:
                f.write(wrapper_code)
            
            # Build and run the container
            image_name = f"metapilot-sandbox-{sandbox_id}"
            container_name = f"metapilot-sandbox-{sandbox_id}"
            
            try:
                # Build image
                subprocess.run(
                    ["docker", "build", "-t", image_name, "-f", str(dockerfile), str(self.temp_dir)],
                    capture_output=True,
                    check=True,
                    timeout=60
                )
                
                # Run container
                process = subprocess.Popen(
                    ["docker", "run", "--rm", "--name", container_name, 
                     "-m", str(self.config.memory_limit) + "m",
                     "-e", f"METAPILOT_SANDBOX_ID={sandbox_id}",
                     image_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=self.config.timeout)
                    execution_time = time.time() - start_time
                    
                    if stdout:
                        try:
                            result = json.loads(stdout.decode('utf-8'))
                            if result.get("success"):
                                return SandboxResult(
                                    success=True,
                                    output=result.get("output"),
                                    execution_time=execution_time,
                                    status=SandboxStatus.READY,
                                    exit_code=process.returncode or 0
                                )
                            else:
                                return SandboxResult(
                                    success=False,
                                    error=result.get("error", "Unknown error"),
                                    execution_time=execution_time,
                                    status=SandboxStatus.ERROR,
                                    exit_code=process.returncode or 1
                                )
                        except json.JSONDecodeError:
                            return SandboxResult(
                                success=False,
                                error=stdout.decode('utf-8') or stderr.decode('utf-8'),
                                execution_time=execution_time,
                                status=SandboxStatus.ERROR,
                                exit_code=process.returncode or 1
                            )
                    
                    return SandboxResult(
                        success=False,
                        error=stderr.decode('utf-8') or "No output",
                        execution_time=execution_time,
                        status=SandboxStatus.ERROR,
                        exit_code=process.returncode or 1
                    )
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    return SandboxResult(
                        success=False,
                        error=f"Execution timed out after {self.config.timeout} seconds",
                        execution_time=self.config.timeout,
                        status=SandboxStatus.TIMEOUT,
                        exit_code=-1
                    )
                
            finally:
                # Clean up
                try:
                    subprocess.run(["docker", "rmi", image_name], capture_output=True)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Error in container execution: {e}")
            return SandboxResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                status=SandboxStatus.ERROR,
                exit_code=-1
            )
    
    def _execute_direct(self, code: str, context: Dict[str, Any], sandbox_id: str) -> SandboxResult:
        """
        Execute code directly in the main process (no isolation).
        
        WARNING: This provides no security isolation!
        """
        start_time = time.time()
        
        try:
            # Create a copy of globals with context
            execution_globals = globals().copy()
            execution_globals.update(context)
            
            # Execute the code
            exec(compile(code, "<sandbox>", "exec"), execution_globals)
            
            # Get result
            output = execution_globals.get("_")
            
            return SandboxResult(
                success=True,
                output=output,
                execution_time=time.time() - start_time,
                status=SandboxStatus.READY,
                exit_code=0
            )
            
        except Exception as e:
            return SandboxResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                status=SandboxStatus.ERROR,
                exit_code=1
            )
    
    def create_isolated_plugin_environment(self, plugin_id: str, plugin_code: str) -> Dict[str, Any]:
        """
        Create an isolated environment for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            plugin_code: Plugin code
        
        Returns:
            Dictionary with environment information
        """
        plugin_dir = Path(self.temp_dir) / "plugins" / plugin_id
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Save plugin code
        plugin_file = plugin_dir / f"{plugin_id}.py"
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        return {
            "plugin_dir": str(plugin_dir),
            "plugin_file": str(plugin_file),
            "sandbox_id": hashlib.sha256(plugin_id.encode()).hexdigest()[:16]
        }
    
    def cleanup(self) -> None:
        """Clean up all temporary files and resources."""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up sandbox temp directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up sandbox: {e}")
    
    def __del__(self):
        """Destructor to clean up resources."""
        self.cleanup()


# Global sandbox manager instance
sandbox_manager = None


def get_sandbox_manager(config: Optional[SandboxConfig] = None, temp_dir: Optional[str] = None) -> SandboxManager:
    """Get or create the global sandbox manager."""
    global sandbox_manager
    if sandbox_manager is None:
        sandbox_manager = SandboxManager(config, temp_dir)
    return sandbox_manager
