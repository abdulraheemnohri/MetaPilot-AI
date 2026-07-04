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
    """
    Plans the execution of complex tasks.
    """

    def __init__(self):
        pass

    async def create_plan(self, prompt: str, intent_type: str) -> TaskPlan:
        """
        Create a plan for the given prompt.
        """
        loaded_models = [m["id"] for m in local_ai_manager.list_models() if m["is_loaded"]]

        if loaded_models:
            try:
                model_id = loaded_models[0]
                planning_prompt = f"""Break down the following user request into subtasks if necessary.
Request: "{prompt}"
Intent: {intent_type}
Respond only with a JSON object like: {{"is_complex": true, "subtasks": [{{"id": "1", "description": "task description", "intent_type": "research", "dependencies": []}}]}}"""

                response = await local_ai_manager.generate(model_id, planning_prompt, max_tokens=500)
                data = json.loads(response["content"])

                subtasks = [SubTask(**st) for st in data.get("subtasks", [])]
                return TaskPlan(
                    original_prompt=prompt,
                    subtasks=subtasks,
                    is_complex=data.get("is_complex", False)
                )
            except Exception as e:
                logger.warning(f"Local AI planning failed, falling back: {e}")

        # Fallback to simple rule-based planning
        subtasks = []
        if "build" in prompt.lower() and ("app" in prompt.lower() or "website" in prompt.lower()):
            subtasks = [
                SubTask(id="1", description=f"Research requirements for: {prompt}", intent_type="research"),
                SubTask(id="2", description=f"Design architecture for: {prompt}", intent_type="planning", dependencies=["1"]),
                SubTask(id="3", description=f"Implement core logic for: {prompt}", intent_type="code", dependencies=["2"]),
                SubTask(id="4", description=f"Create documentation for: {prompt}", intent_type="creative", dependencies=["3"])
            ]
            return TaskPlan(original_prompt=prompt, subtasks=subtasks, is_complex=True)

        subtasks = [SubTask(id="1", description=prompt, intent_type=intent_type)]
        return TaskPlan(original_prompt=prompt, subtasks=subtasks, is_complex=False)

# Global task planner instance
task_planner = TaskPlanner()
