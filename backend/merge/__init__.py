"""
MetaPilot AI - Merge Module

Provides response merging and deduplication functionality.
"""

from .conflict_resolver import ConflictResolver
from .duplicate_remover import DuplicateRemover
from .result_fuser import ResultFuser
from .similarity_detector import SimilarityDetector

__all__ = [
    "ConflictResolver",
    "DuplicateRemover",
    "ResultFuser",
    "SimilarityDetector"
]
