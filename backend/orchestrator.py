"""
MetaPilot AI - Orchestrator Module

Main orchestration logic for combining multiple AI providers.
Handles request routing, response aggregation, and result optimization.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .providers.registry import provider_registry
from .merge.result_fuser import ResultFuser
from .ranking.ranker import Ranker
from .validator.completeness_checker import CompletenessChecker
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
    statistics: Dict[str, Any] = {}
    processing_time: float = 0.0
    created_at: str = ""


class Orchestrator:
    def __init__(self):
        self.result_fuser = ResultFuser()
        self.ranker = Ranker()
        self.completeness_checker = CompletenessChecker()
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResult:
        start_time = datetime.now()
        providers = self._get_providers(request.provider_ids)
        
        if not providers:
            raise ValueError("No AI providers available")
        
        logger.info(f"Orchestrating request with {len(providers)} providers")
        
        responses = []
        errors = []
        
        try:
            tasks = []
            for provider in providers:
                task = asyncio.create_task(self._get_provider_response(provider, request))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                elif result:
                    responses.append(result)
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            raise
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        merged_result = None
        ranked_results = None
        best_response = None
        
        if responses:
            if request.enable_ranking and len(responses) > 1:
                ranked_results = self.ranker.rank(responses)
                best_response = ranked_results[0] if ranked_results else None
            
            if request.enable_merging and len(responses) > 1:
                contents = [r.get("content", "") for r in responses]
                merged_result = self.result_fuser.intelligent_fuse(contents)
            
            if request.enable_validation:
                for response in responses:
                    self.completeness_checker.check(response.get("content", ""))
        
        statistics = {
            "total_providers": len(providers),
            "successful_responses": len(responses),
            "failed_responses": len(errors),
            "strategy": request.strategy,
        }
        
        return OrchestrationResult(
            query=request.prompt,
            responses=responses,
            merged_result=merged_result,
            ranked_results=ranked_results,
            best_response=best_response,
            statistics=statistics,
            processing_time=processing_time,
            created_at=datetime.now().isoformat(),
        )
    
    def _get_providers(self, provider_ids: Optional[List[str]] = None) -> List[Any]:
        if provider_ids:
            return [provider_registry.get_provider(pid) for pid in provider_ids if provider_registry.has_provider(pid)]
        else:
            return [p for p in provider_registry.providers.values() if p.is_active]
    
    async def _get_provider_response(self, provider: Any, request: OrchestrationRequest) -> Dict[str, Any]:
        try:
            response = await provider.generate(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            return {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "provider_type": provider.type,
                "content": response.get("content", ""),
                "model": response.get("model", provider.id),
                "tokens_used": response.get("tokens_used", 0),
                "finish_reason": response.get("finish_reason", "unknown"),
                "generated_at": datetime.now().isoformat(),
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error from provider {provider.name}: {e}")
            return {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "provider_type": provider.type,
                "content": "",
                "model": provider.id,
                "tokens_used": 0,
                "finish_reason": "error",
                "generated_at": datetime.now().isoformat(),
                "error": str(e),
            }