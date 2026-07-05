"""
MetaPilot AI - Orchestrator Module

Main orchestration logic for combining multiple AI providers.
Handles request routing, response aggregation, and parallel execution.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .providers.registry import provider_registry
from .planner.intent_analyzer import intent_analyzer
from .planner.task_planner import task_planner
from .memory.memory_system import MemorySystem
from .knowledge.knowledge_base import KnowledgeBase
from .merge.result_fuser import ResultFuser
from .ranking.ranker import Ranker
from .validator.completeness_checker import CompletenessChecker
from .validator.safety_checker import safety_checker
from .validator.fact_checker import fact_checker
from .providers.capabilities import get_best_provider
from .plugins.loader import plugin_manager
from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationRequest:
    prompt: str
    provider_ids: Optional[List[str]] = None
    conversation_id: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    strategy: str = "consensus"
    enable_ranking: bool = True
    enable_validation: bool = True
    enable_merging: bool = True


@dataclass
class OrchestrationResult:
    query: str
    responses: List[Dict[str, Any]]
    merged_result: Optional[str] = None
    ranked_results: Optional[List[Dict[str, Any]]] = None
    best_response: Optional[Dict[str, Any]] = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    created_at: str = ""


class Orchestrator:
    def __init__(self):
        self.result_fuser = ResultFuser()
        self.ranker = Ranker()
        self.completeness_checker = CompletenessChecker()
        self.memory = MemorySystem()
        self.knowledge = KnowledgeBase()
        plugin_manager.load_plugins()
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        start_time = datetime.now()
        intent = await intent_analyzer.analyze(request.prompt)
        plan = await task_planner.create_plan(request.prompt, intent.type)
        logger.info(f"Detected intent: {intent.type}, Complex: {plan.is_complex}")

        providers = self._get_providers(request.provider_ids)
        if not providers:
            raise ValueError("No AI providers available")
        
        responses = []
        errors = []
        merged_result = None
        
        try:
            if plan.is_complex:
                completed_tasks = {} # id -> content
                pending_tasks = list(plan.subtasks)

                while pending_tasks:
                    ready_tasks = [t for t in pending_tasks if all(d in completed_tasks for d in t.dependencies)]
                    if not ready_tasks:
                        if pending_tasks: logger.error("Potential circular dependency or unmet requirements")
                        break

                    async def execute_subtask(task):
                        # Check if a plugin can handle this
                        for plugin in plugin_manager.plugins.values():
                            if plugin.name.lower() in task.description.lower():
                                res = await plugin.execute(task.description, completed_tasks)
                                return task.id, {"content": str(res), "provider_name": plugin.name, "metadata": {"is_plugin": True}}

                        provider = get_best_provider(task.intent_type, providers)
                        context = "\n".join([f"Result of {st_id}: {content}" for st_id, content in completed_tasks.items() if st_id in task.dependencies])
                        prompt = f"Previous Context:\n{context}\n\nCurrent Subtask: {task.description}"
                        return task.id, await self._get_provider_response(provider, request, prompt)

                    batch_results = await asyncio.gather(*[execute_subtask(t) for t in ready_tasks], return_exceptions=True)

                    for result in batch_results:
                        if isinstance(result, tuple):
                            tid, res = result
                            completed_tasks[tid] = res.get("content", "")
                            responses.append(res)
                        else:
                            errors.append(str(result))

                    ready_ids = [t.id for t in ready_tasks]
                    pending_tasks = [t for t in pending_tasks if t.id not in ready_ids]

                merged_result = "\n\n".join([f"### {st.description}\n{completed_tasks.get(st.id, 'Task failed.')}" for st in plan.subtasks])
            else:
                task_executions = [self._get_provider_response(p, request, request.prompt) for p in providers]
                batch_results = await asyncio.gather(*task_executions, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, Exception): errors.append(str(result))
                    elif result: responses.append(result)

                if responses:
                    if request.enable_ranking and len(responses) > 1:
                        ranked_results = self.ranker.rank(responses)
                        best_response = ranked_results[0]

                    if request.enable_merging and len(responses) > 1:
                        merged_result = self.result_fuser.intelligent_fuse([r.get("content", "") for r in responses])
                    elif request.enable_merging and len(responses) == 1:
                        merged_result = responses[0].get("content", "")

        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if responses and request.enable_validation:
            all_contents = [r.get("content", "") for r in responses]
            for response in responses:
                self.completeness_checker.check(response)
                safety_checker.check(response.get("content", ""))
                await fact_checker.check(response.get("content", ""), all_contents)
        
        return OrchestrationResult(
            query=request.prompt,
            responses=responses,
            merged_result=merged_result,
            ranked_results=ranked_results if 'ranked_results' in locals() else None,
            best_response=best_response if 'best_response' in locals() else (responses[0] if responses else None),
            statistics={"total_providers": len(providers), "successful": len(responses), "failed": len(errors), "intent": intent.type, "is_complex": plan.is_complex},
            processing_time=processing_time,
            created_at=datetime.now().isoformat(),
        )
    
    def _get_providers(self, provider_ids: Optional[List[str]] = None) -> List[Any]:
        if provider_ids:
            return [provider_registry.get_provider(pid) for pid in provider_ids if provider_registry.has_provider(pid)]
        return [p.provider for p in provider_registry.providers.values()]
    
    async def _get_provider_response(self, provider: Any, request: OrchestrationRequest, prompt: str) -> Dict[str, Any]:
        try:
            response = await provider.generate(prompt=prompt, max_tokens=request.max_tokens, temperature=request.temperature, conversation_id=request.conversation_id)
            return {
                "provider_id": getattr(provider, "id", provider.name.lower().replace(" ", "_")),
                "provider_name": provider.name,
                "provider_type": provider.provider_type,
                "content": response.text,
                "model": response.model,
                "tokens": response.tokens_prompt + response.tokens_completion,
                "finish_reason": response.finish_reason,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error from {provider.name}: {e}")
            return {
                "provider_id": getattr(provider, "id", provider.name.lower().replace(" ", "_")),
                "provider_name": provider.name,
                "provider_type": provider.provider_type,
                "content": "",
                "model": "unknown",
                "tokens": 0,
                "finish_reason": "error",
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }

orchestrator = Orchestrator()
