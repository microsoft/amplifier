#!/usr/bin/env python3
"""
Knowledge Store - Organize and index extracted knowledge for fast retrieval.
Simple graph-based storage optimized for AI queries.
"""

import json
from collections import defaultdict
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths

from .knowledge_extractor import Concept
from .knowledge_extractor import Extraction
from .pattern_finder import Pattern


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph"""

    id: str
    type: str  # concept, insight, pattern, code
    content: dict[str, Any]
    sources: list[str]
    created_at: str
    connections: list[str]  # IDs of connected nodes
    metadata: dict[str, Any]


class KnowledgeStore:
    """Store and index extracted knowledge for fast retrieval"""

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or (paths.data_dir / "knowledge" / "store.json")
        self.nodes: dict[str, KnowledgeNode] = {}
        self.index: dict[str, list[str]] = defaultdict(list)  # type -> node_ids
        self.concept_index: dict[str, str] = {}  # concept_name -> node_id
        self.source_index: dict[str, list[str]] = defaultdict(list)  # source -> node_ids
        self.processed_sources: set[str] = set()  # Track which sources have been processed
        self.next_id = 1

        if self.storage_path.exists():
            self.load()

    def is_source_processed(self, source: str) -> bool:
        """Check if a source has already been processed"""
        return source in self.processed_sources

    def add_extraction(self, extraction: Extraction) -> list[str]:
        """Add an extraction to the store, return node IDs created"""
        created_nodes = []

        # Store concepts
        for concept in extraction.concepts:
            node_id = self._add_concept(concept, extraction.source)
            created_nodes.append(node_id)

        # Store insights
        for insight in extraction.key_insights:
            node_id = self._add_insight(insight, extraction.source)
            created_nodes.append(node_id)

        # Store code patterns
        for pattern in extraction.code_patterns:
            node_id = self._add_code_pattern(pattern, extraction.source)
            created_nodes.append(node_id)

        # Create relationships
        for rel in extraction.relationships:
            # Convert Relationship object to dict for compatibility
            rel_dict = {"from": rel.source, "to": rel.target, "type": rel.relationship_type}
            self._add_relationship(rel_dict)

        # Mark source as processed
        if extraction.source:
            self.processed_sources.add(extraction.source)

        # Update indices
        self._rebuild_indices()

        return created_nodes

    def add_pattern(self, pattern: Pattern) -> str:
        """Add a discovered pattern to the store"""
        node_id = f"pattern_{self.next_id}"
        self.next_id += 1

        node = KnowledgeNode(
            id=node_id,
            type="pattern",
            content={
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "strength": pattern.strength,
                "concepts": pattern.concepts_involved,
            },
            sources=[occ["source"] for occ in pattern.occurrences],
            created_at=datetime.now().isoformat(),
            connections=[],
            metadata={"occurrences": len(pattern.occurrences)},
        )

        self.nodes[node_id] = node

        # Connect to involved concepts
        for concept_name in pattern.concepts_involved:
            if concept_name in self.concept_index:
                concept_id = self.concept_index[concept_name]
                node.connections.append(concept_id)
                if concept_id in self.nodes:
                    self.nodes[concept_id].connections.append(node_id)

        self._rebuild_indices()
        return node_id

    def _add_concept(self, concept: Concept, source: str) -> str:
        """Add or update a concept node"""
        # Check if concept already exists
        if concept.name in self.concept_index:
            node_id = self.concept_index[concept.name]
            node = self.nodes[node_id]
            # Update existing concept
            if source not in node.sources:
                node.sources.append(source)
            # Merge descriptions if different
            existing_desc = node.content.get("description", "")
            if concept.description not in existing_desc:
                node.content["description"] = f"{existing_desc} | {concept.description}"
            return node_id

        # Create new concept node
        node_id = f"concept_{self.next_id}"
        self.next_id += 1

        node = KnowledgeNode(
            id=node_id,
            type="concept",
            content={
                "name": concept.name,
                "description": concept.description,
                "category": concept.category,
                "importance": concept.importance,
            },
            sources=[source],
            created_at=datetime.now().isoformat(),
            connections=[],
            metadata={"category": concept.category, "importance": concept.importance},
        )

        self.nodes[node_id] = node
        self.concept_index[concept.name] = node_id
        return node_id

    def _add_insight(self, insight: str, source: str) -> str:
        """Add an insight node"""
        node_id = f"insight_{self.next_id}"
        self.next_id += 1

        node = KnowledgeNode(
            id=node_id,
            type="insight",
            content={"text": insight},
            sources=[source],
            created_at=datetime.now().isoformat(),
            connections=[],
            metadata={"length": len(insight)},
        )

        self.nodes[node_id] = node
        return node_id

    def _add_code_pattern(self, pattern: dict[str, str], source: str) -> str:
        """Add a code pattern node"""
        node_id = f"code_{self.next_id}"
        self.next_id += 1

        node = KnowledgeNode(
            id=node_id,
            type="code",
            content=pattern,
            sources=[source],
            created_at=datetime.now().isoformat(),
            connections=[],
            metadata={"language": pattern.get("language", "unknown")},
        )

        self.nodes[node_id] = node
        return node_id

    def _add_relationship(self, rel: dict[str, str]):
        """Add a relationship between concepts"""
        from_name = rel["from"]
        to_name = rel["to"]

        if from_name in self.concept_index and to_name in self.concept_index:
            from_id = self.concept_index[from_name]
            to_id = self.concept_index[to_name]

            # Add bidirectional connections
            if to_id not in self.nodes[from_id].connections:
                self.nodes[from_id].connections.append(to_id)
            if from_id not in self.nodes[to_id].connections:
                self.nodes[to_id].connections.append(from_id)

    def _rebuild_indices(self):
        """Rebuild all indices from nodes"""
        self.index.clear()
        self.source_index.clear()

        for node_id, node in self.nodes.items():
            # Type index
            self.index[node.type].append(node_id)

            # Source index
            for source in node.sources:
                self.source_index[source].append(node_id)

    def query(self, query_type: str = "", concept: str = "", source: str = "") -> list[KnowledgeNode]:
        """Query the knowledge store"""
        results = []

        if query_type:
            # Get all nodes of a specific type
            node_ids = self.index.get(query_type, [])
            results.extend([self.nodes[nid] for nid in node_ids])

        if concept and concept in self.concept_index:
            # Get concept and related nodes
            concept_id = self.concept_index[concept]
            concept_node = self.nodes[concept_id]
            results.append(concept_node)

            # Add connected nodes
            for conn_id in concept_node.connections:
                if conn_id in self.nodes:
                    results.append(self.nodes[conn_id])

        if source:
            # Get all nodes from a source
            node_ids = self.source_index.get(source, [])
            results.extend([self.nodes[nid] for nid in node_ids if nid not in [r.id for r in results]])

        return results

    def get_concept_graph(self, start_concept: str, max_depth: int = 2) -> dict[str, Any]:
        """Get concept graph starting from a concept"""
        if start_concept not in self.concept_index:
            return {}

        graph = {"nodes": [], "edges": []}
        visited = set()
        to_explore = [(self.concept_index[start_concept], 0)]

        while to_explore:
            node_id, depth = to_explore.pop(0)
            if node_id in visited or depth > max_depth:
                continue

            visited.add(node_id)
            node = self.nodes[node_id]

            # Add node to graph
            graph["nodes"].append(
                {
                    "id": node_id,
                    "type": node.type,
                    "label": node.content.get("name", node.content.get("text", node_id)[:50]),
                    "depth": depth,
                }
            )

            # Add edges and explore connections
            for conn_id in node.connections:
                if conn_id in self.nodes:
                    graph["edges"].append({"from": node_id, "to": conn_id})
                    if depth < max_depth:
                        to_explore.append((conn_id, depth + 1))

        return graph

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge store"""
        stats: dict[str, Any] = {
            "total_nodes": len(self.nodes),
            "concepts": len(self.concept_index),
            "insights": len(self.index.get("insight", [])),
            "code_patterns": len(self.index.get("code", [])),
            "patterns": len(self.index.get("pattern", [])),
            "sources": len(self.source_index),
            "total_connections": sum(len(n.connections) for n in self.nodes.values()),
        }

        # Category breakdown
        categories: dict[str, int] = {}
        for node_id in self.index.get("concept", []):
            node = self.nodes[node_id]
            category = node.metadata.get("category", "unknown")
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        stats["categories"] = categories

        return stats

    def save(self):
        """Save the knowledge store to disk"""
        data = {
            "nodes": {nid: asdict(node) for nid, node in self.nodes.items()},
            "concept_index": self.concept_index,
            "processed_sources": list(self.processed_sources),
            "next_id": self.next_id,
        }
        self.storage_path.write_text(json.dumps(data, indent=2))

    def load(self):
        """Load the knowledge store from disk"""
        if not self.storage_path.exists():
            return

        data = json.loads(self.storage_path.read_text())
        self.nodes = {nid: KnowledgeNode(**node_data) for nid, node_data in data["nodes"].items()}
        self.concept_index = data["concept_index"]
        self.processed_sources = set(data.get("processed_sources", []))
        self.next_id = data["next_id"]
        self._rebuild_indices()


if __name__ == "__main__":
    # Test the knowledge store
    from knowledge_extractor import KnowledgeExtractor

    store = KnowledgeStore(Path("test_store.json"))
    extractor = KnowledgeExtractor()

    # Add sample extraction
    sample = """
    # API Design Best Practices

    The principle of least surprise states that APIs should behave predictably.
    The repository pattern provides clean data abstraction. Remember that
    consistency is key to good API design.

    ```python
    class APIClient:
        async def get(self, endpoint: str):
            return await self.session.get(endpoint)
    ```
    """

    extraction = extractor.extract(sample, "API Design", "api_design.md")
    node_ids = store.add_extraction(extraction)

    print(f"Added {len(node_ids)} nodes to store")

    # Query the store
    concepts = store.query(query_type="concept")
    print(f"\nFound {len(concepts)} concepts:")
    for concept in concepts[:3]:
        desc = concept.content.get("description", "")
        print(f"  - {concept.content.get('name')}: {desc[:50] if desc else 'No description'}...")

    # Get statistics
    stats = store.get_statistics()
    print(f"\nStore statistics: {json.dumps(stats, indent=2)}")
