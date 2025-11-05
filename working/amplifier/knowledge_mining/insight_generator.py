#!/usr/bin/env python3
"""
Insight Generator - Generate actionable insights from patterns and knowledge.
"""

from dataclasses import dataclass

from .knowledge_store import KnowledgeNode
from .knowledge_store import KnowledgeStore
from .pattern_finder import Pattern


@dataclass
class Insight:
    """An actionable insight derived from patterns"""

    type: str  # solution, recommendation, warning, opportunity
    title: str
    description: str
    supporting_evidence: list[str]
    applicable_contexts: list[str]
    confidence: float
    action_items: list[str]


class InsightGenerator:
    """Generate actionable insights from stored knowledge and patterns"""

    def __init__(self, store: KnowledgeStore):
        self.store = store

    def generate_insights(self, patterns: list[Pattern], context: str = "") -> list[Insight]:
        """Generate insights from patterns"""
        insights = []

        # Generate different types of insights
        insights.extend(self._generate_solution_insights(patterns))
        insights.extend(self._generate_recommendation_insights(patterns))
        insights.extend(self._generate_warning_insights(patterns))
        insights.extend(self._generate_opportunity_insights(patterns))

        # Filter by context if provided
        if context:
            insights = self._filter_by_context(insights, context)

        # Sort by confidence
        return sorted(insights, key=lambda i: i.confidence, reverse=True)

    def _generate_solution_insights(self, patterns: list[Pattern]) -> list[Insight]:
        """Generate solution-type insights from patterns"""
        insights = []

        for pattern in patterns:
            if pattern.pattern_type == "technique_combination":
                # Techniques used together suggest solutions
                insight = Insight(
                    type="solution",
                    title=f"Combine {pattern.concepts_involved[0]} with {pattern.concepts_involved[1]}",
                    description=f"These techniques are frequently used together successfully. {pattern.description}",
                    supporting_evidence=[f"Pattern strength: {pattern.strength:.2f}"]
                    + [occ["context"] for occ in pattern.occurrences[:3]],
                    applicable_contexts=self._identify_contexts(pattern),
                    confidence=pattern.strength,
                    action_items=[
                        f"Implement {pattern.concepts_involved[0]}",
                        f"Integrate with {pattern.concepts_involved[1]}",
                        "Test the combination",
                    ],
                )
                insights.append(insight)

        return insights

    def _generate_recommendation_insights(self, patterns: list[Pattern]) -> list[Insight]:
        """Generate recommendation insights from patterns"""
        insights = []

        for pattern in patterns:
            if pattern.pattern_type == "recurring_concept" and pattern.strength > 0.5:
                insight = Insight(
                    type="recommendation",
                    title=f"Focus on {pattern.concepts_involved[0]}",
                    description=f"This concept appears frequently across sources. {pattern.description}",
                    supporting_evidence=[f"Appears in {len(pattern.occurrences)} sources"],
                    applicable_contexts=["general", "architecture", "design"],
                    confidence=pattern.strength,
                    action_items=[
                        f"Study {pattern.concepts_involved[0]} in depth",
                        "Apply to current project",
                        "Document learnings",
                    ],
                )
                insights.append(insight)

        return insights

    def _generate_warning_insights(self, patterns: list[Pattern]) -> list[Insight]:
        """Generate warning insights from patterns"""
        insights = []

        # Look for anti-patterns or problematic combinations
        for pattern in patterns:
            if pattern.pattern_type == "concept_cluster" and len(pattern.concepts_involved) > 5:
                # Check for complexity indicators
                insight = Insight(
                    type="warning",
                    title=f"High complexity around {pattern.concepts_involved[0]}",
                    description="This area shows high conceptual complexity with many interconnected concepts.",
                    supporting_evidence=[f"{len(pattern.concepts_involved)} related concepts"],
                    applicable_contexts=["architecture", "refactoring"],
                    confidence=0.7,
                    action_items=[
                        "Review for simplification opportunities",
                        "Consider breaking into smaller components",
                        "Document complexity reasons",
                    ],
                )
                insights.append(insight)

        return insights

    def _generate_opportunity_insights(self, patterns: list[Pattern]) -> list[Insight]:
        """Generate opportunity insights from patterns"""
        insights = []

        for pattern in patterns:
            if pattern.pattern_type == "principle_application" and len(pattern.concepts_involved) > 3:
                # Principles with multiple applications suggest opportunities
                insight = Insight(
                    type="opportunity",
                    title=f"Leverage {pattern.concepts_involved[0]} broadly",
                    description=f"This principle has proven applications in multiple areas. {pattern.description}",
                    supporting_evidence=[f"Applied to: {', '.join(pattern.concepts_involved[1:4])}"],
                    applicable_contexts=self._identify_contexts(pattern),
                    confidence=pattern.strength,
                    action_items=[
                        f"Identify where {pattern.concepts_involved[0]} applies",
                        "Create implementation plan",
                        "Measure impact",
                    ],
                )
                insights.append(insight)

        return insights

    def _identify_contexts(self, pattern: Pattern) -> list[str]:
        """Identify applicable contexts for a pattern"""
        contexts = []

        # Heuristic context identification
        concept_text = " ".join(pattern.concepts_involved).lower()

        if any(word in concept_text for word in ["api", "service", "endpoint"]):
            contexts.append("api_design")
        if any(word in concept_text for word in ["test", "testing", "qa"]):
            contexts.append("testing")
        if any(word in concept_text for word in ["pattern", "architecture", "design"]):
            contexts.append("architecture")
        if any(word in concept_text for word in ["data", "database", "storage"]):
            contexts.append("data_management")
        if any(word in concept_text for word in ["async", "concurrent", "parallel"]):
            contexts.append("concurrency")

        return contexts if contexts else ["general"]

    def _filter_by_context(self, insights: list[Insight], context: str) -> list[Insight]:
        """Filter insights by context relevance"""
        filtered = []
        context_lower = context.lower()

        for insight in insights:
            # Check if context matches any applicable context
            if (
                any(context_lower in ctx.lower() for ctx in insight.applicable_contexts)
                or context_lower in insight.description.lower()
                or context_lower in insight.title.lower()
            ):
                filtered.append(insight)

        return filtered

    def generate_problem_insights(self, problem_description: str) -> list[Insight]:
        """Generate insights relevant to a specific problem"""
        insights = []

        # Extract key terms from problem
        key_terms = self._extract_key_terms(problem_description)

        # Query store for relevant concepts
        for term in key_terms:
            nodes = self.store.query(concept=term)
            if nodes:
                # Generate insight from found concepts
                concept_node = nodes[0]  # Primary concept
                related = nodes[1:] if len(nodes) > 1 else []

                insight = Insight(
                    type="solution",
                    title=f"Apply {concept_node.content.get('name', term)}",
                    description=concept_node.content.get("description", ""),
                    supporting_evidence=[f"From: {', '.join(concept_node.sources[:2])}"],
                    applicable_contexts=[problem_description[:50]],
                    confidence=0.6,
                    action_items=self._generate_action_items(concept_node, related),
                )
                insights.append(insight)

        return insights

    def _extract_key_terms(self, text: str) -> list[str]:
        """Extract key terms from text (simple implementation)"""
        # Simple keyword extraction
        important_words = []
        words = text.lower().split()

        # Look for technical terms (simple heuristic)
        for word in words:
            if (
                len(word) > 5
                and word.isalpha()
                and any(
                    tech in word
                    for tech in [
                        "data",
                        "api",
                        "service",
                        "pattern",
                        "design",
                        "system",
                        "process",
                        "method",
                    ]
                )
            ):
                important_words.append(word)

        return list(set(important_words))[:5]

    def _generate_action_items(self, concept_node: KnowledgeNode, related_nodes: list[KnowledgeNode]) -> list[str]:
        """Generate action items from concept nodes"""
        actions = []

        # Based on concept type
        if concept_node.type == "concept":
            category = concept_node.metadata.get("category", "")
            if category == "pattern":
                actions.append(f"Implement the {concept_node.content.get('name')} pattern")
            elif category == "technique":
                actions.append(f"Apply the {concept_node.content.get('name')} technique")
            elif category == "principle":
                actions.append(f"Follow the {concept_node.content.get('name')} principle")
            else:
                actions.append(f"Research {concept_node.content.get('name')}")

        # Add related actions
        for node in related_nodes[:2]:
            if node.type == "code":
                actions.append(f"Review code example in {node.metadata.get('language', 'unknown')}")
            elif node.type == "insight":
                actions.append("Consider related insight")

        return actions if actions else ["Investigate further", "Create proof of concept"]


if __name__ == "__main__":
    # Test insight generation
    from .knowledge_extractor import KnowledgeExtractor
    from .pattern_finder import PatternFinder

    # Create components
    store = KnowledgeStore()
    extractor = KnowledgeExtractor()
    finder = PatternFinder()
    generator = InsightGenerator(store)

    # Sample content
    sample = """
    # Microservices Best Practices

    The principle of single responsibility is crucial. Each microservice should do one thing well.
    The repository pattern provides clean data access. Use async communication between services.
    Remember that testing is essential for microservices.
    """

    # Extract and find patterns
    extraction = extractor.extract(sample, "Microservices", "micro.md")
    store.add_extraction(extraction)
    finder.add_extraction(extraction)
    patterns = finder.find_patterns(min_occurrences=1)

    # Generate insights
    insights = generator.generate_insights(patterns)

    print(f"Generated {len(insights)} insights:\n")
    for insight in insights[:3]:
        print(f"Type: {insight.type}")
        print(f"Title: {insight.title}")
        print(f"Description: {insight.description}")
        print(f"Confidence: {insight.confidence:.2f}")
        print(f"Actions: {', '.join(insight.action_items[:2])}")
        print()
