"""
MetaPilot AI - Orchestrator Module

Main orchestration logic for combining multiple AI providers.
Handles request routing, response aggregation, and result optimization.
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
from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationRequest:
    prompt: str
    provider_ids: Optional[List[str]] = None
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
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        start_time = datetime.now()
        # Analyze intent and plan
        intent = await intent_analyzer.analyze(request.prompt)
        plan = await task_planner.create_plan(request.prompt, intent.type)
        logger.info(f"Detected intent: {intent.type}, Complex: {plan.is_complex}")

        providers = self._get_providers(request.provider_ids)
        
        if not providers:
            raise ValueError("No AI providers available")
        
        logger.info(f"Orchestrating request with {len(providers)} providers")
        
        responses = []
        errors = []
        
        try:
            # Parallel execution of subtasks or full prompt
            if plan.is_complex:
                # For complex plans, we'll execute sequentially for now following dependencies
                # This is a simplified implementation of the Task Splitter/Parallel workers architecture
                plan_results = {}
                for subtask in plan.subtasks:
                    # In a real system, we would route based on subtask.intent_type
                    # Here we just use the first available provider for simplicity in this version
                    provider = providers[0]
                    sub_response = await self._get_provider_response(provider, request, subtask.description)
                    plan_results[subtask.id] = sub_response.get("content", "")
                    responses.append(sub_response)

                # Merge subtask results
                merged_result = "\n\n".join([f"## {st.description}\n{plan_results[st.id]}" for st in plan.subtasks])
            else:
                tasks = []
                for provider in providers:
                    task = asyncio.create_task(self._get_provider_response(provider, request, request.prompt))
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                    elif result:
                        responses.append(result)

                # Ranking and Merging
                if responses:
                    if request.enable_ranking and len(responses) > 1:
                        ranked_results = self.ranker.rank(responses)
                        best_response = ranked_results[0] if ranked_results else None

                    if request.enable_merging and len(responses) > 1:
                        contents = [r.get("content", "") for r in responses]
                        merged_result = self.result_fuser.intelligent_fuse(contents)
                    elif request.enable_merging and len(responses) == 1:
                        merged_result = responses[0].get("content", "")

        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if responses and request.enable_validation:
            for response in responses:
                self.completeness_checker.check(response)
                safety_checker.check(response.get("content", ""))
        
        statistics = {
            "total_providers": len(providers),
            "successful_responses": len(responses),
            "failed_responses": len(errors),
            "strategy": request.strategy,
            "intent": intent.type,
            "is_complex": plan.is_complex
        }
        
        return OrchestrationResult(
            query=request.prompt,
            responses=responses,
            merged_result=merged_result,
            ranked_results=ranked_results if 'ranked_results' in locals() else None,
            best_response=best_response if 'best_response' in locals() else (responses[0] if responses else None),
            statistics=statistics,
            processing_time=processing_time,
            created_at=datetime.now().isoformat(),
        )
    
    def _get_providers(self, provider_ids: Optional[List[str]] = None) -> List[Any]:
        if provider_ids:
            return [provider_registry.get_provider(pid) for pid in provider_ids if provider_registry.has_provider(pid)]
        else:
            return [p.provider for p in provider_registry.providers.values()]
    
    async def _get_provider_response(self, provider: Any, request: OrchestrationRequest, prompt: str) -> Dict[str, Any]:
        try:
            response = await provider.generate(
                prompt=prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            return {
                "provider_id": getattr(provider, "id", provider.name.lower()),
                "provider_name": provider.name,
                "provider_type": provider.provider_type,
                "content": response.text,
                "model": response.model,
                "tokens_used": response.tokens_prompt + response.tokens_completion,
                "finish_reason": response.finish_reason,
                "generated_at": datetime.now().isoformat(),
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error from provider {provider.name}: {e}")
            return {
                "provider_id": getattr(provider, "id", provider.name.lower()),
                "provider_name": provider.name,
                "provider_type": provider.provider_type,
                "content": "",
                "model": "unknown",
                "tokens_used": 0,
                "finish_reason": "error",
                "generated_at": datetime.now().isoformat(),
                "error": str(e),
            }

# Global orchestrator instance
orchestrator = Orchestrator()
