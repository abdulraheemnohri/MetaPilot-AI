"""
Provider Registry for MetaPilot AI

Manages registration and retrieval of AI providers.
"""

import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .base import AIProvider, ProviderType, ProviderConfig
from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class RegisteredProvider:
    """Information about a registered provider."""
    name: str
    provider: AIProvider
    config: ProviderConfig
    is_default: bool = False


class ProviderRegistry:
    """
    Registry for AI providers.
    
    Manages:
    - Provider registration and unregistration
    - Provider retrieval by name or type
    - Default provider management
    - Provider configuration
    """
    
    def __init__(self):
        self.providers: Dict[str, RegisteredProvider] = {}
        self._default_provider: Optional[str] = None
        self._initialized = False
    
    def register(
        self,
        name: str,
        provider: AIProvider,
        config: Optional[ProviderConfig] = None,
        is_default: bool = False,
    ) -> bool:
        """
        Register a provider.
        """
        if name in self.providers:
            logger.warning(f"Provider '{name}' already registered, overwriting")
        
        if config is None:
            config = provider.get_config()
        
        self.providers[name] = RegisteredProvider(
            name=name,
            provider=provider,
            config=config,
            is_default=is_default,
        )
        
        if is_default:
            self._default_provider = name
        
        logger.info(f"Registered provider: {name} ({provider.provider_type.value})")
        return True
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a provider.
        """
        if name not in self.providers:
            logger.warning(f"Provider '{name}' not found")
            return False
        
        del self.providers[name]
        
        if self._default_provider == name:
            self._default_provider = None
        
        logger.info(f"Unregistered provider: {name}")
        return True
    
    def get_provider(self, name: str) -> Optional[AIProvider]:
        """
        Get a provider by name.
        """
        if name not in self.providers:
            logger.warning(f"Provider '{name}' not found")
            return None
        
        return self.providers[name].provider

    def get(self, name: str) -> Optional[AIProvider]:
        return self.get_provider(name)
    
    def get_config(self, name: str) -> Optional[ProviderConfig]:
        """
        Get a provider's configuration.
        """
        if name not in self.providers:
            return None
        
        return self.providers[name].config
    
    def get_default(self) -> Optional[AIProvider]:
        """
        Get the default provider.
        """
        if not self._default_provider:
            if self.providers:
                return list(self.providers.values())[0].provider
            return None
        
        return self.get(self._default_provider)
    
    def set_default(self, name: str) -> bool:
        """
        Set the default provider.
        """
        if name not in self.providers:
            logger.warning(f"Provider '{name}' not found")
            return False
        
        self._default_provider = name
        logger.info(f"Set default provider: {name}")
        return True
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """
        List all registered providers.
        """
        providers = []
        for name, registered in self.providers.items():
            providers.append({
                "id": name,
                "name": registered.provider.name,
                "type": registered.provider.provider_type.value,
                "is_default": name == self._default_provider,
                "default_model": registered.provider.default_model,
                "config": registered.config.to_dict(),
                "is_active": True,
            })
        
        return providers
    
    def list_by_type(self, provider_type: ProviderType) -> List[str]:
        """
        List all providers of a specific type.
        """
        return [
            name for name, registered in self.providers.items()
            if registered.provider.provider_type == provider_type
        ]
    
    def get_by_type(self, provider_type: ProviderType) -> List[AIProvider]:
        """
        Get all providers of a specific type.
        """
        return [
            registered.provider for registered in self.providers.values()
            if registered.provider.provider_type == provider_type
        ]
    
    def has_provider(self, name: str) -> bool:
        """
        Check if a provider is registered.
        """
        return name in self.providers
    
    def count(self) -> int:
        """Get the number of registered providers."""
        return len(self.providers)
    
    def clear(self):
        """Clear all registered providers."""
        self.providers.clear()
        self._default_provider = None
        logger.info("Cleared all providers")
    
    async def initialize(self):
        """Initialize the registry by registering available providers."""
        if self._initialized:
            return

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

        # Register OpenAI
        if settings.OPENAI_API_KEY:
            config = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                name="OpenAI",
                api_key=settings.OPENAI_API_KEY
            )
            self.register("openai", OpenAIProvider(config), is_default=True)

        # Register Anthropic
        if settings.ANTHROPIC_API_KEY:
            config = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                name="Anthropic",
                api_key=settings.ANTHROPIC_API_KEY
            )
            self.register("anthropic", AnthropicProvider(config))

        # Register Mistral
        if settings.MISTRAL_API_KEY:
            config = ProviderConfig(
                provider_type=ProviderType.MISTRAL,
                name="Mistral",
                api_key=settings.MISTRAL_API_KEY
            )
            self.register("mistral", MistralProvider(config))

        # Register Google
        if settings.GOOGLE_API_KEY:
            config = ProviderConfig(
                provider_type=ProviderType.GOOGLE,
                name="Google",
                api_key=settings.GOOGLE_API_KEY
            )
            self.register("google", GoogleProvider(config))

        # Register Perplexity
        if settings.PERPLEXITY_API_KEY:
            config = ProviderConfig(
                provider_type=ProviderType.PERPLEXITY,
                name="Perplexity",
                api_key=settings.PERPLEXITY_API_KEY
            )
            self.register("perplexity", PerplexityProvider(config))

        # Register local GGUF
        self.register("local_gguf", LocalGGUFProvider())

        # Register Browser Providers
        self.register("chatgpt_browser", ChatGPTBrowserProvider())
        self.register("claude_browser", ClaudeBrowserProvider())
        self.register("gemini_browser", GeminiBrowserProvider())
        self.register("perplexity_browser", PerplexityBrowserProvider())
        self.register("deepseek_browser", DeepSeekBrowserProvider())
        self.register("mistral_browser", MistralBrowserProvider())
        self.register("huggingchat_browser", HuggingChatBrowserProvider())

        self._initialized = True
        logger.info(f"Provider registry initialized with {self.count()} providers")

    async def shutdown(self):
        """Shutdown all providers."""
        self.clear()
        self._initialized = False

    def is_initialized(self) -> bool:
        """Check if the registry is initialized."""
        return self._initialized

# Global registry instance
provider_registry = ProviderRegistry()
