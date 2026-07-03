"""
MetaPilot AI - Result Fuser

Fuses multiple AI results into a single coherent result.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import json

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """Strategies for fusing results."""
    CONCATENATE = "concatenate"  # Simply concatenate all results
    VOTE = "vote"  # Use voting for each part
    CONSENSUS = "consensus"  # Find consensus
    BEST_OF = "best_of"  # Select the best result
    WEIGHTED = "weighted"  # Weight by quality score
    CUSTOM = "custom"  # Custom fusion function


@dataclass
class FusionResult:
    """Result of fusion operation."""
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
    
    Combines responses from different AI systems to create a unified,
    more comprehensive result.
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        """
        Initialize the result fuser.
        
        Args:
            config: Fusion configuration
        """
        self.config = config or FusionConfig()
    
    def fuse(self, 
             results: List[Dict[str, Any]],
             strategy: Optional[FusionStrategy] = None,
             config: Optional[FusionConfig] = None) -> FusionResult:
        """
        Fuse multiple results into a single result.
        
        Args:
            results: List of result dictionaries
            strategy: Fusion strategy to use
            config: Optional fusion configuration
        
        Returns:
            FusionResult with fused result
        """
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
        
        # Use provided config or default
        fusion_config = config or self.config
        effective_strategy = strategy or fusion_config.strategy
        
        # Calculate weights if using weighted strategy
        weights: List[float] = []
        if effective_strategy == FusionStrategy.WEIGHTED:
            weights = self._calculate_weights(results, fusion_config)
        
        # Fuse based on strategy
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
    
    def _calculate_weights(self, results: List[Dict[str, Any]], config: FusionConfig) -> List[float]:
        """Calculate weights for each result."""
        weights = []
        weight_field = config.weight_field
        
        for result in results:
            # Get weight from result
            weight = result.get(weight_field, 1.0)
            
            # Ensure it's a number
            if not isinstance(weight, (int, float)):
                weight = 1.0
            
            weights.append(float(weight))
        
        # Normalize if requested
        if config.normalize_weights and weights:
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]
        
        return weights
    
    def _fuse_concatenate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fuse by concatenating values."""
        fused: Dict[str, Any] = {}
        
        for result in results:
            for key, value in result.items():
                if key in fused:
                    # Concatenate existing value with new value
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
        """Fuse by voting for each field."""
        from collections import Counter
        
        fused: Dict[str, Any] = {}
        
        # Collect all keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        for key in all_keys:
            # Get all values for this key
            values = [r.get(key) for r in results if key in r]
            
            if not values:
                continue
            
            # Count occurrences
            counter = Counter(values)
            
            # Get the most common value
            most_common = counter.most_common(1)[0][0]
            
            # If there's a tie, use the first one
            fused[key] = most_common
        
        return fused
    
    def _fuse_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fuse by finding consensus."""
        # For now, use voting as consensus
        return self._fuse_vote(results)
    
    def _fuse_best_of(self, results: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], int]:
        """Fuse by selecting the best result."""
        # Score each result
        scores = []
        for result in results:
            score = result.get("quality_score", result.get("score", 0))
            scores.append(float(score) if isinstance(score, (int, float)) else 0)
        
        # Find the best
        best_idx = max(range(len(scores)), key=lambda i: scores[i])
        
        return results[best_idx], best_idx
    
    def _fuse_weighted(self, results: List[Dict[str, Any]], weights: List[float]) -> Dict[str, Any]:
        """Fuse by weighting each result."""
        if len(results) != len(weights):
            logger.warning("Results and weights length mismatch. Using equal weights.")
            weights = [1.0 / len(results) for _ in range(len(results))]
        
        fused: Dict[str, Any] = {}
        
        # Collect all keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        for key in all_keys:
            # Get all values for this key
            values = [r.get(key) for r in results if key in r]
            
            if not values:
                continue
            
            # Check if values are numeric
            if all(isinstance(v, (int, float)) for v in values):
                # Weighted average
                weighted_sum = sum(v * w for v, w in zip(values, weights[:len(values)]))
                total_weight = sum(weights[:len(values)])
                fused[key] = weighted_sum / total_weight if total_weight > 0 else 0
            else:
                # For non-numeric, use the value from the highest weight
                max_weight_idx = max(range(len(weights[:len(values)])), key=lambda i: weights[i])
                fused[key] = values[max_weight_idx]
        
        return fused
    
    def _fuse_custom(self, results: List[Dict[str, Any]], config: FusionConfig) -> Dict[str, Any]:
        """Fuse using custom functions."""
        fused: Dict[str, Any] = {}
        
        # Collect all keys
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        
        for key in all_keys:
            # Check for custom fusion function
            if key in config.custom_fusion_functions:
                values = [r.get(key) for r in results if key in r]
                fused[key] = config.custom_fusion_functions[key](values)
            else:
                # Default to first value
                for result in results:
                    if key in result:
                        fused[key] = result[key]
                        break
        
        return fused
    
    def add_custom_fusion_function(self, field: str, func: Any) -> None:
        """Add a custom fusion function for a specific field."""
        self.config.custom_fusion_functions[field] = func
    
    def remove_custom_fusion_function(self, field: str) -> bool:
        """Remove a custom fusion function."""
        if field in self.config.custom_fusion_functions:
            del self.config.custom_fusion_functions[field]
            return True
        return False


# Global result fuser instance
result_fuser = None


def get_result_fuser(config: Optional[FusionConfig] = None) -> ResultFuser:
    """Get or create the global result fuser."""
    global result_fuser
    if result_fuser is None:
        result_fuser = ResultFuser(config)
    return result_fuser
