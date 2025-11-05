"""
Unified Knowledge Store - Manages both concepts and relationships.

Simple, direct implementation with no unnecessary abstractions.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from amplifier.knowledge_integration.entity_resolver import EntityResolver
from amplifier.knowledge_integration.models import Relationship
from amplifier.knowledge_integration.models import UnifiedExtraction
from amplifier.knowledge_integration.models import UnifiedKnowledgeNode

logger = logging.getLogger(__name__)


class UnifiedKnowledgeStore:
    """
    Store for unified knowledge graph with concepts and relationships.

    Handles incremental updates and maintains indices for fast retrieval.
    """

    def __init__(self, storage_path: Path | None = None, use_entity_resolution: bool = True):
        """
        Initialize the unified knowledge store.

        Args:
            storage_path: Path to JSON storage file
            use_entity_resolution: Whether to use entity resolution for deduplication
        """
        self.storage_path = storage_path or Path(".data/knowledge/graph.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.use_entity_resolution = use_entity_resolution

        # Initialize entity resolver
        if self.use_entity_resolution:
            entity_cache_path = self.storage_path.parent / "entity_cache.json"
            self.entity_resolver = EntityResolver(cache_path=entity_cache_path)
        else:
            self.entity_resolver = None

        # Core storage
        self.nodes: dict[str, UnifiedKnowledgeNode] = {}
        self.relationships: list[Relationship] = []
        self.relationship_signatures: set[str] = set()  # For deduplication

        # Indices for fast lookup
        self.name_to_id: dict[str, str] = {}
        self.type_index: dict[str, list[str]] = defaultdict(list)
        self.source_index: dict[str, list[str]] = defaultdict(list)

        # Track processed sources
        self.processed_sources: set[str] = set()

        # ID counter
        self.next_id = 1

        # Load existing data
        if self.storage_path.exists():
            self.load()

    def add_extraction(self, extraction: UnifiedExtraction) -> dict[str, Any]:
        """
        Add a unified extraction to the store.

        Processes both concepts and relationships, creating nodes as needed.

        Args:
            extraction: UnifiedExtraction containing concepts and relationships

        Returns:
            Summary of what was added
        """
        added_nodes = []
        added_relationships = []

        # Process concepts
        for concept_data in extraction.concepts:
            node_id = self._add_or_update_node(
                name=concept_data.get("name", ""),
                node_type=concept_data.get("category", "concept"),
                definition=concept_data.get("description", ""),
                source=extraction.source,
                metadata=concept_data,
            )
            added_nodes.append(node_id)

        # Process relationships
        for rel in extraction.relationships:
            # Resolve entity names for subject and object
            if self.entity_resolver:
                subject_match = self.entity_resolver.resolve(rel.subject)
                object_match = self.entity_resolver.resolve(rel.object)
                resolved_subject = subject_match.canonical
                resolved_object = object_match.canonical

                # Create normalized relationship with resolved names
                normalized_rel = Relationship(
                    subject=resolved_subject,
                    predicate=rel.predicate,
                    object=resolved_object,
                    confidence=rel.confidence,
                    source=rel.source or extraction.source,
                )
            else:
                resolved_subject = rel.subject
                resolved_object = rel.object
                normalized_rel = rel

            # Create signature for deduplication
            rel_signature = f"{resolved_subject}|{normalized_rel.predicate}|{resolved_object}"

            # Skip if relationship already exists
            if rel_signature in self.relationship_signatures:
                continue

            # Ensure nodes exist for subject and object
            if resolved_subject not in self.name_to_id:
                self._add_or_update_node(
                    name=rel.subject,  # Use original name, will be resolved inside
                    node_type="entity",
                    definition=f"Entity from relationship: {rel}",
                    source=extraction.source,
                )

            if resolved_object not in self.name_to_id:
                self._add_or_update_node(
                    name=rel.object,  # Use original name, will be resolved inside
                    node_type="entity",
                    definition=f"Entity from relationship: {rel}",
                    source=extraction.source,
                )

            # Add relationship to nodes (using resolved names)
            if resolved_subject in self.name_to_id:
                self.nodes[self.name_to_id[resolved_subject]].add_relationship(normalized_rel)
            if resolved_object in self.name_to_id:
                self.nodes[self.name_to_id[resolved_object]].add_relationship(normalized_rel)

            # Store relationship and signature
            self.relationships.append(normalized_rel)
            self.relationship_signatures.add(rel_signature)
            added_relationships.append(str(normalized_rel))

        # Only mark source as processed if we actually extracted something
        if added_nodes or added_relationships:
            self.processed_sources.add(extraction.source)
            # Save immediately (incremental saving)
            self.save()

        return {
            "nodes_added": len(added_nodes),
            "relationships_added": len(added_relationships),
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
        }

    def _add_or_update_node(
        self,
        name: str,
        node_type: str,
        definition: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add or update a node in the store.

        Args:
            name: Node name
            node_type: Type of node (concept, entity, etc.)
            definition: Node definition/description
            source: Source of the node
            metadata: Additional metadata

        Returns:
            Node ID
        """
        # Resolve entity name if resolver is available
        if self.entity_resolver:
            match = self.entity_resolver.resolve(name)
            resolved_name = match.canonical
            # Store original name in metadata if it was resolved
            if match.original != match.canonical:
                if metadata is None:
                    metadata = {}
                if "original_names" not in metadata:
                    metadata["original_names"] = []
                if match.original not in metadata["original_names"]:
                    metadata["original_names"].append(match.original)
        else:
            resolved_name = name

        # Check if node already exists (using resolved name)
        if resolved_name in self.name_to_id:
            node_id = self.name_to_id[resolved_name]
            node = self.nodes[node_id]

            # Update existing node
            if source not in node.sources:
                node.sources.append(source)

            # Merge metadata
            if metadata:
                node.metadata.update(metadata)

            return node_id

        # Create new node
        node_id = f"node_{self.next_id}"
        self.next_id += 1

        node = UnifiedKnowledgeNode(
            id=node_id,
            name=resolved_name,
            type=node_type,
            definition=definition,
            sources=[source],
            metadata=metadata or {},
        )

        # Store node and update indices
        self.nodes[node_id] = node
        self.name_to_id[resolved_name] = node_id
        self.type_index[node_type].append(node_id)
        self.source_index[source].append(node_id)

        return node_id

    def is_source_processed(self, source: str) -> bool:
        """Check if a source has already been processed."""
        return source in self.processed_sources

    def get_node_by_name(self, name: str) -> UnifiedKnowledgeNode | None:
        """Get a node by its name."""
        # Resolve entity name if resolver is available
        if self.entity_resolver:
            match = self.entity_resolver.resolve(name)
            resolved_name = match.canonical
        else:
            resolved_name = name

        node_id = self.name_to_id.get(resolved_name)
        return self.nodes.get(node_id) if node_id else None

    def get_nodes_by_type(self, node_type: str) -> list[UnifiedKnowledgeNode]:
        """Get all nodes of a specific type."""
        node_ids = self.type_index.get(node_type, [])
        return [self.nodes[node_id] for node_id in node_ids]

    def get_relationships_for_node(self, name: str) -> list[Relationship]:
        """Get all relationships involving a node."""
        node = self.get_node_by_name(name)
        if not node:
            return []

        return node.relationships_as_subject + node.relationships_as_object

    def save(self) -> None:
        """Save the knowledge store to JSON."""
        data = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "definition": node.definition,
                    "sources": node.sources,
                    "metadata": node.metadata,
                }
                for node in self.nodes.values()
            ],
            "relationships": [
                {
                    "subject": rel.subject,
                    "predicate": rel.predicate,
                    "object": rel.object,
                    "confidence": rel.confidence,
                    "source": rel.source,
                }
                for rel in self.relationships
            ],
            "processed_sources": list(self.processed_sources),
            "next_id": self.next_id,
        }

        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

        # Save entity resolver cache if available
        if self.entity_resolver:
            self.entity_resolver.save_cache()

        logger.info(f"Saved knowledge store to {self.storage_path}")

    def load(self) -> None:
        """Load the knowledge store from JSON."""
        with open(self.storage_path) as f:
            data = json.load(f)

        # Clear existing data
        self.nodes.clear()
        self.relationships.clear()
        self.relationship_signatures.clear()
        self.name_to_id.clear()
        self.type_index.clear()
        self.source_index.clear()
        self.processed_sources.clear()

        # Load nodes
        for node_data in data.get("nodes", []):
            node = UnifiedKnowledgeNode(
                id=node_data["id"],
                name=node_data["name"],
                type=node_data["type"],
                definition=node_data["definition"],
                sources=node_data.get("sources", []),
                metadata=node_data.get("metadata", {}),
            )

            self.nodes[node.id] = node
            self.name_to_id[node.name] = node.id
            self.type_index[node.type].append(node.id)

            for source in node.sources:
                self.source_index[source].append(node.id)

        # Load relationships
        for rel_data in data.get("relationships", []):
            rel = Relationship(
                subject=rel_data["subject"],
                predicate=rel_data["predicate"],
                object=rel_data["object"],
                confidence=rel_data.get("confidence", 1.0),
                source=rel_data.get("source"),
            )

            self.relationships.append(rel)

            # Rebuild relationship signature for deduplication
            rel_signature = f"{rel.subject}|{rel.predicate}|{rel.object}"
            self.relationship_signatures.add(rel_signature)

            # Add to nodes
            if rel.subject in self.name_to_id:
                self.nodes[self.name_to_id[rel.subject]].add_relationship(rel)
            if rel.object in self.name_to_id:
                self.nodes[self.name_to_id[rel.object]].add_relationship(rel)

        # Load other data
        self.processed_sources = set(data.get("processed_sources", []))
        self.next_id = data.get("next_id", len(self.nodes) + 1)

        logger.info(f"Loaded {len(self.nodes)} nodes and {len(self.relationships)} relationships")

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge store."""
        type_counts = {node_type: len(node_ids) for node_type, node_ids in self.type_index.items()}

        return {
            "total_nodes": len(self.nodes),
            "total_relationships": len(self.relationships),
            "total_sources": len(self.processed_sources),
            "nodes_by_type": type_counts,
            "average_relationships_per_node": (
                sum(
                    len(node.relationships_as_subject) + len(node.relationships_as_object)
                    for node in self.nodes.values()
                )
                / len(self.nodes)
                if self.nodes
                else 0
            ),
        }
