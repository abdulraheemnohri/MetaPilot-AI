"""
MetaPilot AI - Task Planner

Breaks down complex user requests into smaller, manageable subtasks.
Uses local AI for reasoning if available.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..local_ai import local_ai_manager

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    id: str
    description: str
    intent_type: str
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    status: str = "pending"

@dataclass
class TaskPlan:
    original_prompt: str
    subtasks: List[SubTask]
    is_complex: bool = False

class TaskPlanner:
    def __init__(self):
        pass

    async def create_plan(self, prompt: str, intent_type: str) -> TaskPlan:
        loaded_models = [m["id"] for m in local_ai_manager.list_models() if m["is_loaded"]]

        if loaded_models:
            try:
                model_id = loaded_models[0]
                planning_prompt = f"""Break down the following user request into subtasks with clear dependencies.
Request: "{prompt}"
Intent: {intent_type}
Respond only with a JSON object like: {{"is_complex": true, "subtasks": [{{"id": "st1", "description": "task description", "intent_type": "research", "dependencies": []}}, {{"id": "st2", "description": "task description", "intent_type": "code", "dependencies": ["st1"]}}]}}"""

                response = await local_ai_manager.generate(model_id, planning_prompt, max_tokens=1000)
                data = json.loads(response["content"])

                subtasks = [SubTask(**st) for st in data.get("subtasks", [])]
                return TaskPlan(original_prompt=prompt, subtasks=subtasks, is_complex=data.get("is_complex", len(subtasks) > 1))
            except Exception as e:
                logger.warning(f"Local AI planning failed: {e}")

        # Fallback to rule-based breakdown for common complex tasks
        if "build" in prompt.lower() and ("app" in prompt.lower() or "website" in prompt.lower()):
            subtasks = [
                SubTask(id="st1", description=f"Analyze requirements for {prompt}", intent_type="research"),
                SubTask(id="st2", description=f"Define architecture and data schema", intent_type="planning", dependencies=["st1"]),
                SubTask(id="st3", description=f"Implement frontend components", intent_type="code", dependencies=["st2"]),
                SubTask(id="st4", description=f"Implement backend logic and APIs", intent_type="code", dependencies=["st2"]),
                SubTask(id="st5", description=f"Write tests and documentation", intent_type="creative", dependencies=["st3", "st4"])
            ]
            return TaskPlan(original_prompt=prompt, subtasks=subtasks, is_complex=True)

        return TaskPlan(original_prompt=prompt, subtasks=[SubTask(id="st1", description=prompt, intent_type=intent_type)], is_complex=False)

task_planner = TaskPlanner()
