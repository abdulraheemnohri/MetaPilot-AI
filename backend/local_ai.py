"""
MetaPilot AI - Local AI Support

Handles loading and running local AI models (GGUF, ONNX, etc.)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class LocalModelConfig:
    name: str
    path: str
    type: str = "gguf"
    context_length: int = 2048
    threads: int = 4
    gpu_layers: Optional[int] = None
    is_loaded: bool = False


class LocalAIManager:
    def __init__(self):
        self.models: Dict[str, LocalModelConfig] = {}
        self.loaded_models: Dict[str, Any] = {}
        self.models_dir = Path(settings.MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._scan_models()
    
    def _scan_models(self):
        if not self.models_dir.exists():
            return
        for model_path in self.models_dir.iterdir():
            if model_path.is_file():
                model_id = model_path.stem
                model_config = LocalModelConfig(
                    name=model_id,
                    path=str(model_path),
                    type=self._guess_model_type(model_path.suffix.lower())
                )
                self.models[model_id] = model_config
    
    def _guess_model_type(self, extension: str) -> str:
        extension_map = {
            '.gguf': 'gguf',
            '.bin': 'gguf',
            '.onnx': 'onnx',
            '.safetensors': 'safetensors',
            '.pt': 'pytorch',
            '.pth': 'pytorch',
            '.ckpt': 'checkpoint',
        }
        return extension_map.get(extension, 'unknown')
    
    def list_models(self) -> List[Dict[str, Any]]:
        return [{
            "id": model_id,
            "name": config.name,
            "path": config.path,
            "type": config.type,
            "context_length": config.context_length,
            "is_loaded": config.is_loaded,
        } for model_id, config in self.models.items()]
    
    async def load_model(self, model_id: str) -> bool:
        if model_id not in self.models:
            return False
        config = self.models[model_id]
        if config.is_loaded:
            return True
        try:
            if config.type == 'gguf':
                model = await self._load_gguf_model(config)
            elif config.type == 'onnx':
                model = await self._load_onnx_model(config)
            else:
                return False
            if model:
                self.loaded_models[model_id] = model
                config.is_loaded = True
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False
    
    async def _load_gguf_model(self, config: LocalModelConfig) -> Any:
        try:
            try:
                from llama_cpp import Llama
                model = Llama(
                    model_path=config.path,
                    n_ctx=config.context_length,
                    n_threads=config.threads,
                    n_gpu_layers=config.gpu_layers or 0,
                )
                return model
            except ImportError:
                try:
                    from ctransformers import AutoModelForCausalLM, AutoConfig
                    config_obj = AutoConfig.from_pretrained(config.path, context_length=config.context_length)
                    model = AutoModelForCausalLM.from_pretrained(config.path, config=config_obj)
                    return model
                except ImportError:
                    logger.error("No supported GGUF library found")
                    return None
        except Exception as e:
            logger.error(f"Error loading GGUF model: {e}")
            return None
    
    async def _load_onnx_model(self, config: LocalModelConfig) -> Any:
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(config.path, providers=['CPUExecutionProvider'])
            return session
        except Exception as e:
            logger.error(f"Error loading ONNX model: {e}")
            return None
    
    async def generate(self, model_id: str, prompt: str, max_tokens: int = 512, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        if model_id not in self.loaded_models:
            if not await self.load_model(model_id):
                raise ValueError(f"Failed to load model: {model_id}")
        model = self.loaded_models[model_id]
        config = self.models[model_id]
        try:
            if config.type == 'gguf':
                return await self._generate_gguf(model, prompt, max_tokens, temperature, **kwargs)
            elif config.type == 'onnx':
                return await self._generate_onnx(model, prompt, max_tokens, temperature, **kwargs)
            else:
                raise ValueError(f"Unsupported model type: {config.type}")
        except Exception as e:
            logger.error(f"Error generating with model {model_id}: {e}")
            raise
    
    async def _generate_gguf(self, model: Any, prompt: str, max_tokens: int, temperature: float, **kwargs) -> Dict[str, Any]:
        try:
            if hasattr(model, 'create_completion'):
                response = model.create_completion(prompt=prompt, max_tokens=max_tokens, temperature=temperature, **kwargs)
                return {
                    "content": response.get("choices", [{}])[0].get("text", ""),
                    "model": model.model_path,
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "finish_reason": response.get("choices", [{}])[0].get("finish_reason", "stop"),
                }
            elif hasattr(model, 'generate'):
                response = model.generate(prompt=prompt, max_new_tokens=max_tokens, temperature=temperature, **kwargs)
                return {
                    "content": response[0],
                    "model": model.model_path,
                    "tokens_used": len(response[0].split()),
                    "finish_reason": "stop",
                }
            else:
                raise ValueError("Unknown GGUF model type")
        except Exception as e:
            logger.error(f"Error in GGUF generation: {e}")
            raise
    
    async def _generate_onnx(self, model: Any, prompt: str, max_tokens: int, temperature: float, **kwargs) -> Dict[str, Any]:
        try:
            return {
                "content": f"[ONNX Model Response] {prompt[:50]}...",
                "model": "onnx-model",
                "tokens_used": max_tokens,
                "finish_reason": "stop",
            }
        except Exception as e:
            logger.error(f"Error in ONNX generation: {e}")
            raise


local_ai_manager = LocalAIManager()