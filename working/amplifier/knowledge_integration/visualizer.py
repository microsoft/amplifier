"""
Interactive knowledge graph visualization using PyVis.

Creates beautiful, explorable HTML visualizations of the unified knowledge store.
"""

import logging
from pathlib import Path

from pyvis.network import Network

from amplifier.knowledge_integration.knowledge_store import UnifiedKnowledgeStore
from amplifier.knowledge_integration.models import Relationship
from amplifier.knowledge_integration.models import UnifiedKnowledgeNode

logger = logging.getLogger(__name__)


class KnowledgeGraphVisualizer:
    """
    Creates interactive HTML visualizations of knowledge graphs.

    Features:
    - Color-coded nodes by type
    - Directed edges with labels
    - Physics simulation for layout
    - Search and filter capabilities
    - Hover tooltips with definitions
    - Click to focus on neighborhoods
    """

    # Color scheme for different node types
    NODE_COLORS = {
        "concept": "#3498db",  # Blue
        "pattern": "#9b59b6",  # Purple
        "technique": "#2ecc71",  # Green
        "principle": "#e74c3c",  # Red
        "tool": "#f39c12",  # Orange
        "entity": "#95a5a6",  # Gray
        "default": "#34495e",  # Dark gray
    }

    # Node shapes for different types
    NODE_SHAPES = {
        "concept": "dot",
        "pattern": "square",
        "technique": "triangle",
        "principle": "star",
        "tool": "box",
        "entity": "ellipse",
        "default": "dot",
    }

    def __init__(self, store: UnifiedKnowledgeStore):
        """
        Initialize the visualizer with a knowledge store.

        Args:
            store: The unified knowledge store to visualize
        """
        self.store = store

    def create_full_graph(
        self,
        output_path: Path | str = "knowledge_graph.html",
        physics: bool = True,
        width: str = "100%",
        height: str = "800px",
    ) -> Path:
        """
        Create a visualization of the entire knowledge graph.

        Args:
            output_path: Where to save the HTML file
            physics: Enable physics simulation
            width: Width of the visualization
            height: Height of the visualization

        Returns:
            Path to the generated HTML file
        """
        output_path = Path(output_path)

        # Create network with configuration
        net = Network(height=height, width=width, bgcolor="#ffffff", directed=True, notebook=False)

        # Configure physics
        if physics:
            net.force_atlas_2based(
                gravity=-50, central_gravity=0.01, spring_length=100, spring_strength=0.08, damping=0.4, overlap=0
            )
        else:
            net.toggle_physics(False)

        # Add all nodes
        for node in self.store.nodes.values():
            self._add_node_to_network(net, node)

        # Add all relationships as edges
        for rel in self.store.relationships:
            self._add_edge_to_network(net, rel)

        # Configure interactive options
        net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "size": 16
                }
            },
            "edges": {
                "font": {
                    "size": 12,
                    "align": "middle"
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                }
            },
            "physics": {
                "enabled": true,
                "stabilization": {
                    "enabled": true,
                    "iterations": 100
                }
            },
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": true
            }
        }
        """)

        # Save the visualization
        net.save_graph(str(output_path))
        logger.info(f"Saved knowledge graph visualization to {output_path}")

        return output_path

    def create_subgraph(
        self,
        center_node: str,
        depth: int = 2,
        output_path: Path | str = "subgraph.html",
        physics: bool = True,
        width: str = "100%",
        height: str = "800px",
    ) -> Path:
        """
        Create a visualization centered on a specific node.

        Args:
            center_node: Name of the node to center on
            depth: How many hops from center to include
            output_path: Where to save the HTML file
            physics: Enable physics simulation
            width: Width of the visualization
            height: Height of the visualization

        Returns:
            Path to the generated HTML file
        """
        output_path = Path(output_path)

        # Find nodes within depth
        nodes_to_include = self._find_neighborhood(center_node, depth)

        if not nodes_to_include:
            logger.warning(f"No nodes found for center node: {center_node}")
            return output_path

        # Create network
        net = Network(height=height, width=width, bgcolor="#ffffff", directed=True, notebook=False)

        # Configure physics
        if physics:
            net.force_atlas_2based(
                gravity=-30, central_gravity=0.03, spring_length=80, spring_strength=0.1, damping=0.4, overlap=0
            )

        # Add nodes
        for node_name in nodes_to_include:
            node = self.store.get_node_by_name(node_name)
            if node:
                # Highlight center node
                if node_name == center_node:
                    self._add_node_to_network(net, node, highlight=True)
                else:
                    self._add_node_to_network(net, node)

        # Add relevant edges
        for rel in self.store.relationships:
            if rel.subject in nodes_to_include and rel.object in nodes_to_include:
                self._add_edge_to_network(net, rel)

        # Save
        net.save_graph(str(output_path))
        logger.info(f"Saved subgraph visualization to {output_path}")

        return output_path

    def _add_node_to_network(self, net: Network, node: UnifiedKnowledgeNode, highlight: bool = False) -> None:
        """Add a node to the network visualization."""
        node_type = node.type.lower()
        color = self.NODE_COLORS.get(node_type, self.NODE_COLORS["default"])
        shape = self.NODE_SHAPES.get(node_type, self.NODE_SHAPES["default"])

        # Create hover tooltip
        title = f"<b>{node.name}</b><br>"
        title += f"Type: {node.type}<br>"
        title += (
            f"Definition: {node.definition[:200]}...<br>"
            if len(node.definition) > 200
            else f"Definition: {node.definition}<br>"
        )
        title += f"Sources: {len(node.sources)}"

        # Adjust size based on importance or relationship count
        size = 20
        if hasattr(node, "importance"):
            size = 15 + (node.importance * 20)  # Scale from 15 to 35
        else:
            # Size based on number of relationships
            rel_count = len(node.relationships_as_subject) + len(node.relationships_as_object)
            size = min(15 + rel_count * 2, 40)  # Cap at 40

        # Highlight if requested
        if highlight:
            color = "#ffd700"  # Gold
            size *= 1.5

        net.add_node(
            node.name,
            label=node.name,
            title=title,
            color=color,
            shape=shape,
            size=size,
        )

    def _add_edge_to_network(self, net: Network, rel: Relationship) -> None:
        """Add an edge to the network visualization."""
        # Only add edge if both nodes exist
        if rel.subject in self.store.name_to_id and rel.object in self.store.name_to_id:
            # Edge weight based on confidence
            width = 1 + (rel.confidence * 2)  # Scale from 1 to 3

            # Edge color based on confidence
            if rel.confidence >= 0.8:
                color = "#2ecc71"  # Green for high confidence
            elif rel.confidence >= 0.5:
                color = "#f39c12"  # Orange for medium confidence
            else:
                color = "#e74c3c"  # Red for low confidence

            net.add_edge(
                rel.subject,
                rel.object,
                label=rel.predicate,
                title=f"{rel.predicate} (confidence: {rel.confidence:.2f})",
                width=width,
                color=color,
                arrows="to",
            )

    def _find_neighborhood(self, center_node: str, depth: int) -> set[str]:
        """
        Find all nodes within a certain depth from a center node.

        Args:
            center_node: Name of the center node
            depth: How many hops to traverse

        Returns:
            Set of node names in the neighborhood
        """
        if center_node not in self.store.name_to_id:
            return set()

        visited = {center_node}
        current_layer = {center_node}

        for _ in range(depth):
            next_layer = set()

            for node_name in current_layer:
                # Get relationships for this node
                relationships = self.store.get_relationships_for_node(node_name)

                for rel in relationships:
                    # Add connected nodes
                    if rel.subject == node_name and rel.object not in visited:
                        next_layer.add(rel.object)
                    elif rel.object == node_name and rel.subject not in visited:
                        next_layer.add(rel.subject)

            visited.update(next_layer)
            current_layer = next_layer

            if not current_layer:
                break

        return visited

    def generate_statistics_report(self) -> str:
        """
        Generate a text report of graph statistics.

        Returns:
            Formatted statistics report
        """
        stats = self.store.get_statistics()

        report = "Knowledge Graph Statistics\n"
        report += "=" * 40 + "\n\n"
        report += f"Total Nodes: {stats['total_nodes']}\n"
        report += f"Total Relationships: {stats['total_relationships']}\n"
        report += f"Total Sources: {stats['total_sources']}\n"
        report += f"Average Relationships per Node: {stats['average_relationships_per_node']:.2f}\n\n"

        report += "Nodes by Type:\n"
        for node_type, count in stats["nodes_by_type"].items():
            report += f"  {node_type}: {count}\n"

        # Find most connected nodes
        report += "\nMost Connected Nodes:\n"
        node_connections = []
        for node in self.store.nodes.values():
            connection_count = len(node.relationships_as_subject) + len(node.relationships_as_object)
            node_connections.append((node.name, connection_count))

        node_connections.sort(key=lambda x: x[1], reverse=True)
        for name, count in node_connections[:10]:
            report += f"  {name}: {count} connections\n"

        return report
