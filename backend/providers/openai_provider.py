"""
OpenAI Provider for MetaPilot AI

Implementation of AIProvider for OpenAI API.
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


class OpenAIProvider(AIProvider):
    """
    OpenAI API provider.
    
    Supports:
    - Text generation (Completions API)
    - Chat completions (Chat API)
    - Streaming
    - Embeddings
    
    Requires:
    - openai Python package
    - OPENAI_API_KEY environment variable
    """
    
    provider_type = ProviderType.OPENAI
    name = "OpenAI"
    default_model = "gpt-3.5-turbo"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._client = None
        self._async_client = None
    
    async def _get_client(self):
        """Get or create the OpenAI client."""
        if self._async_client is None:
            try:
                import openai
                
                api_key = self.config.api_key
                if not api_key:
                    raise ValueError("OPENAI_API_KEY is required")
                
                self._async_client = openai.AsyncClient(
                    api_key=api_key,
                    base_url=self.config.base_url or "https://api.openai.com/v1",
                    timeout=self.config.timeout,
                    max_retries=self.config.max_retries,
                )
            except ImportError:
                raise ImportError("openai package is required for OpenAIProvider")
        
        return self._async_client
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text using the Completions API.
        
        Note: For most use cases, use the chat() method instead.
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            response = await client.completions.create(**params)
            
            self._log_response("generate", response)
            
            return ProviderResponse(
                text=response.choices[0].text,
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
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
            
            # Remove unsupported parameters
            params.pop("stream", None)
            params.pop("stop", None)
            
            response = await client.chat.completions.create(**params)
            
            self._log_response("chat", response)
            
            choice = response.choices[0]
            message = choice.message
            
            return ChatResponse(
                text=message.content or "",
                model=response.model,
                provider=self.name,
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                finish_reason=choice.finish_reason,
                message=message,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "system_fingerprint": response.system_fingerprint,
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
                "stream": True,
                **kwargs,
            }
            
            response = await client.chat.completions.create(**params)
            
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
        Generate an embedding using OpenAI's Embedding API.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector
        """
        self._log_request("embed", model=model, text=text[:50])
        
        try:
            client = await self._get_client()
            
            response = await client.embeddings.create(
                model=model or "text-embedding-ada-002",
                input=text,
            )
            
            self._log_response("embed", response)
            
            return response.data[0].embedding
            
        except Exception as e:
            self._handle_error(e, "embed")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            client = await self._get_client()
            response = await client.models.list()
            
            return [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by,
                }
                for model in response.data
            ]
        except Exception as e:
            self._handle_error(e, "list_models")
            return []
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        try:
            client = await self._get_client()
            response = await client.models.retrieve(model)
            
            return {
                "id": response.id,
                "created": response.created,
                "owned_by": response.owned_by,
                "permission": [p.to_dict() for p in response.permission],
                "root": response.root,
                "parent": response.parent,
            }
        except Exception as e:
            self._handle_error(e, "get_model_info")
            return {"id": model, "provider": self.name}
