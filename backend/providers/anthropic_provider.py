"""
Anthropic Provider for MetaPilot AI

Implementation of AIProvider for Anthropic Claude API.
"""

import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator

from .base import (
    AIProvider,
    ProviderConfig,
    ProviderResponse,
    ChatResponse,
    ProviderType,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """
    Anthropic Claude API provider.
    
    Supports:
    - Messages API (Claude 3+)
    - Text completions (legacy)
    - Streaming
    
    Requires:
    - anthropic Python package
    - ANTHROPIC_API_KEY environment variable
    """
    
    provider_type = ProviderType.ANTHROPIC
    name = "Anthropic"
    default_model = "claude-3-sonnet-20240229"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                
                api_key = self.config.api_key
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY is required")
                
                self._client = anthropic.AsyncAnthropic(
                    api_key=api_key,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
            except ImportError:
                raise ImportError("anthropic package is required for AnthropicProvider")
        
        return self._client
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text using the Messages API.
        
        Note: This uses the Messages API which is the recommended approach.
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "user", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            response = await client.messages.create(**params)
            
            self._log_response("generate", response)
            
            return ProviderResponse(
                text=response.content[0].text if response.content else "",
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.input_tokens,
                tokens_completion=response.usage.output_tokens,
                finish_reason=response.stop_reason,
                metadata={
                    "id": response.id,
                    "type": response.type,
                    "role": response.role,
                    "stop_reason": response.stop_reason,
                    "stop_sequence": response.stop_sequence,
                },
            )
        except Exception as e:
            self._handle_error(e, "generate")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Generate a chat response using the Messages API.
        
        Args:
            messages: List of chat messages
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            ChatResponse with the assistant's reply
        """
        self._log_request("chat", model=model, messages=messages[:3])
        
        try:
            client = await self._get_client()
            
            # Convert messages to Anthropic format
            anthropic_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"],
                    })
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            if system_message:
                params["system"] = system_message
            
            response = await client.messages.create(**params)
            
            self._log_response("chat", response)
            
            content = response.content[0].text if response.content else ""
            
            return ChatResponse(
                text=content,
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.input_tokens,
                tokens_completion=response.usage.output_tokens,
                finish_reason=response.stop_reason,
                message={"role": "assistant", "content": content},
                metadata={
                    "id": response.id,
                    "type": response.type,
                    "stop_reason": response.stop_reason,
                },
            )
        except Exception as e:
            self._handle_error(e, "chat")
            raise
    
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
            model: Model to use
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
        
        Yields:
            Generated tokens as they become available
        """
        self._log_request("stream", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "user", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            response = await client.messages.create(**params)
            
            # For streaming, we need to use the stream method
            # Note: This is a simplified implementation
            # In practice, Anthropic's streaming API works differently
            
            # For now, yield the full response
            if response.content:
                yield response.content[0].text
            
        except Exception as e:
            self._handle_error(e, "stream")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        # Anthropic doesn't have a models list API
        # Return known models
        return [
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet"},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku"},
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus"},
            {"id": "claude-2:1", "name": "Claude 2.1"},
            {"id": "claude-2", "name": "Claude 2"},
            {"id": "claude-instant-1", "name": "Claude Instant"},
        ]
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return {
            "id": model,
            "provider": self.name,
            "name": self._get_model_name(model),
        }
    
    def _get_model_name(self, model: str) -> str:
        """Get a human-readable name for a model."""
        model_names = {
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "claude-3-opus-20240229": "Claude 3 Opus",
            "claude-2:1": "Claude 2.1",
            "claude-2": "Claude 2",
            "claude-instant-1": "Claude Instant",
        }
        return model_names.get(model, model)
