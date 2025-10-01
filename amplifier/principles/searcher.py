"""Advanced search capabilities for AI-First Principles."""

import logging
import re
from collections import defaultdict
from typing import Any

from .loader import Principle
from .loader import PrincipleLoader

logger = logging.getLogger(__name__)


class PrincipleSearcher:
    """Advanced search and discovery for AI-First principles."""

    def __init__(self, loader: PrincipleLoader = None):
        """Initialize the searcher with a principle loader."""
        self.loader = loader or PrincipleLoader()
        self._build_indices()

    def _build_indices(self):
        """Build search indices for efficient querying."""
        self.keyword_index = defaultdict(set)
        self.category_index = defaultdict(set)
        self.relationship_graph = defaultdict(set)

        for principle in self.loader.get_all_principles():
            # Build keyword index
            content_lower = (principle.content or "").lower()
            words = re.findall(r"\b\w+\b", content_lower)
            for word in set(words):
                if len(word) > 3:  # Skip short words
                    self.keyword_index[word].add(principle.number)

            # Build category index
            self.category_index[principle.category].add(principle.number)

            # Build relationship graph
            for related in principle.related_principles:
                self.relationship_graph[principle.number].add(related)
                self.relationship_graph[related].add(principle.number)  # Bidirectional

    def search(
        self,
        query: str = None,
        category: str = None,
        keywords: list[str] = None,
        min_examples: int = None,
        has_checklist: bool = None,
    ) -> list[Principle]:
        """Advanced search with multiple filters."""
        results = set(self.loader.principles.keys())

        # Filter by query (searches all content)
        if query:
            query_results = set()
            query_lower = query.lower()
            for principle in self.loader.get_all_principles():
                if principle.content and query_lower in principle.content.lower():
                    query_results.add(principle.number)
            results &= query_results

        # Filter by category
        if category:
            results &= self.category_index.get(category, set())

        # Filter by keywords
        if keywords:
            keyword_results = set()
            for keyword in keywords:
                keyword_lower = keyword.lower()
                keyword_results |= self.keyword_index.get(keyword_lower, set())
            results &= keyword_results

        # Filter by minimum examples
        if min_examples is not None:
            example_results = set()
            for num in results:
                principle = self.loader.get_principle(num)
                if principle and len(principle.examples) >= min_examples:
                    example_results.add(num)
            results &= example_results

        # Filter by checklist presence
        if has_checklist is not None:
            checklist_results = set()
            for num in results:
                principle = self.loader.get_principle(num)
                if principle and bool(principle.checklist) == has_checklist:
                    checklist_results.add(num)
            results &= checklist_results

        # Convert to principle objects and sort
        principle_objects = [self.loader.get_principle(num) for num in results]
        principle_objects = [p for p in principle_objects if p is not None]
        principle_objects.sort(key=lambda p: p.number)

        return principle_objects

    def find_similar(self, principle_number: int, max_results: int = 5) -> list[Principle]:
        """Find principles similar to a given principle."""
        source = self.loader.get_principle(principle_number)
        if not source:
            return []

        # Extract keywords from source
        source_words = set()
        if source.content:
            words = re.findall(r"\b\w+\b", source.content.lower())
            source_words = {w for w in words if len(w) > 4}  # Longer words are more specific

        # Score all other principles
        scores = {}
        for principle in self.loader.get_all_principles():
            if principle.number == principle_number:
                continue

            score = 0

            # Category match
            if principle.category == source.category:
                score += 10

            # Related principles
            if principle.number in source.related_principles:
                score += 20
            if principle_number in principle.related_principles:
                score += 20

            # Keyword overlap
            if principle.content:
                principle_words = set(re.findall(r"\b\w+\b", principle.content.lower()))
                overlap = len(source_words & principle_words)
                score += min(overlap, 50)  # Cap at 50 to prevent domination

            if score > 0:
                scores[principle.number] = score

        # Sort by score and return top results
        sorted_nums = sorted(scores.keys(), key=lambda n: scores[n], reverse=True)
        similar = []
        for num in sorted_nums[:max_results]:
            principle = self.loader.get_principle(num)
            if principle:
                similar.append(principle)

        return similar

    def find_clusters(self) -> dict[str, list[int]]:
        """Find clusters of highly interconnected principles."""
        clusters = {}
        visited = set()

        def explore_cluster(start: int, cluster_name: str):
            if start in visited:
                return []

            cluster = []
            to_visit = [start]

            while to_visit:
                current = to_visit.pop()
                if current in visited:
                    continue

                visited.add(current)
                cluster.append(current)

                # Add strongly connected neighbors
                neighbors = self.relationship_graph.get(current, set())
                for neighbor in neighbors:
                    # Check if bidirectional relationship (strong connection)
                    if neighbor not in visited and current in self.relationship_graph.get(neighbor, set()):
                        to_visit.append(neighbor)

            return cluster

        # Find clusters starting from key principles
        cluster_seeds = [
            (1, "team-formation"),
            (7, "regeneration"),
            (8, "contracts"),
            (9, "testing"),
            (20, "self-modifying"),
            (26, "stateless"),
            (31, "idempotency"),
            (38, "governance"),
        ]

        for seed, name in cluster_seeds:
            if seed not in visited:
                cluster = explore_cluster(seed, name)
                if len(cluster) > 1:
                    clusters[name] = sorted(cluster)

        return clusters

    def find_learning_path(self, start_principles: list[int] = None) -> list[int]:
        """Generate a learning path through principles."""
        if start_principles is None:
            # Default starting points
            start_principles = [1, 7, 20, 38]  # One from each category

        path = []
        visited = set()
        queue = start_principles.copy()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue

            visited.add(current)
            principle = self.loader.get_principle(current)
            if not principle:
                continue

            path.append(current)

            # Add related principles to queue
            for related in principle.related_principles:
                if related not in visited:
                    queue.append(related)

        return path

    def analyze_connections(self, principle_number: int) -> dict:
        """Analyze all connections for a principle."""
        principle = self.loader.get_principle(principle_number)
        if not principle:
            return {}

        analysis = {
            "principle": principle.to_dict(),
            "direct_relations": principle.related_principles,
            "reverse_relations": [],  # Principles that reference this one
            "cluster_members": [],
            "connection_strength": {},
        }

        # Find reverse relations
        for other in self.loader.get_all_principles():
            if principle_number in other.related_principles:
                analysis["reverse_relations"].append(other.number)

        # Find cluster members
        all_connected = set(analysis["direct_relations"]) | set(analysis["reverse_relations"])
        analysis["cluster_members"] = sorted(all_connected)

        # Calculate connection strength
        for connected in all_connected:
            strength = 0
            if connected in analysis["direct_relations"]:
                strength += 1
            if connected in analysis["reverse_relations"]:
                strength += 1

            # Check for shared connections
            connected_principle = self.loader.get_principle(connected)
            if connected_principle:
                shared = set(principle.related_principles) & set(connected_principle.related_principles)
                strength += len(shared) * 0.5

            analysis["connection_strength"][connected] = strength

        return analysis

    def get_implementation_examples(self, principle_numbers: list[int]) -> dict[str, Any]:
        """Extract implementation examples from principles."""
        examples = {
            "good_examples": [],
            "bad_examples": [],
            "code_snippets": [],
            "tools_mentioned": set(),
        }

        for num in principle_numbers:
            principle = self.loader.get_principle(num)
            if not principle or not principle.content:
                continue

            # Extract good examples
            good_matches = re.findall(r"Good:.*?```python(.*?)```", principle.content, re.DOTALL)
            for code in good_matches:
                examples["good_examples"].append({"principle": num, "code": code.strip()})

            # Extract bad examples
            bad_matches = re.findall(r"Bad:.*?```python(.*?)```", principle.content, re.DOTALL)
            for code in bad_matches:
                examples["bad_examples"].append({"principle": num, "code": code.strip()})

            # Extract any code snippets
            all_code = re.findall(r"```(?:python)?(.*?)```", principle.content, re.DOTALL)
            for code in all_code:
                if code.strip():
                    examples["code_snippets"].append({"principle": num, "code": code.strip()})

            # Extract tools mentioned
            if principle.tools:
                examples["tools_mentioned"].update(principle.tools)

        examples["tools_mentioned"] = sorted(examples["tools_mentioned"])
        return examples

    def generate_summary_report(self) -> dict:
        """Generate a comprehensive summary report of all principles."""
        stats = self.loader.get_statistics()

        # Find most connected principles
        connection_counts = {}
        for num in self.loader.principles:
            principle = self.loader.get_principle(num)
            if principle:
                connection_counts[num] = len(principle.related_principles)

        most_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Find principles with most examples
        example_counts = {}
        for num in self.loader.principles:
            principle = self.loader.get_principle(num)
            if principle:
                example_counts[num] = len(principle.examples)

        most_examples = sorted(example_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Build report
        report = {
            "statistics": stats,
            "clusters": self.find_clusters(),
            "most_connected": [
                {"number": num, "name": self.loader.get_principle(num).name, "connections": count}
                for num, count in most_connected
            ],
            "most_examples": [
                {"number": num, "name": self.loader.get_principle(num).name, "examples": count}
                for num, count in most_examples
            ],
            "coverage": {
                "with_related": len([p for p in self.loader.get_all_principles() if p.related_principles]),
                "with_examples": stats["with_examples"],
                "with_checklist": stats["with_checklist"],
                "complete": stats["complete"],
            },
        }

        return report
