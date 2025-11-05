"""
Deterministic DOT to Mermaid converter using pattern matching.
"""

import logging
import re

from ..models import DotGraph

logger = logging.getLogger(__name__)


def sanitize_mermaid_id(node_id: str) -> str:
    """Sanitize node ID for Mermaid compatibility.

    Mermaid has restrictions on node IDs:
    - Can't start with numbers
    - Special characters need escaping
    """
    # Remove quotes
    node_id = node_id.strip('"').strip("'")

    # Replace spaces and special chars with underscores
    node_id = re.sub(r"[^\w]", "_", node_id)

    # Ensure it doesn't start with a number
    if node_id and node_id[0].isdigit():
        node_id = f"node_{node_id}"

    return node_id or "unnamed"


def format_node_label(node_id: str, attributes: dict) -> str:
    """Format node with label and shape based on attributes."""
    label = attributes.get("label", node_id).strip('"')
    shape = attributes.get("shape", "default")

    # Map DOT shapes to Mermaid shapes
    shape_map = {
        "box": "[{}]",  # Rectangle
        "square": "[{}]",  # Rectangle
        "rect": "[{}]",  # Rectangle
        "rectangle": "[{}]",  # Rectangle
        "circle": "(({}))",  # Circle
        "ellipse": "(({}))",  # Circle (closest match)
        "diamond": "{{{}}}",  # Diamond/rhombus
        "parallelogram": "[/{}\\]",  # Parallelogram
        "trapezium": "[/{}\\]",  # Trapezoid (use parallelogram)
        "hexagon": "{{{{{}}}}}",  # Hexagon
        "cylinder": "[({})]",  # Cylinder (database)
        "default": "[{}]",  # Default rectangle
    }

    template = shape_map.get(shape, shape_map["default"])
    return template.format(label)


def convert_deterministic(graph: DotGraph) -> str | None:
    """Convert DOT graph to Mermaid using deterministic rules.

    Args:
        graph: Parsed DOT graph structure

    Returns:
        Mermaid diagram string or None if conversion fails
    """
    try:
        lines = []

        # Determine graph direction
        rankdir = graph.attributes.get("rankdir", "TB")
        direction_map = {
            "TB": "TD",  # Top to Bottom
            "BT": "BT",  # Bottom to Top
            "LR": "LR",  # Left to Right
            "RL": "RL",  # Right to Left
        }
        direction = direction_map.get(rankdir, "TD")

        # Start with graph declaration
        if graph.graph_type == "graph":
            lines.append(f"graph {direction}")
        else:
            lines.append(f"flowchart {direction}")

        # Track which nodes have been defined
        defined_nodes = set()

        # Add edges (this will implicitly define nodes)
        for edge in graph.edges:
            source = sanitize_mermaid_id(edge["source"])
            target = sanitize_mermaid_id(edge["target"])

            # Get source node label if not yet defined
            if source not in defined_nodes:
                if edge["source"] in graph.nodes:
                    source_label = format_node_label(edge["source"], graph.nodes[edge["source"]])
                else:
                    source_label = f"[{edge['source']}]"
                defined_nodes.add(source)
            else:
                source_label = source

            # Get target node label if not yet defined
            if target not in defined_nodes:
                if edge["target"] in graph.nodes:
                    target_label = format_node_label(edge["target"], graph.nodes[edge["target"]])
                else:
                    target_label = f"[{edge['target']}]"
                defined_nodes.add(target)
            else:
                target_label = target

            # Determine edge style
            edge_attrs = edge.get("attributes", {})
            edge_label = edge_attrs.get("label", "").strip('"')

            # Build edge connector based on attributes
            if graph.graph_type == "graph":
                # Undirected graph
                if edge_label:
                    connector = f" --- |{edge_label}| "
                else:
                    connector = " --- "
            else:
                # Directed graph
                style = edge_attrs.get("style", "")
                if "dotted" in style or "dashed" in style:
                    connector = " -.-> " if not edge_label else f" -.{edge_label}.-> "
                else:
                    connector = " --> " if not edge_label else f" -->|{edge_label}| "

            # Format the edge line
            if source not in defined_nodes or target not in defined_nodes:
                # First occurrence, include labels
                lines.append(
                    f"    {source}{source_label if source not in defined_nodes else ''}{connector}{target}{target_label if target not in defined_nodes else ''}"
                )
            else:
                # Already defined, just use IDs
                lines.append(f"    {source}{connector}{target}")

        # Add isolated nodes (nodes without edges)
        for node_id, attrs in graph.nodes.items():
            san_id = sanitize_mermaid_id(node_id)
            if san_id not in defined_nodes:
                label = format_node_label(node_id, attrs)
                lines.append(f"    {san_id}{label}")

        # Handle subgraphs (basic support)
        for i, subgraph in enumerate(graph.subgraphs):
            sub_name = subgraph.name or f"subgraph_{i}"
            lines.append(f"    subgraph {sanitize_mermaid_id(sub_name)}")

            # Recursively convert subgraph
            sub_mermaid = convert_deterministic(subgraph)
            if sub_mermaid:
                # Indent subgraph content
                sub_lines = sub_mermaid.split("\n")[1:]  # Skip the graph declaration
                for line in sub_lines:
                    if line.strip():
                        lines.append(f"    {line}")

            lines.append("    end")

        # Add styling if present
        if "bgcolor" in graph.attributes or "color" in graph.attributes:
            lines.append("")
            lines.append("    %% Graph styling")
            if "bgcolor" in graph.attributes:
                lines.append(
                    f"    %%{{init: {{'theme':'base', 'themeVariables': {{'primaryColor':'{graph.attributes['bgcolor']}'}} }} }}%%"
                )

        result = "\n".join(lines)
        logger.debug(f"Deterministic conversion successful: {len(lines)} lines generated")
        return result

    except Exception as e:
        logger.warning(f"Deterministic conversion failed: {e}")
        return None
