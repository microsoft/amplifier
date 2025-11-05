#!/usr/bin/env python3
"""
Semantic search interface for the knowledge graph.
Enables Claude Code to query the graph with natural language.
Following ruthless simplicity - direct implementation, no unnecessary abstractions.
"""

import json
import logging
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import networkx as nx

from amplifier.config.paths import paths

from .graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class GraphSearch:
    """Simple semantic search interface for knowledge graph."""

    def __init__(self, graph: nx.MultiDiGraph | None = None, query_log_path: str | None = None):
        """Initialize with existing graph or build from extractions."""
        if graph is None:
            # Build graph from extractions
            builder = GraphBuilder()
            self.graph = builder.build_graph()
        else:
            self.graph = graph

        # Set up query logging for pattern tracking
        self.query_log_path = (
            Path(query_log_path) if query_log_path else paths.data_dir / "knowledge" / "query_log.jsonl"
        )
        self.query_patterns = {}  # Cache for successful query patterns

    def search_concepts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Fuzzy search for concepts matching the query.
        Returns list of matching concepts sorted by relevance.
        """
        query_lower = query.lower()
        results = []

        for node in self.graph.nodes(data=True):
            node_name = node[0]
            node_data = node[1]

            # Skip non-concept nodes
            if node_data.get("type") not in ["concept", "entity", None]:
                continue

            # Calculate similarity score
            similarity = SequenceMatcher(None, query_lower, node_name.lower()).ratio()

            # Also check description
            description = node_data.get("description", "")
            if description:
                desc_similarity = SequenceMatcher(None, query_lower, description.lower()).ratio()
                similarity = max(similarity, desc_similarity * 0.7)  # Weight description matches lower

            if similarity > 0.3:  # Threshold for matches
                results.append(
                    {
                        "name": node_name,
                        "similarity": similarity,
                        "description": description,
                        "importance": node_data.get("importance", 0),
                        "pagerank": node_data.get("pagerank", 0),
                        "degree_centrality": node_data.get("degree_centrality", 0),
                    }
                )

        # Sort by combined score (similarity + pagerank)
        results.sort(key=lambda x: x["similarity"] + x["pagerank"] * 0.3, reverse=True)

        # Log successful query if we found results
        final_results = results[:limit]
        if final_results:
            self._log_query(query, "search_concepts", len(final_results), final_results[0]["name"])

        return final_results

    def find_path(self, concept1: str, concept2: str) -> dict[str, Any]:
        """
        Find shortest path between two concepts.
        Returns path and relationships along the path.
        """
        # Find matching nodes for concepts
        node1 = self._find_node(concept1)
        node2 = self._find_node(concept2)

        if not node1:
            return {"error": f"Concept '{concept1}' not found"}
        if not node2:
            return {"error": f"Concept '{concept2}' not found"}

        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, node1, node2)

            # Get relationships along path
            relationships = []
            for i in range(len(path) - 1):
                edges = self.graph.get_edge_data(path[i], path[i + 1])
                if edges:
                    # MultiDiGraph can have multiple edges
                    for _edge_key, edge_data in edges.items():
                        relationships.append(
                            {
                                "from": path[i],
                                "to": path[i + 1],
                                "predicate": edge_data.get("predicate", edge_data.get("relation", "related")),
                                "confidence": edge_data.get("confidence", edge_data.get("weight", 1.0)),
                            }
                        )

            result = {"path": path, "length": len(path) - 1, "relationships": relationships}
            # Log successful path finding
            self._log_query(f"{concept1} -> {concept2}", "find_path", len(path), f"{node1} -> {node2}")
            return result

        except nx.NetworkXNoPath:
            return {"error": f"No path found between '{concept1}' and '{concept2}'"}

    def get_neighborhood(self, concept: str, hops: int = 2) -> dict[str, Any]:
        """
        Get related concepts within N hops of the given concept.
        Returns structured neighborhood with relationships.
        """
        node = self._find_node(concept)
        if not node:
            return {"error": f"Concept '{concept}' not found"}

        # Get all nodes within N hops
        neighborhood = {node}
        current_level = {node}

        levels = {node: 0}
        for hop in range(1, hops + 1):
            next_level = set()
            for n in current_level:
                # Get both predecessors and successors (directed graph)
                neighbors = set(self.graph.predecessors(n)) | set(self.graph.successors(n))
                for neighbor in neighbors:
                    if neighbor not in neighborhood:
                        next_level.add(neighbor)
                        levels[neighbor] = hop
            neighborhood.update(next_level)
            current_level = next_level

        # Build subgraph and extract relationships
        subgraph = self.graph.subgraph(neighborhood)

        # Convert to JSON-serializable format
        nodes = []
        for n in neighborhood:
            node_data = self.graph.nodes[n]
            nodes.append(
                {
                    "name": n,
                    "level": levels[n],
                    "description": node_data.get("description", ""),
                    "importance": node_data.get("importance", 0),
                    "pagerank": node_data.get("pagerank", 0),
                }
            )

        edges = []
        for u, v, data in subgraph.edges(data=True):
            edges.append(
                {
                    "from": u,
                    "to": v,
                    "predicate": data.get("predicate", data.get("relation", "related")),
                    "confidence": data.get("confidence", data.get("weight", 1.0)),
                }
            )

        # Sort nodes by level then pagerank
        nodes.sort(key=lambda x: (x["level"], -x["pagerank"]))

        result = {"center": node, "nodes": nodes, "edges": edges, "total_nodes": len(nodes), "total_edges": len(edges)}

        # Log successful neighborhood query
        self._log_query(concept, "get_neighborhood", len(nodes), node)

        return result

    def query(self, natural_language_query: str) -> dict[str, Any]:
        """
        Main entry point for Claude Code to query the graph.
        Interprets natural language and routes to appropriate method.
        """
        query_lower = natural_language_query.lower()

        # Detect query type and extract parameters
        if "path" in query_lower or "between" in query_lower or "connect" in query_lower:
            # Try to extract two concepts for path finding
            # Simple heuristic: look for "between X and Y" or "from X to Y"
            import re

            pattern = r"(?:between|from)\s+(.+?)\s+(?:and|to)\s+(.+)"
            match = re.search(pattern, query_lower)
            if match:
                concept1 = match.group(1).strip()
                concept2 = match.group(2).strip()
                return self.find_path(concept1, concept2)

        elif "related" in query_lower or "neighbors" in query_lower or "around" in query_lower:
            # Extract concept for neighborhood search
            # Look for "related to X" or "neighbors of X"
            import re

            pattern = r"(?:related to|neighbors of|around)\s+(.+)"
            match = re.search(pattern, query_lower)
            if match:
                concept = match.group(1).strip()
                # Check for hop count
                hop_match = re.search(r"(\d+)\s*hop", query_lower)
                hops = int(hop_match.group(1)) if hop_match else 2
                return self.get_neighborhood(concept, hops)

        # Default to concept search
        return {"results": self.search_concepts(natural_language_query)}

    def _log_query(self, query: str, query_type: str, result_count: int, top_result: str | None = None) -> None:
        """Log successful queries to build intelligence about search patterns."""
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_type": query_type,
            "result_count": result_count,
            "top_result": top_result,
        }

        # Ensure log directory exists
        self.query_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to log file
        try:
            with open(self.query_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log query: {e}")

        # Update pattern cache for successful queries
        if result_count > 0:
            query_lower = query.lower()
            if query_lower not in self.query_patterns:
                self.query_patterns[query_lower] = {"count": 0, "avg_results": 0}

            pattern = self.query_patterns[query_lower]
            pattern["count"] += 1
            pattern["avg_results"] = (pattern["avg_results"] * (pattern["count"] - 1) + result_count) / pattern["count"]

    def get_query_patterns(self) -> dict[str, Any]:
        """Analyze logged queries to find successful patterns."""
        if not self.query_log_path.exists():
            return {"message": "No query log found"}

        patterns = {}
        total_queries = 0
        successful_queries = 0

        with open(self.query_log_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        total_queries += 1
                        if entry.get("result_count", 0) > 0:
                            successful_queries += 1

                            # Track query types
                            query_type = entry.get("query_type", "unknown")
                            if query_type not in patterns:
                                patterns[query_type] = {"count": 0, "queries": []}
                            patterns[query_type]["count"] += 1

                            # Store example queries (limit to 10 most recent)
                            if len(patterns[query_type]["queries"]) < 10:
                                patterns[query_type]["queries"].append(
                                    {
                                        "query": entry["query"],
                                        "top_result": entry.get("top_result"),
                                        "timestamp": entry.get("timestamp"),
                                    }
                                )
                    except json.JSONDecodeError:
                        continue

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "patterns_by_type": patterns,
            "cached_patterns": len(self.query_patterns),
        }

    def _find_node(self, concept: str) -> str | None:
        """Find best matching node for a concept name."""
        # Try exact match first
        if concept in self.graph:
            return concept

        # Try fuzzy match
        concept_lower = concept.lower()
        best_match = None
        best_score = 0

        for node in self.graph.nodes():
            score = SequenceMatcher(None, concept_lower, node.lower()).ratio()
            if score > best_score and score > 0.7:  # Threshold for accepting match
                best_score = score
                best_match = node

        return best_match


def main():
    """CLI interface for testing graph search."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Search knowledge graph")

    # Support both subcommands and direct query for backward compatibility
    if len(sys.argv) > 1 and sys.argv[1] in ["path", "neighbors"]:
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # Path command
        path_parser = subparsers.add_parser("path", help="Find path between concepts")
        path_parser.add_argument("from_concept", help="Starting concept")
        path_parser.add_argument("to_concept", help="Target concept")

        # Neighbors command
        neighbors_parser = subparsers.add_parser("neighbors", help="Explore concept neighborhood")
        neighbors_parser.add_argument("concept", help="Concept to explore")
        neighbors_parser.add_argument("--hops", type=int, default=2, help="Number of hops")
    else:
        # Default query mode
        parser.add_argument("query", help="Natural language query")
        parser.add_argument("--limit", type=int, default=10, help="Max results for concept search")
        parser.add_argument("--hops", type=int, default=2, help="Hops for neighborhood search")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Initialize search
    search = GraphSearch()

    # Execute appropriate command
    if hasattr(args, "command"):
        if args.command == "path":
            result = search.find_path(args.from_concept, args.to_concept)
            if "error" in result:
                print(result["error"])
            else:
                print(f"Path found ({result['length']} steps):")
                for i, node in enumerate(result["path"]):
                    print(f"  {i}: {node}")
                print("\nRelationships:")
                for rel in result["relationships"]:
                    print(f"  {rel['from']} --[{rel['predicate']}]--> {rel['to']}")
        elif args.command == "neighbors":
            result = search.get_neighborhood(args.concept, hops=args.hops)
            if "error" in result:
                print(result["error"])
            else:
                print(
                    f"Neighborhood of '{result['center']}' ({result['total_nodes']} nodes, {result['total_edges']} edges):"
                )
                for node in result["nodes"][:20]:  # Show first 20
                    print(f"  Level {node['level']}: {node['name']}")
                if result["total_nodes"] > 20:
                    print(f"  ... and {result['total_nodes'] - 20} more nodes")
    else:
        # Default query mode
        result = search.query(args.query)
        # Pretty print result
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
