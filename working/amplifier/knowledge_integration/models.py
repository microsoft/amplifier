"""
Data models for knowledge graph integration.

Combines concepts from knowledge mining with SPO relationships.
"""

from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class Relationship:
    """A relationship between two entities in the knowledge graph"""

    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source: str | None = None

    def __str__(self) -> str:
        return f"{self.subject} --{self.predicate}--> {self.object}"


@dataclass
class UnifiedKnowledgeNode:
    """
    Unified node combining concept definitions with relationships.
    """

    id: str
    name: str
    type: str  # concept, pattern, technique, principle, tool, etc.
    definition: str

    # From concept mining
    category: str | None = None
    importance: float = 0.5
    article_source: str | None = None

    # Relationships this node participates in
    relationships_as_subject: list[Relationship] = field(default_factory=list)
    relationships_as_object: list[Relationship] = field(default_factory=list)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    sources: list[str] = field(default_factory=list)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to this node"""
        if relationship.subject == self.name:
            self.relationships_as_subject.append(relationship)
        elif relationship.object == self.name:
            self.relationships_as_object.append(relationship)


@dataclass
class UnifiedExtraction:
    """
    Result of unified extraction containing both concepts and relationships.
    """

    title: str
    source: str

    # Extracted concepts with definitions
    concepts: list[dict[str, Any]] = field(default_factory=list)

    # Extracted relationships (SPO triples)
    relationships: list[Relationship] = field(default_factory=list)

    # Additional insights
    key_insights: list[str] = field(default_factory=list)
    code_patterns: list[dict[str, str]] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    extraction_timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "source": self.source,
            "concepts": self.concepts,
            "relationships": [
                {
                    "subject": r.subject,
                    "predicate": r.predicate,
                    "object": r.object,
                    "confidence": r.confidence,
                    "source": r.source,
                }
                for r in self.relationships
            ],
            "key_insights": self.key_insights,
            "code_patterns": self.code_patterns,
            "metadata": self.metadata,
            "extraction_timestamp": self.extraction_timestamp,
        }
