"""
Embedding Management for MetaPilot AI

Provides embedding generation and vector operations.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingModelConfig:
    """Configuration for an embedding model."""
    name: str
    dimension: int
    provider: str
    model_id: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None


# Supported embedding models
EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2": EmbeddingModelConfig(
        name="all-MiniLM-L6-v2",
        dimension=384,
        provider="sentence-transformers",
        model_id="sentence-transformers/all-MiniLM-L6-v2",
    ),
    "paraphrase-MiniLM-L6-v2": EmbeddingModelConfig(
        name="paraphrase-MiniLM-L6-v2",
        dimension=384,
        provider="sentence-transformers",
        model_id="sentence-transformers/paraphrase-MiniLM-L6-v2",
    ),
    "text-embedding-ada-002": EmbeddingModelConfig(
        name="text-embedding-ada-002",
        dimension=1536,
        provider="openai",
        model_id="text-embedding-ada-002",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    ),
    "text-embedding-3-small": EmbeddingModelConfig(
        name="text-embedding-3-small",
        dimension=1536,
        provider="openai",
        model_id="text-embedding-3-small",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    ),
    "text-embedding-3-large": EmbeddingModelConfig(
        name="text-embedding-3-large",
        dimension=3072,
        provider="openai",
        model_id="text-embedding-3-large",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
    ),
}


class EmbeddingManager:
    """
    Manages embedding generation using various models.
    
    Supports:
    - Local Sentence Transformers models
    - OpenAI embedding API
    - Custom embedding providers
    """
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model_config: Optional[EmbeddingModelConfig] = None
        self.model: Optional[Any] = None
        self.tokenizer: Optional[Any] = None
        self.dimension: int = 0
        self._initialized = False
    
    async def initialize(self):
        """Initialize the embedding manager."""
        if self._initialized:
            return
        
        logger.info(f"Initializing Embedding Manager with model: {self.model_name}")
        
        # Get model config
        if self.model_name not in EMBEDDING_MODELS:
            logger.warning(f"Model {self.model_name} not in predefined models, using default")
            self.model_name = "all-MiniLM-L6-v2"
        
        self.model_config = EMBEDDING_MODELS[self.model_name]
        self.dimension = self.model_config.dimension
        
        # Initialize based on provider
        if self.model_config.provider == "sentence-transformers":
            await self._initialize_sentence_transformers()
        elif self.model_config.provider == "openai":
            await self._initialize_openai()
        else:
            logger.error(f"Unsupported embedding provider: {self.model_config.provider}")
            raise ValueError(f"Unsupported embedding provider: {self.model_config.provider}")
        
        self._initialized = True
        logger.info(f"Embedding Manager initialized with {self.model_name} ({self.dimension} dimensions)")
    
    async def _initialize_sentence_transformers(self):
        """Initialize Sentence Transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading Sentence Transformers model: {self.model_config.model_id}")
            
            # Download model if not present
            model_path = Path(settings.MODELS_DIR) / "embeddings" / self.model_name
            model_path.mkdir(parents=True, exist_ok=True)
            
            self.model = SentenceTransformer(str(model_path))
            self.tokenizer = self.model.tokenizer
            
            logger.info(f"Sentence Transformers model loaded successfully")
            
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to load Sentence Transformers model: {e}")
            raise
    
    async def _initialize_openai(self):
        """Initialize OpenAI embedding client."""
        try:
            import openai
            
            api_key = os.getenv(self.model_config.api_key_env)
            if not api_key:
                logger.error(f"API key not found for {self.model_config.api_key_env}")
                raise ValueError(f"API key not found for {self.model_config.api_key_env}")
            
            self.client = openai.AsyncClient(
                api_key=api_key,
                base_url=self.model_config.base_url,
            )
            
            logger.info(f"OpenAI embedding client initialized")
            
        except ImportError:
            logger.error("openai package not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        
        Args:
            text: The text to embed
        
        Returns:
            Embedding vector as a list of floats
        """
        if not self._initialized:
            await self.initialize()
        
        if self.model_config.provider == "sentence-transformers":
            return self._embed_sentence_transformers(text)
        elif self.model_config.provider == "openai":
            return await self._embed_openai(text)
        else:
            raise ValueError(f"Unsupported provider: {self.model_config.provider}")
    
    async def _embed_sentence_transformers(self, text: str) -> List[float]:
        """Generate embedding using Sentence Transformers."""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def _embed_openai(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = await self.client.embeddings.create(
                model=self.model_config.model_id,
                input=text,
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()
        
        if self.model_config.provider == "sentence-transformers":
            return self._embed_batch_sentence_transformers(texts)
        elif self.model_config.provider == "openai":
            return await self._embed_batch_openai(texts)
        else:
            raise ValueError(f"Unsupported provider: {self.model_config.provider}")
    
    async def _embed_batch_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using Sentence Transformers."""
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    async def _embed_batch_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts using OpenAI API."""
        try:
            response = await self.client.embeddings.create(
                model=self.model_config.model_id,
                input=texts,
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
        
        Returns:
            Cosine similarity score (0 to 1)
        """
        a_arr = np.array(a)
        b_arr = np.array(b)
        
        dot_product = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def euclidean_distance(self, a: List[float], b: List[float]) -> float:
        """
        Calculate Euclidean distance between two vectors.
        
        Args:
            a: First vector
            b: Second vector
        
        Returns:
            Euclidean distance
        """
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.linalg.norm(a_arr - b_arr))
    
    def normalize(self, vector: List[float]) -> List[float]:
        """
        Normalize a vector to unit length.
        
        Args:
            vector: The vector to normalize
        
        Returns:
            Normalized vector
        """
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return vector
        return (arr / norm).tolist()
    
    def average(self, vectors: List[List[float]]) -> List[float]:
        """
        Calculate the average of multiple vectors.
        
        Args:
            vectors: List of vectors to average
        
        Returns:
            Average vector
        """
        if not vectors:
            return []
        
        arr = np.array(vectors)
        return np.mean(arr, axis=0).tolist()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model."""
        return {
            "name": self.model_name,
            "provider": self.model_config.provider if self.model_config else None,
            "dimension": self.dimension,
            "model_id": self.model_config.model_id if self.model_config else None,
        }
    
    async def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available embedding models."""
        models = []
        for name, config in EMBEDDING_MODELS.items():
            models.append({
                "name": name,
                "dimension": config.dimension,
                "provider": config.provider,
                "model_id": config.model_id,
            })
        return models
    
    async def change_model(self, model_name: str) -> bool:
        """Change the embedding model."""
        if model_name not in EMBEDDING_MODELS:
            logger.error(f"Model {model_name} not found")
            return False
        
        self.model_name = model_name
        self.model_config = EMBEDDING_MODELS[model_name]
        self.dimension = self.model_config.dimension
        self._initialized = False
        
        await self.initialize()
        return True
