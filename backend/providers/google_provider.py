"""
Google Provider for MetaPilot AI

Implementation of AIProvider for Google Generative AI API.
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


class GoogleProvider(AIProvider):
    """
    Google Generative AI provider.
    
    Supports:
    - Chat completions (Gemini API)
    - Embeddings
    
    Requires:
    - google-generativeai Python package
    - GOOGLE_API_KEY environment variable
    """
    
    provider_type = ProviderType.GOOGLE
    name = "Google"
    default_model = "gemini-1.5-flash"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        """Get or create the Google client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                
                api_key = self.config.api_key
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY is required")
                
                genai.configure(api_key=api_key)
                self._client = genai
            except ImportError:
                raise ImportError("google-generativeai package is required for GoogleProvider")
        
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
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "user", "parts": [{"text": system_prompt}], "system": True})
            messages.append({"role": "user", "parts": [{"text": prompt}]})
            
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
            params.pop("stop", None)
            
            model = client.GenerativeModel(params["model"])
            response = await model.generate_content_async(
                messages,
                generation_config={
                    "max_output_tokens": params["max_tokens"],
                    "temperature": params["temperature"],
                    "top_p": params["top_p"],
                },
            )
            
            self._log_response("generate", response)
            
            return ProviderResponse(
                text=response.text or "",
                model=params["model"],
                provider=self.name,
                tokens_prompt=0,  # Google doesn't provide token counts in the same way
                tokens_completion=0,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
                metadata={
                    "candidates": len(response.candidates) if response.candidates else 0,
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
            
            # Convert messages to Google format
            google_messages = []
            system_message = None
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    google_messages.append({
                        "role": msg["role"],
                        "parts": [{"text": msg["content"]}],
                    })
            
            # Merge kwargs with config
            params = {
                "model": model or self.config.default_model or self.default_model,
                "messages": google_messages,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                **kwargs,
            }
            
            model = client.GenerativeModel(params["model"])
            
            if system_message:
                # Add system message as the first user message
                google_messages.insert(0, {
                    "role": "user",
                    "parts": [{"text": system_message}],
                    "system": True,
                })
            
            chat = model.start_chat(history=[])
            response = await chat.send_message_async(google_messages[-1]["parts"][0]["text"])
            
            self._log_response("chat", response)
            
            return ChatResponse(
                text=response.text or "",
                model=params["model"],
                provider=self.name,
                tokens_prompt=0,
                tokens_completion=0,
                finish_reason=str(response.candidates[0].finish_reason) if response.candidates else None,
                message={"role": "assistant", "content": response.text or ""},
                metadata={
                    "candidates": len(response.candidates) if response.candidates else 0,
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
        
        Note: Google's streaming API is different and may not support true token-by-token streaming.
        """
        self._log_request("stream", model=model, prompt=prompt[:50])
        
        try:
            client = await self._get_client()
            
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "user", "parts": [{"text": system_prompt}], "system": True})
            messages.append({"role": "user", "parts": [{"text": prompt}]})
            
            model = client.GenerativeModel(model or self.config.default_model or self.default_model)
            
            response = await model.generate_content_async(
                messages,
                stream=True,
            )
            
            # Note: Google's streaming returns chunks, but not necessarily token-by-token
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
            
        except Exception as e:
            self._handle_error(e, "stream")
            raise
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate an embedding using Google's Embedding API.
        
        Args:
            text: Text to embed
            model: Embedding model to use
        
        Returns:
            Embedding vector
        """
        self._log_request("embed", model=model, text=text[:50])
        
        try:
            client = await self._get_client()
            
            model = client.GenerativeModel(
                model or "embedding-001"
            )
            
            response = await model.generate_embeddings([text])
            
            self._log_response("embed", response)
            
            return response.embeddings[0].values
            
        except Exception as e:
            self._handle_error(e, "embed")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        return [
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro"},
            {"id": "gemini-1.0-ultra", "name": "Gemini 1.0 Ultra"},
            {"id": "embedding-001", "name": "Embedding 001"},
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
            "gemini-1.5-flash": "Gemini 1.5 Flash",
            "gemini-1.5-pro": "Gemini 1.5 Pro",
            "gemini-1.0-pro": "Gemini 1.0 Pro",
            "gemini-1.0-ultra": "Gemini 1.0 Ultra",
            "embedding-001": "Embedding 001",
        }
        return model_names.get(model, model)
