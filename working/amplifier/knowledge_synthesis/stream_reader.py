"""
Stream Reader - Processes JSONL as a temporal knowledge stream.
Maintains sliding windows and tracks concept emergence over time.
"""

import json
from collections import Counter
from collections import deque
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from amplifier.config.paths import paths


class StreamReader:
    """Streams through knowledge extractions with sliding window tracking."""

    def __init__(self, path: Path | None = None, window_size: int = 10):
        """
        Initialize stream reader.

        Args:
            path: Path to extractions JSONL file
            window_size: Number of articles to keep in sliding window
        """
        self.path = path or paths.data_dir / "knowledge" / "extractions.jsonl"
        self.window_size = window_size
        self.window = deque(maxlen=window_size)

        # Track concept frequencies across the stream
        self.concept_freq = Counter()
        self.relationship_freq = Counter()
        self.cooccurrence_matrix = Counter()  # (concept1, concept2) -> count

    def stream_articles(self) -> Iterator[dict[str, Any]]:
        """
        Stream articles from JSONL file.

        Contract: yields article dicts one at a time

        Yields:
            Article extraction dictionaries
        """
        if not self.path.exists():
            return

        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    article = json.loads(line)
                    self._update_window(article)
                    yield article
                except json.JSONDecodeError:
                    continue

    def get_window_context(self) -> dict[str, Any]:
        """
        Get current window context for synthesis.

        Returns:
            Dictionary with window statistics and patterns
        """
        if not self.window:
            return {"window_size": 0, "concepts": {}, "relationships": {}, "cooccurrences": {}}

        # Collect concepts from window
        window_concepts = Counter()
        window_relationships = Counter()

        for article in self.window:
            for concept in article.get("concepts", []):
                name = concept.get("name", "")
                if name:
                    window_concepts[name] += 1

            for rel in article.get("relationships", []):
                triple = (rel.get("subject"), rel.get("predicate"), rel.get("object"))
                if all(triple):
                    window_relationships[triple] += 1

        return {
            "window_size": len(self.window),
            "concepts": dict(window_concepts.most_common(20)),
            "relationships": dict(window_relationships.most_common(10)),
            "cooccurrences": dict(self.cooccurrence_matrix.most_common(10)),
            "temporal_order": [a.get("source_id") for a in self.window],
        }

    def find_emerging_concepts(self, threshold: float = 0.3) -> list[str]:
        """
        Find concepts emerging in recent window vs overall.

        Args:
            threshold: Minimum frequency increase ratio

        Returns:
            List of emerging concept names
        """
        if not self.window:
            return []

        # Count recent concepts
        recent_concepts = Counter()
        for article in list(self.window)[-3:]:  # Last 3 articles
            for concept in article.get("concepts", []):
                name = concept.get("name", "")
                if name:
                    recent_concepts[name] += 1

        # Find concepts with increased frequency
        emerging = []
        for concept, recent_count in recent_concepts.items():
            overall_freq = self.concept_freq.get(concept, 0)
            if overall_freq > 0:
                increase_ratio = recent_count / (overall_freq / max(len(self.window), 1))
                if increase_ratio > (1 + threshold):
                    emerging.append(concept)

        return emerging

    def _update_window(self, article: dict[str, Any]) -> None:
        """Update sliding window and statistics."""
        self.window.append(article)

        # Update concept frequencies
        concepts_in_article = []
        for concept in article.get("concepts", []):
            name = concept.get("name", "")
            if name:
                self.concept_freq[name] += 1
                concepts_in_article.append(name)

        # Update co-occurrence matrix
        for i, c1 in enumerate(concepts_in_article):
            for c2 in concepts_in_article[i + 1 :]:
                # Store in sorted order for consistency
                pair = tuple(sorted([c1, c2]))
                self.cooccurrence_matrix[pair] += 1

        # Update relationship frequencies
        for rel in article.get("relationships", []):
            triple = (rel.get("subject"), rel.get("predicate"), rel.get("object"))
            if all(triple):
                self.relationship_freq[triple] += 1
