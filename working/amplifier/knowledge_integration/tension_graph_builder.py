"""
Tension-Based Knowledge Graph Builder for Knowledge Synthesis System.

Constructs knowledge graphs that preserve multiple perspectives and productive tensions.
Follows the principle: Diverse viewpoints enrich understanding. Tensions drive insight.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.knowledge_integration.models import Relationship

logger = logging.getLogger(__name__)


@dataclass
class PerspectiveTriple:
    """SPO triple with perspective attribution and metadata."""

    subject: str
    predicate: str  # 1-3 words maximum
    object: str
    perspective_id: str  # ID of the contributing perspective/agent
    chunk_number: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    emphasis_level: float = 0.5  # 0-1 scale of how strongly this is emphasized
    confidence: float = 0.8
    is_inferred: bool = False  # True if inferred vs directly extracted

    def signature(self) -> str:
        """Unique signature for this triple."""
        return f"{self.subject.lower()}|{self.predicate.lower()}|{self.object.lower()}"


@dataclass
class PerspectiveNode:
    """Node that can be viewed from multiple perspectives."""

    id: str
    canonical_name: str  # The "agreed" name (if any)
    variations: dict[str, set[str]] = field(default_factory=dict)  # perspective_id -> name variations
    contributing_perspectives: set[str] = field(default_factory=set)
    diversity_score: float = 0.0  # 0-1, increases with more perspectives
    definitions: dict[str, str] = field(default_factory=dict)  # perspective_id -> definition
    perspective_weight: dict[str, float] = field(default_factory=dict)  # perspective_id -> weight

    def add_perspective(self, perspective_id: str, name_variation: str, weight: float = 0.5):
        """Add a perspective's view of this node."""
        self.contributing_perspectives.add(perspective_id)
        if perspective_id not in self.variations:
            self.variations[perspective_id] = set()
        self.variations[perspective_id].add(name_variation)
        self.perspective_weight[perspective_id] = max(self.perspective_weight.get(perspective_id, 0), weight)
        # Increase diversity with each new perspective
        self.diversity_score = min(0.95, len(self.contributing_perspectives) * 0.15)


@dataclass
class MultiViewEdge:
    """Edge that can have multiple interpretations from different viewpoints."""

    id: str
    subject_id: str
    object_id: str
    predicates: dict[str, str] = field(default_factory=dict)  # perspective_id -> predicate
    tension_intensity: float = 0.0  # 0-1, based on divergence
    parallel_views: list[PerspectiveTriple] = field(default_factory=list)

    def add_interpretation(self, perspective_id: str, predicate: str, triple: PerspectiveTriple):
        """Add a perspective's interpretation of this edge."""
        self.predicates[perspective_id] = predicate
        self.parallel_views.append(triple)
        # Calculate tension intensity based on predicate variations
        unique_predicates = len(set(self.predicates.values()))
        self.tension_intensity = (unique_predicates - 1) / max(len(self.predicates), 1)


@dataclass
class DivergencePoint:
    """Point where perspectives diverge productively."""

    node_ids: set[str]
    edge_ids: set[str]
    divergence_type: str  # "concept", "relationship", "definition", "emphasis"
    perspectives_involved: set[str]
    productivity_factor: float  # 0-1, how productive is this divergence
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""


class TensionGraphBuilder:
    """
    Builds and maintains multi-perspective knowledge graphs.
    Preserves all viewpoints and identifies productive tensions.
    """

    def __init__(self, storage_path: Path | None = None):
        """Initialize the tension graph builder."""
        self.storage_path = storage_path or Path(".data/knowledge/tension_graph.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Core graph structures
        self.nodes: dict[str, PerspectiveNode] = {}
        self.edges: dict[str, MultiViewEdge] = {}
        self.triples: list[PerspectiveTriple] = []

        # Perspective management
        self.perspectives: dict[str, dict[str, Any]] = defaultdict(dict)
        self.divergence_points: list[DivergencePoint] = []

        # Indices for fast lookup
        self.name_to_nodes: dict[str, set[str]] = defaultdict(set)  # name -> node_ids
        self.perspective_nodes: dict[str, set[str]] = defaultdict(set)  # perspective -> node_ids
        self.perspective_edges: dict[str, set[str]] = defaultdict(set)  # perspective -> edge_ids

        # Configuration
        self.config = {
            "triple_extraction": {
                "max_predicate_words": 3,
                "entity_variations_allowed": True,
                "parallel_edges_enabled": True,
                "synthesis_threshold": 0.4,
            },
            "diversity": {
                "agreement_threshold": 0.8,
                "diversity_bonus": 0.1,
                "max_diversity": 0.95,
            },
            "visualization": {
                "edge_style_by_perspective": True,
                "show_perspective_clusters": True,
                "highlight_tensions": True,
                "animate_synthesis": False,
            },
        }

        # ID counters
        self.next_node_id = 1
        self.next_edge_id = 1

        # Load existing graph if available
        if self.storage_path.exists():
            self.load()

    def extract_triples_from_text(
        self, text: str, perspective_id: str, chunk_number: int = 0, emphasis_level: float = 0.5
    ) -> list[PerspectiveTriple]:
        """
        Extract SPO triples from perspective output text.

        This is a simplified extraction - in production, would use NLP.
        For now, creates triples based on sentence patterns.
        """
        triples = []

        # Simple pattern-based extraction (would use NLP in production)
        # Look for patterns like "X is Y", "X has Y", "X uses Y", etc.
        sentences = text.split(".")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Extract based on common patterns
            if " is " in sentence:
                parts = sentence.split(" is ", 1)
                if len(parts) == 2:
                    subject = parts[0].strip().lower()
                    object_part = parts[1].strip().lower()
                    if subject and object_part:
                        triple = PerspectiveTriple(
                            subject=subject,
                            predicate="is",
                            object=object_part,
                            perspective_id=perspective_id,
                            chunk_number=chunk_number,
                            emphasis_level=emphasis_level,
                        )
                        triples.append(triple)

            # More patterns would be added here

        return triples

    def extract_comprehensive_triples(self) -> list[PerspectiveTriple]:
        """
        Extract comprehensive SPO triples from the system's knowledge base.
        This demonstrates the types of triples the system manages.
        """
        comprehensive_triples = [
            # AI Engineering and Development Philosophy
            PerspectiveTriple("claude code", "is", "cli tool", "architect-1", 1, confidence=0.95),
            PerspectiveTriple("claude code", "serves as", "orchestrator", "architect-1", 1, confidence=0.9),
            PerspectiveTriple("claude code", "delegates to", "sub-agents", "architect-1", 1, confidence=0.95),
            PerspectiveTriple("sub-agents", "provide", "specialized expertise", "architect-1", 2, confidence=0.9),
            PerspectiveTriple("sub-agents", "conserve", "context window", "architect-1", 2, confidence=0.85),
            PerspectiveTriple("context window", "requires", "strategic compaction", "architect-1", 3, confidence=0.9),
            # Modular Design Philosophy
            PerspectiveTriple("software modules", "are", "bricks", "modular-builder", 1, confidence=0.95),
            PerspectiveTriple("interfaces", "are", "studs", "modular-builder", 1, confidence=0.95),
            PerspectiveTriple("bricks", "deliver", "single responsibility", "modular-builder", 2, confidence=0.9),
            PerspectiveTriple("studs", "enable", "module connection", "modular-builder", 2, confidence=0.9),
            PerspectiveTriple("modules", "allow", "regeneration", "modular-builder", 3, confidence=0.85),
            PerspectiveTriple("ai", "builds", "modules", "modular-builder", 3, confidence=0.9),
            PerspectiveTriple("humans", "define", "specifications", "modular-builder", 4, confidence=0.95),
            PerspectiveTriple("humans", "act as", "architects", "modular-builder", 4, confidence=0.9),
            # Implementation Philosophy - Simplicity
            PerspectiveTriple("implementation", "values", "ruthless simplicity", "zen-master", 1, confidence=0.95),
            PerspectiveTriple("code", "follows", "wabi-sabi philosophy", "zen-master", 1, confidence=0.85),
            PerspectiveTriple("abstractions", "must justify", "existence", "zen-master", 2, confidence=0.9),
            PerspectiveTriple("complexity", "emerges from", "simplicity", "zen-master", 2, confidence=0.85),
            PerspectiveTriple("solutions", "avoid", "future-proofing", "zen-master", 3, confidence=0.8),
            PerspectiveTriple("development", "uses", "80/20 principle", "zen-master", 3, confidence=0.9),
            # Python Development Practices
            PerspectiveTriple("project", "uses", "uv", "python-dev", 1, confidence=0.95),
            PerspectiveTriple("uv", "manages", "dependencies", "python-dev", 1, confidence=0.95),
            PerspectiveTriple("code", "requires", "type hints", "python-dev", 2, confidence=0.9),
            PerspectiveTriple("project", "uses", "ruff", "python-dev", 2, confidence=0.95),
            PerspectiveTriple("ruff", "handles", "formatting", "python-dev", 3, confidence=0.9),
            PerspectiveTriple("tests", "run via", "pytest", "python-dev", 3, confidence=0.95),
            PerspectiveTriple("pydantic", "validates", "data", "python-dev", 4, confidence=0.9),
            # Knowledge Synthesis System
            PerspectiveTriple(
                "graph builder", "constructs", "tension graphs", "synthesis-architect", 1, confidence=0.95
            ),
            PerspectiveTriple("graph", "preserves", "diverse perspectives", "synthesis-architect", 1, confidence=0.95),
            PerspectiveTriple("tensions", "are", "productive features", "synthesis-architect", 2, confidence=0.9),
            PerspectiveTriple("consensus", "requires", "examination", "synthesis-architect", 2, confidence=0.85),
            PerspectiveTriple("nodes", "can have", "multiple viewpoints", "synthesis-architect", 3, confidence=0.9),
            PerspectiveTriple("edges", "support", "parallel interpretations", "synthesis-architect", 3, confidence=0.9),
            PerspectiveTriple(
                "diversity", "indicates", "rich understanding", "synthesis-architect", 4, confidence=0.85
            ),
            PerspectiveTriple("graph", "identifies", "divergence points", "synthesis-architect", 4, confidence=0.8),
            # Claude Code SDK Integration
            PerspectiveTriple("claude code sdk", "requires", "npm package", "integration-expert", 1, confidence=0.95),
            PerspectiveTriple("claude cli", "needs", "global installation", "integration-expert", 1, confidence=0.95),
            PerspectiveTriple("sdk operations", "use", "120-second timeout", "integration-expert", 2, confidence=0.9),
            PerspectiveTriple("responses", "may contain", "markdown", "integration-expert", 2, confidence=0.85),
            PerspectiveTriple(
                "json parsing", "requires", "markdown stripping", "integration-expert", 3, confidence=0.9
            ),
            # Knowledge Extraction System
            PerspectiveTriple("extraction", "uses", "unified extractor", "knowledge-miner", 1, confidence=0.9),
            PerspectiveTriple("extractor", "extracts", "concepts", "knowledge-miner", 1, confidence=0.95),
            PerspectiveTriple("extractor", "extracts", "spo triples", "knowledge-miner", 2, confidence=0.95),
            PerspectiveTriple("chunk size", "increased to", "10000 words", "knowledge-miner", 2, confidence=0.9),
            PerspectiveTriple("claude", "handles", "100k+ tokens", "knowledge-miner", 3, confidence=0.95),
            # Development Workflow
            PerspectiveTriple("changes", "require", "make check", "workflow-expert", 1, confidence=0.95),
            PerspectiveTriple("services", "need", "runtime testing", "workflow-expert", 1, confidence=0.9),
            PerspectiveTriple("decisions", "are documented", "in ai_working", "workflow-expert", 2, confidence=0.85),
            PerspectiveTriple("discoveries", "go in", "discoveries.md", "workflow-expert", 2, confidence=0.9),
            PerspectiveTriple("context7", "provides", "documentation", "workflow-expert", 3, confidence=0.85),
            # Parallel Development
            PerspectiveTriple("ai", "enables", "parallel variants", "innovation-agent", 1, confidence=0.85),
            PerspectiveTriple("variants", "test", "alternatives", "innovation-agent", 1, confidence=0.8),
            PerspectiveTriple("development", "becomes", "exploration space", "innovation-agent", 2, confidence=0.75),
            PerspectiveTriple("regeneration", "replaces", "patching", "innovation-agent", 2, confidence=0.85),
            # Error Handling Philosophy
            PerspectiveTriple("errors", "fail", "fast", "error-handler", 1, confidence=0.9),
            PerspectiveTriple("common errors", "handled", "robustly", "error-handler", 1, confidence=0.85),
            PerspectiveTriple("edge cases", "deferred", "initially", "error-handler", 2, confidence=0.8),
            PerspectiveTriple("logs", "provide", "detailed information", "error-handler", 2, confidence=0.9),
        ]

        return comprehensive_triples

    def add_perspective_output(
        self, perspective_id: str, extraction_data: dict[str, Any], emphasis_level: float = 0.5
    ) -> dict[str, Any]:
        """
        Process output from a single perspective and add to tension graph.

        Args:
            perspective_id: Unique identifier for the perspective/agent
            extraction_data: Dict with 'concepts', 'relationships', etc.
            emphasis_level: How strongly this perspective emphasizes its view

        Returns:
            Summary of additions and tensions identified
        """
        added_triples = []
        new_divergences = []

        # Process relationships as triples
        relationships = extraction_data.get("relationships", [])
        for rel_data in relationships:
            if isinstance(rel_data, dict):
                triple = PerspectiveTriple(
                    subject=rel_data.get("subject", "").lower(),
                    predicate=self._normalize_predicate(rel_data.get("predicate", "")),
                    object=rel_data.get("object", "").lower(),
                    perspective_id=perspective_id,
                    emphasis_level=emphasis_level,
                    confidence=rel_data.get("confidence", 0.8),
                )
            elif isinstance(rel_data, Relationship):
                triple = PerspectiveTriple(
                    subject=rel_data.subject.lower(),
                    predicate=self._normalize_predicate(rel_data.predicate),
                    object=rel_data.object.lower(),
                    perspective_id=perspective_id,
                    emphasis_level=emphasis_level,
                    confidence=rel_data.confidence,
                )
            else:
                continue

            self.triples.append(triple)
            added_triples.append(triple)

            # Process nodes and edges
            subject_node_id = self._get_or_create_node(triple.subject, perspective_id, emphasis_level)
            object_node_id = self._get_or_create_node(triple.object, perspective_id, emphasis_level)

            edge_id = self._add_multi_view_edge(
                subject_node_id, object_node_id, triple.predicate, perspective_id, triple
            )

            # Track perspectives
            self.perspective_nodes[perspective_id].add(subject_node_id)
            self.perspective_nodes[perspective_id].add(object_node_id)
            self.perspective_edges[perspective_id].add(edge_id)

            # Check for divergence points
            divergence = self._detect_divergence(subject_node_id, object_node_id, edge_id)
            if divergence:
                new_divergences.append(divergence)

        return {
            "added_triples": len(added_triples),
            "new_divergences": len(new_divergences),
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "perspective_contributions": {perspective_id: len(self.perspective_nodes[perspective_id])},
        }

    def _normalize_predicate(self, predicate: str) -> str:
        """Normalize predicate to 1-3 words."""
        words = predicate.lower().strip().split()
        return " ".join(words[:3])

    def _get_or_create_node(self, name: str, perspective_id: str, weight: float = 0.5) -> str:
        """Get existing node or create new one."""
        # Check if node with this name exists
        for node_id in self.name_to_nodes.get(name, []):
            self.nodes[node_id].add_perspective(perspective_id, name, weight)
            return node_id

        # Create new node
        node_id = f"node_{self.next_node_id}"
        self.next_node_id += 1

        node = PerspectiveNode(id=node_id, canonical_name=name)
        node.add_perspective(perspective_id, name, weight)

        self.nodes[node_id] = node
        self.name_to_nodes[name].add(node_id)

        return node_id

    def _add_multi_view_edge(
        self, subject_id: str, object_id: str, predicate: str, perspective_id: str, triple: PerspectiveTriple
    ) -> str:
        """Add or update a multi-view edge."""
        # Check if edge exists between these nodes
        for edge_id, edge in self.edges.items():
            if edge.subject_id == subject_id and edge.object_id == object_id:
                edge.add_interpretation(perspective_id, predicate, triple)
                return edge_id

        # Create new edge
        edge_id = f"edge_{self.next_edge_id}"
        self.next_edge_id += 1

        edge = MultiViewEdge(id=edge_id, subject_id=subject_id, object_id=object_id)
        edge.add_interpretation(perspective_id, predicate, triple)

        self.edges[edge_id] = edge
        return edge_id

    def _detect_divergence(self, subject_id: str, object_id: str, edge_id: str) -> DivergencePoint | None:
        """Detect if this creates a divergence point."""
        # Check if multiple perspectives view these nodes or edge
        subject_node = self.nodes.get(subject_id)
        object_node = self.nodes.get(object_id)
        edge = self.edges.get(edge_id)

        if not (subject_node and object_node and edge):
            return None

        perspectives_involved = subject_node.contributing_perspectives | object_node.contributing_perspectives

        if len(perspectives_involved) > 1 or edge.tension_intensity > 0.3:
            divergence = DivergencePoint(
                node_ids={subject_id, object_id},
                edge_ids={edge_id},
                divergence_type="relationship",
                perspectives_involved=perspectives_involved,
                productivity_factor=edge.tension_intensity,
                description=f"Different interpretations of {subject_node.canonical_name} -> {object_node.canonical_name}",
            )
            self.divergence_points.append(divergence)
            return divergence

        return None

    def load(self) -> None:
        """Load existing graph from storage."""
        # Simplified load - would implement full loading in production
        logger.info(f"Loading graph from {self.storage_path}")
        # Implementation would deserialize the full graph state

    def save(self) -> None:
        """Save graph to storage."""
        # Simplified save - would implement full saving in production
        logger.info(f"Saving graph to {self.storage_path}")
        # Implementation would serialize the full graph state
