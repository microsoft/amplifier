#!/usr/bin/env python3
"""
Simple graph builder for knowledge synthesis system.
Reads extractions.jsonl and builds a NetworkX graph for analysis and visualization.
Following ruthless simplicity - no unnecessary abstractions.
"""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

import networkx as nx

from amplifier.config.paths import paths

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Simple graph builder from knowledge extractions."""

    def __init__(self, extractions_path: Path | None = None):
        """Initialize with path to extractions file."""
        if extractions_path is None:
            extractions_path = paths.data_dir / "knowledge" / "extractions.jsonl"
        self.extractions_path = extractions_path
        self.graph = nx.MultiDiGraph()
        self.concept_counts = defaultdict(int)

    def load_extractions(self) -> list[dict]:
        """Load all extractions from JSONL file."""
        if not self.extractions_path.exists():
            logger.warning(f"Extractions file not found: {self.extractions_path}")
            return []

        extractions = []
        with open(self.extractions_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        extractions.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line: {e}")

        logger.info(f"Loaded {len(extractions)} extractions")
        return extractions

    def normalize_concept(self, name: str) -> str:
        """Simple normalization: lowercase, strip punctuation at ends."""
        name = name.strip().lower()
        # Remove trailing punctuation but keep internal punctuation
        name = re.sub(r"^[^\w]+|[^\w]+$", "", name)
        return name

    def build_graph(self) -> nx.MultiDiGraph:
        """Build graph from extractions with simple entity resolution."""
        extractions = self.load_extractions()

        # Track concept mappings for simple entity resolution
        concept_map = {}  # normalized -> canonical name

        for extraction in extractions:
            source_id = extraction.get("source_id", "unknown")
            # Extract timestamp metadata if available
            timestamp = extraction.get("timestamp") or extraction.get("date") or extraction.get("created_at")
            # Extract perspective/viewpoint tags if available
            perspective = (
                extraction.get("perspective") or extraction.get("viewpoint") or extraction.get("author_stance")
            )

            # Add concepts as nodes
            for concept in extraction.get("concepts", []):
                name = concept.get("name", "")
                if not name:
                    continue

                normalized = self.normalize_concept(name)

                # Simple entity resolution - use first occurrence as canonical
                if normalized in concept_map:
                    canonical = concept_map[normalized]
                else:
                    canonical = name  # Use original casing
                    concept_map[normalized] = canonical

                # Add or update node
                if self.graph.has_node(canonical):
                    # Merge attributes - keep highest importance
                    old_importance = self.graph.nodes[canonical].get("importance", 0)
                    new_importance = concept.get("importance", 0.5)
                    self.graph.nodes[canonical]["importance"] = max(old_importance, new_importance)

                    # Append descriptions
                    old_desc = self.graph.nodes[canonical].get("description", "")
                    new_desc = concept.get("description", "")
                    if new_desc and new_desc not in old_desc:
                        self.graph.nodes[canonical]["description"] = f"{old_desc} | {new_desc}"

                    # Update timestamp metadata
                    if timestamp:
                        # Store as occurrence_times to avoid GEXF treating it as temporal data
                        existing_times = self.graph.nodes[canonical].get("occurrence_times", [])
                        if timestamp not in existing_times:
                            existing_times.append(timestamp)
                            self.graph.nodes[canonical]["occurrence_times"] = existing_times

                    # Update perspective tags
                    if perspective:
                        existing_perspectives = self.graph.nodes[canonical].get("perspectives", [])
                        if perspective not in existing_perspectives:
                            existing_perspectives.append(perspective)
                            self.graph.nodes[canonical]["perspectives"] = existing_perspectives
                else:
                    node_attrs = {
                        "description": concept.get("description", ""),
                        "importance": concept.get("importance", 0.5),
                        "type": "concept",
                    }
                    # Add timestamp metadata if available
                    if timestamp:
                        # Store as occurrence_times to avoid GEXF treating it as temporal data
                        node_attrs["occurrence_times"] = [timestamp]

                    # Add perspective metadata if available
                    if perspective:
                        node_attrs["perspectives"] = [perspective]

                    self.graph.add_node(canonical, **node_attrs)

                # Track concept frequency
                self.concept_counts[canonical] += 1

                # Add source relationship with timestamp and perspective
                edge_attrs = {"relation": "mentions", "weight": 1.0}
                if timestamp:
                    # Store timestamp as string to avoid GEXF export issues
                    edge_attrs["timestamp_value"] = str(timestamp)
                if perspective:
                    edge_attrs["perspective"] = perspective
                self.graph.add_edge(source_id, canonical, **edge_attrs)

            # Add SPO relationships
            for rel in extraction.get("relationships", []):
                subject = rel.get("subject", "")
                predicate = rel.get("predicate", "")
                obj = rel.get("object", "")
                confidence = rel.get("confidence", 0.5)

                if not (subject and predicate and obj):
                    continue

                # Normalize and resolve entities
                subj_norm = self.normalize_concept(subject)
                obj_norm = self.normalize_concept(obj)

                subject = concept_map.get(subj_norm, subject)
                obj = concept_map.get(obj_norm, obj)

                # Ensure nodes exist
                if not self.graph.has_node(subject):
                    self.graph.add_node(subject, type="entity")
                if not self.graph.has_node(obj):
                    self.graph.add_node(obj, type="entity")

                # Add relationship edge with timestamp and perspective
                edge_attrs = {"predicate": predicate, "confidence": confidence, "source": source_id}
                if timestamp:
                    # Store timestamp as string to avoid GEXF export issues
                    edge_attrs["timestamp_value"] = str(timestamp)
                if perspective:
                    edge_attrs["perspective"] = perspective
                self.graph.add_edge(subject, obj, **edge_attrs)

            # Add co-occurrence edges between concepts in same article
            concepts = [
                concept_map.get(self.normalize_concept(c["name"]), c["name"])
                for c in extraction.get("concepts", [])
                if c.get("name")
            ]

            for i, c1 in enumerate(concepts):
                for c2 in concepts[i + 1 :]:
                    if c1 != c2:
                        # Add weak co-occurrence edge with timestamp and perspective
                        edge_attrs = {"relation": "co-occurs", "weight": 0.3, "source": source_id}
                        if timestamp:
                            # Store timestamp as string to avoid GEXF export issues
                            edge_attrs["timestamp_value"] = str(timestamp)
                        if perspective:
                            edge_attrs["perspective"] = perspective
                        self.graph.add_edge(c1, c2, **edge_attrs)

        # Calculate centrality metrics
        self._calculate_metrics()

        # Detect and add tensions to the graph
        try:
            from amplifier.knowledge.tension_detector import TensionDetector

            logger.info("Detecting tensions in the graph...")
            tension_detector = TensionDetector(self.graph)
            tensions_added = tension_detector.add_tensions_to_graph()
            logger.info(f"Added {tensions_added} tensions to the graph")
        except ImportError:
            logger.warning("TensionDetector not available, skipping tension detection")
        except Exception as e:
            logger.error(f"Failed to detect tensions: {e}")

        logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")

        return self.graph

    def _calculate_metrics(self):
        """Calculate basic graph metrics."""
        # Degree centrality
        degree_centrality = nx.degree_centrality(self.graph)
        for node, centrality in degree_centrality.items():
            self.graph.nodes[node]["degree_centrality"] = centrality

        # PageRank for importance
        try:
            pagerank = nx.pagerank(self.graph, max_iter=100)
            for node, rank in pagerank.items():
                self.graph.nodes[node]["pagerank"] = rank
        except Exception:
            logger.warning("PageRank calculation failed")

    def get_top_concepts(self, n: int = 20) -> list[tuple[str, int]]:
        """Get most frequently mentioned concepts."""
        return sorted(self.concept_counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_related_concepts(self, concept: str, max_distance: int = 2) -> list[str]:
        """Get concepts related to given concept within max_distance."""
        if concept not in self.graph:
            # Try normalized version
            normalized = self.normalize_concept(concept)
            for node in self.graph.nodes():
                if self.normalize_concept(node) == normalized:
                    concept = node
                    break
            else:
                return []

        # Get neighbors within distance
        related = set()
        current_level = {concept}

        for _ in range(max_distance):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.neighbors(node))
            related.update(next_level)
            current_level = next_level

        return list(related - {concept})

    def export_gexf(self, output_path: Path):
        """Export graph to GEXF format for Gephi visualization."""
        # Create a copy of the graph with converted attributes for GEXF compatibility
        export_graph = self.graph.copy()

        # Convert problematic node attributes
        for _node, attrs in export_graph.nodes(data=True):
            # Convert lists of floats to comma-separated strings
            if "occurrence_times" in attrs:
                times = attrs["occurrence_times"]
                if isinstance(times, list):
                    attrs["occurrence_times"] = ",".join(str(t) for t in times)

            # Convert any other list attributes that might contain floats
            for key, value in list(attrs.items()):
                if isinstance(value, list) and value and isinstance(value[0], int | float):
                    attrs[key] = ",".join(str(v) for v in value)

        nx.write_gexf(export_graph, output_path)
        logger.info(f"Exported graph to {output_path}")

    def export_graphml(self, output_path: Path):
        """Export graph to GraphML format."""
        # Create a copy of the graph with converted attributes for GraphML compatibility
        export_graph = self.graph.copy()

        # Convert problematic node attributes
        for _node, attrs in export_graph.nodes(data=True):
            # Convert lists to comma-separated strings for GraphML
            for key, value in list(attrs.items()):
                if isinstance(value, list):
                    if value and isinstance(value[0], int | float):
                        attrs[key] = ",".join(str(v) for v in value)
                    else:
                        attrs[key] = ",".join(str(v) for v in value)

        nx.write_graphml(export_graph, output_path)
        logger.info(f"Exported graph to {output_path}")

    def get_summary(self) -> dict:
        """Get basic graph statistics."""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "top_concepts": self.get_top_concepts(10),
            "strongly_connected_components": nx.number_strongly_connected_components(self.graph),
            "weakly_connected_components": nx.number_weakly_connected_components(self.graph),
        }


def main():
    """Simple CLI for graph building."""
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge graph from extractions")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to extractions JSONL file (defaults to configured data directory)",
    )
    parser.add_argument("--export-gexf", type=Path, help="Export graph to GEXF file")
    parser.add_argument("--export-graphml", type=Path, help="Export graph to GraphML file")
    parser.add_argument("--summary", action="store_true", help="Print graph summary")
    parser.add_argument("--top-concepts", type=int, default=20, help="Show top N concepts")
    parser.add_argument("--top-predicates", type=int, default=0, help="Show top N predicates with counts")
    parser.add_argument("--only-predicate-edges", action="store_true", help="Export only edges with predicates")
    parser.add_argument(
        "--allowed-predicates",
        type=str,
        default="",
        help="Comma-separated list of allowed predicates (applies only if predicate edges are exported)",
    )
    parser.add_argument(
        "--drop-untype-nodes",
        action="store_true",
        help="Drop nodes without a 'type' attribute (typically source/article nodes)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Build graph
    input_path = args.input or (paths.data_dir / "knowledge" / "extractions.jsonl")
    builder = GraphBuilder(input_path)
    builder.build_graph()

    # Optionally filter graph for export
    graph_to_export = builder.graph
    if args.only_predicate_edges or args.allowed_predicates or args.drop_untype_nodes:
        allowed_preds = (
            [p.strip() for p in args.allowed_predicates.split(",") if p.strip()] if args.allowed_predicates else None
        )
        g2 = nx.MultiDiGraph()
        # Nodes first (respect drop-untype-nodes)
        for node, attrs in graph_to_export.nodes(data=True):
            if args.drop_untype_nodes and attrs.get("type") is None:
                continue
            g2.add_node(node, **attrs)
        # Edges
        for u, v, key, data in graph_to_export.edges(keys=True, data=True):
            if u not in g2 or v not in g2:
                continue
            if args.only_predicate_edges and "predicate" not in data:
                continue
            if allowed_preds is not None:
                pred = data.get("predicate")
                if pred not in allowed_preds:
                    continue
            g2.add_edge(u, v, key=key, **data)
        graph_to_export = g2

    # Export if requested
    if args.export_gexf:
        if graph_to_export is builder.graph:
            builder.export_gexf(args.export_gexf)
        else:
            nx.write_gexf(graph_to_export, args.export_gexf)
            logger.info(f"Exported graph to {args.export_gexf}")

    if args.export_graphml:
        if graph_to_export is builder.graph:
            builder.export_graphml(args.export_graphml)
        else:
            nx.write_graphml(graph_to_export, args.export_graphml)
            logger.info(f"Exported graph to {args.export_graphml}")

    # Show summary
    if args.summary:
        summary = builder.get_summary()
        print("\n=== Graph Summary ===")
        print(f"Nodes: {summary['nodes']}")
        print(f"Edges: {summary['edges']}")
        print(f"Density: {summary['density']:.4f}")
        print(f"Strongly connected components: {summary['strongly_connected_components']}")
        print(f"Weakly connected components: {summary['weakly_connected_components']}")

    # Show top concepts
    if args.top_concepts:
        print(f"\n=== Top {args.top_concepts} Concepts ===")
        for concept, count in builder.get_top_concepts(args.top_concepts):
            print(f"{count:3d} - {concept}")

    # Show top predicates if requested
    if args.top_predicates and args.top_predicates > 0:
        from collections import Counter

        cnt: Counter[str] = Counter()
        for _u, _v, data in builder.graph.edges(data=True):
            pred = data.get("predicate")
            if pred:
                cnt[str(pred)] += 1
        if cnt:
            print(f"\n=== Top {args.top_predicates} Predicates ===")
            for pred, c in cnt.most_common(args.top_predicates):
                print(f"{c:3d} - {pred}")


if __name__ == "__main__":
    main()
