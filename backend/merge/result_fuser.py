"""
MetaPilot AI - Result Fuser

Combines multiple AI responses into a single, comprehensive response.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from .conflict_resolver import conflict_resolver, ConflictResolutionStrategy, ConflictResolutionResult

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """Strategies for fusion."""
    CONCATENATE = "concatenate"
    VOTE = "vote"
    CONSENSUS = "consensus"
    BEST_OF = "best_of"
    WEIGHTED = "weighted"
    CUSTOM = "custom"


@dataclass
class FusionResult:
    """Result of a fusion."""
    original_results: List[Dict[str, Any]]
    fused_result: Dict[str, Any]
    strategy: FusionStrategy
    scores: List[float] = field(default_factory=list)
    weights: List[float] = field(default_factory=list)
    fusion_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_count": len(self.original_results),
            "fused_result": self.fused_result,
            "strategy": self.strategy.value,
            "scores": self.scores,
            "weights": self.weights,
            "fusion_time": self.fusion_time
        }


@dataclass
class FusionConfig:
    """Configuration for fusion."""
    strategy: FusionStrategy = FusionStrategy.WEIGHTED
    field_strategies: Dict[str, FusionStrategy] = field(default_factory=dict)
    weight_field: str = "quality_score"
    normalize_weights: bool = True
    custom_fusion_functions: Dict[str, Any] = field(default_factory=dict)


class ResultFuser:
    """
    Fuses multiple AI results into a single result.
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig()
    
    def fuse(self, 
             results: List[Dict[str, Any]],
             strategy: Optional[FusionStrategy] = None,
             config: Optional[FusionConfig] = None) -> FusionResult:
        import time
        start_time = time.time()
        
        if not results:
            return FusionResult(
                original_results=[],
                fused_result={},
                strategy=strategy or self.config.strategy,
                fusion_time=0.0
            )
        
        if len(results) == 1:
            return FusionResult(
                original_results=results,
                fused_result=results[0],
                strategy=strategy or self.config.strategy,
                fusion_time=time.time() - start_time
            )
        
        fusion_config = config or self.config
        effective_strategy = strategy or fusion_config.strategy
        
        weights: List[float] = []
        if effective_strategy == FusionStrategy.WEIGHTED:
            weights = self._calculate_weights(results, fusion_config)
        
        if effective_strategy == FusionStrategy.CONCATENATE:
            fused_result = self._fuse_concatenate(results)
        elif effective_strategy == FusionStrategy.VOTE:
            fused_result = self._fuse_vote(results)
        elif effective_strategy == FusionStrategy.CONSENSUS:
            fused_result = self._fuse_consensus(results)
        elif effective_strategy == FusionStrategy.BEST_OF:
            fused_result, best_idx = self._fuse_best_of(results)
            weights = [1.0 if i == best_idx else 0.0 for i in range(len(results))]
        elif effective_strategy == FusionStrategy.WEIGHTED:
            fused_result = self._fuse_weighted(results, weights)
        else:  # CUSTOM
            fused_result = self._fuse_custom(results, fusion_config)
        
        return FusionResult(
            original_results=results,
            fused_result=fused_result,
            strategy=effective_strategy,
            weights=weights,
            fusion_time=time.time() - start_time
        )

    def intelligent_fuse(self, contents: List[str]) -> str:
        """
        Merge multiple contents intelligently using conflict resolution.
        """
        if not contents:
            return ""
        if len(contents) == 1:
            return contents[0]

        # Convert strings to dummy dicts for conflict resolver
        responses = [{"content": c} for c in contents]

        # Use CONSENSUS strategy
        result = conflict_resolver.resolve(
            responses,
            strategy=ConflictResolutionStrategy.CONSENSUS
        )

        return result.resolved_response.get("content", contents[0])
    
    def _calculate_weights(self, results: List[Dict[str, Any]], config: FusionConfig) -> List[float]:
        weights = []
        weight_field = config.weight_field
        
        for result in results:
            weight = result.get(weight_field, 1.0)
            if not isinstance(weight, (int, float)):
                weight = 1.0
            weights.append(float(weight))
        
        if config.normalize_weights and weights:
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]
        
        return weights
    
    def _fuse_concatenate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        fused: Dict[str, Any] = {}
        for result in results:
            for key, value in result.items():
                if key in fused:
                    if isinstance(fused[key], list):
                        if isinstance(value, list):
                            fused[key] = fused[key] + value
                        else:
                            fused[key].append(value)
                    else:
                        fused[key] = [fused[key], value]
                else:
                    fused[key] = value
        return fused
    
    def _fuse_vote(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        from collections import Counter
        fused: Dict[str, Any] = {}
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        for key in all_keys:
            values = [r.get(key) for r in results if key in r]
            if not values:
                continue
            import json
            counter = Counter([json.dumps(v, sort_keys=True, default=str) for v in values])
            most_common_str = counter.most_common(1)[0][0]
            fused[key] = json.loads(most_common_str)
        return fused
    
    def _fuse_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._fuse_vote(results)
    
    def _fuse_best_of(self, results: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
        scores = []
        for result in results:
            score = result.get("quality_score", result.get("score", 0))
            scores.append(float(score) if isinstance(score, (int, float)) else 0)
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        return results[best_idx], best_idx
    
    def _fuse_weighted(self, results: List[Dict[str, Any]], weights: List[float]) -> Dict[str, Any]:
        fused: Dict[str, Any] = {}
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        for key in all_keys:
            values = [r.get(key) for r in results if key in r]
            if not values:
                continue
            if all(isinstance(v, (int, float)) for v in values):
                weighted_sum = sum(v * w for v, w in zip(values, weights))
                fused[key] = weighted_sum
            else:
                max_weight_idx = max(range(len(weights)), key=lambda i: weights[i])
                fused[key] = values[max_weight_idx]
        return fused
    
    def _fuse_custom(self, results: List[Dict[str, Any]], config: FusionConfig) -> Dict[str, Any]:
        return results[0]

# Global result fuser instance
result_fuser = ResultFuser()

def get_result_fuser(config: Optional[FusionConfig] = None) -> ResultFuser:
    global result_fuser
    if config:
        return ResultFuser(config)
    return result_fuser
