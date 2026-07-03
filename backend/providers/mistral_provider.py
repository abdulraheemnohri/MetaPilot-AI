"""
Mistral Provider for MetaPilot AI

Implementation of AIProvider for Mistral API.
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


class MistralProvider(AIProvider):
    """
    Mistral API provider.
    
    Supports:
    - Chat completions
    - Streaming
    - Embeddings (via Mistral Embeddings API)
    
    Requires:
    - mistralai Python package
    - MISTRAL_API_KEY environment variable
    """
    
    provider_type = ProviderType.MISTRAL
    name = "Mistral"
    default_model = "mistral-tiny"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """Get or create the Mistral client."""
        if self._client is None:
            try:
                from mistralai.async_client import MistralAsyncClient
                
                api_key = self.config.api_key
                if not api_key:
                    raise ValueError("MISTRAL_API_KEY is required")
                
                self._client = MistralAsyncClient(
                    api_key=api_key,
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
            except ImportError:
                raise ImportError("mistralai package is required for MistralProvider")
        
        return self._client
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text using the Chat API.
        
        Note: Mistral primarily uses the Chat API.
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
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
            
            response = await client.chat_complete(**params)
            
            self._log_response("generate", response)
            
            return ProviderResponse(
                text=response.choices[0].message.content,
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
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
        Generate a chat response using the Chat API.
        
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
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            response = await client.chat_complete(**params)
            
            self._log_response("chat", response)
            
            choice = response.choices[0]
            
            return ChatResponse(
                text=choice.message.content,
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                finish_reason=choice.finish_reason,
                message=choice.message,
                metadata={
                    "id": response.id,
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
                messages.append({"role": "system", "content": system_prompt})
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
            
            response = await client.chat_stream(**params)
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            self._handle_error(e, "stream")
            raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate an embedding using Mistral Embeddings API.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector
        """
        self._log_request("embed", model=model, text=text[:50])
        
        try:
            client = await self._get_client()
            
            response = await client.embeddings(
                model=model or "mistral-embed",
                texts=[text],
            )
            
            self._log_response("embed", response)
            
            return response.data[0].embedding
            
        except Exception as e:
            self._handle_error(e, "embed")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        return [
            {"id": "mistral-tiny", "name": "Mistral Tiny"},
            {"id": "mistral-small", "name": "Mistral Small"},
            {"id": "mistral-medium", "name": "Mistral Medium"},
            {"id": "mistral-large", "name": "Mistral Large"},
            {"id": "codestral-latest", "name": "Codestral"},
            {"id": "mistral-embed", "name": "Mistral Embeddings"},
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
            "mistral-tiny": "Mistral Tiny",
            "mistral-small": "Mistral Small",
            "mistral-medium": "Mistral Medium",
            "mistral-large": "Mistral Large",
            "codestral-latest": "Codestral",
            "mistral-embed": "Mistral Embeddings",
        }
        return model_names.get(model, model)
