"""
MetaPilot AI - Provider Capabilities

Defines the capabilities and routing logic for different AI providers.
"""

from enum import Enum
from typing import Dict, List, Any
from .base import ProviderType

class Capability(str, Enum):
    CHAT = "chat"
    CODE = "code"
    RESEARCH = "research"
    TRANSLATION = "translation"
    MATH = "math"
    CREATIVE = "creative"
    PLANNING = "planning"
    VISION = "vision"

# Map provider IDs to their specialized capabilities
PROVIDER_CAPABILITIES: Dict[str, List[Capability]] = {
    "openai": [Capability.CHAT, Capability.CODE, Capability.MATH, Capability.CREATIVE, Capability.PLANNING, Capability.VISION],
    "anthropic": [Capability.CHAT, Capability.CODE, Capability.PLANNING, Capability.CREATIVE],
    "google": [Capability.CHAT, Capability.RESEARCH, Capability.VISION],
    "mistral": [Capability.CHAT, Capability.CODE],
    "perplexity": [Capability.RESEARCH],
    "deepseek": [Capability.CODE, Capability.MATH],
    "local_gguf": [Capability.PLANNING, Capability.CHAT],
    "chatgpt_browser": [Capability.CHAT, Capability.CODE],
    "claude_browser": [Capability.CHAT, Capability.CODE],
    "gemini_browser": [Capability.CHAT, Capability.RESEARCH],
    "perplexity_browser": [Capability.RESEARCH],
    "deepseek_browser": [Capability.CODE, Capability.MATH],
    "mistral_browser": [Capability.CHAT],
    "huggingchat_browser": [Capability.CHAT]
}

def get_best_provider(intent_type: str, available_providers: List[Any]) -> Any:
    """
    Select the most suitable provider for a given intent.
    """
    # Map intent strings to Capability enums
    intent_map = {
        "code": Capability.CODE,
        "research": Capability.RESEARCH,
        "translation": Capability.TRANSLATION,
        "math": Capability.MATH,
        "creative": Capability.CREATIVE,
        "planning": Capability.PLANNING,
        "chat": Capability.CHAT
    }

    required_cap = intent_map.get(intent_type, Capability.CHAT)

    # Filter available providers by capability
    suitable = []
    for p in available_providers:
        pid = getattr(p, "id", p.name.lower().replace(" ", "_"))
        if required_cap in PROVIDER_CAPABILITIES.get(pid, []):
            suitable.append(p)

    # Return first suitable or fallback to first available
    return suitable[0] if suitable else available_providers[0]
