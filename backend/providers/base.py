"""
Base AI Provider for MetaPilot AI

Defines the interface and base implementation for AI providers.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    LOCAL = "local"


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    provider_type: ProviderType
    name: str
    api_key: Optional[str] = None
    base_url: str = ""
    default_model: str = ""
    timeout: int = 30
    max_retries: int = 3
    rate_limit: Optional[int] = None
    
    # Model parameters
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_tokens: int = 2048
    
    # Extra headers
    extra_headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_type": self.provider_type.value,
            "name": self.name,
            "api_key": "***" if self.api_key else None,
            "base_url": self.base_url,
            "default_model": self.default_model,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "rate_limit": self.rate_limit,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_tokens": self.max_tokens,
            "extra_headers": self.extra_headers,
        }


@dataclass
class ProviderResponse:
    """Response from an AI provider."""
    text: str
    model: str
    provider: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
        }


@dataclass
class ChatMessage:
    """A chat message."""
    role: str  # "system", "user", "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class ChatResponse:
    """Response from a chat completion."""
    text: str
    model: str
    provider: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: Optional[str] = None
    message: Optional[ChatMessage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "provider": self.provider,
            "tokens_prompt": self.tokens_prompt,
            "tokens_completion": self.tokens_completion,
            "finish_reason": self.finish_reason,
            "message": self.message.to_dict() if self.message else None,
            "metadata": self.metadata,
        }


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All AI providers must implement the following methods:
    - generate: Generate text from a prompt
    - chat: Generate a chat response
    - stream: Stream generation token by token
    
    Providers may optionally implement:
    - embed: Generate embeddings
    - list_models: List available models
    - get_model_info: Get information about a model
    """
    
    provider_type: ProviderType = ProviderType.LOCAL
    name: str = "Base Provider"
    default_model: str = ""
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or self._create_default_config()
        self._logger = logging.getLogger(f"{__name__}.{self.name}")
    
    def _create_default_config(self) -> ProviderConfig:
        """Create a default configuration."""
        return ProviderConfig(
            provider_type=self.provider_type,
            name=self.name,
            default_model=self.default_model,
        )
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The user prompt
            model: Model to use (defaults to default_model)
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
        
        Returns:
            ProviderResponse with generated text
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Generate a chat response.
        
        Args:
            messages: List of chat messages (role: "system", "user", "assistant")
            model: Model to use (defaults to default_model)
            **kwargs: Additional provider-specific parameters
        
        Returns:
            ChatResponse with the assistant's reply
        """
        pass
    
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream generation token by token.
        
        Args:
            prompt: The user prompt
            model: Model to use (defaults to default_model)
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Generated tokens as they become available
        """
        yield ""
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            model: Model to use
        
        Returns:
            Embedding vector
        
        Raises:
            NotImplementedError: If the provider doesn't support embeddings
        """
        raise NotImplementedError(f"{self.name} does not support embeddings")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model information dictionaries
        """
        return []
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model: Model name
        
        Returns:
            Model information dictionary
        """
        return {"model": model, "provider": self.name}
    
    def get_config(self) -> ProviderConfig:
        """Get the provider configuration."""
        return self.config
    
    def set_config(self, config: ProviderConfig):
        """Set the provider configuration."""
        self.config = config
    
    def _log_request(self, method: str, **kwargs):
        """Log an API request."""
        self._logger.debug(f"{method} request: {json.dumps(kwargs, default=str)}")
    
    def _log_response(self, method: str, response: Any):
        """Log an API response."""
        self._logger.debug(f"{method} response: {json.dumps(response, default=str) if response else 'None'}")
    
    def _handle_error(self, error: Exception, context: str) -> None:
        """Handle an error."""
        self._logger.error(f"{context} error: {error}", exc_info=True)
        raise error
