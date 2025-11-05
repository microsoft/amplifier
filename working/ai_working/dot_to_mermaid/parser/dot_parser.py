"""
DOT file parser implementation using pydot.
"""

import logging
from pathlib import Path

import pydot

from ..models import DotGraph

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def parse_dot_string(dot_content: str) -> DotGraph:
    """Parse DOT content string into structured representation.

    Args:
        dot_content: DOT format string

    Returns:
        DotGraph object with parsed structure or raw_source only on failure
    """
    try:
        # Parse with pydot
        graphs = pydot.graph_from_dot_data(dot_content)
        if not graphs:
            logger.warning("No graphs found in DOT content")
            return DotGraph(
                name="unknown",
                graph_type="digraph",
                nodes={},
                edges=[],
                subgraphs=[],
                attributes={},
                raw_source=dot_content,
            )

        graph = graphs[0]  # Take first graph

        # Extract graph type and name
        graph_type = graph.get_type() or "digraph"
        graph_name = graph.get_name() or "unnamed"

        # Extract nodes
        nodes = {}
        for node in graph.get_nodes():
            node_name = node.get_name().strip('"')
            if node_name in ("node", "edge", "graph"):  # Skip default attributes
                continue

            attrs = {}
            for key, value in node.get_attributes().items():
                if value:
                    attrs[key] = value.strip('"')
            nodes[node_name] = attrs

        # Extract edges
        edges = []
        for edge in graph.get_edges():
            edge_dict = {
                "source": edge.get_source().strip('"'),
                "target": edge.get_destination().strip('"'),
                "attributes": {},
            }
            for key, value in edge.get_attributes().items():
                if value:
                    edge_dict["attributes"][key] = value.strip('"')
            edges.append(edge_dict)

        # Extract graph attributes
        attributes = {}
        for key, value in graph.get_attributes().items():
            if value:
                attributes[key] = value.strip('"')

        # Extract subgraphs
        subgraphs = []
        for subgraph in graph.get_subgraphs():
            # Extract subgraph nodes directly
            sub_nodes = {}
            for node in subgraph.get_nodes():
                node_name = node.get_name().strip('"')
                if node_name not in ("node", "edge", "graph"):
                    attrs = {}
                    for key, value in node.get_attributes().items():
                        if value:
                            attrs[key] = value.strip('"')
                    sub_nodes[node_name] = attrs

            # Extract subgraph edges directly
            sub_edges = []
            for edge in subgraph.get_edges():
                edge_dict = {
                    "source": edge.get_source().strip('"'),
                    "target": edge.get_destination().strip('"'),
                    "attributes": {},
                }
                for key, value in edge.get_attributes().items():
                    if value:
                        edge_dict["attributes"][key] = value.strip('"')
                sub_edges.append(edge_dict)

            # Extract subgraph attributes
            sub_attrs = {}
            for key, value in subgraph.get_attributes().items():
                if value:
                    sub_attrs[key] = value.strip('"')

            # Create DotGraph for subgraph
            sub_parsed = DotGraph(
                name=subgraph.get_name() or f"subgraph_{len(subgraphs)}",
                graph_type="subgraph",
                nodes=sub_nodes,
                edges=sub_edges,
                subgraphs=[],  # Could handle nested subgraphs recursively if needed
                attributes=sub_attrs,
                raw_source="",
            )
            subgraphs.append(sub_parsed)

        return DotGraph(
            name=graph_name,
            graph_type=graph_type,
            nodes=nodes,
            edges=edges,
            subgraphs=subgraphs,
            attributes=attributes,
            raw_source=dot_content,
        )

    except Exception as e:
        logger.warning(f"Failed to parse DOT content: {e}")
        # Return minimal graph with raw source for AI fallback
        return DotGraph(
            name="unknown",
            graph_type="digraph",
            nodes={},
            edges=[],
            subgraphs=[],
            attributes={},
            raw_source=dot_content,
        )


def parse_dot_file(file_path: Path) -> DotGraph:
    """Parse DOT file into structured representation.

    Args:
        file_path: Path to DOT file

    Returns:
        DotGraph object with parsed structure
    """
    try:
        dot_content = file_path.read_text(encoding="utf-8")
        result = parse_dot_string(dot_content)
        logger.debug(f"Parsed {file_path.name}: {len(result.nodes)} nodes, {len(result.edges)} edges")
        return result
    except Exception as e:
        logger.error(f"Failed to read DOT file {file_path}: {e}")
        # Return empty graph with error
        return DotGraph(
            name=file_path.stem,
            graph_type="digraph",
            nodes={},
            edges=[],
            subgraphs=[],
            attributes={},
            raw_source=f"# Error reading file: {e}",
        )
