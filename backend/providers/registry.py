"""
Provider Registry for MetaPilot AI
"""

import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .base import AIProvider, ProviderType, ProviderConfig
from ..config import settings

logger = logging.getLogger(__name__)

@dataclass
class RegisteredProvider:
    name: str
    provider: AIProvider
    config: ProviderConfig
    is_default: bool = False

class ProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, RegisteredProvider] = {}
        self._default_provider: Optional[str] = None
        self._initialized = False
    
    def register(self, name: str, provider: AIProvider, config: Optional[ProviderConfig] = None, is_default: bool = False) -> bool:
        if config is None:
            config = provider.get_config()
        self.providers[name] = RegisteredProvider(name=name, provider=provider, config=config, is_default=is_default)
        if is_default:
            self._default_provider = name
        logger.info(f"Registered provider: {name}")
        return True

    def get_provider(self, name: str) -> Optional[AIProvider]:
        return self.providers[name].provider if name in self.providers else None

    def has_provider(self, name: str) -> bool:
        return name in self.providers

    def is_initialized(self) -> bool:
        return self._initialized

    def count(self) -> int:
        return len(self.providers)

    async def initialize(self):
        if self._initialized: return
        from .openai_provider import OpenAIProvider
        from .anthropic_provider import AnthropicProvider
        from .mistral_provider import MistralProvider
        from .google_provider import GoogleProvider
        from .perplexity_provider import PerplexityProvider
        from .local_gguf import LocalGGUFProvider
        from .chatgpt_browser import ChatGPTBrowserProvider
        from .claude_browser import ClaudeBrowserProvider
        from .gemini_browser import GeminiBrowserProvider
        from .perplexity_browser import PerplexityBrowserProvider
        from .deepseek_browser import DeepSeekBrowserProvider
        from .mistral_browser import MistralBrowserProvider
        from .huggingchat_browser import HuggingChatBrowserProvider
        from .copilot_browser import CopilotBrowserProvider
        from .grok_browser import GrokBrowserProvider
        from .qwen_browser import QwenBrowserProvider

        if settings.OPENAI_API_KEY:
            self.register("openai", OpenAIProvider(ProviderConfig(ProviderType.OPENAI, "OpenAI", api_key=settings.OPENAI_API_KEY)), is_default=True)

        self.register("local_gguf", LocalGGUFProvider())
        self.register("chatgpt_browser", ChatGPTBrowserProvider())
        self.register("claude_browser", ClaudeBrowserProvider())
        self.register("gemini_browser", GeminiBrowserProvider())
        self.register("perplexity_browser", PerplexityBrowserProvider())
        self.register("deepseek_browser", DeepSeekBrowserProvider())
        self.register("mistral_browser", MistralBrowserProvider())
        self.register("huggingchat_browser", HuggingChatBrowserProvider())
        self.register("copilot_browser", CopilotBrowserProvider())
        self.register("grok_browser", GrokBrowserProvider())
        self.register("qwen_browser", QwenBrowserProvider())

        self._initialized = True

    async def shutdown(self):
        self.providers.clear()
        self._initialized = False

provider_registry = ProviderRegistry()
