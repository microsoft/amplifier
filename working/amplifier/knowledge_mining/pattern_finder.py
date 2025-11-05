#!/usr/bin/env python3
"""
Pattern Finder - Find connections and patterns across multiple articles.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from .knowledge_extractor import Extraction


@dataclass
class Pattern:
    """A discovered pattern across articles"""

    pattern_type: str  # recurring_concept, technique_combination, principle_application
    description: str
    occurrences: list[dict[str, str]]  # [{source, context}]
    strength: float  # 0-1 confidence/frequency
    concepts_involved: list[str]


@dataclass
class ConceptCluster:
    """A cluster of related concepts"""

    core_concept: str
    related_concepts: list[str]
    shared_contexts: list[str]
    frequency: int


class PatternFinder:
    """Find patterns and connections across extracted knowledge"""

    def __init__(self):
        self.concept_graph = defaultdict(set)  # concept -> related concepts
        self.concept_sources = defaultdict(list)  # concept -> sources
        self.co_occurrences = defaultdict(int)  # (concept1, concept2) -> count

    def add_extraction(self, extraction: Extraction):
        """Add an extraction to the pattern finder"""

        # Track concept sources
        for concept in extraction.concepts:
            self.concept_sources[concept.name].append(extraction.source)

        # Build concept graph from relationships
        for rel in extraction.relationships:
            # Access Relationship object attributes
            self.concept_graph[rel.source].add(rel.target)
            self.concept_graph[rel.target].add(rel.source)

            # Track co-occurrences
            pair = tuple(sorted([rel.source, rel.target]))
            self.co_occurrences[pair] += 1

    def find_patterns(self, min_occurrences: int = 2) -> list[Pattern]:
        """Find patterns across all added extractions"""
        patterns = []

        # Find recurring concepts
        recurring = self._find_recurring_concepts(min_occurrences)
        patterns.extend(recurring)

        # Find concept clusters
        clusters = self._find_concept_clusters()
        patterns.extend(self._clusters_to_patterns(clusters))

        # Find technique combinations
        combinations = self._find_technique_combinations()
        patterns.extend(combinations)

        # Find principle applications
        applications = self._find_principle_applications()
        patterns.extend(applications)

        return sorted(patterns, key=lambda p: p.strength, reverse=True)

    def _find_recurring_concepts(self, min_occurrences: int) -> list[Pattern]:
        """Find concepts that appear across multiple sources"""
        patterns = []

        for concept, sources in self.concept_sources.items():
            if len(sources) >= min_occurrences:
                unique_sources = list(set(sources))
                patterns.append(
                    Pattern(
                        pattern_type="recurring_concept",
                        description=f"'{concept}' appears across {len(unique_sources)} sources",
                        occurrences=[{"source": s, "context": concept} for s in unique_sources],
                        strength=min(1.0, len(unique_sources) / 10),  # Normalize to 0-1
                        concepts_involved=[concept],
                    )
                )

        return patterns

    def _find_concept_clusters(self) -> list[ConceptCluster]:
        """Find clusters of frequently co-occurring concepts"""
        clusters = []
        processed = set()

        for concept, related in self.concept_graph.items():
            if concept in processed or len(related) < 2:
                continue

            # Find strongly connected concepts
            cluster_concepts = {concept}
            for rel in related:
                # Check if this concept is strongly connected
                if rel in self.concept_graph and concept in self.concept_graph[rel]:
                    cluster_concepts.add(rel)

            if len(cluster_concepts) >= 3:
                cluster = ConceptCluster(
                    core_concept=concept,
                    related_concepts=list(cluster_concepts - {concept}),
                    shared_contexts=self.concept_sources.get(concept, []),
                    frequency=len(self.concept_sources.get(concept, [])),
                )
                clusters.append(cluster)
                processed.update(cluster_concepts)

        return clusters

    def _clusters_to_patterns(self, clusters: list[ConceptCluster]) -> list[Pattern]:
        """Convert concept clusters to patterns"""
        patterns = []

        for cluster in clusters:
            all_concepts = [cluster.core_concept] + cluster.related_concepts
            patterns.append(
                Pattern(
                    pattern_type="concept_cluster",
                    description=f"Cluster around '{cluster.core_concept}': {', '.join(cluster.related_concepts[:3])}",
                    occurrences=[{"source": s, "context": "cluster"} for s in cluster.shared_contexts[:5]],
                    strength=min(1.0, len(cluster.related_concepts) / 5),
                    concepts_involved=all_concepts,
                )
            )

        return patterns

    def _find_technique_combinations(self) -> list[Pattern]:
        """Find techniques that are frequently used together"""
        patterns = []
        technique_pairs = defaultdict(list)

        # Find co-occurring technique concepts
        for (c1, c2), count in self.co_occurrences.items():
            # Check if both are likely techniques (heuristic) with minimum co-occurrence
            if (
                count >= 2
                and any(word in c1 for word in ["method", "technique", "approach", "pattern", "strategy"])
                and any(word in c2 for word in ["method", "technique", "approach", "pattern", "strategy"])
            ):
                technique_pairs[(c1, c2)].append(count)

        for (tech1, tech2), counts in technique_pairs.items():
            patterns.append(
                Pattern(
                    pattern_type="technique_combination",
                    description=f"'{tech1}' frequently combined with '{tech2}'",
                    occurrences=[
                        {"source": "multiple", "context": f"co-occurred {sum(counts)} times"},
                    ],
                    strength=min(1.0, sum(counts) / 5),
                    concepts_involved=[tech1, tech2],
                )
            )

        return patterns

    def _find_principle_applications(self) -> list[Pattern]:
        """Find principles and their applications"""
        patterns = []
        principle_applications = defaultdict(set)

        # Find principles and what they're connected to
        for concept, related in self.concept_graph.items():
            if "principle" in concept.lower():
                for rel in related:
                    if "principle" not in rel.lower():
                        principle_applications[concept].add(rel)

        for principle, applications in principle_applications.items():
            if len(applications) >= 2:
                patterns.append(
                    Pattern(
                        pattern_type="principle_application",
                        description=f"Principle '{principle}' applied to: {', '.join(list(applications)[:3])}",
                        occurrences=[
                            {"source": s, "context": principle} for s in self.concept_sources.get(principle, [])[:3]
                        ],
                        strength=min(1.0, len(applications) / 5),
                        concepts_involved=[principle] + list(applications),
                    )
                )

        return patterns

    def find_related_concepts(self, concept: str, max_depth: int = 2) -> set[str]:
        """Find concepts related to a given concept up to max_depth"""
        if concept not in self.concept_graph:
            return set()

        related = set()
        to_explore = [(concept, 0)]
        visited = set()

        while to_explore:
            current, depth = to_explore.pop(0)
            if current in visited or depth > max_depth:
                continue

            visited.add(current)
            if depth > 0:  # Don't include the original concept
                related.add(current)

            if depth < max_depth:
                for neighbor in self.concept_graph.get(current, []):
                    if neighbor not in visited:
                        to_explore.append((neighbor, depth + 1))

        return related

    def get_concept_context(self, concept: str) -> dict[str, Any]:
        """Get full context for a concept"""
        return {
            "concept": concept,
            "sources": list(set(self.concept_sources.get(concept, []))),
            "related_concepts": list(self.concept_graph.get(concept, set())),
            "occurrence_count": len(self.concept_sources.get(concept, [])),
            "co_occurrences": {str(pair): count for pair, count in self.co_occurrences.items() if concept in pair},
        }


if __name__ == "__main__":
    # Test with sample extractions
    from knowledge_extractor import KnowledgeExtractor

    finder = PatternFinder()

    # Create sample extractions
    extractor = KnowledgeExtractor()

    sample1 = """
    # Microservices Architecture
    The key principle of microservices is separation of concerns. This technique enables
    independent deployment and scaling. The repository pattern provides clean data access.
    """

    sample2 = """
    # Event-Driven Systems
    Event-driven architecture uses the principle of loose coupling. The repository pattern
    is essential for maintaining state. This technique enables real-time processing.
    """

    extraction1 = extractor.extract(sample1, "Article 1", "source1.md")
    extraction2 = extractor.extract(sample2, "Article 2", "source2.md")

    finder.add_extraction(extraction1)
    finder.add_extraction(extraction2)

    patterns = finder.find_patterns(min_occurrences=1)

    print(f"Found {len(patterns)} patterns\n")
    for pattern in patterns[:5]:
        print(f"Type: {pattern.pattern_type}")
        print(f"Description: {pattern.description}")
        print(f"Strength: {pattern.strength:.2f}")
        print(f"Concepts: {', '.join(pattern.concepts_involved[:3])}")
        print()
