"""
AI Router for MetaPilot AI

Provides endpoints for AI inference and orchestration.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from ..orchestrator import OrchestrationRequest, orchestrator
from ..security.auth import get_current_user
from ..security.permission_manager import check_permission
from ..providers.registry import provider_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


class AIRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The input prompt")
    provider_ids: Optional[List[str]] = None
    max_tokens: int = Field(default=4096, ge=1, le=32768)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    strategy: str = Field(default="consensus")
    enable_ranking: bool = True
    enable_validation: bool = True
    enable_merging: bool = True


class AIResponse(BaseModel):
    query: str
    responses: List[Dict[str, Any]]
    merged_result: Optional[str] = None
    best_response: Optional[Dict[str, Any]] = None
    statistics: Dict[str, Any] = {}
    processing_time: float
    created_at: str


@router.post("/infer", response_model=AIResponse)
async def ai_inference(request: AIRequest, current_user: dict = Depends(get_current_user)):
    check_permission(current_user, "ai:use")
    orch_request = OrchestrationRequest(
        prompt=request.prompt,
        provider_ids=request.provider_ids,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        strategy=request.strategy,
        enable_ranking=request.enable_ranking,
        enable_validation=request.enable_validation,
        enable_merging=request.enable_merging,
    )
    try:
        result = await orchestrator.orchestrate(orch_request)
        return AIResponse(
            query=result.query,
            responses=result.responses,
            merged_result=result.merged_result,
            best_response=result.best_response,
            statistics=result.statistics,
            processing_time=result.processing_time,
            created_at=result.created_at,
        )
    except Exception as e:
        logger.error(f"AI inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers(current_user: dict = Depends(get_current_user)):
    check_permission(current_user, "ai:read")
    providers = []
    for provider_id, provider in provider_registry.providers.items():
        providers.append({
            "id": provider_id,
            "name": provider.name,
            "type": provider.type,
            "is_active": provider.is_active,
            "models": provider.models,
        })
    return {"success": True, "providers": providers, "total": len(providers)}


@router.get("/models")
async def list_models(current_user: dict = Depends(get_current_user)):
    check_permission(current_user, "ai:read")
    all_models = []
    for provider_id, provider in provider_registry.providers.items():
        if provider.models:
            for model in provider.models:
                all_models.append({
                    "model_id": model,
                    "provider_id": provider_id,
                    "provider_name": provider.name,
                })
    return {"success": True, "models": all_models, "total": len(all_models)}