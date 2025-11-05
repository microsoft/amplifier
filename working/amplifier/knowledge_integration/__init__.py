"""
Unified Knowledge Graph Integration System

Combines concept mining and relationship extraction into a unified knowledge graph.
"""

from amplifier.knowledge_integration.entity_resolver import EntityMatch
from amplifier.knowledge_integration.entity_resolver import EntityResolver
from amplifier.knowledge_integration.entity_resolver import MatchType
from amplifier.knowledge_integration.inference_engine import InferenceRule
from amplifier.knowledge_integration.inference_engine import InferredRelationship
from amplifier.knowledge_integration.inference_engine import RelationshipInferenceEngine
from amplifier.knowledge_integration.knowledge_store import UnifiedKnowledgeStore
from amplifier.knowledge_integration.models import Relationship
from amplifier.knowledge_integration.models import UnifiedExtraction
from amplifier.knowledge_integration.models import UnifiedKnowledgeNode
from amplifier.knowledge_integration.unified_extractor import UnifiedKnowledgeExtractor
from amplifier.knowledge_integration.visualizer import KnowledgeGraphVisualizer

__all__ = [
    # Models
    "Relationship",
    "UnifiedKnowledgeNode",
    "UnifiedExtraction",
    # Core Components
    "UnifiedKnowledgeExtractor",
    "UnifiedKnowledgeStore",
    # Entity Resolution
    "EntityResolver",
    "EntityMatch",
    "MatchType",
    # Inference
    "InferenceRule",
    "InferredRelationship",
    "RelationshipInferenceEngine",
    # Visualization
    "KnowledgeGraphVisualizer",
]
