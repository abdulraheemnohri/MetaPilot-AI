"""
MetaPilot AI - Confidence Calculator

Calculates confidence scores for AI responses.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import json

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ConfidenceScore:
    """Represents a confidence score."""
    score: float  # 0-1
    level: ConfidenceLevel
    explanation: str
    factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level.value,
            "explanation": self.explanation,
            "factors": self.factors
        }


class ConfidenceCalculator:
    """
    Calculates confidence scores for AI responses.
    
    Considers multiple factors to determine how confident we should be
    in a particular AI response.
    """
    
    def __init__(self, 
                 weights: Optional[Dict[str, float]] = None,
                 thresholds: Optional[Dict[ConfidenceLevel, Tuple[float, float]]] = None):
        """
        Initialize the confidence calculator.
        
        Args:
            weights: Weights for different confidence factors
            thresholds: Thresholds for confidence levels
        """
        # Default weights for different factors
        self.weights = weights or {
            "consistency": 0.25,  # Consistency with other responses
            "certainty": 0.20,   # Certainty language in response
            "specificity": 0.20, # Specificity of the answer
            "coherence": 0.15,   # Coherence of the text
            "length": 0.10,      # Length of the response
            "source": 0.10       # Source/model reliability
        }
        
        # Default thresholds for confidence levels
        self.thresholds = thresholds or {
            ConfidenceLevel.VERY_LOW: (0.0, 0.2),
            ConfidenceLevel.LOW: (0.2, 0.4),
            ConfidenceLevel.MEDIUM: (0.4, 0.6),
            ConfidenceLevel.HIGH: (0.6, 0.8),
            ConfidenceLevel.VERY_HIGH: (0.8, 1.0)
        }
    
    def calculate(self, 
                  response: Dict[str, Any],
                  context: Optional[Dict[str, Any]] = None) -> ConfidenceScore:
        """
        Calculate confidence score for a response.
        
        Args:
            response: The AI response to evaluate
            context: Optional context (other responses, user query, etc.)
        
        Returns:
            ConfidenceScore with score and explanation
        """
        factors: Dict[str, float] = {}
        
        # Calculate each factor
        factors["consistency"] = self._calculate_consistency(response, context)
        factors["certainty"] = self._calculate_certainty(response)
        factors["specificity"] = self._calculate_specificity(response)
        factors["coherence"] = self._calculate_coherence(response)
        factors["length"] = self._calculate_length(response)
        factors["source"] = self._calculate_source(response)
        
        # Calculate weighted score
        total_weight = sum(self.weights.values())
        weighted_sum = sum(
            factors.get(factor, 0) * weight 
            for factor, weight in self.weights.items()
        )
        score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Determine level
        level = self._get_confidence_level(score)
        
        # Generate explanation
        explanation = self._generate_explanation(score, factors)
        
        return ConfidenceScore(
            score=round(score, 4),
            level=level,
            explanation=explanation,
            factors=factors
        )
    
    def calculate_batch(self, 
                        responses: List[Dict[str, Any]],
                        context: Optional[Dict[str, Any]] = None) -> List[ConfidenceScore]:
        """
        Calculate confidence scores for multiple responses.
        
        Args:
            responses: List of responses to evaluate
            context: Optional context
        
        Returns:
            List of ConfidenceScore objects
        """
        return [self.calculate(response, context) for response in responses]
    
    def _calculate_consistency(self, 
                              response: Dict[str, Any],
                              context: Optional[Dict[str, Any]]) -> float:
        """Calculate consistency score based on agreement with other responses."""
        if not context or "other_responses" not in context:
            # No other responses to compare with, assume medium consistency
            return 0.5
        
        other_responses = context["other_responses"]
        if not other_responses:
            return 0.5
        
        # Compare this response with others
        this_content = response.get("content", "") or response.get("text", "")
        
        if not this_content:
            return 0.0
        
        # Count how many other responses are similar
        similar_count = 0
        total = 0
        
        from ..merge.similarity_detector import SimilarityDetector, SimilarityMethod
        detector = SimilarityDetector()
        
        for other_response in other_responses:
            other_content = other_response.get("content", "") or other_response.get("text", "")
            if other_content:
                result = detector.compare(
                    this_content,
                    other_content,
                    SimilarityMethod.JACCARD
                )
                if result.score >= 0.7:
                    similar_count += 1
                total += 1
        
        if total == 0:
            return 0.5
        
        return similar_count / total
    
    def _calculate_certainty(self, response: Dict[str, Any]) -> float:
        """Calculate certainty score based on language in the response."""
        content = response.get("content", "") or response.get("text", "")
        content_lower = content.lower()
        
        if not content:
            return 0.0
        
        # Words that indicate certainty
        certainty_words = [
            "certain", "definitely", "absolutely", "without doubt",
            "confident", "sure", "positive", "100%", "always",
            "never", "proven", "fact", "truth", "obvious"
        ]
        
        # Words that indicate uncertainty
        uncertainty_words = [
            "maybe", "perhaps", "possibly", "might", "could",
            "unsure", "uncertain", "doubt", "probably",
            "likely", "sometimes", "often", "usually"
        ]
        
        certainty_count = sum(1 for word in certainty_words if word in content_lower)
        uncertainty_count = sum(1 for word in uncertainty_words if word in content_lower)
        
        # Normalize by content length
        word_count = len(content.split())
        if word_count == 0:
            return 0.5
        
        certainty_score = certainty_count / word_count
        uncertainty_score = uncertainty_count / word_count
        
        # Certainty reduces uncertainty
        return max(0, min(1, certainty_score - uncertainty_score * 0.5))
    
    def _calculate_specificity(self, response: Dict[str, Any]) -> float:
        """Calculate specificity score based on how specific the answer is."""
        content = response.get("content", "") or response.get("text", "")
        
        if not content:
            return 0.0
        
        # Check for vague language
        vague_words = [
            "thing", "stuff", "something", "anything", "everything",
            "someone", "anyone", "everyone", "many", "few",
            "various", "different", "several", "multiple"
        ]
        
        # Check for specific elements
        has_numbers = any(char.isdigit() for char in content)
        has_proper_nouns = any(word[0].isupper() for word in content.split() if len(word) > 1)
        has_quotes = '"' in content or "'" in content
        
        vague_count = sum(1 for word in vague_words if word in content.lower())
        word_count = len(content.split())
        
        if word_count == 0:
            return 0.0
        
        vague_ratio = vague_count / word_count
        
        # Specificity score based on various factors
        specificity_score = 0.0
        
        if has_numbers:
            specificity_score += 0.3
        if has_proper_nouns:
            specificity_score += 0.2
        if has_quotes:
            specificity_score += 0.2
        
        # Reduce for vague language
        specificity_score = max(0, specificity_score - vague_ratio * 0.5)
        
        return min(1, specificity_score)
    
    def _calculate_coherence(self, response: Dict[str, Any]) -> float:
        """Calculate coherence score based on text structure."""
        content = response.get("content", "") or response.get("text", "")
        
        if not content or len(content.split()) < 2:
            return 0.5
        
        # Check for sentence structure
        sentences = re.split(r'[.!?]+', content)
        
        if len(sentences) <= 1:
            return 0.7
        
        # Check for logical flow (simple heuristic: sentences have some length)
        short_sentences = sum(1 for s in sentences if len(s.strip().split()) < 3)
        short_ratio = short_sentences / len(sentences) if sentences else 0
        
        # Coherence score
        coherence_score = 1.0 - short_ratio * 0.5
        
        return max(0.3, min(1.0, coherence_score))
    
    def _calculate_length(self, response: Dict[str, Any]) -> float:
        """Calculate length score based on response length."""
        content = response.get("content", "") or response.get("text", "")
        word_count = len(content.split())
        
        # Ideal length is around 50-200 words
        if word_count == 0:
            return 0.0
        
        # Normalize to 0-1 range with peak at 100 words
        if word_count <= 50:
            return word_count / 50
        elif word_count <= 100:
            return 1.0
        elif word_count <= 200:
            return 2.0 - (word_count / 100)
        else:
            return max(0, 2.0 - (word_count / 100))
    
    def _calculate_source(self, response: Dict[str, Any]) -> float:
        """Calculate source reliability score."""
        provider = response.get("provider", "") or response.get("source", "")
        
        # Known reliable providers
        reliable_providers = ["openai", "anthropic", "mistral", "google", "perplexity"]
        
        if any(rp in provider.lower() for rp in reliable_providers):
            return 0.9
        elif "local" in provider.lower():
            return 0.7
        else:
            return 0.5
    
    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """Get confidence level based on score."""
        for level, (min_score, max_score) in self.thresholds.items():
            if min_score <= score < max_score:
                return level
        return ConfidenceLevel.MEDIUM
    
    def _generate_explanation(self, score: float, factors: Dict[str, float]) -> str:
        """Generate a human-readable explanation of the confidence score."""
        level = self._get_confidence_level(score)
        
        explanations = []
        
        if factors.get("consistency", 0) > 0.7:
            explanations.append("consistent with other responses")
        elif factors.get("consistency", 0) < 0.3:
            explanations.append("inconsistent with other responses")
        
        if factors.get("certainty", 0) > 0.7:
            explanations.append("uses confident language")
        elif factors.get("certainty", 0) < 0.3:
            explanations.append("uses uncertain language")
        
        if factors.get("specificity", 0) > 0.7:
            explanations.append("highly specific")
        elif factors.get("specificity", 0) < 0.3:
            explanations.append("vague or general")
        
        if factors.get("coherence", 0) > 0.7:
            explanations.append("well-structured and coherent")
        elif factors.get("coherence", 0) < 0.3:
            explanations.append("poorly structured")
        
        if factors.get("length", 0) > 0.7:
            explanations.append("appropriate length")
        elif factors.get("length", 0) < 0.3:
            explanations.append("too short")
        
        if factors.get("source", 0) > 0.7:
            explanations.append("from reliable source")
        
        if not explanations:
            explanations.append("based on multiple factors")
        
        return f"{level.value.replace('_', ' ').title()} confidence ({score:.2%}): {', '.join(explanations)}"


# Global confidence calculator instance
confidence_calculator = None


def get_confidence_calculator(weights: Optional[Dict[str, float]] = None,
                               thresholds: Optional[Dict[ConfidenceLevel, Tuple[float, float]]] = None) -> ConfidenceCalculator:
    """Get or create the global confidence calculator."""
    global confidence_calculator
    if confidence_calculator is None:
        confidence_calculator = ConfidenceCalculator(weights, thresholds)
    return confidence_calculator
