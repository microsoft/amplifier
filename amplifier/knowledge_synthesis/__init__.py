"""
Knowledge Synthesis Module

Simple, direct knowledge extraction from text using Claude Code SDK.
Extracts concepts, relationships, insights, and patterns in a single pass.
"""

from .article_processor import ArticleProcessingStatus
from .article_processor import ArticleProcessor
from .article_processor import ProcessingStatusStore
from .article_processor import ProcessorResult
from .extractor import KnowledgeSynthesizer
from .store import KnowledgeStore

__all__ = [
    # Core extraction
    "KnowledgeSynthesizer",
    "KnowledgeStore",
    # Article Processing
    "ArticleProcessor",
    "ProcessingStatusStore",
    # Data Models
    "ProcessorResult",
    "ArticleProcessingStatus",
]
