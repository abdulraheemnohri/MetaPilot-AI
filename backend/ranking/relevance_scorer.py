"""
MetaPilot AI - Relevance Scorer

Scores how relevant AI responses are to the user's query.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import json

logger = logging.getLogger(__name__)


class RelevanceFactor(Enum):
    """Factors that contribute to relevance."""
    KEYWORD_MATCH = "keyword_match"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    QUERY_COVERAGE = "query_coverage"
    CONTEXTUAL_FIT = "contextual_fit"
    SPECIFICITY = "specificity"


@dataclass
class RelevanceScore:
    """Represents a relevance score."""
    score: float  # 0-1
    factor_scores: Dict[RelevanceFactor, float] = field(default_factory=dict)
    explanation: str = ""
    matched_terms: List[str] = field(default_factory=list)
    missing_terms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "factor_scores": {k.value: v for k, v in self.factor_scores.items()},
            "explanation": self.explanation,
            "matched_terms": self.matched_terms,
            "missing_terms": self.missing_terms
        }


class RelevanceScorer:
    """
    Scores how relevant AI responses are to user queries.
    
    Uses multiple techniques to determine relevance, including:
    - Keyword matching
    - Semantic similarity
    - Query coverage
    - Contextual fit
    """
    
    def __init__(self, 
                 factor_weights: Optional[Dict[RelevanceFactor, float]] = None,
                 use_semantic: bool = True,
                 embedding_model: Optional[Any] = None):
        """
        Initialize the relevance scorer.
        
        Args:
            factor_weights: Weights for different relevance factors
            use_semantic: Whether to use semantic similarity
            embedding_model: Optional embedding model for semantic comparison
        """
        self.factor_weights = factor_weights or {
            RelevanceFactor.KEYWORD_MATCH: 0.3,
            RelevanceFactor.SEMANTIC_SIMILARITY: 0.3,
            RelevanceFactor.QUERY_COVERAGE: 0.2,
            RelevanceFactor.CONTEXTUAL_FIT: 0.1,
            RelevanceFactor.SPECIFICITY: 0.1
        }
        
        self.use_semantic = use_semantic and embedding_model is not None
        self.embedding_model = embedding_model
    
    def score(self, 
              response: Dict[str, Any],
              query: str,
              context: Optional[Dict[str, Any]] = None) -> RelevanceScore:
        """
        Score the relevance of a response to a query.
        
        Args:
            response: The AI response to score
            query: The user's query
            context: Additional context
        
        Returns:
            RelevanceScore with score and details
        """
        content = response.get("content", "") or response.get("text", "")
        
        if not content or not query:
            return RelevanceScore(
                score=0.0,
                explanation="Empty response or query"
            )
        
        factor_scores: Dict[RelevanceFactor, float] = {}
        matched_terms: List[str] = []
        missing_terms: List[str] = []
        
        # Score each factor
        for factor in RelevanceFactor:
            score, matched, missing = self._score_factor(factor, content, query, context)
            factor_scores[factor] = score
            matched_terms.extend(matched)
            missing_terms.extend(missing)
        
        # Calculate overall score (weighted average)
        total_weight = sum(self.factor_weights.values())
        overall_score = sum(
            factor_scores[f] * self.factor_weights.get(f, 0) 
            for f in factor_scores
        ) / total_weight if total_weight > 0 else 0
        
        # Generate explanation
        explanation = self._generate_explanation(overall_score, factor_scores)
        
        # Deduplicate terms
        matched_terms = list(set(matched_terms))
        missing_terms = list(set(missing_terms))
        
        return RelevanceScore(
            score=round(overall_score, 4),
            factor_scores=factor_scores,
            explanation=explanation,
            matched_terms=matched_terms,
            missing_terms=missing_terms
        )
    
    def score_batch(self, 
                    responses: List[Dict[str, Any]],
                    query: str,
                    context: Optional[Dict[str, Any]] = None) -> List[RelevanceScore]:
        """
        Score relevance for multiple responses.
        
        Args:
            responses: List of responses to score
            query: The user's query
            context: Additional context
        
        Returns:
            List of RelevanceScore objects
        """
        return [self.score(response, query, context) for response in responses]
    
    def _score_factor(self, 
                      factor: RelevanceFactor,
                      content: str,
                      query: str,
                      context: Optional[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
        """Score a specific relevance factor."""
        try:
            if factor == RelevanceFactor.KEYWORD_MATCH:
                return self._score_keyword_match(content, query)
            elif factor == RelevanceFactor.SEMANTIC_SIMILARITY:
                return self._score_semantic_similarity(content, query), [], []
            elif factor == RelevanceFactor.QUERY_COVERAGE:
                return self._score_query_coverage(content, query)
            elif factor == RelevanceFactor.CONTEXTUAL_FIT:
                return self._score_contextual_fit(content, query, context), [], []
            elif factor == RelevanceFactor.SPECIFICITY:
                return self._score_specificity(content, query), [], []
            else:
                return 0.5, [], []
        except Exception as e:
            logger.error(f"Error scoring factor {factor.value}: {e}")
            return 0.5, [], []
    
    def _score_keyword_match(self, content: str, query: str) -> Tuple[float, List[str], List[str]]:
        """Score based on keyword matching."""
        # Extract keywords from query
        query_keywords = self._extract_keywords(query)
        content_keywords = self._extract_keywords(content)
        
        # Find matched and missing keywords
        matched = [kw for kw in query_keywords if kw in content_keywords]
        missing = [kw for kw in query_keywords if kw not in content_keywords]
        
        if not query_keywords:
            return 0.5, [], []
        
        # Calculate match ratio
        match_ratio = len(matched) / len(query_keywords) if query_keywords else 0
        
        # Bonus for exact matches of important terms
        important_terms = [kw for kw in query_keywords if len(kw) > 3]
        if important_terms:
            important_matches = [t for t in important_terms if t in content_keywords]
            important_ratio = len(important_matches) / len(important_terms)
            match_ratio = 0.7 * match_ratio + 0.3 * important_ratio
        
        return match_ratio, matched, missing
    
    def _score_semantic_similarity(self, content: str, query: str) -> float:
        """Score based on semantic similarity."""
        if not self.use_semantic or not self.embedding_model:
            # Fallback to Jaccard similarity
            from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
            detector = SimilarityDetector()
            result = detector.compare(query, content, SimilarityMethod.JACCARD)
            return result.score
        
        try:
            import asyncio
            from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
            
            detector = SimilarityDetector(self.embedding_model)
            result = detector.compare(query, content, SimilarityMethod.SEMANTIC)
            return result.score
            
        except Exception as e:
            logger.error(f"Error in semantic similarity: {e}")
            # Fallback
            from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
            detector = SimilarityDetector()
            result = detector.compare(query, content, SimilarityMethod.JACCARD)
            return result.score
    
    def _score_query_coverage(self, content: str, query: str) -> Tuple[float, List[str], List[str]]:
        """Score based on how well the query is covered."""
        # Split query into parts (questions, statements)
        query_parts = self._split_query(query)
        
        matched_parts = []
        missing_parts = []
        
        for part in query_parts:
            # Check if this part is addressed in the content
            if self._is_part_addressed(part, content):
                matched_parts.append(part)
            else:
                missing_parts.append(part)
        
        if not query_parts:
            return 0.5, [], []
        
        coverage = len(matched_parts) / len(query_parts)
        
        return coverage, matched_parts, missing_parts
    
    def _score_contextual_fit(self, content: str, query: str, context: Optional[Dict[str, Any]]) -> float:
        """Score based on contextual fit."""
        # Check if response fits the context
        if not context:
            return 0.5
        
        # Check for conversation context
        if "conversation_history" in context:
            history = context["conversation_history"]
            # Simple check: does the response reference previous messages?
            for msg in history[-3:]:  # Check last 3 messages
                msg_content = msg.get("content", "") or msg.get("text", "")
                if msg_content and msg_content in content:
                    return 0.8
            return 0.5
        
        # Check for user preferences
        if "user_preferences" in context:
            prefs = context["user_preferences"]
            # Check if response aligns with preferences
            if prefs.get("verbose") and len(content.split()) > 50:
                return 0.7
            elif not prefs.get("verbose") and len(content.split()) < 50:
                return 0.7
        
        return 0.5
    
    def _score_specificity(self, content: str, query: str) -> float:
        """Score based on how specific the response is to the query."""
        # Check if response directly addresses the query
        query_keywords = self._extract_keywords(query)
        content_keywords = self._extract_keywords(content)
        
        if not query_keywords:
            return 0.5
        
        # Calculate specificity as the ratio of query keywords in content
        query_in_content = [kw for kw in query_keywords if kw in content_keywords]
        specificity = len(query_in_content) / len(query_keywords) if query_keywords else 0
        
        # Bonus for using query keywords prominently
        content_lower = content.lower()
        early_usage = sum(
            1 for kw in query_keywords 
            if kw in content_lower[:len(content_lower) // 2]
        )
        early_ratio = early_usage / len(query_keywords) if query_keywords else 0
        
        return 0.7 * specificity + 0.3 * early_ratio
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove punctuation and split
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter out common words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'should', 'could', 'may', 'might',
            'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her',
            'its', 'our', 'their'
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _split_query(self, query: str) -> List[str]:
        """Split query into logical parts."""
        # Split by question marks and periods
        parts = re.split(r'[.!?]', query)
        
        # Filter out empty parts
        return [p.strip() for p in parts if p.strip()]
    
    def _is_part_addressed(self, part: str, content: str) -> bool:
        """Check if a query part is addressed in the content."""
        part_keywords = self._extract_keywords(part)
        content_keywords = self._extract_keywords(content)
        
        if not part_keywords:
            return True
        
        # Check if most keywords from the part are in the content
        matched = sum(1 for kw in part_keywords if kw in content_keywords)
        return matched / len(part_keywords) >= 0.5
    
    def _generate_explanation(self, score: float, factor_scores: Dict[RelevanceFactor, float]) -> str:
        """Generate a human-readable explanation."""
        if score >= 0.8:
            return f"Highly relevant ({score:.2%})"
        elif score >= 0.6:
            return f"Relevant ({score:.2%})"
        elif score >= 0.4:
            return f"Somewhat relevant ({score:.2%})"
        else:
            return f"Not very relevant ({score:.2%})"


# Global relevance scorer instance
relevance_scorer = None


def get_relevance_scorer(factor_weights: Optional[Dict[RelevanceFactor, float]] = None,
                         use_semantic: bool = True,
                         embedding_model: Optional[Any] = None) -> RelevanceScorer:
    """Get or create the global relevance scorer."""
    global relevance_scorer
    if relevance_scorer is None:
        relevance_scorer = RelevanceScorer(factor_weights, use_semantic, embedding_model)
    return relevance_scorer
