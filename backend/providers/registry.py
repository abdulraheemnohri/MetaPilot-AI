"""
Provider Registry for MetaPilot AI

Manages registration and retrieval of AI providers.
"""

import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .base import AIProvider, ProviderType, ProviderConfig

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
        
        Args:
            name: Unique name for the provider
            provider: The provider instance
            config: Optional configuration
            is_default: Whether to set as default
        
        Returns:
            True if registration was successful
        """
        if name in self.providers:
            logger.warning(f"Provider '{name}' already registered, overwriting")
        
        # Use provider's config if not provided
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
        
        Args:
            name: Name of the provider to unregister
        
        Returns:
            True if unregistration was successful
        """
        if name not in self.providers:
            logger.warning(f"Provider '{name}' not found")
            return False
        
        del self.providers[name]
        
        if self._default_provider == name:
            self._default_provider = None
        
        logger.info(f"Unregistered provider: {name}")
        return True
    
    def get(self, name: str) -> Optional[AIProvider]:
        """
        Get a provider by name.
        
        Args:
            name: Name of the provider
        
        Returns:
            The provider instance, or None if not found
        """
        if name not in self.providers:
            logger.warning(f"Provider '{name}' not found")
            return None
        
        return self.providers[name].provider
    
    def get_config(self, name: str) -> Optional[ProviderConfig]:
        """
        Get a provider's configuration.
        
        Args:
            name: Name of the provider
        
        Returns:
            The provider's configuration, or None if not found
        """
        if name not in self.providers:
            return None
        
        return self.providers[name].config
    
    def get_default(self) -> Optional[AIProvider]:
        """
        Get the default provider.
        
        Returns:
            The default provider, or None if not set
        """
        if not self._default_provider:
            # Return the first provider if no default is set
            if self.providers:
                return list(self.providers.values())[0].provider
            return None
        
        return self.get(self._default_provider)
    
    def set_default(self, name: str) -> bool:
        """
        Set the default provider.
        
        Args:
            name: Name of the provider to set as default
        
        Returns:
            True if the provider was found and set as default
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
        
        Returns:
            List of provider information dictionaries
        """
        providers = []
        for name, registered in self.providers.items():
            providers.append({
                "name": name,
                "type": registered.provider.provider_type.value,
                "is_default": name == self._default_provider,
                "default_model": registered.provider.default_model,
                "config": registered.config.to_dict(),
            })
        
        return providers
    
    def list_by_type(self, provider_type: ProviderType) -> List[str]:
        """
        List all providers of a specific type.
        
        Args:
            provider_type: The provider type to filter by
        
        Returns:
            List of provider names
        """
        return [
            name for name, registered in self.providers.items()
            if registered.provider.provider_type == provider_type
        ]
    
    def get_by_type(self, provider_type: ProviderType) -> List[AIProvider]:
        """
        Get all providers of a specific type.
        
        Args:
            provider_type: The provider type to filter by
        
        Returns:
            List of provider instances
        """
        return [
            registered.provider for registered in self.providers.values()
            if registered.provider.provider_type == provider_type
        ]
    
    def has_provider(self, name: str) -> bool:
        """
        Check if a provider is registered.
        
        Args:
            name: Name of the provider
        
        Returns:
            True if the provider is registered
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
        """Initialize the registry (can be overridden by subclasses)."""
        self._initialized = True
    
    def is_initialized(self) -> bool:
        """Check if the registry is initialized."""
        return self._initialized
