"""Knowledge manager for amplifier - singleton pattern for global access."""

import logging
from pathlib import Path

from .loader import KnowledgeLoader

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """Singleton knowledge manager for amplifier."""

    _instance = None
    _loader: KnowledgeLoader | None = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._loader = None
        return cls._instance

    def initialize(self, knowledge_dir: Path | None = None) -> None:
        """Initialize the knowledge manager.

        Args:
            knowledge_dir: Optional directory containing knowledge files
        """
        if self._loader is None:
            self._loader = KnowledgeLoader(knowledge_dir)
            self._loader.load()
            logger.info("Knowledge manager initialized")

    @property
    def loader(self) -> KnowledgeLoader:
        """Get the knowledge loader, initializing if needed."""
        if self._loader is None:
            self.initialize()
        return self._loader

    def get_concepts(self) -> list[dict]:
        """Get all extracted concepts."""
        return self.loader.get_concepts()

    def get_patterns(self) -> list[dict]:
        """Get identified patterns."""
        return self.loader.get_patterns()

    def get_insights(self) -> list[dict]:
        """Get strategic insights."""
        return self.loader.get_insights()

    def get_knowledge_graph(self) -> dict[str, list[str]]:
        """Get the knowledge graph."""
        return self.loader.get_knowledge_graph()

    def search_concepts(self, query: str) -> list[dict]:
        """Search for concepts containing the query string."""
        return self.loader.search_concepts(query)

    def get_concepts_for_principles(self, principle_numbers: list[int]) -> list[dict]:
        """Get concepts related to specific principles."""
        return self.loader.get_concepts_for_principles(principle_numbers)

    def get_recommendations_for_context(self, context: str) -> list[dict]:
        """Get recommendations based on context.

        Args:
            context: Context string to get recommendations for

        Returns:
            List of recommendations with concepts and principles
        """
        # Search for relevant concepts
        concepts = self.search_concepts(context)

        if not concepts:
            # Try breaking down the context
            words = context.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    concepts.extend(self.search_concepts(word))

        if not concepts:
            return []

        # Get unique principle numbers from concepts
        principle_numbers = set()
        for concept in concepts[:10]:  # Top 10 concepts
            principle_numbers.update(concept.get("principle_numbers", []))

        recommendations = []
        if concepts:
            recommendations.append(
                {
                    "title": "Relevant Concepts",
                    "type": "concepts",
                    "items": [c["name"] for c in concepts[:5]],
                    "principles": sorted(principle_numbers)[:10],
                }
            )

        # Add patterns if applicable
        patterns = self.get_patterns()
        relevant_patterns = []
        context_lower = context.lower()

        for pattern in patterns:
            pattern_name = pattern.get("name", "").lower()
            if any(word in pattern_name for word in context_lower.split()):
                relevant_patterns.append(pattern)

        if relevant_patterns:
            recommendations.append(
                {
                    "title": "Applicable Patterns",
                    "type": "patterns",
                    "items": [p["name"] for p in relevant_patterns[:3]],
                    "principles": sorted(set().union(*[set(p.get("principles", [])) for p in relevant_patterns]))[:10],
                }
            )

        return recommendations

    def get_summary(self) -> dict:
        """Get a summary of loaded knowledge."""
        return self.loader.get_summary()

    def reload(self) -> None:
        """Force reload of knowledge from disk."""
        if self._loader:
            self._loader.reload()
            logger.info("Knowledge reloaded")

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance."""
        cls._instance = None
        cls._loader = None


# Global instance for easy access
_knowledge_manager = KnowledgeManager()


def get_knowledge_manager() -> KnowledgeManager:
    """Get the global knowledge manager instance.

    Returns:
        The singleton KnowledgeManager instance
    """
    return _knowledge_manager
