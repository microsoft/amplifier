"""
Tension Detector - Identifies contradictions and divergent ideas.
Finds semantic tensions between concepts across articles.
"""

from typing import Any


class TensionDetector:
    """Detects contradictions, tensions, and divergent perspectives."""

    def __init__(self):
        """Initialize tension detector with contradiction patterns."""
        # Contradictory relationship predicates
        self.opposing_predicates = {
            "enables": ["prevents", "blocks", "inhibits"],
            "increases": ["decreases", "reduces", "diminishes"],
            "supports": ["opposes", "contradicts", "challenges"],
            "requires": ["eliminates", "removes", "excludes"],
            "improves": ["worsens", "degrades", "harms"],
            "accelerates": ["slows", "delays", "hinders"],
            "simplifies": ["complicates", "complexifies"],
            "centralizes": ["decentralizes", "distributes"],
            "automates": ["manualizes", "requires human"],
        }

        # Add reverse mappings
        for key, values in list(self.opposing_predicates.items()):
            for value in values:
                if value not in self.opposing_predicates:
                    self.opposing_predicates[value] = [key]

    def find_tensions(self, window: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Find tensions and contradictions in article window.

        Contract: window of articles -> list of tensions

        Args:
            window: List of article extractions

        Returns:
            List of tension dictionaries
        """
        tensions = []

        # Find relationship contradictions
        rel_tensions = self._find_relationship_tensions(window)
        tensions.extend(rel_tensions)

        # Find insight contradictions
        insight_tensions = self._find_insight_tensions(window)
        tensions.extend(insight_tensions)

        # Find pattern conflicts
        pattern_tensions = self._find_pattern_tensions(window)
        tensions.extend(pattern_tensions)

        return tensions

    def _find_relationship_tensions(self, window: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find contradictory relationships."""
        tensions = []
        relationships_by_pair = {}

        # Collect all relationships by subject-object pair
        for article in window:
            source_id = article.get("source_id", "unknown")

            for rel in article.get("relationships", []):
                subject = rel.get("subject", "")
                predicate = rel.get("predicate", "").lower()
                obj = rel.get("object", "")

                if not all([subject, predicate, obj]):
                    continue

                # Create normalized pair key
                pair_key = (subject.lower(), obj.lower())

                if pair_key not in relationships_by_pair:
                    relationships_by_pair[pair_key] = []

                relationships_by_pair[pair_key].append(
                    {"predicate": predicate, "source": source_id, "confidence": rel.get("confidence", 0.5)}
                )

        # Find contradictions
        for (subject, obj), rels in relationships_by_pair.items():
            predicates = [r["predicate"] for r in rels]

            # Check for opposing predicates
            for pred in predicates:
                if pred in self.opposing_predicates:
                    opposites = self.opposing_predicates[pred]
                    conflicts = [r for r in rels if r["predicate"] in opposites]

                    if conflicts:
                        original = [r for r in rels if r["predicate"] == pred]
                        tensions.append(
                            {
                                "type": "relationship_contradiction",
                                "subject": subject,
                                "object": obj,
                                "assertion": pred,
                                "contradiction": conflicts[0]["predicate"],
                                "sources": [original[0]["source"], conflicts[0]["source"]],
                                "severity": self._calculate_severity(
                                    original[0].get("confidence", 0.5), conflicts[0].get("confidence", 0.5)
                                ),
                            }
                        )

        return tensions

    def _find_insight_tensions(self, window: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find contradictory insights."""
        tensions = []

        # Collect insights with semantic opposites
        all_insights = []
        for article in window:
            source_id = article.get("source_id", "unknown")
            for insight in article.get("insights", []):
                if insight:
                    all_insights.append({"text": insight.lower(), "source": source_id})

        # Simple contradiction detection based on keywords
        contradiction_patterns = [
            ("increases", "decreases"),
            ("improves", "worsens"),
            ("essential", "unnecessary"),
            ("critical", "optional"),
            ("must", "must not"),
            ("always", "never"),
            ("all", "none"),
        ]

        for i, insight1 in enumerate(all_insights):
            for insight2 in all_insights[i + 1 :]:
                # Check if insights contradict
                for pos_word, neg_word in contradiction_patterns:
                    if (pos_word in insight1["text"] and neg_word in insight2["text"]) or (
                        neg_word in insight1["text"] and pos_word in insight2["text"]
                    ):
                        # Check if they're about similar topics (share words)
                        words1 = set(insight1["text"].split())
                        words2 = set(insight2["text"].split())
                        overlap = words1 & words2

                        if len(overlap) > 2:  # At least 2 common words
                            tensions.append(
                                {
                                    "type": "insight_contradiction",
                                    "insight1": insight1["text"],
                                    "insight2": insight2["text"],
                                    "sources": [insight1["source"], insight2["source"]],
                                    "common_topics": list(overlap)[:5],
                                    "severity": 0.7,
                                }
                            )
                            break

        return tensions

    def _find_pattern_tensions(self, window: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find conflicting patterns."""
        tensions = []
        pattern_map = {}

        # Collect patterns by similar names
        for article in window:
            source_id = article.get("source_id", "unknown")

            for pattern in article.get("patterns", []):
                name = pattern.get("name", "").lower()
                if name:
                    if name not in pattern_map:
                        pattern_map[name] = []

                    pattern_map[name].append({"description": pattern.get("description", ""), "source": source_id})

        # Find patterns with conflicting descriptions
        conflict_keywords = [
            ("centralized", "decentralized"),
            ("synchronous", "asynchronous"),
            ("stateful", "stateless"),
            ("monolithic", "microservice"),
            ("push", "pull"),
            ("real-time", "batch"),
        ]

        for pattern_name, implementations in pattern_map.items():
            if len(implementations) > 1:
                for i, impl1 in enumerate(implementations):
                    for impl2 in implementations[i + 1 :]:
                        desc1 = impl1["description"].lower()
                        desc2 = impl2["description"].lower()

                        for word1, word2 in conflict_keywords:
                            if (word1 in desc1 and word2 in desc2) or (word2 in desc1 and word1 in desc2):
                                tensions.append(
                                    {
                                        "type": "pattern_conflict",
                                        "pattern": pattern_name,
                                        "approach1": word1 if word1 in desc1 else word2,
                                        "approach2": word2 if word2 in desc2 else word1,
                                        "sources": [impl1["source"], impl2["source"]],
                                        "severity": 0.6,
                                    }
                                )
                                break

        return tensions

    def _calculate_severity(self, conf1: float, conf2: float) -> float:
        """Calculate tension severity based on confidence scores."""
        # Higher severity when both assertions are confident
        return (conf1 + conf2) / 2
