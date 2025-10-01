"""Advanced knowledge extraction from AI-First Principles."""

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from .loader import PrincipleLoader

logger = logging.getLogger(__name__)


@dataclass
class Concept:
    """Represents a concept extracted from principles."""

    name: str
    principle_numbers: set[int]
    frequency: int
    context: list[str]
    category: str
    relationships: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        """Convert concept to dictionary."""
        return {
            "name": self.name,
            "principle_numbers": sorted(self.principle_numbers),
            "frequency": self.frequency,
            "category": self.category,
            "relationships": sorted(self.relationships),
            "context_samples": self.context[:3],
        }


@dataclass
class Pattern:
    """Represents a pattern found across principles."""

    name: str
    description: str
    principles: list[int]
    examples: list[str]
    anti_patterns: list[str]
    confidence: float

    def to_dict(self) -> dict:
        """Convert pattern to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "principles": self.principles,
            "examples": self.examples[:3],
            "anti_patterns": self.anti_patterns[:3],
            "confidence": self.confidence,
        }


@dataclass
class Insight:
    """Represents a synthesized insight from principles."""

    title: str
    description: str
    supporting_principles: list[int]
    evidence: list[str]
    implications: list[str]
    actionable_recommendations: list[str]

    def to_dict(self) -> dict:
        """Convert insight to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "supporting_principles": self.supporting_principles,
            "evidence": self.evidence[:3],
            "implications": self.implications,
            "recommendations": self.actionable_recommendations,
        }


class PrincipleKnowledgeExtractor:
    """Extracts deep knowledge from AI-First Principles."""

    def __init__(self, loader: PrincipleLoader = None):
        """Initialize the knowledge extractor."""
        self.loader = loader or PrincipleLoader()
        self.concepts: dict[str, Concept] = {}
        self.patterns: list[Pattern] = []
        self.insights: list[Insight] = []
        self.knowledge_graph: dict[str, set[str]] = defaultdict(set)

    def extract_all_knowledge(self) -> dict:
        """Extract comprehensive knowledge from all principles."""
        logger.info("Starting comprehensive knowledge extraction from principles")

        # Extract concepts
        self._extract_concepts()

        # Identify patterns
        self._identify_patterns()

        # Generate insights
        self._generate_insights()

        # Build knowledge graph
        self._build_knowledge_graph()

        return {
            "concepts": [c.to_dict() for c in self.concepts.values()],
            "patterns": [p.to_dict() for p in self.patterns],
            "insights": [i.to_dict() for i in self.insights],
            "knowledge_graph": self._serialize_graph(),
            "statistics": self._get_statistics(),
        }

    def _extract_concepts(self):
        """Extract key concepts from all principles."""
        # Key concept patterns to look for
        concept_patterns = [
            (r"\b(prompt\s+\w+|prompting)\b", "prompting"),
            (r"\b(context\s+\w+|contextual\s+\w+)\b", "context"),
            (r"\b(agent\s+\w+|multi-agent)\b", "agents"),
            (r"\b(memory\s+\w+|memorization)\b", "memory"),
            (r"\b(tool\s+use|function\s+calling)\b", "tools"),
            (r"\b(evaluation|testing|validation)\b", "testing"),
            (r"\b(iteration|iterative\s+\w+)\b", "iteration"),
            (r"\b(chain.?of.?thought|reasoning)\b", "reasoning"),
            (r"\b(few.?shot|zero.?shot|learning)\b", "learning"),
            (r"\b(retrieval|RAG|augment\w+)\b", "retrieval"),
            (r"\b(orchestration|coordination)\b", "orchestration"),
            (r"\b(window\s+\w+|token\s+\w+)\b", "tokens"),
            (r"\b(pattern\s+\w+|template\s+\w+)\b", "patterns"),
            (r"\b(pipeline\s+\w+|workflow\s+\w+)\b", "workflows"),
            (r"\b(framework\s+\w+|system\s+\w+)\b", "systems"),
        ]

        for principle in self.loader.get_all_principles():
            if not principle.content:
                continue

            content_lower = principle.content.lower()

            for pattern, category in concept_patterns:
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    concept_text = match.group(0).strip()

                    # Normalize concept name
                    concept_key = re.sub(r"\s+", "_", concept_text.lower())

                    if concept_key not in self.concepts:
                        self.concepts[concept_key] = Concept(
                            name=concept_text, principle_numbers=set(), frequency=0, context=[], category=category
                        )

                    self.concepts[concept_key].principle_numbers.add(principle.number)
                    self.concepts[concept_key].frequency += 1

                    # Extract context
                    start = max(0, match.start() - 50)
                    end = min(len(content_lower), match.end() + 50)
                    context = content_lower[start:end]
                    self.concepts[concept_key].context.append(context)

        logger.info(f"Extracted {len(self.concepts)} unique concepts")

    def _identify_patterns(self):
        """Identify common patterns across principles."""
        # Pattern 1: Iteration and refinement
        iteration_principles = []
        for p in self.loader.get_all_principles():
            if p.content and ("iteration" in p.content.lower() or "refinement" in p.content.lower()):
                iteration_principles.append(p.number)

        if iteration_principles:
            self.patterns.append(
                Pattern(
                    name="Iterative Refinement",
                    description="Continuous improvement through systematic iteration",
                    principles=iteration_principles,
                    examples=["Prompt iteration workflows", "A/B testing prompts", "Gradient-based optimization"],
                    anti_patterns=["One-shot solutions", "Fixed prompts without testing", "No measurement or feedback"],
                    confidence=0.9,
                )
            )

        # Pattern 2: Context management
        context_principles = []
        for p in self.loader.get_all_principles():
            if p.content and ("context" in p.content.lower() or "window" in p.content.lower()):
                context_principles.append(p.number)

        if context_principles:
            self.patterns.append(
                Pattern(
                    name="Context Optimization",
                    description="Efficient use of limited context windows",
                    principles=context_principles,
                    examples=["Semantic chunking", "Context curation pipelines", "Dynamic context selection"],
                    anti_patterns=["Context stuffing", "Random context selection", "Ignoring token limits"],
                    confidence=0.95,
                )
            )

        # Pattern 3: Multi-agent collaboration
        agent_principles = []
        for p in self.loader.get_all_principles():
            if p.content and ("agent" in p.content.lower() or "orchestration" in p.content.lower()):
                agent_principles.append(p.number)

        if agent_principles:
            self.patterns.append(
                Pattern(
                    name="Agent Orchestration",
                    description="Coordinating multiple agents for complex tasks",
                    principles=agent_principles,
                    examples=["Specialized agent roles", "Consensus mechanisms", "Hierarchical orchestration"],
                    anti_patterns=["Monolithic agents", "No agent coordination", "Circular dependencies"],
                    confidence=0.85,
                )
            )

        # Pattern 4: Evaluation and testing
        testing_principles = []
        for p in self.loader.get_all_principles():
            if p.content and ("test" in p.content.lower() or "evaluation" in p.content.lower()):
                testing_principles.append(p.number)

        if testing_principles:
            self.patterns.append(
                Pattern(
                    name="Systematic Evaluation",
                    description="Data-driven testing and validation",
                    principles=testing_principles,
                    examples=["Golden datasets", "LLM-as-judge", "Regression testing"],
                    anti_patterns=["No testing", "Subjective evaluation only", "Testing in production"],
                    confidence=0.9,
                )
            )

        logger.info(f"Identified {len(self.patterns)} patterns")

    def _generate_insights(self):
        """Generate high-level insights from principles."""
        # Insight 1: The iteration-context-evaluation triangle
        self.insights.append(
            Insight(
                title="The AI Development Triangle",
                description="Successful AI systems require balanced focus on iteration, context management, and evaluation",
                supporting_principles=[46, 53, 54, 55],
                evidence=[
                    "Principle #53 emphasizes systematic prompt iteration",
                    "Principle #54 focuses on context curation",
                    "Principle #55 provides evaluation frameworks",
                ],
                implications=[
                    "All three aspects must be addressed for robust AI systems",
                    "Neglecting any aspect leads to suboptimal performance",
                    "These form a feedback loop for continuous improvement",
                ],
                actionable_recommendations=[
                    "Implement prompt iteration workflows from day one",
                    "Build context curation pipelines before scaling",
                    "Establish evaluation metrics before deployment",
                ],
            )
        )

        # Insight 2: Modular AI architectures
        self.insights.append(
            Insight(
                title="Modular AI System Design",
                description="Complex AI systems benefit from modular, composable architectures",
                supporting_principles=[49, 50, 51, 52],
                evidence=[
                    "Tool use and function calling enable modularity",
                    "RAG systems separate retrieval from generation",
                    "Multi-agent systems distribute complexity",
                ],
                implications=[
                    "Monolithic prompts are harder to maintain",
                    "Modular systems are more testable",
                    "Specialization improves individual component performance",
                ],
                actionable_recommendations=[
                    "Break complex prompts into specialized agents",
                    "Implement tool use for external capabilities",
                    "Use RAG for knowledge-intensive tasks",
                ],
            )
        )

        # Insight 3: Learning architectures
        self.insights.append(
            Insight(
                title="Adaptive Learning Systems",
                description="AI systems should learn and adapt from their interactions",
                supporting_principles=[47, 51, 53],
                evidence=[
                    "Few-shot learning improves task performance",
                    "Agent memory enables learning from experience",
                    "Iteration workflows capture improvements",
                ],
                implications=[
                    "Static systems become obsolete quickly",
                    "Learning systems improve over time",
                    "Memory and iteration are key to adaptation",
                ],
                actionable_recommendations=[
                    "Implement few-shot learning with dynamic examples",
                    "Build memory systems for agent state",
                    "Track and analyze iteration outcomes",
                ],
            )
        )

        # Insight 4: Reasoning and transparency
        self.insights.append(
            Insight(
                title="Transparent Reasoning Systems",
                description="Explicit reasoning chains improve reliability and debuggability",
                supporting_principles=[45, 48],
                evidence=[
                    "Chain-of-thought improves complex reasoning",
                    "Prompt patterns make behavior predictable",
                    "Structured outputs enable validation",
                ],
                implications=[
                    "Black-box systems are hard to trust",
                    "Explicit reasoning enables error detection",
                    "Structured approaches improve consistency",
                ],
                actionable_recommendations=[
                    "Use chain-of-thought for complex decisions",
                    "Implement structured prompt patterns",
                    "Log reasoning traces for debugging",
                ],
            )
        )

        logger.info(f"Generated {len(self.insights)} insights")

    def _build_knowledge_graph(self):
        """Build a knowledge graph from principles."""
        # Build edges based on related principles
        for principle in self.loader.get_all_principles():
            principle_key = f"principle_{principle.number}"

            # Add connections to related principles
            for related in principle.related_principles:
                related_key = f"principle_{related}"
                self.knowledge_graph[principle_key].add(related_key)
                self.knowledge_graph[related_key].add(principle_key)

            # Add connections to concepts
            for concept in self.concepts.values():
                if principle.number in concept.principle_numbers:
                    concept_key = f"concept_{concept.name}"
                    self.knowledge_graph[principle_key].add(concept_key)
                    self.knowledge_graph[concept_key].add(principle_key)

            # Add connections to patterns
            for i, pattern in enumerate(self.patterns):
                if principle.number in pattern.principles:
                    pattern_key = f"pattern_{i}_{pattern.name}"
                    self.knowledge_graph[principle_key].add(pattern_key)
                    self.knowledge_graph[pattern_key].add(principle_key)

        logger.info(f"Built knowledge graph with {len(self.knowledge_graph)} nodes")

    def _serialize_graph(self) -> dict[str, list[str]]:
        """Serialize the knowledge graph."""
        return {k: sorted(v) for k, v in self.knowledge_graph.items()}

    def _get_statistics(self) -> dict:
        """Get statistics about the extracted knowledge."""
        return {
            "total_principles": len(self.loader.principles),
            "total_concepts": len(self.concepts),
            "total_patterns": len(self.patterns),
            "total_insights": len(self.insights),
            "graph_nodes": len(self.knowledge_graph),
            "graph_edges": sum(len(v) for v in self.knowledge_graph.values()) // 2,
            "top_concepts": self._get_top_concepts(5),
            "coverage_by_category": self._get_category_coverage(),
        }

    def _get_top_concepts(self, n: int) -> list[dict]:
        """Get the top N most frequent concepts."""
        sorted_concepts = sorted(self.concepts.values(), key=lambda c: c.frequency, reverse=True)
        return [
            {"name": c.name, "frequency": c.frequency, "principles": sorted(c.principle_numbers)}
            for c in sorted_concepts[:n]
        ]

    def _get_category_coverage(self) -> dict[str, int]:
        """Get concept coverage by category."""
        coverage = defaultdict(int)
        for concept in self.concepts.values():
            coverage[concept.category] += 1
        return dict(coverage)

    def generate_synthesis_report(self) -> str:
        """Generate a human-readable synthesis report."""
        report = []
        report.append("# AI-First Principles Knowledge Synthesis Report\n")
        report.append(f"Analyzed {len(self.loader.principles)} principles\n\n")

        # Top concepts
        report.append("## Key Concepts Identified\n")
        top_concepts = self._get_top_concepts(10)
        for concept in top_concepts:
            report.append(f"- **{concept['name']}**: Found in {concept['frequency']} instances")
            report.append(f"  (Principles: {', '.join(f'#{p}' for p in concept['principles'])})\n")

        # Patterns
        report.append("\n## Common Patterns\n")
        for pattern in self.patterns:
            report.append(f"### {pattern.name}\n")
            report.append(f"{pattern.description}\n")
            report.append(f"- **Confidence**: {pattern.confidence:.0%}\n")
            report.append(f"- **Principles**: {', '.join(f'#{p}' for p in pattern.principles)}\n")
            report.append("- **Examples**:\n")
            for ex in pattern.examples[:3]:
                report.append(f"  - {ex}\n")

        # Insights
        report.append("\n## Strategic Insights\n")
        for i, insight in enumerate(self.insights, 1):
            report.append(f"### {i}. {insight.title}\n")
            report.append(f"{insight.description}\n\n")
            report.append("**Recommendations**:\n")
            for rec in insight.actionable_recommendations:
                report.append(f"- {rec}\n")

        # Statistics
        stats = self._get_statistics()
        report.append("\n## Statistics\n")
        report.append(f"- Total Concepts: {stats['total_concepts']}\n")
        report.append(f"- Total Patterns: {stats['total_patterns']}\n")
        report.append(f"- Total Insights: {stats['total_insights']}\n")
        report.append(f"- Knowledge Graph: {stats['graph_nodes']} nodes, {stats['graph_edges']} edges\n")

        return "".join(report)

    def export_knowledge(self, output_path: Path):
        """Export extracted knowledge to JSON file."""
        knowledge = self.extract_all_knowledge()

        with open(output_path, "w") as f:
            json.dump(knowledge, f, indent=2)

        logger.info(f"Exported knowledge to {output_path}")

    def get_recommendations_for_context(self, context: str) -> list[dict]:
        """Get recommendations based on a specific context."""
        recommendations = []
        context_lower = context.lower()

        # Find relevant concepts
        relevant_concepts = []
        for concept in self.concepts.values():
            if concept.name.lower() in context_lower:
                relevant_concepts.append(concept)

        # Find relevant patterns
        relevant_patterns = []
        for pattern in self.patterns:
            if any(ex.lower() in context_lower for ex in pattern.examples):
                relevant_patterns.append(pattern)

        # Generate recommendations
        if relevant_concepts:
            recommendations.append(
                {
                    "type": "concepts",
                    "title": "Relevant Concepts",
                    "items": [c.name for c in relevant_concepts],
                    "principles": list(set().union(*[c.principle_numbers for c in relevant_concepts])),
                }
            )

        if relevant_patterns:
            recommendations.append(
                {
                    "type": "patterns",
                    "title": "Applicable Patterns",
                    "items": [p.name for p in relevant_patterns],
                    "principles": list(set().union(*[set(p.principles) for p in relevant_patterns])),
                }
            )

        # Add insights if relevant
        for insight in self.insights:
            if any(
                keyword in context_lower
                for keyword in ["iteration", "context", "evaluation", "modular", "learning", "reasoning"]
            ):
                recommendations.append(
                    {
                        "type": "insight",
                        "title": insight.title,
                        "description": insight.description,
                        "recommendations": insight.actionable_recommendations,
                    }
                )
                break

        return recommendations
