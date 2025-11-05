"""
Knowledge Mining System - Extract and apply knowledge from articles.
"""

from .insight_generator import InsightGenerator
from .knowledge_assistant import KnowledgeAssistant
from .knowledge_extractor import KnowledgeExtractor
from .knowledge_store import KnowledgeStore
from .pattern_finder import PatternFinder

__all__ = [
    "InsightGenerator",
    "KnowledgeAssistant",
    "KnowledgeExtractor",
    "KnowledgeStore",
    "PatternFinder",
]

__version__ = "1.0.0"
