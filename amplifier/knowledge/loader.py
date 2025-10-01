"""Knowledge loader for persistent storage access."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class KnowledgeLoader:
    """Loads and provides access to extracted knowledge."""

    def __init__(self, knowledge_dir: Path | None = None):
        """Initialize the knowledge loader.

        Args:
            knowledge_dir: Directory containing knowledge files.
                         Defaults to amplifier/data/knowledge
        """
        if knowledge_dir is None:
            # Default to amplifier data directory
            self.knowledge_dir = Path(__file__).parent.parent / "data" / "knowledge"
        else:
            self.knowledge_dir = Path(knowledge_dir)

        self.knowledge_data: dict[str, Any] = {}
        self.synthesis_report: str = ""
        self._loaded = False

    def load(self) -> None:
        """Load knowledge from persistent storage."""
        if self._loaded:
            return

        # Load knowledge JSON
        knowledge_file = self.knowledge_dir / "principles_knowledge.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file, encoding="utf-8") as f:
                    self.knowledge_data = json.load(f)
                logger.info(f"Loaded knowledge from {knowledge_file}")
            except Exception as e:
                logger.error(f"Failed to load knowledge: {e}")
                self.knowledge_data = {}
        else:
            logger.warning(f"Knowledge file not found: {knowledge_file}")
            self.knowledge_data = {}

        # Load synthesis report
        report_file = self.knowledge_dir / "synthesis_report.md"
        if report_file.exists():
            try:
                self.synthesis_report = report_file.read_text(encoding="utf-8")
                logger.info(f"Loaded synthesis report from {report_file}")
            except Exception as e:
                logger.error(f"Failed to load synthesis report: {e}")
                self.synthesis_report = ""
        else:
            logger.warning(f"Report file not found: {report_file}")

        self._loaded = True

    def get_concepts(self) -> list[dict]:
        """Get all extracted concepts."""
        self.load()
        return self.knowledge_data.get("concepts", [])

    def get_patterns(self) -> list[dict]:
        """Get identified patterns."""
        self.load()
        return self.knowledge_data.get("patterns", [])

    def get_insights(self) -> list[dict]:
        """Get strategic insights."""
        self.load()
        return self.knowledge_data.get("insights", [])

    def get_knowledge_graph(self) -> dict[str, list[str]]:
        """Get the knowledge graph."""
        self.load()
        return self.knowledge_data.get("knowledge_graph", {})

    def get_statistics(self) -> dict:
        """Get knowledge statistics."""
        self.load()
        return self.knowledge_data.get("statistics", {})

    def get_synthesis_report(self) -> str:
        """Get the synthesis report."""
        self.load()
        return self.synthesis_report

    def search_concepts(self, query: str) -> list[dict]:
        """Search for concepts containing the query string.

        Args:
            query: Search query string

        Returns:
            List of matching concepts
        """
        self.load()
        query_lower = query.lower()
        concepts = self.get_concepts()

        results = []
        for concept in concepts:
            if query_lower in concept.get("name", "").lower():
                results.append(concept)

        # Sort by frequency
        results.sort(key=lambda c: c.get("frequency", 0), reverse=True)
        return results

    def get_concepts_for_principles(self, principle_numbers: list[int]) -> list[dict]:
        """Get concepts related to specific principles.

        Args:
            principle_numbers: List of principle numbers

        Returns:
            List of relevant concepts
        """
        self.load()
        concepts = self.get_concepts()
        principle_set = set(principle_numbers)

        results = []
        for concept in concepts:
            concept_principles = set(concept.get("principle_numbers", []))
            if concept_principles & principle_set:  # Has intersection
                results.append(concept)

        # Sort by frequency
        results.sort(key=lambda c: c.get("frequency", 0), reverse=True)
        return results

    def get_graph_neighbors(self, node: str) -> list[str]:
        """Get neighbors of a node in the knowledge graph.

        Args:
            node: Node identifier (concept, pattern, or principle)

        Returns:
            List of connected nodes
        """
        self.load()
        graph = self.get_knowledge_graph()
        return graph.get(node, [])

    def is_loaded(self) -> bool:
        """Check if knowledge has been loaded."""
        return self._loaded

    def reload(self) -> None:
        """Force reload of knowledge from disk."""
        self._loaded = False
        self.knowledge_data = {}
        self.synthesis_report = ""
        self.load()

    def get_summary(self) -> dict:
        """Get a summary of loaded knowledge.

        Returns:
            Dictionary with summary statistics
        """
        self.load()
        stats = self.get_statistics()

        return {
            "total_concepts": stats.get("total_concepts", 0),
            "total_patterns": stats.get("total_patterns", 0),
            "total_insights": stats.get("total_insights", 0),
            "graph_nodes": stats.get("graph_nodes", 0),
            "graph_edges": stats.get("graph_edges", 0),
            "top_concepts": stats.get("top_concepts", [])[:5],
            "loaded": self._loaded,
        }
