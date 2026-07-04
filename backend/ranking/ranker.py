"""
MetaPilot AI - Ranker

Ranks multiple AI responses based on various factors.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

logger = logging.getLogger(__name__)

ScoringFunction = Callable[[Dict[str, Any]], float]

class Ranker:
    """
    Ranks AI responses based on quality, relevance, and completeness.
    """
    
    def __init__(self, 
                 scoring_function: Optional[ScoringFunction] = None,
                 default_method: str = "composite"):
        self.scoring_function = scoring_function or self._default_scoring_function
        self.default_method = default_method
        self.weights = {
            "length": 0.1,
            "punctuation": 0.1,
            "capitalization": 0.1,
            "relevance": 0.4,
            "completeness": 0.3
        }

    def rank(self, results: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        Rank a list of results.
        """
        if not results:
            return []

        scored_results = []
        for result in results:
            score = self.scoring_function(result, **kwargs)
            result_copy = result.copy()
            result_copy["quality_score"] = score
            scored_results.append(result_copy)
            
        return sorted(scored_results, key=lambda x: x["quality_score"], reverse=True)

    def _default_scoring_function(self, result: Dict[str, Any], **kwargs) -> float:
        score = 0.0
        total_weight = 0.0
        
        for factor, weight in self.weights.items():
            factor_score = self._get_factor_score(factor, result, kwargs)
            score += factor_score * weight
            total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _get_factor_score(self, factor: str, result: Dict[str, Any], kwargs: Dict[str, Any]) -> float:
        content = result.get("content", "") or result.get("text", "")
        
        if factor == "length":
            word_count = len(content.split())
            return min(1.0, word_count / 100)
        elif factor == "punctuation":
            return 1.0 if any(p in content for p in ['.', '!', '?']) else 0.0
        elif factor == "capitalization":
            return 1.0 if content and content[0].isupper() else 0.0
        elif factor == "completeness":
            word_count = len(content.split())
            return 1.0 if word_count > 50 else 0.5
        elif factor == "relevance":
            return 0.8  # Placeholder
        return 0.5

# Global ranker instance
ranker = Ranker()

def get_ranker(scoring_function: Optional[ScoringFunction] = None,
               default_method: str = "composite") -> Ranker:
    global ranker
    if scoring_function or default_method != "composite":
        return Ranker(scoring_function, default_method)
    return ranker
