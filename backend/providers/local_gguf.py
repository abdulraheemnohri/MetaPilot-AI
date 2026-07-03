"""
Local GGUF Provider for MetaPilot AI

Implementation of AIProvider for local GGUF models using llama.cpp.
"""

import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from pathlib import Path

from .base import (
    AIProvider,
    ProviderConfig,
    ProviderResponse,
    ChatResponse,
    ProviderType,
)

logger = logging.getLogger(__name__)


class LocalGGUFProvider(AIProvider):
    """
    Local GGUF model provider using llama.cpp.
    
    Supports:
    - Text generation
    - Chat completions
    - Streaming
    
    Requires:
    - llama-cpp-python package
    - GGUF model files
    """
    
    provider_type = ProviderType.LOCAL_GGUF
    name = "Local GGUF"
    default_model = "llama-2-7b"
    
    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config)
        self._models: Dict[str, Any] = {}
        self._loaded_models: Dict[str, Any] = {}
    
    async def _get_model(self, model_name: str) -> Any:
        """Get or load a GGUF model."""
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]
        
        # Find model path
        model_path = self._find_model_path(model_name)
        
        if not model_path:
            raise ValueError(f"Model '{model_name}' not found")
        
        try:
            from llama_cpp import Llama
            
            logger.info(f"Loading GGUF model: {model_name}")
            
            model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.max_tokens * 2,  # Context window
                n_threads=-1,  # Use all available threads
                n_batch=512,
                n_gpu_layers=0,  # CPU only for now
            )
            
            self._loaded_models[model_name] = model
            logger.info(f"Loaded GGUF model: {model_name}")
            
            return model
            
        except ImportError:
            raise ImportError("llama-cpp-python package is required for LocalGGUFProvider")
        except Exception as e:
            logger.error(f"Failed to load GGUF model '{model_name}': {e}")
            raise
    
    def _find_model_path(self, model_name: str) -> Optional[Path]:
        """Find the path to a GGUF model file."""
        # Check common locations
        search_paths = [
            Path(settings.LOCAL_AI_MODEL_PATH),
            Path(settings.MODELS_DIR),
            Path("models"),
        ]
        
        # Try different extensions
        extensions = [".gguf", ""]
        
        for search_path in search_paths:
            for ext in extensions:
                model_file = search_path / f"{model_name}{ext}"
                if model_file.exists():
                    return model_file
                
                # Try with common naming patterns
                for pattern in ["Q4_K_M", "Q4_0", "Q5_K_M", "Q8_0"]:
                    model_file = search_path / f"{model_name}.{pattern}.gguf"
                    if model_file.exists():
                        return model_file
        
        return None
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate text using a local GGUF model.
        """
        self._log_request("generate", model=model, prompt=prompt[:50])
        
        try:
            model_name = model or self.config.default_model or self.default_model
            llama_model = await self._get_model(model_name)
            
            # Build prompt
            full_prompt = self._build_prompt(prompt, system_prompt)
            
            # Merge kwargs with config
            params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "echo": False,
            }
            
            response = llama_model(
                full_prompt,
                **params,
            )
            
            self._log_response("generate", response)
            
            return ProviderResponse(
                text=response["choices"][0]["text"],
                model=model_name,
                provider=self.name,
                tokens_prompt=response["usage"]["prompt_tokens"],
                tokens_completion=response["usage"]["completion_tokens"],
                finish_reason=response["choices"][0].get("finish_reason", "stop"),
                metadata={
                    "model_path": str(llama_model.model_path),
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
        Generate a chat response using a local GGUF model.
        
        Args:
            messages: List of chat messages
            model: Model to use
            **kwargs: Additional parameters
        
        Returns:
            ChatResponse with the assistant's reply
        """
        self._log_request("chat", model=model, messages=messages[:3])
        
        try:
            model_name = model or self.config.default_model or self.default_model
            llama_model = await self._get_model(model_name)
            
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)
            
            # Merge kwargs with config
            params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "echo": False,
            }
            
            response = llama_model(
                prompt,
                **params,
            )
            
            self._log_response("chat", response)
            
            return ChatResponse(
                text=response["choices"][0]["text"],
                model=model_name,
                provider=self.name,
                tokens_prompt=response["usage"]["prompt_tokens"],
                tokens_completion=response["usage"]["completion_tokens"],
                finish_reason=response["choices"][0].get("finish_reason", "stop"),
                message={"role": "assistant", "content": response["choices"][0]["text"]},
                metadata={
                    "model_path": str(llama_model.model_path),
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
            model_name = model or self.config.default_model or self.default_model
            llama_model = await self._get_model(model_name)
            
            # Build prompt
            full_prompt = self._build_prompt(prompt, system_prompt)
            
            # Merge kwargs with config
            params = {
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
                "echo": False,
                "stream": True,
            }
            
            response = llama_model(
                full_prompt,
                **params,
            )
            
            for chunk in response:
                if "choices" in chunk and chunk["choices"]:
                    if "text" in chunk["choices"][0]:
                        yield chunk["choices"][0]["text"]
            
        except Exception as e:
            self._handle_error(e, "stream")
            raise
    
    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Build a full prompt for GGUF models."""
        if system_prompt:
            return f"<s>[INST] {system_prompt} [/INST]\n{prompt} [/INST]"
        else:
            return f"<s>[INST] {prompt} [/INST]"
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert chat messages to a prompt for GGUF models."""
        prompt = ""
        
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"<s>[INST] {msg['content']} [/INST]\n"
            elif msg["role"] == "user":
                prompt += f"[INST] {msg['content']} [/INST]\n"
            elif msg["role"] == "assistant":
                prompt += f"{msg['content']}\n"
        
        return prompt
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available GGUF models."""
        models = []
        
        # Check common locations
        search_paths = [
            Path(settings.LOCAL_AI_MODEL_PATH),
            Path(settings.MODELS_DIR),
            Path("models"),
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for model_file in search_path.glob("*.gguf"):
                    models.append({
                        "id": model_file.stem,
                        "name": model_file.stem,
                        "path": str(model_file),
                        "size": model_file.stat().st_size,
                    })
        
        return models
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        model_path = self._find_model_path(model)
        
        if model_path:
            return {
                "id": model,
                "provider": self.name,
                "name": model,
                "path": str(model_path),
                "size": model_path.stat().st_size,
            }
        
        return {
            "id": model,
            "provider": self.name,
            "name": model,
        }
    
    async def unload_model(self, model_name: str) -> bool:
        """Unload a model from memory."""
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            logger.info(f"Unloaded GGUF model: {model_name}")
            return True
        return False
    
    async def unload_all(self):
        """Unload all models from memory."""
        for model_name in list(self._loaded_models.keys()):
            await self.unload_model(model_name)
