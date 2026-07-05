"""
MetaPilot AI - Sandbox Manager
"""

import logging
import subprocess
import os
import tempfile
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class SandboxType(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"

class SandboxStatus(Enum):
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class SandboxConfig:
    sandbox_type: SandboxType = SandboxType.PYTHON
    timeout: int = 30
    memory_limit_mb: int = 128

@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    success: bool

class SandboxManager:
    def __init__(self):
        pass
        
    async def run_code(self, code: str, language: str = "python", timeout: int = 30) -> SandboxResult:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            temp_file = f.name
        try:
            process = subprocess.run(["python3", temp_file], capture_output=True, text=True, timeout=timeout, env={})
            return SandboxResult(process.stdout, process.stderr, process.returncode, process.returncode == 0)
        except Exception as e:
            return SandboxResult("", str(e), 1, False)
        finally:
            if os.path.exists(temp_file): os.remove(temp_file)

def get_sandbox_manager():
    return SandboxManager()

sandbox_manager = SandboxManager()
