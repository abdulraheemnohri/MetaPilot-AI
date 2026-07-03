"""
MetaPilot AI - Similarity Detector

Detects similarity between AI responses.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
import json
import hashlib
import numpy as np

logger = logging.getLogger(__name__)


class SimilarityMethod(Enum):
    """Methods for calculating similarity."""
    EXACT = "exact"  # Exact match
    JACCARD = "jaccard"  # Jaccard similarity (word overlap)
    COSINE = "cosine"  # Cosine similarity (requires embeddings)
    LEVENSHTEIN = "levenshtein"  # Levenshtein distance
    SEMANTIC = "semantic"  # Semantic similarity (using embeddings)
    HYBRID = "hybrid"  # Combination of methods


@dataclass
class SimilarityResult:
    """Result of a similarity comparison."""
    item1: Any
    item2: Any
    score: float
    method: SimilarityMethod
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item1": str(self.item1)[:100],  # Truncate for readability
            "item2": str(self.item2)[:100],
            "score": self.score,
            "method": self.method.value,
            "details": self.details
        }


@dataclass
class SimilarityMatrix:
    """Matrix of similarity scores between items."""
    items: List[Any]
    matrix: List[List[float]]
    method: SimilarityMethod
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [str(item)[:50] for item in self.items],
            "matrix": self.matrix,
            "method": self.method.value
        }
    
    def get_most_similar(self, index: int, k: int = 5) -> List[Tuple[int, float]]:
        """Get the k most similar items to the item at the given index."""
        if index < 0 or index >= len(self.matrix):
            return []
        
        # Get scores for this index
        scores = self.matrix[index]
        
        # Pair with indices and sort
        indexed_scores = [(i, score) for i, score in enumerate(scores) if i != index]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        return indexed_scores[:k]
    
    def get_clusters(self, threshold: float = 0.7) -> List[List[int]]:
        """
        Cluster items based on similarity.
        
        Args:
            threshold: Similarity threshold for clustering
        
        Returns:
            List of clusters (each cluster is a list of item indices)
        """
        # Simple clustering: start with each item as its own cluster
        clusters: List[List[int]] = [[i] for i in range(len(self.items))]
        
        # Merge clusters based on similarity
        changed = True
        while changed:
            changed = False
            new_clusters: List[List[int]] = []
            
            for cluster in clusters:
                if not cluster:
                    continue
                
                # Find similar clusters
                similar_clusters = [cluster]
                for other_cluster in clusters:
                    if cluster == other_cluster:
                        continue
                    
                    # Check if any pair of items between clusters is similar
                    for i in cluster:
                        for j in other_cluster:
                            if self.matrix[i][j] >= threshold:
                                similar_clusters.append(other_cluster)
                                break
                
                # Merge similar clusters
                merged_cluster = []
                for c in similar_clusters:
                    merged_cluster.extend(c)
                    if c in clusters:
                        clusters.remove(c)
                
                new_clusters.append(merged_cluster)
            
            clusters = new_clusters
            
            # Check if we made changes
            if len(clusters) < len(new_clusters):
                changed = True
        
        return clusters


class SimilarityDetector:
    """
    Detects similarity between AI responses.
    
    Supports multiple similarity calculation methods.
    """
    
    def __init__(self, 
                 embedding_model: Optional[Any] = None,
                 default_method: SimilarityMethod = SimilarityMethod.JACCARD):
        """
        Initialize the similarity detector.
        
        Args:
            embedding_model: Optional embedding model for semantic similarity
            default_method: Default similarity method to use
        """
        self.embedding_model = embedding_model
        self.default_method = default_method
    
    def compare(self, 
                item1: Any,
                item2: Any,
                method: Optional[SimilarityMethod] = None) -> SimilarityResult:
        """
        Compare two items for similarity.
        
        Args:
            item1: First item
            item2: Second item
            method: Similarity method to use
        
        Returns:
            SimilarityResult with score
        """
        effective_method = method or self.default_method
        
        # Convert items to comparable form
        str1 = self._to_string(item1)
        str2 = self._to_string(item2)
        
        # Calculate similarity based on method
        if effective_method == SimilarityMethod.EXACT:
            score = 1.0 if str1 == str2 else 0.0
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={"exact_match": str1 == str2}
            )
        
        elif effective_method == SimilarityMethod.JACCARD:
            score = self._jaccard_similarity(str1, str2)
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={"jaccard": score}
            )
        
        elif effective_method == SimilarityMethod.LEVENSHTEIN:
            score = self._levenshtein_similarity(str1, str2)
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={"levenshtein": score}
            )
        
        elif effective_method == SimilarityMethod.COSINE:
            score = self._cosine_similarity(str1, str2)
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={"cosine": score}
            )
        
        elif effective_method == SimilarityMethod.SEMANTIC:
            score = self._semantic_similarity(str1, str2)
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={"semantic": score}
            )
        
        elif effective_method == SimilarityMethod.HYBRID:
            jaccard = self._jaccard_similarity(str1, str2)
            levenshtein = self._levenshtein_similarity(str1, str2)
            
            # Weighted average
            score = 0.5 * jaccard + 0.5 * levenshtein
            
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=effective_method,
                details={
                    "jaccard": jaccard,
                    "levenshtein": levenshtein,
                    "hybrid": score
                }
            )
        
        else:
            # Default to Jaccard
            score = self._jaccard_similarity(str1, str2)
            return SimilarityResult(
                item1=item1,
                item2=item2,
                score=score,
                method=SimilarityMethod.JACCARD,
                details={"jaccard": score}
            )
    
    def compare_batch(self, 
                     items: List[Any],
                     method: Optional[SimilarityMethod] = None) -> SimilarityMatrix:
        """
        Compare all pairs of items in a batch.
        
        Args:
            items: List of items to compare
            method: Similarity method to use
        
        Returns:
            SimilarityMatrix with all pairwise scores
        """
        n = len(items)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        effective_method = method or self.default_method
        
        for i in range(n):
            for j in range(i, n):
                result = self.compare(items[i], items[j], effective_method)
                matrix[i][j] = result.score
                matrix[j][i] = result.score
        
        return SimilarityMatrix(
            items=items,
            matrix=matrix,
            method=effective_method
        )
    
    def find_duplicates(self, 
                       items: List[Any],
                       threshold: float = 0.9,
                       method: Optional[SimilarityMethod] = None) -> List[List[int]]:
        """
        Find groups of duplicate items.
        
        Args:
            items: List of items to check
            threshold: Similarity threshold for duplicates
            method: Similarity method to use
        
        Returns:
            List of duplicate groups (each group is a list of item indices)
        """
        matrix = self.compare_batch(items, method)
        clusters = matrix.get_clusters(threshold)
        
        # Filter out single-item clusters
        duplicate_groups = [c for c in clusters if len(c) > 1]
        
        return duplicate_groups
    
    def find_most_similar(self, 
                         query: Any,
                         items: List[Any],
                         k: int = 5,
                         method: Optional[SimilarityMethod] = None) -> List[Tuple[int, float]]:
        """
        Find the k most similar items to a query.
        
        Args:
            query: Query item
            items: List of items to search
            k: Number of results to return
            method: Similarity method to use
        
        Returns:
            List of (index, score) tuples sorted by score (descending)
        """
        scores = []
        
        for i, item in enumerate(items):
            result = self.compare(query, item, method)
            scores.append((i, result.score))
        
        # Sort by score (descending)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:k]
    
    def _to_string(self, item: Any) -> str:
        """Convert an item to a string for comparison."""
        if isinstance(item, (dict, list)):
            return json.dumps(item, sort_keys=True, default=str)
        return str(item)
    
    def _jaccard_similarity(self, str1: str, str2: str) -> float:
        """Calculate Jaccard similarity between two strings."""
        if not str1 or not str2:
            return 0.0
        
        # Tokenize into words
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _levenshtein_similarity(self, str1: str, str2: str) -> float:
        """Calculate Levenshtein similarity between two strings."""
        if not str1 or not str2:
            return 0.0
        
        distance = self._levenshtein_distance(str1, str2)
        max_len = max(len(str1), len(str2))
        
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def _levenshtein_distance(self, str1: str, str2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        m, n = len(str1), len(str2)
        
        # Create distance matrix
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        # Fill the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if str1[i - 1] == str2[j - 1]:
                    cost = 0
                else:
                    cost = 1
                
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # Deletion
                    dp[i][j - 1] + 1,  # Insertion
                    dp[i - 1][j - 1] + cost  # Substitution
                )
        
        return dp[m][n]
    
    def _cosine_similarity(self, str1: str, str2: str) -> float:
        """Calculate cosine similarity between two strings (using word frequency vectors)."""
        if not str1 or not str2:
            return 0.0
        
        # Get word frequencies
        vec1 = self._get_word_vector(str1)
        vec2 = self._get_word_vector(str2)
        
        # Calculate cosine similarity
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1.values(), vec2.values()))
        norm1 = sum(v ** 2 for v in vec1.values()) ** 0.5
        norm2 = sum(v ** 2 for v in vec2.values()) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_word_vector(self, text: str) -> Dict[str, float]:
        """Get word frequency vector for a text."""
        import re
        from collections import Counter
        
        words = re.findall(r'\w+', text.lower())
        return dict(Counter(words))
    
    def _semantic_similarity(self, str1: str, str2: str) -> float:
        """Calculate semantic similarity using embeddings."""
        if not self.embedding_model:
            logger.warning("No embedding model provided for semantic similarity. Falling back to cosine.")
            return self._cosine_similarity(str1, str2)
        
        try:
            import asyncio
            
            async def get_similarity():
                embedding1 = await self.embedding_model.encode(str1)
                embedding2 = await self.embedding_model.encode(str2)
                
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)
                
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return float(dot_product / (norm1 * norm2))
            
            # Run async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import asyncio
                new_loop = asyncio.new_event_loop()
                similarity = new_loop.run_until_complete(get_similarity())
                new_loop.close()
            else:
                similarity = loop.run_until_complete(get_similarity())
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0


# Global similarity detector instance
similarity_detector = None


def get_similarity_detector(embedding_model: Optional[Any] = None,
                             default_method: SimilarityMethod = SimilarityMethod.JACCARD) -> SimilarityDetector:
    """Get or create the global similarity detector."""
    global similarity_detector
    if similarity_detector is None:
        similarity_detector = SimilarityDetector(embedding_model, default_method)
    return similarity_detector
