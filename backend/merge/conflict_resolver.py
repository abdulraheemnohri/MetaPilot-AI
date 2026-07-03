"""
MetaPilot AI - Conflict Resolver

Resolves conflicts between multiple AI responses.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import hashlib

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts."""
    FIRST = "first"  # Use the first response
    LAST = "last"  # Use the last response
    LONGEST = "longest"  # Use the longest response
    SHORTEST = "shortest"  # Use the shortest response
    MAJORITY = "majority"  # Use the most common response
    CONSENSUS = "consensus"  # Try to find consensus
    CUSTOM = "custom"  # Use custom resolver function


@dataclass
class Conflict:
    """Represents a conflict between responses."""
    field: str
    responses: List[Any]
    strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MAJORITY
    resolved_value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "responses": self.responses,
            "strategy": self.strategy.value,
            "resolved_value": self.resolved_value
        }


@dataclass
class ConflictResolutionResult:
    """Result of conflict resolution."""
    original_responses: List[Dict[str, Any]]
    resolved_response: Dict[str, Any]
    conflicts: List[Conflict] = field(default_factory=list)
    resolution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_responses": self.original_responses,
            "resolved_response": self.resolved_response,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "resolution_time": self.resolution_time
        }


class ConflictResolver:
    """
    Resolves conflicts between multiple AI responses.
    
    When multiple AI systems provide different answers to the same question,
    this class helps resolve those conflicts using various strategies.
    """
    
    def __init__(self, 
                 default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MAJORITY,
                 custom_resolvers: Optional[Dict[str, Any]] = None):
        """
        Initialize the conflict resolver.
        
        Args:
            default_strategy: Default strategy for resolving conflicts
            custom_resolvers: Dictionary of custom resolver functions by field
        """
        self.default_strategy = default_strategy
        self.custom_resolvers = custom_resolvers or {}
    
    def resolve(self, 
                responses: List[Dict[str, Any]],
                strategy: Optional[ConflictResolutionStrategy] = None,
                field_strategies: Optional[Dict[str, ConflictResolutionStrategy]] = None) -> ConflictResolutionResult:
        """
        Resolve conflicts between multiple responses.
        
        Args:
            responses: List of response dictionaries
            strategy: Default strategy to use
            field_strategies: Per-field strategies
        
        Returns:
            ConflictResolutionResult with resolved response
        """
        import time
        start_time = time.time()
        
        if not responses:
            return ConflictResolutionResult(
                original_responses=[],
                resolved_response={},
                conflicts=[],
                resolution_time=0.0
            )
        
        if len(responses) == 1:
            return ConflictResolutionResult(
                original_responses=responses,
                resolved_response=responses[0],
                conflicts=[],
                resolution_time=time.time() - start_time
            )
        
        # Collect all fields
        all_fields = set()
        for response in responses:
            all_fields.update(response.keys())
        
        resolved_response: Dict[str, Any] = {}
        conflicts: List[Conflict] = []
        
        # Resolve each field
        for field in all_fields:
            # Get all values for this field
            values = [r.get(field) for r in responses]
            
            # Check if there's a conflict (not all values are the same)
            if self._has_conflict(values):
                # Get strategy for this field
                field_strategy = field_strategies.get(field) if field_strategies else None
                strategy = field_strategy or strategy or self.default_strategy
                
                # Resolve the conflict
                resolved_value, conflict = self._resolve_field(field, values, strategy)
                
                resolved_response[field] = resolved_value
                conflicts.append(conflict)
            else:
                # No conflict, use the first non-None value
                resolved_response[field] = next((v for v in values if v is not None), None)
        
        return ConflictResolutionResult(
            original_responses=responses,
            resolved_response=resolved_response,
            conflicts=conflicts,
            resolution_time=time.time() - start_time
        )
    
    def _has_conflict(self, values: List[Any]) -> bool:
        """Check if there's a conflict in the values."""
        # Remove None values
        non_none_values = [v for v in values if v is not None]
        
        if not non_none_values:
            return False
        
        # Check if all values are the same
        first = non_none_values[0]
        return any(self._values_differ(v, first) for v in non_none_values[1:])
    
    def _values_differ(self, v1: Any, v2: Any) -> bool:
        """Check if two values differ."""
        if type(v1) != type(v2):
            return True
        
        if isinstance(v1, (list, dict)):
            return json.dumps(v1, sort_keys=True) != json.dumps(v2, sort_keys=True)
        
        return v1 != v2
    
    def _resolve_field(self, 
                       field: str,
                       values: List[Any],
                       strategy: ConflictResolutionStrategy) -> Tuple[Any, Conflict]:
        """
        Resolve a conflict for a specific field.
        
        Args:
            field: Field name
            values: List of values for this field
            strategy: Strategy to use
        
        Returns:
            Tuple of (resolved_value, Conflict)
        """
        # Remove None values
        non_none_values = [v for v in values if v is not None]
        
        if not non_none_values:
            return None, Conflict(field=field, responses=values, strategy=strategy)
        
        # Check for custom resolver
        if field in self.custom_resolvers:
            resolved_value = self.custom_resolvers[field](non_none_values)
            return resolved_value, Conflict(
                field=field,
                responses=values,
                strategy=strategy,
                resolved_value=resolved_value
            )
        
        # Apply strategy
        if strategy == ConflictResolutionStrategy.FIRST:
            resolved_value = non_none_values[0]
        elif strategy == ConflictResolutionStrategy.LAST:
            resolved_value = non_none_values[-1]
        elif strategy == ConflictResolutionStrategy.LONGEST:
            resolved_value = max(non_none_values, key=lambda x: len(str(x)))
        elif strategy == ConflictResolutionStrategy.SHORTEST:
            resolved_value = min(non_none_values, key=lambda x: len(str(x)))
        elif strategy == ConflictResolutionStrategy.MAJORITY:
            resolved_value = self._majority_vote(non_none_values)
        elif strategy == ConflictResolutionStrategy.CONSENSUS:
            resolved_value = self._find_consensus(non_none_values)
        else:  # CUSTOM or unknown
            resolved_value = non_none_values[0]
        
        return resolved_value, Conflict(
            field=field,
            responses=values,
            strategy=strategy,
            resolved_value=resolved_value
        )
    
    def _majority_vote(self, values: List[Any]) -> Any:
        """
        Find the value that appears most frequently.
        
        Args:
            values: List of values
        
        Returns:
            The most common value
        """
        if not values:
            return None
        
        # Count occurrences
        counts: Dict[str, Any] = {}
        for value in values:
            # Use JSON for hashable representation
            key = json.dumps(value, sort_keys=True, default=str)
            counts[key] = counts.get(key, 0) + 1
        
        # Find the value with the highest count
        max_count = max(counts.values())
        majority_keys = [k for k, v in counts.items() if v == max_count]
        
        # If there's a tie, return the first one
        return json.loads(majority_keys[0])
    
    def _find_consensus(self, values: List[Any]) -> Any:
        """
        Try to find a consensus value.
        
        This looks for common substrings or patterns.
        
        Args:
            values: List of values
        
        Returns:
            Consensus value or the first value if no consensus found
        """
        if len(values) == 1:
            return values[0]
        
        # For strings, try to find common substrings
        if all(isinstance(v, str) for v in values):
            return self._find_string_consensus([str(v) for v in values])
        
        # For other types, use majority vote
        return self._majority_vote(values)
    
    def _find_string_consensus(self, strings: List[str]) -> str:
        """Find consensus among strings."""
        # Simple implementation: find the longest common substring
        if not strings:
            return ""
        
        if len(strings) == 1:
            return strings[0]
        
        # Find the longest common substring
        shortest = min(strings, key=len)
        max_len = len(shortest)
        
        for length in range(max_len, 0, -1):
            for start in range(0, max_len - length + 1):
                substring = shortest[start:start + length]
                if all(substring in s for s in strings):
                    return substring
        
        # If no common substring, return the first string
        return strings[0]
    
    def add_custom_resolver(self, field: str, resolver: Any) -> None:
        """
        Add a custom resolver for a specific field.
        
        Args:
            field: Field name
            resolver: Function that takes a list of values and returns a resolved value
        """
        self.custom_resolvers[field] = resolver
    
    def remove_custom_resolver(self, field: str) -> bool:
        """
        Remove a custom resolver for a specific field.
        
        Args:
            field: Field name
        
        Returns:
            True if resolver was removed
        """
        if field in self.custom_resolvers:
            del self.custom_resolvers[field]
            return True
        return False


# Global conflict resolver instance
conflict_resolver = None


def get_conflict_resolver(default_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MAJORITY,
                           custom_resolvers: Optional[Dict[str, Any]] = None) -> ConflictResolver:
    """Get or create the global conflict resolver."""
    global conflict_resolver
    if conflict_resolver is None:
        conflict_resolver = ConflictResolver(default_strategy, custom_resolvers)
    return conflict_resolver
