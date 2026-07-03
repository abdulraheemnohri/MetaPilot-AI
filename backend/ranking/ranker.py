"""
MetaPilot AI - Ranker

Ranks AI responses based on multiple criteria.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import json

logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """A ranked result with score and metadata."""
    result: Dict[str, Any]
    rank: int
    score: float
    normalized_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "normalized_score": self.normalized_score,
            "result": self.result,
            "metadata": self.metadata
        }


@dataclass
class RankingResult:
    """Result of a ranking operation."""
    ranked_results: List[RankedResult]
    total_results: int
    scoring_method: str
    ranking_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_results": self.total_results,
            "scoring_method": self.scoring_method,
            "ranking_time": self.ranking_time,
            "ranked_results": [r.to_dict() for r in self.ranked_results]
        }
    
    def get_top_k(self, k: int) -> List[RankedResult]:
        """Get the top k results."""
        return self.ranked_results[:k]
    
    def get_by_rank(self, rank: int) -> Optional[RankedResult]:
        """Get result by rank (1-based)."""
        if 1 <= rank <= len(self.ranked_results):
            return self.ranked_results[rank - 1]
        return None


class ScoringFunction:
    """Base class for scoring functions."""
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """
        Score a single result.
        
        Args:
            result: The result to score
            **kwargs: Additional arguments
        
        Returns:
            Score (0-1)
        """
        raise NotImplementedError("Subclasses must implement score()")


class CompositeScoringFunction(ScoringFunction):
    """Scoring function that combines multiple scoring functions."""
    
    def __init__(self, 
                 scoring_functions: List[ScoringFunction],
                 weights: Optional[List[float]] = None):
        """
        Initialize composite scoring function.
        
        Args:
            scoring_functions: List of scoring functions to combine
            weights: Optional weights for each function
        """
        self.scoring_functions = scoring_functions
        self.weights = weights or [1.0 / len(scoring_functions) for _ in scoring_functions]
        
        # Normalize weights
        total_weight = sum(self.weights)
        if total_weight > 0:
            self.weights = [w / total_weight for w in self.weights]
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """Score by combining all scoring functions."""
        scores = []
        
        for i, func in enumerate(self.scoring_functions):
            try:
                score = func.score(result, **kwargs)
                scores.append(score * self.weights[i])
            except Exception as e:
                logger.error(f"Error in scoring function {i}: {e}")
                scores.append(0.0)
        
        return sum(scores)


class Ranker:
    """
    Ranks AI responses based on multiple criteria.
    
    Uses scoring functions to evaluate and rank responses.
    """
    
    def __init__(self, 
                 scoring_function: Optional[ScoringFunction] = None,
                 default_method: str = "composite"):
        """
        Initialize the ranker.
        
        Args:
            scoring_function: Default scoring function to use
            default_method: Default ranking method
        """
        self.scoring_function = scoring_function
        self.default_method = default_method
        self._scoring_functions: Dict[str, ScoringFunction] = {}
        self._register_default_functions()
    
    def _register_default_functions(self):
        """Register default scoring functions."""
        # Register a basic scoring function
        self._scoring_functions["basic"] = BasicScoringFunction()
        
        # Register composite function
        self._scoring_functions["composite"] = CompositeScoringFunction(
            [
                BasicScoringFunction(),
                LengthScoringFunction(),
                RelevanceScoringFunction()
            ],
            weights=[0.4, 0.3, 0.3]
        )
    
    def register_scoring_function(self, name: str, func: ScoringFunction) -> None:
        """Register a scoring function."""
        self._scoring_functions[name] = func
    
    def get_scoring_function(self, name: str) -> Optional[ScoringFunction]:
        """Get a scoring function by name."""
        return self._scoring_functions.get(name)
    
    def rank(self, 
             results: List[Dict[str, Any]],
             method: Optional[str] = None,
             scoring_function: Optional[ScoringFunction] = None,
             reverse: bool = False,
             **kwargs) -> RankingResult:
        """
        Rank a list of results.
        
        Args:
            results: List of results to rank
            method: Ranking method to use
            scoring_function: Optional scoring function to use
            reverse: Whether to sort in reverse order (lowest first)
            **kwargs: Additional arguments for scoring function
        
        Returns:
            RankingResult with ranked results
        """
        import time
        start_time = time.time()
        
        if not results:
            return RankingResult(
                ranked_results=[],
                total_results=0,
                scoring_method=method or self.default_method,
                ranking_time=0.0
            )
        
        # Get scoring function
        effective_method = method or self.default_method
        func = scoring_function or self.get_scoring_function(effective_method)
        
        if not func:
            func = self.get_scoring_function(self.default_method)
            if not func:
                # Fallback to basic scoring
                func = BasicScoringFunction()
                effective_method = "basic"
        
        # Score all results
        scored_results = []
        for result in results:
            try:
                score = func.score(result, **kwargs)
                scored_results.append((result, score))
            except Exception as e:
                logger.error(f"Error scoring result: {e}")
                scored_results.append((result, 0.0))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=not reverse)
        
        # Normalize scores to 0-1 range
        if scored_results:
            min_score = min(s for _, s in scored_results)
            max_score = max(s for _, s in scored_results)
            score_range = max_score - min_score
            
            if score_range > 0:
                normalized_scores = [
                    (s - min_score) / score_range 
                    for _, s in scored_results
                ]
            else:
                normalized_scores = [0.5 for _ in scored_results]
        else:
            normalized_scores = []
        
        # Create ranked results
        ranked_results = []
        for i, (result, score) in enumerate(scored_results):
            ranked_results.append(RankedResult(
                result=result,
                rank=i + 1,
                score=score,
                normalized_score=normalized_scores[i] if i < len(normalized_scores) else 0.5,
                metadata={
                    "scoring_method": effective_method
                }
            ))
        
        return RankingResult(
            ranked_results=ranked_results,
            total_results=len(results),
            scoring_method=effective_method,
            ranking_time=time.time() - start_time
        )
    
    def rank_with_weights(self, 
                          results: List[Dict[str, Any]],
                          weights: Dict[str, float],
                          **kwargs) -> RankingResult:
        """
        Rank results using custom weights for different factors.
        
        Args:
            results: List of results to rank
            weights: Dictionary of factor weights
            **kwargs: Additional arguments
        
        Returns:
            RankingResult with ranked results
        """
        # Create a custom scoring function with the provided weights
        custom_func = CustomWeightedScoringFunction(weights)
        
        return self.rank(
            results,
            scoring_function=custom_func,
            **kwargs
        )


class BasicScoringFunction(ScoringFunction):
    """Basic scoring function that considers multiple factors."""
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """Score based on basic factors."""
        content = result.get("content", "") or result.get("text", "")
        
        if not content:
            return 0.0
        
        # Simple scoring based on length and some basic checks
        word_count = len(content.split())
        
        # Ideal length is around 50-200 words
        if word_count < 10:
            length_score = word_count / 10
        elif word_count < 50:
            length_score = 0.5 + (word_count - 10) / 80
        elif word_count < 200:
            length_score = 0.75 + (word_count - 50) / 300
        else:
            length_score = 1.0
        
        # Check for punctuation
        has_punctuation = any(p in content for p in ['.', '!', '?'])
        punctuation_score = 1.0 if has_punctuation else 0.5
        
        # Check for capitalization at start
        starts_with_capital = content[0].isupper() if content else False
        capital_score = 1.0 if starts_with_capital else 0.7
        
        # Combine scores
        return 0.4 * length_score + 0.3 * punctuation_score + 0.3 * capital_score


class LengthScoringFunction(ScoringFunction):
    """Scoring function based on length."""
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """Score based on length."""
        content = result.get("content", "") or result.get("text", "")
        word_count = len(content.split())
        
        # Normalize to 0-1 with ideal at 100 words
        if word_count >= 100:
            return 1.0
        return min(1.0, word_count / 100)


class RelevanceScoringFunction(ScoringFunction):
    """Scoring function based on relevance to query."""
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """Score based on relevance."""
        content = result.get("content", "") or result.get("text", "")
        query = kwargs.get("query", "")
        
        if not query:
            return 0.5
        
        from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
        detector = SimilarityDetector()
        result = detector.compare(query, content, SimilarityMethod.JACCARD)
        
        return result.score


class CustomWeightedScoringFunction(ScoringFunction):
    """Scoring function with custom weights for different factors."""
    
    def __init__(self, weights: Dict[str, float]):
        """
        Initialize with custom weights.
        
        Args:
            weights: Dictionary of factor weights
        """
        self.weights = weights
    
    def score(self, result: Dict[str, Any], **kwargs) -> float:
        """Score based on weighted factors."""
        score = 0.0
        total_weight = 0.0
        
        for factor, weight in self.weights.items():
            factor_score = self._get_factor_score(factor, result, kwargs)
            score += factor_score * weight
            total_weight += weight
        
        if total_weight > 0:
            return score / total_weight
        return 0.0
    
    def _get_factor_score(self, factor: str, result: Dict[str, Any], kwargs: Dict[str, Any]) -> float:
        """Get score for a specific factor."""
        content = result.get("content", "") or result.get("text", "")
        
        if factor == "length":
            word_count = len(content.split())
            return min(1.0, word_count / 100)
        
        elif factor == "punctuation":
            return 1.0 if any(p in content for p in ['.', '!', '?']) else 0.0
        
        elif factor == "capitalization":
            return 1.0 if content and content[0].isupper() else 0.0
        
        elif factor == "relevance":
            query = kwargs.get("query", "")
            if not query:
                return 0.5
            from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
            detector = SimilarityDetector()
            result = detector.compare(query, content, SimilarityMethod.JACCARD)
            return result.score
        
        elif factor == "completeness":
            word_count = len(content.split())
            if word_count < 10:
                return 0.0
            elif word_count < 50:
                return 0.5
            else:
                return 1.0
        
        else:
            return 0.5


# Global ranker instance
ranker = None


def get_ranker(scoring_function: Optional[ScoringFunction] = None,
               default_method: str = "composite") -> Ranker:
    """Get or create the global ranker."""
    global ranker
    if ranker is None:
        ranker = Ranker(scoring_function, default_method)
    return ranker
