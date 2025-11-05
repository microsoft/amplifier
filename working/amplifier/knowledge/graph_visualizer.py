#!/usr/bin/env python3
"""
Interactive graph visualizer for knowledge synthesis system.
Creates beautiful, explorable HTML visualizations using PyVis.
Following visualization architecture principles - making knowledge visible.
"""

import json
import logging
from pathlib import Path

import networkx as nx
from pyvis.network import Network

from amplifier.config.paths import paths

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Interactive visualizer for knowledge graphs."""

    def __init__(self, graph: nx.MultiDiGraph | None = None):
        """Initialize with optional graph."""
        self.graph = graph
        self.filtered_graph = None

    def create_visualization(
        self,
        graph: nx.MultiDiGraph | None = None,
        output_path: Path | None = None,
        importance_threshold: float = 0.0,
        max_nodes: int = 500,
    ) -> Path:
        """
        Create interactive HTML visualization of the graph.

        Args:
            graph: NetworkX graph to visualize (uses self.graph if None)
            output_path: Where to save the HTML file
            importance_threshold: Min PageRank/importance to include node
            max_nodes: Maximum number of nodes to display

        Returns:
            Path to the created HTML file
        """
        if graph is not None:
            self.graph = graph
        if self.graph is None:
            raise ValueError("No graph to visualize")

        if output_path is None:
            output_path = paths.data_dir / "knowledge" / "graph.html"

        # Filter graph by importance
        self.filtered_graph = self.filter_by_importance(self.graph, importance_threshold, max_nodes)

        # Create PyVis network
        net = Network(
            height="900px",
            width="100%",
            bgcolor="#1a1a1a",
            font_color="white",  # type: ignore[arg-type]
            directed=True,
            notebook=False,
            cdn_resources="in_line",  # Makes HTML standalone
        )

        # Configure physics for natural clustering
        self.configure_physics(net)

        # Add nodes with visual properties
        self.add_nodes_with_properties(net, self.filtered_graph)

        # Add edges with visual properties
        self.add_edges_with_properties(net, self.filtered_graph)

        # Apply community detection and coloring
        self.apply_community_colors(net, self.filtered_graph)

        # Configure interaction options
        net.set_options("""
        {
            "interaction": {
                "hover": true,
                "navigationButtons": true,
                "keyboard": {"enabled": true},
                "tooltipDelay": 100,
                "zoomView": true,
                "dragView": true
            },
            "nodes": {"font": {"size": 12}},
            "edges": {"font": {"size": 10, "strokeWidth": 0, "color": "#888888"}},
            "physics": {
                "enabled": true,
                "stabilization": {
                    "enabled": true,
                    "iterations": 100
                }
            }
        }
        """)

        # Generate HTML
        output_path.parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(str(output_path))

        # Enhance HTML with custom search
        self._enhance_html_with_search(output_path)

        logger.info(f"Created visualization with {self.filtered_graph.number_of_nodes()} nodes at {output_path}")
        return output_path

    def filter_by_importance(
        self, graph: nx.MultiDiGraph, threshold: float = 0.0, max_nodes: int = 500
    ) -> nx.MultiDiGraph:
        """
        Filter graph to show only important nodes.

        Uses PageRank or degree centrality to determine importance.
        """
        # Calculate importance scores
        importance = {}
        for node in graph.nodes():
            # Use PageRank if available, otherwise degree centrality
            pagerank = graph.nodes[node].get("pagerank", 0)
            centrality = graph.nodes[node].get("degree_centrality", 0)
            node_importance = max(pagerank, centrality)
            importance[node] = node_importance

        # Sort by importance and take top N
        sorted_nodes = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        filtered_nodes = [node for node, imp in sorted_nodes if imp >= threshold][:max_nodes]

        # Create subgraph with filtered nodes
        filtered_graph = graph.subgraph(filtered_nodes).copy()

        # Ensure we return a MultiDiGraph
        if not isinstance(filtered_graph, nx.MultiDiGraph):
            filtered_graph = nx.MultiDiGraph(filtered_graph)

        return filtered_graph

    def configure_physics(self, net: Network):
        """Configure force-directed layout for natural clustering."""
        net.force_atlas_2based(
            gravity=-50,
            central_gravity=0.01,
            spring_length=150,
            spring_strength=0.08,
            damping=0.4,
            overlap=0,
        )

    def add_nodes_with_properties(self, net: Network, graph: nx.MultiDiGraph):
        """Add nodes with visual properties based on their attributes."""
        for node in graph.nodes():
            node_data = graph.nodes[node]

            # Calculate size based on importance
            pagerank = node_data.get("pagerank", 0.001)
            centrality = node_data.get("degree_centrality", 0.001)
            size = max(10, min(50, pagerank * 5000 + centrality * 100))

            # Determine node type and color
            node_type = node_data.get("type", "entity")
            if node_type == "tension":
                color = "#FF5252"  # Red for tensions - productive contradictions
                shape = "star"
                size = max(15, min(60, node_data.get("productivity_score", 0.5) * 80))  # Size by productivity
            elif node_type == "concept":
                color = "#4CAF50"  # Green for concepts
                shape = "dot"
            elif "source_" in str(node):
                color = "#2196F3"  # Blue for sources
                shape = "square"
            else:
                color = "#FFA726"  # Orange for entities
                shape = "dot"

            # Build hover text
            description = node_data.get("description", "")
            importance_val = node_data.get("importance", 0)
            hover_text = f"<b>{node}</b><br>"
            if description:
                hover_text += f"<i>{description[:200]}</i><br>"
            hover_text += f"PageRank: {pagerank:.4f}<br>"
            hover_text += f"Centrality: {centrality:.3f}<br>"
            hover_text += f"Importance: {importance_val:.2f}"

            # Add node to network
            net.add_node(
                node,
                label=str(node)[:30],  # Truncate long labels
                title=hover_text,
                size=size,
                color=color,
                shape=shape,
                font={"size": max(8, min(16, size / 3))},
            )

    def add_edges_with_properties(self, net: Network, graph: nx.MultiDiGraph):
        """Add edges with visual properties based on their attributes."""
        for u, v, data in graph.edges(data=True):
            # Determine edge properties
            relation = data.get("relation", data.get("predicate", "related"))
            weight = data.get("weight", data.get("confidence", 0.5))

            # Set edge color and style based on relation type
            if relation == "mentions":
                color = "#666666"
                dashes = True
            elif relation == "co-occurs":
                color = "#888888"
                dashes = [5, 10]
            else:
                color = "#AAAAAA"
                dashes = False

            # Edge thickness based on weight
            width = max(1, min(5, weight * 5))

            # Add edge to network
            net.add_edge(
                u,
                v,
                title=f"{relation} (w: {weight:.2f})",
                label=relation if relation not in ["mentions", "co-occurs"] else "",
                color=color,
                width=width,
                dashes=dashes,
                arrows={"to": {"enabled": True, "scaleFactor": 0.5}},
            )

    def apply_community_colors(self, net: Network, graph: nx.MultiDiGraph):
        """Detect communities and apply colors to show clustering."""
        try:
            # Convert to undirected for community detection
            undirected = graph.to_undirected()

            # Detect communities using Louvain method
            import community.community_louvain as community_louvain  # type: ignore[import-not-found]

            communities = community_louvain.best_partition(undirected)

            # Color palette for communities
            colors = [
                "#FF6B6B",
                "#4ECDC4",
                "#45B7D1",
                "#96CEB4",
                "#FFA07A",
                "#DDA0DD",
                "#98D8C8",
                "#FFD700",
                "#87CEEB",
                "#F0E68C",
            ]

            # Apply community colors
            for node_id in net.get_nodes():
                if node_id in communities:
                    community_id = communities[node_id]
                    color = colors[community_id % len(colors)]
                    net.get_node(node_id)["color"] = color

            logger.info(f"Detected {len(set(communities.values()))} communities")

        except ImportError:
            logger.warning("python-louvain not installed, skipping community detection")
        except Exception as e:
            logger.warning(f"Community detection failed: {e}")

    def _enhance_html_with_search(self, html_path: Path):
        """Add custom search functionality to the HTML."""
        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()

        # Add custom search box and highlighting script
        search_script = """
        <style>
            #search-box {
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 1000;
                background: rgba(26, 26, 26, 0.9);
                padding: 10px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            }
            #search-input {
                padding: 8px;
                width: 250px;
                border: 1px solid #444;
                border-radius: 3px;
                background: #2a2a2a;
                color: white;
                font-size: 14px;
            }
            #search-input::placeholder {
                color: #888;
            }
        </style>
        <div id="search-box">
            <input type="text" id="search-input" placeholder="Search concepts...">
        </div>
        <script>
            document.getElementById('search-input').addEventListener('input', function(e) {
                const searchTerm = e.target.value.toLowerCase();
                if (searchTerm.length > 0) {
                    // Highlight matching nodes
                    network.selectNodes(
                        network.body.data.nodes.get().filter(node =>
                            node.label.toLowerCase().includes(searchTerm)
                        ).map(node => node.id)
                    );
                } else {
                    // Clear selection
                    network.unselectAll();
                }
            });
        </script>
        """

        # Insert before closing body tag
        html_content = html_content.replace("</body>", search_script + "</body>")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def export_json(self, output_path: Path):
        """Export filtered graph as JSON for custom visualizations."""
        if self.filtered_graph is None:
            raise ValueError("No filtered graph to export")

        # Convert to node-link format
        data = nx.node_link_data(self.filtered_graph)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported graph data to {output_path}")


def main():
    """CLI for creating graph visualizations."""
    import argparse

    from .graph_builder import GraphBuilder

    parser = argparse.ArgumentParser(description="Create interactive graph visualization")
    parser.add_argument(
        "--input", type=Path, default=None, help="Path to extractions JSONL (defaults to configured data directory)"
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Output HTML path (defaults to configured data directory)"
    )
    parser.add_argument("--threshold", type=float, default=0.0, help="Minimum importance threshold")
    parser.add_argument("--max-nodes", type=int, default=500, help="Maximum nodes to display")
    parser.add_argument("--export-json", type=Path, help="Export graph data as JSON")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Build graph
    logger.info("Building knowledge graph...")
    input_path = args.input or (paths.data_dir / "knowledge" / "extractions.jsonl")
    builder = GraphBuilder(input_path)
    graph = builder.build_graph()

    # Create visualization
    logger.info("Creating visualization...")
    visualizer = GraphVisualizer(graph)
    output_path = args.output or (paths.data_dir / "knowledge" / "graph.html")
    output_path = visualizer.create_visualization(
        output_path=output_path,
        importance_threshold=args.threshold,
        max_nodes=args.max_nodes,
    )

    # Export JSON if requested
    if args.export_json:
        visualizer.export_json(args.export_json)

    logger.info(f"Visualization created: {output_path}")
    print(f"\nOpen {output_path} in your browser to explore the knowledge graph!")


if __name__ == "__main__":
    main()
