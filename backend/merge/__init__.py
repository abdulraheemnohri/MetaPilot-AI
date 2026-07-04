"""
MetaPilot AI - Merge Module

Provides response merging and deduplication functionality.
"""

from .conflict_resolver import ConflictResolver
from .conflict_resolver import conflict_resolver, get_conflict_resolver
from .duplicate_remover import DuplicateRemover
from .duplicate_remover import duplicate_remover, get_duplicate_remover
from .result_fuser import ResultFuser
from .result_fuser import result_fuser, get_result_fuser
from .similarity_detector import SimilarityDetector

__all__ = [
    "ConflictResolver",
    "DuplicateRemover",
    "ResultFuser",
    "SimilarityDetector"
]
