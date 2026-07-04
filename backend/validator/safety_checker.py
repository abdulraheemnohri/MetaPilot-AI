"""
MetaPilot AI - Safety Checker

Checks AI responses for safety and ethical boundaries.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SafetyResult:
    """Result of a safety check."""
    is_safe: bool
    score: float  # 0-1 (higher is safer)
    issues: List[str] = field(default_factory=list)
    categories: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "score": self.score,
            "issues": self.issues,
            "categories": self.categories
        }


class SafetyChecker:
    """
    Checks if AI responses are safe.

    Placeholder for more advanced safety checks.
    """

    def __init__(self):
        self.unsafe_keywords = [
            "malicious", "exploit", "hack", "illegal", "dangerous"
        ]

    def check(self, content: str) -> SafetyResult:
        """
        Check if content is safe.
        """
        if not content:
            return SafetyResult(is_safe=True, score=1.0)

        issues = []
        lower_content = content.lower()

        for keyword in self.unsafe_keywords:
            if keyword in lower_content:
                issues.append(f"Detected unsafe keyword: {keyword}")

        is_safe = len(issues) == 0
        score = 1.0 if is_safe else 0.0

        return SafetyResult(
            is_safe=is_safe,
            score=score,
            issues=issues
        )

# Global safety checker instance
safety_checker = SafetyChecker()
