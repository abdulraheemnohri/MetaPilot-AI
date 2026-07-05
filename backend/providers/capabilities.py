"""
MetaPilot AI - Provider Capabilities & Routing
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from .base import ProviderType
from ..database.connection import async_session_maker
from ..database.models import SystemConfig

class Capability(str, Enum):
    CHAT = "chat"
    CODE = "code"
    RESEARCH = "research"
    TRANSLATION = "translation"
    MATH = "math"
    CREATIVE = "creative"
    PLANNING = "planning"
    VISION = "vision"

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
    "huggingchat_browser": [Capability.CHAT],
    "copilot_browser": [Capability.CHAT, Capability.RESEARCH],
    "grok_browser": [Capability.CHAT, Capability.CODE],
    "qwen_browser": [Capability.CHAT, Capability.CODE, Capability.TRANSLATION],
    "you_browser": [Capability.CHAT, Capability.RESEARCH],
    "duckduckgo_browser": [Capability.CHAT, Capability.RESEARCH]
}

async def get_best_provider(intent_type: str, available_providers: List[Any]) -> Any:
    # 1. Check user-defined rules in database
    try:
        async with async_session_maker() as session:
            from sqlalchemy import select
            stmt = select(SystemConfig).where(SystemConfig.key == "routing_rules")
            res = await session.execute(stmt)
            config = res.scalar_one_or_none()
            if config and intent_type in config.value:
                target_id = config.value[intent_type]
                for p in available_providers:
                    pid = getattr(p, "id", p.name.lower().replace(" ", "_"))
                    if pid == target_id: return p
    except Exception: pass

    # 2. Capability matching
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
    suitable = [p for p in available_providers if required_cap in PROVIDER_CAPABILITIES.get(getattr(p, "id", p.name.lower().replace(" ", "_")), [])]
    return suitable[0] if suitable else available_providers[0]
