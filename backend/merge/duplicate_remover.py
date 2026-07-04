"""
MetaPilot AI - Duplicate Remover

Removes duplicate entries from AI responses.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import json
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class DuplicateRemovalResult:
    """Result of duplicate removal."""
    original_items: List[Any]
    unique_items: List[Any]
    duplicates_removed: int
    duplicates: List[Tuple[int, int]]  # List of (original_index, duplicate_index) pairs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_count": len(self.original_items),
            "unique_count": len(self.unique_items),
            "duplicates_removed": self.duplicates_removed,
            "duplicates": self.duplicates
        }


class DuplicateRemover:
    """
    Removes duplicate entries from lists of AI responses.
    
    Supports various comparison methods for detecting duplicates.
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.9,
                 use_semantic_similarity: bool = False,
                 embedding_model: Optional[Any] = None):
        """
        Initialize the duplicate remover.
        
        Args:
            similarity_threshold: Threshold for considering items similar (0-1)
            use_semantic_similarity: Whether to use semantic similarity
            embedding_model: Optional embedding model for semantic comparison
        """
        self.similarity_threshold = similarity_threshold
        self.use_semantic_similarity = use_semantic_similarity
        self.embedding_model = embedding_model
        self._similarity_detector = None
    
    def remove_duplicates(self, 
                          items: List[Any],
                          key: Optional[Callable[[Any], Any]] = None,
                          method: str = "exact") -> DuplicateRemovalResult:
        """
        Remove duplicates from a list of items.
        
        Args:
            items: List of items to deduplicate
            key: Optional function to extract comparison key from each item
            method: Method to use for duplicate detection ("exact", "similar", "semantic")
        
        Returns:
            DuplicateRemovalResult with unique items
        """
        if not items:
            return DuplicateRemovalResult(
                original_items=[],
                unique_items=[],
                duplicates_removed=0,
                duplicates=[]
            )
        
        # Extract comparison keys
        if key:
            key_items = [key(item) for item in items]
        else:
            key_items = items
        
        # Detect duplicates based on method
        if method == "exact":
            return self._remove_exact_duplicates(items, key_items)
        elif method == "similar":
            return self._remove_similar_duplicates(items, key_items)
        elif method == "semantic":
            return self._remove_semantic_duplicates(items, key_items)
        else:
            return self._remove_exact_duplicates(items, key_items)
    
    def _remove_exact_duplicates(self, 
                                items: List[Any],
                                key_items: List[Any]) -> DuplicateRemovalResult:
        """Remove exact duplicates."""
        seen: Dict[str, int] = {}
        unique_items: List[Any] = []
        duplicates: List[Tuple[int, int]] = []
        
        for i, (item, key_item) in enumerate(zip(items, key_items)):
            # Create a hashable key
            if isinstance(key_item, (dict, list)):
                key_str = json.dumps(key_item, sort_keys=True, default=str)
            else:
                key_str = str(key_item)
            
            if key_str in seen:
                # This is a duplicate
                duplicates.append((seen[key_str], i))
            else:
                seen[key_str] = i
                unique_items.append(item)
        
        return DuplicateRemovalResult(
            original_items=items,
            unique_items=unique_items,
            duplicates_removed=len(duplicates),
            duplicates=duplicates
        )
    
    def _remove_similar_duplicates(self, 
                                   items: List[Any],
                                   key_items: List[Any]) -> DuplicateRemovalResult:
        """Remove similar duplicates based on text similarity."""
        # Convert items to strings for comparison
        text_items = [self._to_comparable_string(item) for item in key_items]
        
        # Calculate similarity matrix
        similarity_matrix = self._calculate_similarity_matrix(text_items)
        
        # Find duplicates
        seen: List[int] = []
        duplicates: List[Tuple[int, int]] = []
        
        for i in range(len(items)):
            is_duplicate = False
            for j in seen:
                if similarity_matrix[i][j] >= self.similarity_threshold:
                    duplicates.append((j, i))
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen.append(i)
        
        unique_items = [items[i] for i in seen]
        
        return DuplicateRemovalResult(
            original_items=items,
            unique_items=unique_items,
            duplicates_removed=len(duplicates),
            duplicates=duplicates
        )
    
    def _remove_semantic_duplicates(self, 
                                     items: List[Any],
                                     key_items: List[Any]) -> DuplicateRemovalResult:
        """Remove semantic duplicates using embeddings."""
        if not self.embedding_model:
            logger.warning("No embedding model provided for semantic duplicate removal. Falling back to similar method.")
            return self._remove_similar_duplicates(items, key_items)
        
        try:
            import asyncio
            
            # Convert items to text and get embeddings
            async def get_embeddings():
                text_items = [self._to_comparable_string(item) for item in key_items]
                embeddings = []
                
                for text in text_items:
                    embedding = await self.embedding_model.encode(text)
                    embeddings.append(embedding)
                
                return embeddings
            
            # Run async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a new event loop
                import asyncio
                new_loop = asyncio.new_event_loop()
                embeddings = new_loop.run_until_complete(get_embeddings())
                new_loop.close()
            else:
                embeddings = loop.run_until_complete(get_embeddings())
            
            # Calculate semantic similarity matrix
            similarity_matrix = self._calculate_embedding_similarity(embeddings)
            
            # Find duplicates
            seen: List[int] = []
            duplicates: List[Tuple[int, int]] = []
            
            for i in range(len(items)):
                is_duplicate = False
                for j in seen:
                    if similarity_matrix[i][j] >= self.similarity_threshold:
                        duplicates.append((j, i))
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    seen.append(i)
            
            unique_items = [items[i] for i in seen]
            
            return DuplicateRemovalResult(
                original_items=items,
                unique_items=unique_items,
                duplicates_removed=len(duplicates),
                duplicates=duplicates
            )
            
        except Exception as e:
            logger.error(f"Error in semantic duplicate removal: {e}")
            return self._remove_similar_duplicates(items, key_items)
    
    def _to_comparable_string(self, item: Any) -> str:
        """Convert an item to a comparable string."""
        if isinstance(item, (dict, list)):
            return json.dumps(item, sort_keys=True, default=str)
        return str(item)
    
    def _calculate_similarity_matrix(self, texts: List[str]) -> List[List[float]]:
        """Calculate similarity matrix for a list of texts."""
        n = len(texts)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i, n):
                similarity = self._text_similarity(texts[i], texts[j])
                matrix[i][j] = similarity
                matrix[j][i] = similarity
        
        return matrix
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Uses a combination of Jaccard similarity and sequence matching.
        """
        if not text1 or not text2:
            return 0.0
        
        if text1 == text2:
            return 1.0
        
        # Jaccard similarity (word overlap)
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            jaccard = 0.0
        else:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union if union > 0 else 0.0
        
        # Sequence similarity (longest common subsequence)
        seq_similarity = self._sequence_similarity(text1, text2)
        
        # Combine with weights
        return 0.6 * jaccard + 0.4 * seq_similarity
    
    def _sequence_similarity(self, text1: str, text2: str) -> float:
        """Calculate sequence similarity using longest common subsequence."""
        # Convert to lowercase and split into words
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        
        # Find LCS length
        lcs_length = self._lcs_length(words1, words2)
        
        # Normalize by the length of the longer sequence
        max_len = max(len(words1), len(words2))
        return lcs_length / max_len if max_len > 0 else 0.0
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """Find the length of the longest common subsequence."""
        m, n = len(seq1), len(seq2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        
        return dp[m][n]
    
    def _calculate_embedding_similarity(self, embeddings: List[List[float]]) -> List[List[float]]:
        """Calculate cosine similarity matrix for embeddings."""
        import numpy as np
        
        n = len(embeddings)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(i, n):
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                matrix[i][j] = similarity
                matrix[j][i] = similarity
        
        return matrix
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np
        
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        dot_product = np.dot(vec1_array, vec2_array)
        norm1 = np.linalg.norm(vec1_array)
        norm2 = np.linalg.norm(vec2_array)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))


# Global duplicate remover instance
duplicate_remover = DuplicateRemover()


def get_duplicate_remover(similarity_threshold: float = 0.9,
                          use_semantic_similarity: bool = False,
                          embedding_model: Optional[Any] = None) -> DuplicateRemover:
    """Get or create the global duplicate remover."""
    global duplicate_remover
    if duplicate_remover is None:
        duplicate_remover = DuplicateRemover(
            similarity_threshold,
            use_semantic_similarity,
            embedding_model
        )
    return duplicate_remover
