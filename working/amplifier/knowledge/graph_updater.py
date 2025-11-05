#!/usr/bin/env python3
"""
Graph updater for incremental knowledge graph updates.
Adds new extractions to existing graph without rebuilding from scratch.
Following ruthless simplicity and append-only principles.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

from amplifier.config.paths import paths

from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class GraphUpdater:
    """Incrementally update knowledge graph with new extractions."""

    def __init__(
        self,
        graph_path: Path | None = None,
        state_path: Path | None = None,
    ):
        """Initialize with paths to graph and state files."""
        if graph_path is None:
            graph_path = paths.data_dir / "knowledge" / "graph.gexf"
        if state_path is None:
            state_path = paths.data_dir / "knowledge" / "graph_state.json"
        self.graph_path = graph_path
        self.state_path = state_path
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.processed_sources: set[str] = set()
        self.concept_map: dict[str, str] = {}  # normalized -> canonical name
        self.builder = GraphBuilder()  # Use for normalization

    def load_state(self) -> bool:
        """Load existing graph and processed sources."""
        # Load graph if exists
        if self.graph_path.exists():
            try:
                self.graph = nx.read_gexf(str(self.graph_path))
                logger.info(f"Loaded existing graph with {self.graph.number_of_nodes()} nodes")
            except Exception as e:
                logger.error(f"Failed to load graph: {e}")
                self.graph = nx.MultiDiGraph()
        else:
            logger.info("Starting with empty graph")

        # Load state if exists
        if self.state_path.exists():
            try:
                with open(self.state_path, encoding="utf-8") as f:
                    state = json.load(f)
                    self.processed_sources = set(state.get("processed_sources", []))
                    self.concept_map = state.get("concept_map", {})
                    logger.info(f"Loaded state with {len(self.processed_sources)} processed sources")
                    return True
            except Exception as e:
                logger.error(f"Failed to load state: {e}")

        # Initialize concept map from existing graph
        if not self.concept_map and self.graph.number_of_nodes() > 0:
            for node in self.graph.nodes():
                normalized = self.builder.normalize_concept(node)
                if normalized not in self.concept_map:
                    self.concept_map[normalized] = node

        return False

    def save_state(self):
        """Persist updated graph and metadata."""
        # Save graph
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_gexf(self.graph, str(self.graph_path))
        logger.info(f"Saved graph with {self.graph.number_of_nodes()} nodes to {self.graph_path}")

        # Save state
        state = {
            "processed_sources": list(self.processed_sources),
            "concept_map": self.concept_map,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Saved state to {self.state_path}")

    def merge_concept(self, new_concept: dict[str, Any], canonical_name: str) -> str:
        """Merge new concept with existing one, preserving history."""
        if self.graph.has_node(canonical_name):
            # Update importance - keep maximum
            old_importance = self.graph.nodes[canonical_name].get("importance", 0)
            new_importance = new_concept.get("importance", 0.5)
            self.graph.nodes[canonical_name]["importance"] = max(old_importance, new_importance)

            # Append descriptions if new
            old_desc = self.graph.nodes[canonical_name].get("description", "")
            new_desc = new_concept.get("description", "")
            if new_desc and new_desc not in old_desc:
                if old_desc:
                    self.graph.nodes[canonical_name]["description"] = f"{old_desc} | {new_desc}"
                else:
                    self.graph.nodes[canonical_name]["description"] = new_desc

            # Track update time
            self.add_temporal_metadata(canonical_name, datetime.now())
        else:
            # Add new node
            self.graph.add_node(
                canonical_name,
                description=new_concept.get("description", ""),
                importance=new_concept.get("importance", 0.5),
                type="concept",
                created_at=datetime.now().isoformat(),
            )

        return canonical_name

    def add_temporal_metadata(self, node: str, timestamp: datetime):
        """Track when concepts were added/updated."""
        if not self.graph.has_node(node):
            return

        # Track first occurrence
        if "created_at" not in self.graph.nodes[node]:
            self.graph.nodes[node]["created_at"] = timestamp.isoformat()

        # Track last update
        self.graph.nodes[node]["updated_at"] = timestamp.isoformat()

        # Track update count
        update_count = self.graph.nodes[node].get("update_count", 0)
        self.graph.nodes[node]["update_count"] = update_count + 1

    def process_new_extractions(self, jsonl_path: Path) -> int:
        """Process only new extractions not already in graph."""
        if not jsonl_path.exists():
            logger.warning(f"Extractions file not found: {jsonl_path}")
            return 0

        new_count = 0
        timestamp = datetime.now()

        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    extraction = json.loads(line)
                    source_id = extraction.get("source_id", "unknown")

                    # Skip if already processed
                    if source_id in self.processed_sources:
                        continue

                    # Process concepts
                    for concept in extraction.get("concepts", []):
                        name = concept.get("name", "")
                        if not name:
                            continue

                        # Entity resolution
                        normalized = self.builder.normalize_concept(name)
                        if normalized in self.concept_map:
                            canonical = self.concept_map[normalized]
                        else:
                            canonical = name
                            self.concept_map[normalized] = canonical

                        # Merge concept
                        self.merge_concept(concept, canonical)

                        # Add source relationship
                        self.graph.add_edge(
                            source_id, canonical, relation="mentions", weight=1.0, timestamp=timestamp.isoformat()
                        )

                    # Process relationships
                    for rel in extraction.get("relationships", []):
                        subject = rel.get("subject", "")
                        predicate = rel.get("predicate", "")
                        obj = rel.get("object", "")

                        if not (subject and predicate and obj):
                            continue

                        # Entity resolution
                        subj_norm = self.builder.normalize_concept(subject)
                        obj_norm = self.builder.normalize_concept(obj)

                        subject = self.concept_map.get(subj_norm, subject)
                        obj = self.concept_map.get(obj_norm, obj)

                        # Ensure nodes exist
                        if not self.graph.has_node(subject):
                            self.graph.add_node(subject, type="entity", created_at=timestamp.isoformat())
                        if not self.graph.has_node(obj):
                            self.graph.add_node(obj, type="entity", created_at=timestamp.isoformat())

                        # Add relationship
                        self.graph.add_edge(
                            subject,
                            obj,
                            predicate=predicate,
                            confidence=rel.get("confidence", 0.5),
                            source=source_id,
                            timestamp=timestamp.isoformat(),
                        )

                    # Mark as processed
                    self.processed_sources.add(source_id)
                    new_count += 1

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extraction: {e}")

        logger.info(f"Processed {new_count} new extractions")
        return new_count

    def update(self, extractions_path: Path | None = None) -> dict[str, Any]:
        """Main entry point for incremental updates."""
        if extractions_path is None:
            extractions_path = paths.data_dir / "knowledge" / "extractions.jsonl"

        # Load existing state
        self.load_state()

        initial_nodes = self.graph.number_of_nodes()
        initial_edges = self.graph.number_of_edges()

        # Process new extractions
        new_count = self.process_new_extractions(extractions_path)

        if new_count > 0:
            # Recalculate metrics for updated graph
            self._update_metrics()

            # Save updated state
            self.save_state()

        # Return update summary
        return {
            "new_extractions": new_count,
            "total_sources": len(self.processed_sources),
            "nodes_before": initial_nodes,
            "nodes_after": self.graph.number_of_nodes(),
            "edges_before": initial_edges,
            "edges_after": self.graph.number_of_edges(),
            "nodes_added": self.graph.number_of_nodes() - initial_nodes,
            "edges_added": self.graph.number_of_edges() - initial_edges,
        }

    def _update_metrics(self):
        """Update graph metrics for new nodes."""
        # Recalculate centrality
        degree_centrality = nx.degree_centrality(self.graph)
        for node, centrality in degree_centrality.items():
            self.graph.nodes[node]["degree_centrality"] = centrality

        # Recalculate PageRank
        try:
            pagerank = nx.pagerank(self.graph, max_iter=100)
            for node, rank in pagerank.items():
                self.graph.nodes[node]["pagerank"] = rank
        except Exception:
            logger.warning("PageRank calculation failed")


def main():
    """CLI for incremental graph updates."""
    import argparse

    parser = argparse.ArgumentParser(description="Incrementally update knowledge graph")
    parser.add_argument(
        "--input", type=Path, default=None, help="Path to extractions JSONL (defaults to configured data directory)"
    )
    parser.add_argument(
        "--graph", type=Path, default=None, help="Path to graph file (defaults to configured data directory)"
    )
    parser.add_argument(
        "--state", type=Path, default=None, help="Path to state file (defaults to configured data directory)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Run update
    graph_path = args.graph or (paths.data_dir / "knowledge" / "graph.gexf")
    state_path = args.state or (paths.data_dir / "knowledge" / "graph_state.json")
    input_path = args.input or (paths.data_dir / "knowledge" / "extractions.jsonl")

    updater = GraphUpdater(graph_path, state_path)
    summary = updater.update(input_path)

    # Print summary
    print("\n=== Update Summary ===")
    print(f"New extractions processed: {summary['new_extractions']}")
    print(f"Total sources: {summary['total_sources']}")
    print(f"Nodes added: {summary['nodes_added']} ({summary['nodes_before']} → {summary['nodes_after']})")
    print(f"Edges added: {summary['edges_added']} ({summary['edges_before']} → {summary['edges_after']})")


if __name__ == "__main__":
    main()
