"""
Perplexity Provider for MetaPilot AI

Implementation of AIProvider for Perplexity API.
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


class PerplexityProvider(AIProvider):
    """
    Perplexity API provider.
    
    Supports:
    - Chat completions
    - Text completions
    - Online search (Perplexity's specialty)
    
    Requires:
    - perplexity Python package or direct API calls
    - PERPLEXITY_API_KEY environment variable
    """
    
    provider_type = ProviderType.PERPLEXITY
    name = "Perplexity"
    default_model = "llama-3-sonar-large-32k-online"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """Get or create the Perplexity client."""
        if self._client is None:
            try:
                import httpx
                
                api_key = self.config.api_key
                if not api_key:
                    raise ValueError("PERPLEXITY_API_KEY is required")
                
                base_url = self.config.base_url or "https://api.perplexity.ai"
                
                self._client = httpx.AsyncClient(
                    base_url=base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.config.timeout,
                )
            except ImportError:
                raise ImportError("httpx package is required for PerplexityProvider")
        
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
        
        Note: Perplexity specializes in online search and knowledge.
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build request
            request_data = {
                "model": model or self.config.default_model or self.default_model,
                "messages": [],
            }
            
            if system_prompt:
                request_data["messages"].append({
                    "role": "system",
                    "content": system_prompt,
                })
            
            request_data["messages"].append({
                "role": "user",
                "content": prompt,
            })
            
            # Merge kwargs
            request_data.update({
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            })
            
            response = await client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._log_response("generate", data)
            
            choice = data["choices"][0]
            
            return ProviderResponse(
                text=choice["message"]["content"],
                model=data["model"],
                provider=self.name,
                tokens_prompt=data["usage"]["prompt_tokens"],
                tokens_completion=data["usage"]["completion_tokens"],
                finish_reason=choice["finish_reason"],
                metadata={
                    "id": data.get("id"),
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
        Generate a chat response.
        
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
            
            request_data = {
                "model": model or self.config.default_model or self.default_model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            }
            
            response = await client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._log_response("chat", data)
            
            choice = data["choices"][0]
            
            return ChatResponse(
                text=choice["message"]["content"],
                model=data["model"],
                provider=self.name,
                tokens_prompt=data["usage"]["prompt_tokens"],
                tokens_completion=data["usage"]["completion_tokens"],
                finish_reason=choice["finish_reason"],
                message=choice["message"],
                metadata={
                    "id": data.get("id"),
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
        """
        self._log_request("stream", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build request
            request_data = {
                "model": model or self.config.default_model or self.default_model,
                "messages": [],
                "stream": True,
            }
            
            if system_prompt:
                request_data["messages"].append({
                    "role": "system",
                    "content": system_prompt,
                })
            
            request_data["messages"].append({
                "role": "user",
                "content": prompt,
            })
            
            # Merge kwargs
            request_data.update({
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
            })
            
            response = await client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "choices" in data and data["choices"]:
                        if "delta" in data["choices"][0]:
                            delta = data["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
            
        except Exception as e:
            self._handle_error(e, "stream")
            raise
    
    async def search(
        self,
        query: str,
        model: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Perform a web search using Perplexity's search capability.
        
        This is Perplexity's specialty - answering questions with web search.
        
        Args:
            query: The search query
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            ProviderResponse with the search result
        """
        self._log_request("search", model=model, query=query[:50])
        
        try:
            client = await self._get_client()
            
            request_data = {
                "model": model or self.config.default_model or self.default_model,
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ],
            }
            
            # Add search parameters if provided
            request_data.update(kwargs)
            
            response = await client.post(
                "/chat/completions",
                json=request_data,
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._log_response("search", data)
            
            choice = data["choices"][0]
            
            return ProviderResponse(
                text=choice["message"]["content"],
                model=data["model"],
                provider=self.name,
                tokens_prompt=data["usage"]["prompt_tokens"],
                tokens_completion=data["usage"]["completion_tokens"],
                finish_reason=choice["finish_reason"],
                metadata={
                    "id": data.get("id"),
                    "search_used": True,
                },
            )
        except Exception as e:
            self._handle_error(e, "search")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        return [
            {"id": "llama-3-sonar-large-32k-online", "name": "Llama 3 Sonar Large 32K (Online)"},
            {"id": "llama-3-sonar-small-32k-online", "name": "Llama 3 Sonar Small 32K (Online)"},
            {"id": "llama-3-70b", "name": "Llama 3 70B"},
            {"id": "llama-3-8b", "name": "Llama 3 8B"},
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B"},
            {"id": "codellama-70b", "name": "CodeLlama 70B"},
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
            "llama-3-sonar-large-32k-online": "Llama 3 Sonar Large 32K (Online)",
            "llama-3-sonar-small-32k-online": "Llama 3 Sonar Small 32K (Online)",
            "llama-3-70b": "Llama 3 70B",
            "llama-3-8b": "Llama 3 8B",
            "mixtral-8x7b": "Mixtral 8x7B",
            "codellama-70b": "CodeLlama 70B",
        }
        return model_names.get(model, model)
