"""
Consolidation module for cross-chunk analysis and context expansion.

This module provides intelligent consolidation of chunked analysis results,
identifying relevant chunks, expanding context windows, and merging insights.
"""

from .consolidator import ResultConsolidator
from .models import ChunkAnalysis
from .models import ChunkReference
from .models import ConsolidatedResult

__all__ = ["ResultConsolidator", "ConsolidatedResult", "ChunkAnalysis", "ChunkReference"]
