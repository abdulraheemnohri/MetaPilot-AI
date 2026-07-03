"""
Merge Router for MetaPilot AI

Provides endpoints for merging and combining AI results.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ..merge import conflict_resolver, duplicate_remover, result_fuser, similarity_detector
from ..security.auth import get_current_user
from ..security.permission_manager import check_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/merge", tags=["Merge"])


# Models
class MergeRequest(BaseModel):
    """Request for merging results."""
    results: List[str] = Field(..., description="List of results to merge")
    method: str = Field("fuse", description="Merge method (fuse, concatenate, vote)")


class SimilarityRequest(BaseModel):
    """Request for checking similarity."""
    text1: str = Field(..., description="First text")
    text2: str = Field(..., description="Second text")


class DuplicateRequest(BaseModel):
    """Request for removing duplicates."""
    items: List[str] = Field(..., description="List of items")
    threshold: float = Field(0.8, description="Similarity threshold for duplicates")


# Endpoints
@router.post("/fuse", summary="Fuse results")
async def fuse_results(
    request: MergeRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Fuse multiple results into a single coherent result.
    
    This is useful for:
    - Combining answers from multiple AI providers
    - Merging similar responses
    - Creating consensus answers
    """
    if current_user:
        check_permission("ai:use", current_user)
    
    try:
        if request.method == "fuse":
            merged = result_fuser.fuse(request.results)
        elif request.method == "concatenate":
            merged = "\n\n".join(request.results)
        elif request.method == "vote":
            # Simple voting: use the most common result
            from collections import Counter
            counts = Counter(request.results)
            merged = counts.most_common(1)[0][0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown merge method: {request.method}",
            )
        
        return {
            "success": True,
            "merged_result": merged,
            "method": request.method,
            "input_count": len(request.results),
        }
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/similarity", summary="Check similarity")
async def check_similarity(
    request: SimilarityRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Check the similarity between two texts.
    
    Returns a similarity score between 0 and 1.
    """
    if current_user:
        check_permission("ai:use", current_user)
    
    try:
        # Convert to embeddings and calculate similarity
        # For simplicity, we'll use text-based similarity
        score = similarity_detector.calculate_similarity(request.text1, request.text2)
        
        return {
            "success": True,
            "score": score,
            "text1": request.text1[:50] + "..." if len(request.text1) > 50 else request.text1,
            "text2": request.text2[:50] + "..." if len(request.text2) > 50 else request.text2,
        }
        
    except Exception as e:
        logger.error(f"Similarity check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/duplicates/remove", summary="Remove duplicates")
async def remove_duplicates(
    request: DuplicateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Remove duplicate items from a list.
    
    Uses similarity detection to identify and remove duplicates.
    """
    if current_user:
        check_permission("ai:use", current_user)
    
    try:
        unique_items = duplicate_remover.remove_duplicates(
            request.items,
            request.threshold,
        )
        
        return {
            "success": True,
            "original_count": len(request.items),
            "unique_count": len(unique_items),
            "removed_count": len(request.items) - len(unique_items),
            "unique_items": unique_items,
        }
        
    except Exception as e:
        logger.error(f"Duplicate removal failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/conflicts/resolve", summary="Resolve conflicts")
async def resolve_conflicts(
    conflicts: List[Dict[str, Any]],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Resolve conflicts between multiple results.
    
    Useful for:
    - Handling contradictory answers
    - Resolving disagreements between AI providers
    - Creating consensus from conflicting information
    """
    if current_user:
        check_permission("ai:use", current_user)
    
    try:
        resolved = conflict_resolver.resolve(conflicts)
        
        return {
            "success": True,
            "resolved": resolved,
            "conflict_count": len(conflicts),
        }
        
    except Exception as e:
        logger.error(f"Conflict resolution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
