"""
Synthesizer - Generates new insights from cross-article patterns.
Creates synthesis across article boundaries through pattern emergence.
"""

from collections import Counter
from typing import Any


class Synthesizer:
    """Synthesizes new insights from patterns across articles."""

    def __init__(self):
        """Initialize synthesizer with synthesis patterns."""
        self.synthesis_patterns = {
            "convergence": self._find_convergence,
            "divergence": self._find_divergence,
            "evolution": self._find_evolution,
            "emergence": self._find_emergence,
            "bridge": self._find_bridges,
        }

    def synthesize(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Generate synthesis insights from patterns.

        Contract: pattern dict -> list of insights

        Args:
            patterns: Dictionary containing concepts, relationships, cooccurrences, etc.

        Returns:
            List of synthesis insight dictionaries
        """
        insights = []

        # Run each synthesis pattern
        for _pattern_name, pattern_func in self.synthesis_patterns.items():
            pattern_insights = pattern_func(patterns)
            insights.extend(pattern_insights)

        # Rank insights by novelty and importance
        insights = self._rank_insights(insights)

        return insights[:10]  # Return top 10 insights

    def _find_convergence(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find concepts converging toward common themes."""
        insights = []

        # Look for high co-occurrence patterns
        cooccurrences = patterns.get("cooccurrences", {})

        for (concept1, concept2), count in cooccurrences.items():
            if count >= 3:  # Significant co-occurrence
                insights.append(
                    {
                        "type": "convergence",
                        "insight": f"'{concept1}' and '{concept2}' frequently appear together",
                        "evidence": f"Co-occurred {count} times",
                        "concepts": [concept1, concept2],
                        "strength": min(count / 10, 1.0),
                        "actionable": f"Consider unified approach to {concept1} and {concept2}",
                    }
                )

        return insights

    def _find_divergence(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find concepts diverging into separate paths."""
        insights = []

        # Look for concepts that used to co-occur but don't anymore
        temporal_order = patterns.get("temporal_order", [])
        if len(temporal_order) < 5:
            return insights

        # Simple divergence: high-frequency concepts with low co-occurrence
        concepts = patterns.get("concepts", {})
        cooccurrences = patterns.get("cooccurrences", {})

        high_freq_concepts = [c for c, freq in concepts.items() if freq >= 3]

        for i, c1 in enumerate(high_freq_concepts):
            for c2 in high_freq_concepts[i + 1 :]:
                pair = tuple(sorted([c1, c2]))
                cooccur_count = sum(1 for (p1, p2), _ in cooccurrences.items() if pair == tuple(sorted([p1, p2])))

                if cooccur_count == 0:  # High frequency but never together
                    insights.append(
                        {
                            "type": "divergence",
                            "insight": f"'{c1}' and '{c2}' represent separate approaches",
                            "evidence": "High individual frequency but no co-occurrence",
                            "concepts": [c1, c2],
                            "strength": 0.7,
                            "actionable": f"Evaluate trade-offs between {c1} vs {c2}",
                        }
                    )

        return insights

    def _find_evolution(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find concepts evolving over time."""
        insights = []

        # Look for relationship changes
        relationships = patterns.get("relationships", {})

        # Group relationships by subject
        subject_relations = {}
        for (subj, pred, obj), count in relationships.items():
            if subj not in subject_relations:
                subject_relations[subj] = []
            subject_relations[subj].append((pred, obj, count))

        # Find subjects with multiple relationship types
        for subject, relations in subject_relations.items():
            if len(relations) >= 3:
                insights.append(
                    {
                        "type": "evolution",
                        "insight": f"'{subject}' shows complex evolution with {len(relations)} relationships",
                        "evidence": f"Connected to: {', '.join(obj for _, obj, _ in relations[:3])}",
                        "concepts": [subject],
                        "strength": min(len(relations) / 5, 1.0),
                        "actionable": f"Track the evolution of {subject} across implementations",
                    }
                )

        return insights

    def _find_emergence(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find emergent themes from multiple concepts."""
        insights = []

        # Look for clusters of related concepts
        relationships = patterns.get("relationships", {})

        # Find predicates that appear frequently
        predicate_counts = Counter()
        for (_, pred, _), count in relationships.items():
            predicate_counts[pred] += count

        # Emergent themes based on common predicates
        for predicate, count in predicate_counts.most_common(3):
            if count >= 3:
                # Find all subjects and objects for this predicate
                involved_concepts = set()
                for (subj, pred, obj), _ in relationships.items():
                    if pred == predicate:
                        involved_concepts.add(subj)
                        involved_concepts.add(obj)

                if len(involved_concepts) >= 4:
                    insights.append(
                        {
                            "type": "emergence",
                            "insight": f"Emergent pattern around '{predicate}' action",
                            "evidence": f"Involves {len(involved_concepts)} concepts",
                            "concepts": list(involved_concepts)[:5],
                            "strength": min(count / 10, 1.0),
                            "actionable": f"Design system around '{predicate}' as core operation",
                        }
                    )

        return insights

    def _find_bridges(self, patterns: dict[str, Any]) -> list[dict[str, Any]]:
        """Find concepts that bridge between domains."""
        insights = []

        # Look for concepts that connect many others
        relationships = patterns.get("relationships", {})

        # Count how many unique connections each concept has
        connection_counts = Counter()
        for (subj, _, obj), _ in relationships.items():
            connection_counts[subj] += 1
            connection_counts[obj] += 1

        # Find bridge concepts
        for concept, connections in connection_counts.most_common(5):
            if connections >= 4:
                # Find what this concept connects
                connected = set()
                for (subj, _, obj), _ in relationships.items():
                    if subj == concept:
                        connected.add(obj)
                    elif obj == concept:
                        connected.add(subj)

                if len(connected) >= 3:
                    insights.append(
                        {
                            "type": "bridge",
                            "insight": f"'{concept}' bridges {len(connected)} different areas",
                            "evidence": f"Connects: {', '.join(list(connected)[:3])}",
                            "concepts": [concept] + list(connected)[:3],
                            "strength": min(connections / 10, 1.0),
                            "actionable": f"Use {concept} as integration point",
                        }
                    )

        return insights

    def _rank_insights(self, insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank insights by importance and novelty."""
        # Simple ranking by strength and type diversity
        type_weights = {"emergence": 1.0, "bridge": 0.9, "convergence": 0.8, "evolution": 0.7, "divergence": 0.6}

        for insight in insights:
            type_weight = type_weights.get(insight["type"], 0.5)
            strength = insight.get("strength", 0.5)
            insight["score"] = type_weight * strength

        # Sort by score
        insights.sort(key=lambda x: x["score"], reverse=True)

        return insights
