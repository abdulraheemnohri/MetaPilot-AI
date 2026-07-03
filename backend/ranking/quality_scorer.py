"""
MetaPilot AI - Quality Scorer

Scores the quality of AI responses.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import json

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metrics to evaluate."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    ORIGINALITY = "originality"
    GRAMMAR = "grammar"
    STRUCTURE = "structure"
    DEPTH = "depth"


@dataclass
class QualityScore:
    """Represents a quality score."""
    overall_score: float  # 0-1
    metric_scores: Dict[QualityMetric, float] = field(default_factory=dict)
    explanation: str = ""
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "metric_scores": {k.value: v for k, v in self.metric_scores.items()},
            "explanation": self.explanation,
            "suggestions": self.suggestions
        }


class QualityScorer:
    """
    Scores the quality of AI responses.
    
    Evaluates responses across multiple dimensions to determine overall quality.
    """
    
    def __init__(self, 
                 metric_weights: Optional[Dict[QualityMetric, float]] = None,
                 enable_all_metrics: bool = True):
        """
        Initialize the quality scorer.
        
        Args:
            metric_weights: Weights for different quality metrics
            enable_all_metrics: Whether to enable all metrics by default
        """
        # Default weights
        self.metric_weights = metric_weights or {
            QualityMetric.COMPLETENESS: 0.15,
            QualityMetric.ACCURACY: 0.15,
            QualityMetric.RELEVANCE: 0.20,
            QualityMetric.CLARITY: 0.15,
            QualityMetric.ORIGINALITY: 0.10,
            QualityMetric.GRAMMAR: 0.10,
            QualityMetric.STRUCTURE: 0.10,
            QualityMetric.DEPTH: 0.05
        }
        
        # Enabled metrics
        self.enabled_metrics = [
            m for m in QualityMetric 
            if enable_all_metrics or m in self.metric_weights
        ]
    
    def score(self, 
              response: Dict[str, Any],
              query: Optional[str] = None,
              context: Optional[Dict[str, Any]] = None) -> QualityScore:
        """
        Score the quality of a response.
        
        Args:
            response: The AI response to score
            query: The original query (for relevance scoring)
            context: Additional context
        
        Returns:
            QualityScore with scores and explanation
        """
        content = response.get("content", "") or response.get("text", "")
        
        if not content:
            return QualityScore(
                overall_score=0.0,
                metric_scores={},
                explanation="Empty response",
                suggestions=["Provide a response"]
            )
        
        metric_scores: Dict[QualityMetric, float] = {}
        suggestions: List[str] = []
        
        # Score each metric
        for metric in self.enabled_metrics:
            score, metric_suggestions = self._score_metric(metric, content, query, context)
            metric_scores[metric] = score
            suggestions.extend(metric_suggestions)
        
        # Calculate overall score (weighted average)
        total_weight = sum(
            self.metric_weights.get(m, 0) 
            for m in metric_scores.keys()
        )
        
        if total_weight == 0:
            overall_score = sum(metric_scores.values()) / len(metric_scores) if metric_scores else 0
        else:
            overall_score = sum(
                metric_scores[m] * self.metric_weights.get(m, 0) 
                for m in metric_scores.keys()
            ) / total_weight
        
        # Generate explanation
        explanation = self._generate_explanation(overall_score, metric_scores)
        
        # Deduplicate suggestions
        suggestions = list(set(suggestions))
        
        return QualityScore(
            overall_score=round(overall_score, 4),
            metric_scores=metric_scores,
            explanation=explanation,
            suggestions=suggestions
        )
    
    def score_batch(self, 
                    responses: List[Dict[str, Any]],
                    query: Optional[str] = None,
                    context: Optional[Dict[str, Any]] = None) -> List[QualityScore]:
        """
        Score multiple responses.
        
        Args:
            responses: List of responses to score
            query: The original query
            context: Additional context
        
        Returns:
            List of QualityScore objects
        """
        return [self.score(response, query, context) for response in responses]
    
    def _score_metric(self, 
                      metric: QualityMetric,
                      content: str,
                      query: Optional[str],
                      context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score a specific metric."""
        try:
            if metric == QualityMetric.COMPLETENESS:
                return self._score_completeness(content, query, context)
            elif metric == QualityMetric.ACCURACY:
                return self._score_accuracy(content, query, context)
            elif metric == QualityMetric.RELEVANCE:
                return self._score_relevance(content, query, context)
            elif metric == QualityMetric.CLARITY:
                return self._score_clarity(content, query, context)
            elif metric == QualityMetric.ORIGINALITY:
                return self._score_originality(content, query, context)
            elif metric == QualityMetric.GRAMMAR:
                return self._score_grammar(content, query, context)
            elif metric == QualityMetric.STRUCTURE:
                return self._score_structure(content, query, context)
            elif metric == QualityMetric.DEPTH:
                return self._score_depth(content, query, context)
            else:
                return 0.5, []
        except Exception as e:
            logger.error(f"Error scoring metric {metric.value}: {e}")
            return 0.5, [f"Error scoring {metric.value}"]
    
    def _score_completeness(self, 
                           content: str,
                           query: Optional[str],
                           context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score how complete the response is."""
        suggestions = []
        
        # Check if response answers the query
        if query:
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())
            
            # Check for overlap
            overlap = query_words & content_words
            if not overlap:
                suggestions.append("Response does not address the query")
                return 0.3, suggestions
            
            # Check if all key query terms are addressed
            coverage = len(overlap) / len(query_words) if query_words else 1
            
            if coverage < 0.5:
                suggestions.append("Response does not fully address the query")
                return 0.5, suggestions
        
        # Check for common incomplete patterns
        incomplete_patterns = [
            r"\.\.\.",  # Ellipsis at end
            r"to be continued",
            r"etc\.",
            r"and so on",
            r"and more"
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                suggestions.append("Response seems incomplete")
                return 0.6, suggestions
        
        # Check length
        word_count = len(content.split())
        if word_count < 10:
            suggestions.append("Response is too short")
            return 0.4, suggestions
        
        return 0.9, []
    
    def _score_accuracy(self, 
                       content: str,
                       query: Optional[str],
                       context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score the accuracy of the response."""
        suggestions = []
        
        # This is hard to score without ground truth
        # Use heuristics based on the content
        
        # Check for hallucination indicators
        hallucination_patterns = [
            r"i don't know",
            r"i'm not sure",
            r"i cannot",
            r"i can't",
            r"i don't have",
            r"i am unable"
        ]
        
        for pattern in hallucination_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                suggestions.append("Response indicates uncertainty")
                return 0.6, suggestions
        
        # Check for factual statements (hard to verify, but we can check for confidence)
        # For now, assume medium accuracy
        return 0.7, []
    
    def _score_relevance(self, 
                        content: str,
                        query: Optional[str],
                        context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score how relevant the response is to the query."""
        from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
        
        if not query:
            return 0.5, ["No query provided for relevance scoring"]
        
        detector = SimilarityDetector()
        result = detector.compare(query, content, SimilarityMethod.JACCARD)
        
        if result.score < 0.3:
            return 0.3, ["Response is not relevant to the query"]
        elif result.score < 0.5:
            return 0.5, ["Response is somewhat relevant to the query"]
        elif result.score < 0.7:
            return 0.7, []
        else:
            return 0.9, []
    
    def _score_clarity(self, 
                      content: str,
                      query: Optional[str],
                      context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score how clear the response is."""
        suggestions = []
        
        # Check for readability
        sentences = re.split(r'[.!?]+', content)
        
        if not sentences:
            return 0.3, ["Response has no clear sentences"]
        
        # Check for very long sentences
        long_sentences = [s for s in sentences if len(s.split()) > 30]
        if long_sentences:
            suggestions.append(f"Response has {len(long_sentences)} long sentences")
            return 0.6, suggestions
        
        # Check for very short sentences
        short_sentences = [s for s in sentences if len(s.strip().split()) < 3 and len(s.strip()) > 0]
        if len(short_sentences) > len(sentences) * 0.3:
            suggestions.append("Response has many short, unclear sentences")
            return 0.6, suggestions
        
        # Check for jargon (words with many capital letters)
        jargon_words = [w for w in content.split() if w.isupper() and len(w) > 2]
        if len(jargon_words) > len(content.split()) * 0.1:
            suggestions.append("Response contains excessive jargon")
            return 0.7, suggestions
        
        return 0.9, []
    
    def _score_originality(self, 
                         content: str,
                         query: Optional[str],
                         context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score how original the response is."""
        if not context or "other_responses" not in context:
            return 0.7, []  # Can't score without other responses
        
        other_responses = context["other_responses"]
        if not other_responses:
            return 0.7, []
        
        from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
        detector = SimilarityDetector()
        
        # Compare with other responses
        max_similarity = 0
        for other in other_responses:
            other_content = other.get("content", "") or other.get("text", "")
            if other_content:
                result = detector.compare(content, other_content, SimilarityMethod.JACCARD)
                max_similarity = max(max_similarity, result.score)
        
        # Higher similarity means less original
        originality = 1.0 - max_similarity * 0.8
        
        if originality < 0.3:
            return originality, ["Response is very similar to other responses"]
        elif originality < 0.6:
            return originality, ["Response is somewhat similar to other responses"]
        
        return originality, []
    
    def _score_grammar(self, 
                      content: str,
                      query: Optional[str],
                      context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score the grammar of the response."""
        suggestions = []
        
        # Check for basic grammar issues
        # This is a simplified check
        
        # Check for multiple spaces
        if "  " in content:
            suggestions.append("Response has double spaces")
            return 0.7, suggestions
        
        # Check for sentences starting with lowercase
        sentences = re.split(r'[.!?]+', content)
        lowercase_starts = [
            s for s in sentences 
            if s.strip() and s.strip()[0].islower() and len(s.strip()) > 1
        ]
        
        if lowercase_starts:
            suggestions.append(f"Response has {len(lowercase_starts)} sentences starting with lowercase")
            return 0.7, suggestions
        
        # Check for missing punctuation
        if not any(p in content for p in ['.', '!', '?']):
            suggestions.append("Response is missing punctuation")
            return 0.6, suggestions
        
        return 0.9, []
    
    def _score_structure(self, 
                         content: str,
                         query: Optional[str],
                         context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score the structure of the response."""
        suggestions = []
        
        # Check for logical structure
        lines = content.split('\n')
        
        # Check for headings
        has_headings = any(line.startswith('#') for line in lines)
        
        # Check for lists
        has_lists = any(
            line.startswith(('- ', '* ', '1. ', '   ')) 
            for line in lines
        )
        
        # Check for paragraphs
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        if len(paragraphs) < 2 and len(content) > 200:
            suggestions.append("Response could benefit from paragraph breaks")
            return 0.7, suggestions
        
        # If it has structure elements, score higher
        structure_score = 0.7
        if has_headings:
            structure_score += 0.1
        if has_lists:
            structure_score += 0.1
        if len(paragraphs) >= 3:
            structure_score += 0.1
        
        return min(1.0, structure_score), []
    
    def _score_depth(self, 
                     content: str,
                     query: Optional[str],
                     context: Optional[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score the depth of the response."""
        # Check for depth indicators
        depth_indicators = [
            "in detail",
            "specifically",
            "for example",
            "such as",
            "first",
            "second",
            "third",
            "additionally",
            "moreover",
            "furthermore"
        ]
        
        content_lower = content.lower()
        indicator_count = sum(1 for indicator in depth_indicators if indicator in content_lower)
        
        word_count = len(content.split())
        
        if word_count == 0:
            return 0.0, ["Empty response"]
        
        # Depth score based on indicators and length
        depth_score = min(1.0, indicator_count * 0.1 + min(word_count / 100, 0.5))
        
        return depth_score, []
    
    def _generate_explanation(self, score: float, metric_scores: Dict[QualityMetric, float]) -> str:
        """Generate a human-readable explanation."""
        if score >= 0.8:
            return f"High quality response ({score:.2%})"
        elif score >= 0.6:
            return f"Good quality response ({score:.2%})"
        elif score >= 0.4:
            return f"Acceptable quality response ({score:.2%})"
        else:
            return f"Low quality response ({score:.2%})"


# Global quality scorer instance
quality_scorer = None


def get_quality_scorer(metric_weights: Optional[Dict[QualityMetric, float]] = None,
                      enable_all_metrics: bool = True) -> QualityScorer:
    """Get or create the global quality scorer."""
    global quality_scorer
    if quality_scorer is None:
        quality_scorer = QualityScorer(metric_weights, enable_all_metrics)
    return quality_scorer
