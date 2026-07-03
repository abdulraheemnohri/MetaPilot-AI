"""
Vector Store for MetaPilot AI

Provides vector similarity search and storage capabilities.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
import pickle

from ..config import settings
from ..knowledge.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreEntry:
    """An entry in the vector store."""
    id: str
    vector: List[float]
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vector": self.vector,
            "content": self.content,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """A search result from the vector store."""
    entry: VectorStoreEntry
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": self.score,
        }


class VectorStore:
    """
    Vector store for similarity search.
    
    Supports multiple backends:
    - FAISS (Facebook AI Similarity Search)
    - In-memory (for testing and small datasets)
    - SQLite with vector extensions
    
    Features:
    - Add, update, and delete vectors
    - Similarity search (cosine, Euclidean, dot product)
    - Batch operations
    - Metadata filtering
    """
    
    def __init__(
        self,
        dimension: int = 384,
        backend: str = "faiss",
        index_path: Optional[Union[str, Path]] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
    ):
        self.dimension = dimension
        self.backend = backend or settings.VECTOR_STORE_TYPE
        self.index_path = index_path or (settings.CACHE_DIR / "vector_store")
        self.embedding_manager = embedding_manager
        
        # Initialize backend
        self._index = None
        self._entries: Dict[str, VectorStoreEntry] = {}
        self._initialized = False
        
        # Create directory if it doesn't exist
        if isinstance(self.index_path, Path):
            self.index_path.mkdir(parents=True, exist_ok=True)
        elif isinstance(self.index_path, str):
            Path(self.index_path).mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize the vector store."""
        if self._initialized:
            return
        
        logger.info(f"Initializing Vector Store with backend: {self.backend}")
        
        if self.backend == "faiss":
            await self._initialize_faiss()
        elif self.backend == "memory":
            await self._initialize_memory()
        elif self.backend == "sqlite":
            await self._initialize_sqlite()
        else:
            logger.error(f"Unsupported vector store backend: {self.backend}")
            raise ValueError(f"Unsupported vector store backend: {self.backend}")
        
        self._initialized = True
        logger.info("Vector Store initialized")
    
    async def _initialize_faiss(self):
        """Initialize FAISS index."""
        try:
            import faiss
            
            # Create index
            self._index = faiss.IndexFlatIP(self.dimension)
            
            # Try to load existing index
            index_file = self.index_path / "index.faiss" if isinstance(self.index_path, Path) else f"{self.index_path}/index.faiss"
            
            if os.path.exists(index_file):
                self._index = faiss.read_index(str(index_file))
                logger.info(f"Loaded existing FAISS index from {index_file}")
                
                # Load entries
                entries_file = self.index_path / "entries.json" if isinstance(self.index_path, Path) else f"{self.index_path}/entries.json"
                if os.path.exists(entries_file):
                    with open(entries_file, 'r', encoding='utf-8') as f:
                        entries_data = json.load(f)
                        for entry_data in entries_data:
                            entry = VectorStoreEntry(
                                id=entry_data["id"],
                                vector=entry_data["vector"],
                                content=entry_data["content"],
                                metadata=entry_data["metadata"],
                            )
                            self._entries[entry.id] = entry
            
        except ImportError:
            logger.error("FAISS not installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            raise
    
    async def _initialize_memory(self):
        """Initialize in-memory vector store."""
        logger.info("Using in-memory vector store")
        self._index = None  # Will use brute-force search
    
    async def _initialize_sqlite(self):
        """Initialize SQLite vector store."""
        try:
            import sqlite3
            from sqlite3 import Connection
            
            db_path = self.index_path / "vectors.db" if isinstance(self.index_path, Path) else f"{self.index_path}/vectors.db"
            
            self._conn = sqlite3.connect(str(db_path))
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vectors (
                    id TEXT PRIMARY KEY,
                    vector BLOB NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            self._conn.commit()
            
            logger.info(f"SQLite vector store initialized at {db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SQLite vector store: {e}")
            raise
    
    async def add(
        self,
        vector: List[float],
        content: str,
        id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a vector to the store.
        
        Args:
            vector: The vector to add
            content: Associated content
            id: Optional ID (will be generated if not provided)
            metadata: Optional metadata
        
        Returns:
            The ID of the added entry
        """
        if not self._initialized:
            await self.initialize()
        
        # Generate ID if not provided
        if not id:
            import uuid
            id = str(uuid.uuid4())
        
        # Validate vector
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension {len(vector)} doesn't match expected {self.dimension}")
        
        # Create entry
        entry = VectorStoreEntry(
            id=id,
            vector=vector,
            content=content,
            metadata=metadata or {},
        )
        
        # Store entry
        self._entries[id] = entry
        
        # Add to index
        if self.backend == "faiss":
            await self._add_to_faiss(entry)
        elif self.backend == "sqlite":
            await self._add_to_sqlite(entry)
        
        # Save to disk if using FAISS
        if self.backend == "faiss":
            await self._save_index()
        
        return id
    
    async def _add_to_faiss(self, entry: VectorStoreEntry):
        """Add an entry to FAISS index."""
        import numpy as np
        
        vector_arr = np.array([entry.vector], dtype=np.float32)
        self._index.add(vector_arr)
    
    async def _add_to_sqlite(self, entry: VectorStoreEntry):
        """Add an entry to SQLite database."""
        import pickle
        
        vector_blob = pickle.dumps(entry.vector)
        content = entry.content
        metadata_json = json.dumps(entry.metadata)
        
        self._conn.execute(
            "INSERT OR REPLACE INTO vectors (id, vector, content, metadata) VALUES (?, ?, ?, ?)",
            (entry.id, vector_blob, content, metadata_json),
        )
        self._conn.commit()
    
    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: The query vector
            limit: Maximum number of results
            metadata_filter: Optional metadata to filter by
        
        Returns:
            List of SearchResult objects
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate query vector
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension {len(query_vector)} doesn't match expected {self.dimension}")
        
        if self.backend == "faiss":
            results = await self._search_faiss(query_vector, limit, metadata_filter)
        elif self.backend == "memory":
            results = await self._search_memory(query_vector, limit, metadata_filter)
        elif self.backend == "sqlite":
            results = await self._search_sqlite(query_vector, limit, metadata_filter)
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
        
        return results
    
    async def _search_faiss(
        self,
        query_vector: List[float],
        limit: int,
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[SearchResult]:
        """Search using FAISS."""
        import numpy as np
        
        query_arr = np.array([query_vector], dtype=np.float32)
        
        # Search
        distances, indices = self._index.search(query_arr, limit)
        
        # Get entries
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            # FAISS returns indices in the order they were added
            # We need to map these to our entries
            entry_id = list(self._entries.keys())[idx]
            entry = self._entries[entry_id]
            
            # Apply metadata filter
            if metadata_filter:
                if not self._matches_metadata_filter(entry.metadata, metadata_filter):
                    continue
            
            # FAISS uses cosine similarity by default for normalized vectors
            # Convert distance to similarity
            score = 1.0 - distance
            
            results.append(SearchResult(entry=entry, score=float(score)))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def _search_memory(
        self,
        query_vector: List[float],
        limit: int,
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[SearchResult]:
        """Search using brute-force in memory."""
        results = []
        
        for entry in self._entries.values():
            # Apply metadata filter
            if metadata_filter:
                if not self._matches_metadata_filter(entry.metadata, metadata_filter):
                    continue
            
            # Calculate similarity
            score = self._cosine_similarity(query_vector, entry.vector)
            
            results.append(SearchResult(entry=entry, score=score))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def _search_sqlite(
        self,
        query_vector: List[float],
        limit: int,
        metadata_filter: Optional[Dict[str, Any]],
    ) -> List[SearchResult]:
        """Search using SQLite."""
        import pickle
        
        # Get all vectors
        cursor = self._conn.execute("SELECT id, vector, content, metadata FROM vectors")
        
        results = []
        for row in cursor:
            entry_id, vector_blob, content, metadata_json = row
            
            # Deserialize
            vector = pickle.loads(vector_blob)
            metadata = json.loads(metadata_json)
            
            entry = VectorStoreEntry(
                id=entry_id,
                vector=vector,
                content=content,
                metadata=metadata,
            )
            
            # Apply metadata filter
            if metadata_filter:
                if not self._matches_metadata_filter(metadata, metadata_filter):
                    continue
            
            # Calculate similarity
            score = self._cosine_similarity(query_vector, vector)
            
            results.append(SearchResult(entry=entry, score=score))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:limit]
    
    async def get(self, id: str) -> Optional[VectorStoreEntry]:
        """Get an entry by ID."""
        return self._entries.get(id)
    
    async def update(
        self,
        id: str,
        vector: Optional[List[float]] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update an entry."""
        if id not in self._entries:
            return False
        
        entry = self._entries[id]
        
        if vector is not None:
            entry.vector = vector
        if content is not None:
            entry.content = content
        if metadata is not None:
            entry.metadata = metadata
        
        # Update in index
        if self.backend == "faiss":
            await self._update_faiss(entry)
        elif self.backend == "sqlite":
            await self._update_sqlite(entry)
        
        return True
    
    async def _update_faiss(self, entry: VectorStoreEntry):
        """Update an entry in FAISS index."""
        # FAISS doesn't support easy updates, so we need to rebuild
        # For simplicity, we'll just save the index
        await self._save_index()
    
    async def _update_sqlite(self, entry: VectorStoreEntry):
        """Update an entry in SQLite."""
        import pickle
        
        vector_blob = pickle.dumps(entry.vector)
        metadata_json = json.dumps(entry.metadata)
        
        self._conn.execute(
            "UPDATE vectors SET vector = ?, content = ?, metadata = ? WHERE id = ?",
            (vector_blob, entry.content, metadata_json, entry.id),
        )
        self._conn.commit()
    
    async def delete(self, id: str) -> bool:
        """Delete an entry."""
        if id not in self._entries:
            return False
        
        del self._entries[id]
        
        # Delete from index
        if self.backend == "faiss":
            await self._delete_from_faiss(id)
        elif self.backend == "sqlite":
            await self._delete_from_sqlite(id)
        
        return True
    
    async def _delete_from_faiss(self, id: str):
        """Delete an entry from FAISS index."""
        # FAISS doesn't support easy deletion, so we need to rebuild
        await self._save_index()
    
    async def _delete_from_sqlite(self, id: str):
        """Delete an entry from SQLite."""
        self._conn.execute("DELETE FROM vectors WHERE id = ?", (id,))
        self._conn.commit()
    
    async def list_entries(
        self,
        limit: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[VectorStoreEntry]:
        """List all entries."""
        entries = list(self._entries.values())
        
        if metadata_filter:
            entries = [
                e for e in entries
                if self._matches_metadata_filter(e.metadata, metadata_filter)
            ]
        
        if limit:
            entries = entries[:limit]
        
        return entries
    
    async def clear(self):
        """Clear all entries."""
        self._entries.clear()
        
        if self.backend == "faiss":
            self._index.reset()
        elif self.backend == "sqlite":
            self._conn.execute("DELETE FROM vectors")
            self._conn.commit()
    
    async def _save_index(self):
        """Save FAISS index to disk."""
        if self.backend != "faiss" or not self._index:
            return
        
        import faiss
        
        index_file = self.index_path / "index.faiss" if isinstance(self.index_path, Path) else f"{self.index_path}/index.faiss"
        faiss.write_index(self._index, str(index_file))
        
        # Save entries
        entries_file = self.index_path / "entries.json" if isinstance(self.index_path, Path) else f"{self.index_path}/entries.json"
        entries_data = [
            {
                "id": entry.id,
                "vector": entry.vector,
                "content": entry.content,
                "metadata": entry.metadata,
            }
            for entry in self._entries.values()
        ]
        
        with open(entries_file, 'w', encoding='utf-8') as f:
            json.dump(entries_data, f, ensure_ascii=False, indent=2)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        
        dot_product = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def _matches_metadata_filter(
        self,
        entry_metadata: Dict[str, Any],
        filter_metadata: Dict[str, Any],
    ) -> bool:
        """Check if entry metadata matches the filter."""
        for key, value in filter_metadata.items():
            if key not in entry_metadata:
                return False
            if entry_metadata[key] != value:
                return False
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "backend": self.backend,
            "dimension": self.dimension,
            "entry_count": len(self._entries),
            "index_path": str(self.index_path),
        }
    
    async def change_backend(self, backend: str) -> bool:
        """Change the vector store backend."""
        if backend == self.backend:
            return True
        
        # Save current data
        entries = list(self._entries.values())
        
        # Change backend
        self.backend = backend
        self._initialized = False
        self._index = None
        self._entries = {}
        
        # Reinitialize
        await self.initialize()
        
        # Re-add entries
        for entry in entries:
            await self.add(entry.vector, entry.content, entry.id, entry.metadata)
        
        return True
