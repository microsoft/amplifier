#!/usr/bin/env python3
"""
Tension detection module for knowledge graph.
Identifies productive contradictions and opposing viewpoints as valuable features.
Following the tension preservation philosophy - tensions generate insights.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx

from amplifier.config.paths import paths
from amplifier.knowledge.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class TensionDetector:
    """Detect and analyze productive tensions in knowledge graph."""

    # Define opposite predicate pairs
    OPPOSITE_PAIRS = [
        ("enables", "prevents"),
        ("increases", "decreases"),
        ("supports", "opposes"),
        ("causes", "blocks"),
        ("improves", "degrades"),
        ("simplifies", "complicates"),
        ("accelerates", "slows"),
        ("strengthens", "weakens"),
        ("promotes", "inhibits"),
        ("facilitates", "hinders"),
    ]

    def __init__(self, graph: nx.MultiDiGraph | None = None):
        """Initialize with existing graph or build new one."""
        if graph is None:
            builder = GraphBuilder()
            self.graph = builder.build_graph()
        else:
            self.graph = graph

        # Build opposite predicate lookup
        self.opposites = {}
        for p1, p2 in self.OPPOSITE_PAIRS:
            self.opposites[p1] = p2
            self.opposites[p2] = p1

    def find_opposing_predicates(self) -> list[dict[str, Any]]:
        """Find edges with opposing relationship types about same subject-object pair."""
        tensions = []

        # Group edges by subject-object pairs
        edge_groups = defaultdict(list)
        for u, v, data in self.graph.edges(data=True):
            if "predicate" in data:
                edge_groups[(u, v)].append(data)

        # Check each group for opposing predicates
        for (subject, obj), edges in edge_groups.items():
            predicates = [e.get("predicate", "") for e in edges]

            for i, pred1 in enumerate(predicates):
                if pred1 in self.opposites:
                    opposite = self.opposites[pred1]
                    for j, pred2 in enumerate(predicates[i + 1 :], i + 1):
                        if pred2 == opposite:
                            tension = {
                                "type": "opposing_predicates",
                                "subject": subject,
                                "object": obj,
                                "position_a": {
                                    "predicate": pred1,
                                    "confidence": edges[i].get("confidence", 0.5),
                                    "source": edges[i].get("source", "unknown"),
                                },
                                "position_b": {
                                    "predicate": pred2,
                                    "confidence": edges[j].get("confidence", 0.5),
                                    "source": edges[j].get("source", "unknown"),
                                },
                                "crux": f"Whether {subject} {pred1} or {pred2} {obj}",
                            }
                            tensions.append(tension)

        return tensions

    def find_conflicting_statements(self) -> list[dict[str, Any]]:
        """Find contradictory claims about the same subject from different sources."""
        tensions = []

        # Group edges by subject
        subject_claims = defaultdict(list)
        for u, v, data in self.graph.edges(data=True):
            if "predicate" in data:
                subject_claims[u].append({"object": v, "data": data})

        # Look for conflicting claims
        for subject, claims in subject_claims.items():
            # Group by predicate type
            by_predicate = defaultdict(list)
            for claim in claims:
                pred = claim["data"].get("predicate", "")
                if pred:
                    by_predicate[pred].append(claim)

            # Check for multiple different objects for same predicate
            for predicate, pred_claims in by_predicate.items():
                if len(pred_claims) > 1:
                    objects = [c["object"] for c in pred_claims]
                    sources = [c["data"].get("source", "unknown") for c in pred_claims]

                    # Only flag if objects differ and sources differ
                    if len(set(objects)) > 1 and len(set(sources)) > 1:
                        tension = {
                            "type": "conflicting_statements",
                            "subject": subject,
                            "predicate": predicate,
                            "conflicts": [
                                {
                                    "object": c["object"],
                                    "source": c["data"].get("source", "unknown"),
                                    "confidence": c["data"].get("confidence", 0.5),
                                }
                                for c in pred_claims
                            ],
                            "crux": f"What {subject} actually {predicate}",
                        }
                        tensions.append(tension)

        return tensions

    def score_tension_productivity(self, tension: dict[str, Any]) -> float:
        """Score how productive a tension is based on graph context."""
        score = 0.5  # Base score

        # Higher score for tensions involving high-centrality nodes
        subjects = []
        if "subject" in tension:
            subjects.append(tension["subject"])
        if "object" in tension:
            subjects.append(tension["object"])

        for node in subjects:
            if node in self.graph:
                # PageRank indicates importance
                score += self.graph.nodes[node].get("pagerank", 0) * 2
                # Degree centrality indicates connectivity
                score += self.graph.nodes[node].get("degree_centrality", 0)

        # Higher score for high-confidence opposing views
        if tension["type"] == "opposing_predicates":
            conf_a = tension["position_a"].get("confidence", 0.5)
            conf_b = tension["position_b"].get("confidence", 0.5)
            # Strong opposing views are more productive
            score += min(conf_a, conf_b)

        # Higher score for multiple conflicting sources
        if tension["type"] == "conflicting_statements":
            num_conflicts = len(tension.get("conflicts", []))
            score += 0.2 * num_conflicts

        return min(score, 1.0)  # Cap at 1.0

    def get_all_tensions(self) -> dict[str, Any]:
        """Find all tensions in the graph and return with analysis."""
        # Find different types of tensions
        opposing = self.find_opposing_predicates()
        conflicting = self.find_conflicting_statements()

        all_tensions = opposing + conflicting

        # Score and sort by productivity
        for tension in all_tensions:
            tension["productivity_score"] = self.score_tension_productivity(tension)

        all_tensions.sort(key=lambda t: t["productivity_score"], reverse=True)

        # Add context for top tensions
        for tension in all_tensions[:10]:  # Enrich top 10
            self._add_tension_context(tension)

        return {
            "tensions_found": len(all_tensions),
            "productive_tensions": all_tensions,
            "statistics": {
                "opposing_predicates": len(opposing),
                "conflicting_statements": len(conflicting),
                "avg_productivity": sum(t["productivity_score"] for t in all_tensions) / len(all_tensions)
                if all_tensions
                else 0,
            },
            "top_tension": all_tensions[0] if all_tensions else None,
        }

    def _add_tension_context(self, tension: dict[str, Any]) -> None:
        """Add surrounding context to make tension more understandable."""
        context_nodes = set()

        # Collect relevant nodes
        if "subject" in tension:
            context_nodes.add(tension["subject"])
        if "object" in tension:
            context_nodes.add(tension["object"])

        # Add node descriptions
        tension["context"] = {}
        for node in context_nodes:
            if node in self.graph:
                tension["context"][node] = {
                    "description": self.graph.nodes[node].get("description", ""),
                    "importance": self.graph.nodes[node].get("importance", 0.5),
                    "type": self.graph.nodes[node].get("type", "unknown"),
                }

        # Add why this tension is productive
        tension["productive_because"] = self._explain_productivity(tension)

    def _explain_productivity(self, tension: dict[str, Any]) -> str:
        """Explain why a tension is productive."""
        if tension["type"] == "opposing_predicates":
            return (
                f"This opposition reveals fundamental uncertainty about the relationship "
                f"between '{tension['subject']}' and '{tension['object']}'. "
                f"Different sources see opposite effects, suggesting context-dependent behavior "
                f"or evolving understanding."
            )
        if tension["type"] == "conflicting_statements":
            num_conflicts = len(tension.get("conflicts", []))
            return (
                f"Multiple sources ({num_conflicts}) disagree about {tension['predicate']} "
                f"relationships for '{tension['subject']}'. This diversity of viewpoints "
                f"suggests either contextual variation or an active area of debate."
            )
        return "This tension represents unresolved questions that could drive further investigation."

    def add_tensions_to_graph(self) -> int:
        """Add detected tensions as special nodes in the graph."""
        tensions_data = self.get_all_tensions()
        tensions = tensions_data["productive_tensions"]

        added_count = 0
        for i, tension in enumerate(tensions):
            # Create unique tension node ID
            tension_id = f"tension_{tension['type']}_{i}"

            # Add tension as a special node
            self.graph.add_node(
                tension_id,
                type="tension",
                tension_type=tension["type"],
                crux=tension["crux"],
                productivity_score=tension["productivity_score"],
                productive_because=tension.get("productive_because", ""),
                description=f"Tension: {tension['crux']}",
            )

            # Connect tension to related concepts
            if "subject" in tension:
                self.graph.add_edge(
                    tension["subject"], tension_id, relation="has_tension", weight=tension["productivity_score"]
                )
            if "object" in tension:
                self.graph.add_edge(
                    tension_id, tension["object"], relation="tension_about", weight=tension["productivity_score"]
                )

            # For conflicting statements, connect to all conflicting objects
            if tension["type"] == "conflicting_statements":
                for conflict in tension.get("conflicts", []):
                    self.graph.add_edge(
                        tension_id,
                        conflict["object"],
                        relation="conflict_option",
                        confidence=conflict["confidence"],
                        source=conflict["source"],
                    )

            added_count += 1

        logger.info(f"Added {added_count} tensions as nodes to the graph")
        return added_count

    def export_tensions(self, output_path: Path) -> None:
        """Export tensions to JSON file."""
        tensions = self.get_all_tensions()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(tensions, f, indent=2, default=str)
        logger.info(f"Exported {tensions['tensions_found']} tensions to {output_path}")


def main():
    """CLI for tension detection."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect productive tensions in knowledge graph")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to extractions JSONL file (defaults to configured data directory)",
    )
    parser.add_argument("--output", type=Path, help="Export tensions to JSON file")
    parser.add_argument("--top", type=int, default=10, help="Show top N tensions")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Build graph and detect tensions
    input_path = args.input or (paths.data_dir / "knowledge" / "extractions.jsonl")
    builder = GraphBuilder(input_path)
    graph = builder.build_graph()

    detector = TensionDetector(graph)
    results = detector.get_all_tensions()

    # Display results
    print("\n=== Tension Detection Results ===")
    print(f"Total tensions found: {results['tensions_found']}")
    print(f"Opposing predicates: {results['statistics']['opposing_predicates']}")
    print(f"Conflicting statements: {results['statistics']['conflicting_statements']}")
    print(f"Average productivity: {results['statistics']['avg_productivity']:.3f}")

    if args.top and results["productive_tensions"]:
        print(f"\n=== Top {args.top} Productive Tensions ===")
        for i, tension in enumerate(results["productive_tensions"][: args.top], 1):
            print(f"\n{i}. {tension['type']} (productivity: {tension['productivity_score']:.3f})")
            print(f"   Crux: {tension['crux']}")
            print(f"   Why productive: {tension.get('productive_because', 'Unknown')}")

    # Export if requested
    if args.output:
        detector.export_tensions(args.output)


if __name__ == "__main__":
    main()
