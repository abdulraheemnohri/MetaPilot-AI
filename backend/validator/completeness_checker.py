"""
MetaPilot AI - Completeness Checker

Checks if AI responses are complete and not truncated.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import re

logger = logging.getLogger(__name__)


class CompletenessStatus(Enum):
    """Status of completeness check."""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    TRUNCATED = "truncated"
    PARTIAL = "partial"


@dataclass
class CompletenessResult:
    """Result of a completeness check."""
    status: CompletenessStatus
    score: float  # 0-1
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    is_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "is_valid": self.is_valid
        }


class CompletenessChecker:
    """
    Checks if AI responses are complete.
    
    Detects incomplete or truncated responses and provides feedback.
    """
    
    def __init__(self, 
                 min_length: int = 10,
                 max_length: Optional[int] = None,
                 require_punctuation: bool = True,
                 require_capitalization: bool = True,
                 check_for_cutoff: bool = True):
        """
        Initialize the completeness checker.
        
        Args:
            min_length: Minimum length in words for a response to be considered complete
            max_length: Optional maximum length (responses longer than this might be truncated)
            require_punctuation: Whether to require ending punctuation
            require_capitalization: Whether to require capitalization at start
            check_for_cutoff: Whether to check for common truncation indicators
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_punctuation = require_punctuation
        self.require_capitalization = require_capitalization
        self.check_for_cutoff = check_for_cutoff
        
        # Patterns that indicate truncation
        self.cutoff_patterns = [
            r"\.\.\.",  # Ellipsis
            r"\.\.\.$",  # Ellipsis at end
            r"cut off",
            r"truncated",
            r"to be continued",
            r"etc\.",
            r"and so on",
            r"and more",
            r"\bmore\b",
            r"\bcontinue\b",
            r"\bnext\b"
        ]
        
        # Patterns that indicate incomplete sentences
        self.incomplete_patterns = [
            r"^\s*[a-z]"  # Starts with lowercase (unless it's a quote)
        ]
    
    def check(self, response: Dict[str, Any]) -> CompletenessResult:
        """
        Check if a response is complete.
        
        Args:
            response: The AI response to check
        
        Returns:
            CompletenessResult with status and issues
        """
        content = response.get("content", "") or response.get("text", "")
        
        if not content or not content.strip():
            return CompletenessResult(
                status=CompletenessStatus.INCOMPLETE,
                score=0.0,
                issues=["Empty response"],
                suggestions=["Provide a response"],
                is_valid=False
            )
        
        issues: List[str] = []
        suggestions: List[str] = []
        score = 1.0
        
        # Check length
        word_count = len(content.split())
        
        if word_count < self.min_length:
            issues.append(f"Response is too short ({word_count} words, minimum {self.min_length})")
            suggestions.append(f"Expand response to at least {self.min_length} words")
            score -= 0.4
        
        if self.max_length and word_count > self.max_length:
            issues.append(f"Response may be truncated ({word_count} words, maximum {self.max_length})")
            suggestions.append("Check if response was cut off")
            score -= 0.3
        
        # Check for truncation indicators
        if self.check_for_cutoff:
            for pattern in self.cutoff_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"Response appears to be cut off (matches pattern: {pattern})")
                    suggestions.append("Regenerate with higher token limit")
                    score -= 0.5
                    break
        
        # Check punctuation
        if self.require_punctuation:
            has_punctuation = any(p in content for p in ['.', '!', '?'])
            if not has_punctuation:
                issues.append("Response is missing ending punctuation")
                suggestions.append("Add appropriate punctuation")
                score -= 0.2
        
        # Check capitalization
        if self.require_capitalization:
            # Skip check if response starts with a quote
            stripped = content.lstrip()
            if stripped and stripped[0].islower() and not stripped.startswith('"') and not stripped.startswith("'"):
                issues.append("Response does not start with capital letter")
                suggestions.append("Capitalize the first letter")
                score -= 0.1
        
        # Check for incomplete patterns
        for pattern in self.incomplete_patterns:
            if re.search(pattern, content):
                issues.append("Response may be incomplete")
                suggestions.append("Complete the thought")
                score -= 0.2
                break
        
        # Determine status
        if score >= 0.8:
            status = CompletenessStatus.COMPLETE
        elif score >= 0.5:
            status = CompletenessStatus.PARTIAL
        elif any("cut off" in issue.lower() or "truncated" in issue.lower() for issue in issues):
            status = CompletenessStatus.TRUNCATED
        else:
            status = CompletenessStatus.INCOMPLETE
        
        is_valid = status == CompletenessStatus.COMPLETE
        
        return CompletenessResult(
            status=status,
            score=round(max(0, min(1, score)), 4),
            issues=issues,
            suggestions=suggestions,
            is_valid=is_valid
        )
    
    def check_batch(self, responses: List[Dict[str, Any]]) -> List[CompletenessResult]:
        """
        Check completeness for multiple responses.
        
        Args:
            responses: List of responses to check
        
        Returns:
            List of CompletenessResult objects
        """
        return [self.check(response) for response in responses]
    
    def is_complete(self, response: Dict[str, Any]) -> bool:
        """
        Quick check if a response is complete.
        
        Args:
            response: The response to check
        
        Returns:
            True if response is complete
        """
        result = self.check(response)
        return result.is_valid
    
    def get_issues(self, response: Dict[str, Any]) -> List[str]:
        """
        Get a list of completeness issues for a response.
        
        Args:
            response: The response to check
        
        Returns:
            List of issue descriptions
        """
        result = self.check(response)
        return result.issues


# Global completeness checker instance
completeness_checker = None


def get_completeness_checker(min_length: int = 10,
                              max_length: Optional[int] = None,
                              require_punctuation: bool = True,
                              require_capitalization: bool = True,
                              check_for_cutoff: bool = True) -> CompletenessChecker:
    """Get or create the global completeness checker."""
    global completeness_checker
    if completeness_checker is None:
        completeness_checker = CompletenessChecker(
            min_length,
            max_length,
            require_punctuation,
            require_capitalization,
            check_for_cutoff
        )
    return completeness_checker
