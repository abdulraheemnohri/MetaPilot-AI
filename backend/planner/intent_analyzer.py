"""
MetaPilot AI - Intent Analyzer

Analyzes user input to determine the underlying intent and task type.
Uses local AI for reasoning if available.
"""

import logging
import json
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..local_ai import local_ai_manager

logger = logging.getLogger(__name__)

class IntentType(str, Enum):
    CHAT = "chat"
    CODE = "code"
    RESEARCH = "research"
    TRANSLATION = "translation"
    MATH = "math"
    CREATIVE = "creative"
    PLANNING = "planning"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    type: IntentType
    confidence: float
    reasoning: str
    subtasks_required: bool = False

class IntentAnalyzer:
    """
    Analyzes user intent to help the Planner route tasks.
    """

    def __init__(self):
        self.keywords = {
            IntentType.CODE: ["code", "python", "javascript", "react", "debug", "function", "program"],
            IntentType.RESEARCH: ["research", "who is", "what is", "history", "find out"],
            IntentType.TRANSLATION: ["translate", "to spanish", "in hindi", "language"],
            IntentType.MATH: ["calculate", "solve", "math", "equation"],
            IntentType.CREATIVE: ["write a story", "poem", "song", "creative"],
            IntentType.PLANNING: ["plan", "schedule", "how to build", "roadmap"]
        }

    async def analyze(self, prompt: str) -> Intent:
        """
        Analyze the prompt to determine intent.
        Try to use local AI for analysis if any model is loaded.
        """
        loaded_models = [m["id"] for m in local_ai_manager.list_models() if m["is_loaded"]]

        if loaded_models:
            try:
                model_id = loaded_models[0]
                analysis_prompt = f"""Analyze the following user prompt and categorize its intent.
Prompt: "{prompt}"
Respond only with a JSON object like: {{"type": "code", "confidence": 0.9, "reasoning": "User wants to build a script", "subtasks_required": true}}
Valid types: chat, code, research, translation, math, creative, planning."""

                response = await local_ai_manager.generate(model_id, analysis_prompt, max_tokens=150)
                data = json.loads(response["content"])
                return Intent(
                    type=IntentType(data.get("type", "chat")),
                    confidence=data.get("confidence", 0.7),
                    reasoning=data.get("reasoning", ""),
                    subtasks_required=data.get("subtasks_required", False)
                )
            except Exception as e:
                logger.warning(f"Local AI analysis failed, falling back to keywords: {e}")

        # Fallback to keyword-based analysis
        lower_prompt = prompt.lower()
        best_intent = IntentType.CHAT
        max_matches = 0

        for intent_type, keywords in self.keywords.items():
            matches = sum(1 for k in keywords if k in lower_prompt)
            if matches > max_matches:
                max_matches = matches
                best_intent = intent_type

        subtasks_required = any(word in lower_prompt for word in ["and", "then", "build a complete"]) or len(prompt.split()) > 40

        return Intent(
            type=best_intent,
            confidence=0.8 if max_matches > 0 else 0.5,
            reasoning="Keyword-based detection",
            subtasks_required=subtasks_required
        )

# Global intent analyzer instance
intent_analyzer = IntentAnalyzer()
