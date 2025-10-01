"""Synthesizer for AI-First Principles - combines and analyzes principles for specific contexts."""

import logging
from collections import defaultdict
from typing import Any

from .loader import Principle
from .loader import PrincipleLoader

logger = logging.getLogger(__name__)


class PrincipleSynthesizer:
    """Synthesizes AI-First principles for specific contexts and use cases."""

    def __init__(self, loader: PrincipleLoader = None):
        """Initialize the synthesizer with a principle loader."""
        self.loader = loader or PrincipleLoader()
        self.synthesis_cache = {}

    def synthesize_for_task(self, task_description: str) -> dict:
        """Synthesize relevant principles for a specific task."""
        # Keywords to look for in task description
        keywords = self._extract_keywords(task_description)

        # Find relevant principles
        relevant_principles = self._find_relevant_principles(keywords)

        # Group by category
        by_category = defaultdict(list)
        for principle in relevant_principles:
            by_category[principle.category].append(principle)

        # Build synthesis
        synthesis = {
            "task": task_description,
            "keywords": keywords,
            "relevant_principles": [p.to_dict() for p in relevant_principles],
            "by_category": {cat: [p.number for p in principles] for cat, principles in by_category.items()},
            "recommendations": self._generate_recommendations(relevant_principles, task_description),
            "implementation_order": self._suggest_implementation_order(relevant_principles),
        }

        return synthesis

    def synthesize_for_phase(self, project_phase: str) -> dict:
        """Synthesize principles relevant to a specific project phase."""
        phase_mappings = {
            "planning": ["people", "process"],
            "design": ["technology", "process"],
            "implementation": ["technology", "process"],
            "testing": ["process", "governance"],
            "deployment": ["governance", "technology"],
            "maintenance": ["governance", "process"],
        }

        categories = phase_mappings.get(project_phase.lower(), [])
        principles = []

        for category in categories:
            principles.extend(self.loader.get_by_category(category))

        # Build phase-specific synthesis
        synthesis = {
            "phase": project_phase,
            "focus_categories": categories,
            "principles": [p.to_dict() for p in principles],
            "key_considerations": self._get_phase_considerations(project_phase, principles),
            "checklist": self._build_phase_checklist(principles),
        }

        return synthesis

    def find_principle_chains(self, start_principle: int) -> list[list[int]]:
        """Find chains of related principles starting from a given principle."""
        chains = []
        visited = set()

        def explore_chain(current: int, chain: list[int]):
            if current in visited or len(chain) > 10:  # Prevent infinite loops
                return

            visited.add(current)
            principle = self.loader.get_principle(current)

            if not principle:
                return

            # If we have related principles, explore each
            if principle.related_principles:
                for related in principle.related_principles:
                    if related not in chain:
                        new_chain = chain + [related]
                        chains.append(new_chain)
                        explore_chain(related, new_chain)

        # Start exploration
        explore_chain(start_principle, [start_principle])

        # Sort by chain length (longer chains first)
        chains.sort(key=len, reverse=True)

        return chains[:10]  # Return top 10 chains

    def analyze_principle_coverage(self, principles_used: list[int]) -> dict:
        """Analyze coverage of principles in a project."""
        all_principles = self.loader.get_all_principles()
        used_set = set(principles_used)

        # Calculate coverage
        coverage = {
            "total_principles": len(all_principles),
            "principles_used": len(used_set),
            "coverage_percentage": (len(used_set) / len(all_principles)) * 100 if all_principles else 0,
            "by_category": {},
            "missing_critical": [],
            "underutilized_categories": [],
        }

        # Analyze by category
        for category in ["people", "process", "technology", "governance"]:
            category_principles = self.loader.get_by_category(category)
            category_used = [p for p in category_principles if p.number in used_set]

            coverage["by_category"][category] = {
                "total": len(category_principles),
                "used": len(category_used),
                "percentage": (len(category_used) / len(category_principles)) * 100 if category_principles else 0,
                "missing": [p.number for p in category_principles if p.number not in used_set],
            }

            # Identify underutilized categories
            if coverage["by_category"][category]["percentage"] < 30:
                coverage["underutilized_categories"].append(category)

        # Identify missing critical principles
        critical_principles = [7, 8, 9, 26, 31, 32]  # Key process and technology principles
        for num in critical_principles:
            if num not in used_set:
                principle = self.loader.get_principle(num)
                if principle:
                    coverage["missing_critical"].append(
                        {"number": num, "name": principle.name, "category": principle.category}
                    )

        return coverage

    def generate_implementation_roadmap(self, target_principles: list[int]) -> dict:
        """Generate an implementation roadmap for adopting principles."""
        principles = [self.loader.get_principle(num) for num in target_principles if self.loader.get_principle(num)]

        # Group into phases
        phases = {
            "foundation": [],  # Basic principles that others depend on
            "core": [],  # Essential operational principles
            "optimization": [],  # Performance and quality improvements
            "advanced": [],  # Complex or specialized principles
        }

        # Categorize principles into phases
        for principle in principles:
            if principle.number in [1, 2, 3, 4, 5, 6]:  # People principles
                phases["foundation"].append(principle)
            elif principle.number in [7, 8, 9, 10, 26, 31]:  # Core process/tech
                phases["core"].append(principle)
            elif principle.number in [11, 12, 13, 14, 32, 33]:  # Optimization
                phases["optimization"].append(principle)
            else:
                phases["advanced"].append(principle)

        # Build roadmap
        roadmap = {
            "total_principles": len(principles),
            "phases": [],
            "dependencies": self._analyze_dependencies(principles),
            "estimated_timeline": self._estimate_timeline(principles),
        }

        # Build phase details
        phase_order = ["foundation", "core", "optimization", "advanced"]
        for phase_name in phase_order:
            if phases[phase_name]:
                roadmap["phases"].append(
                    {
                        "name": phase_name,
                        "principles": [p.to_dict() for p in phases[phase_name]],
                        "focus": self._get_phase_focus(phase_name),
                        "success_criteria": self._get_phase_criteria(phase_name),
                    }
                )

        return roadmap

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text for principle matching."""
        # Simple keyword extraction - could be enhanced with NLP
        important_terms = [
            "test",
            "testing",
            "contract",
            "api",
            "regenerate",
            "validate",
            "validation",
            "human",
            "ai",
            "llm",
            "prompt",
            "context",
            "error",
            "recovery",
            "state",
            "stateless",
            "idempotent",
            "cli",
            "tool",
            "memory",
            "agent",
            "parallel",
            "incremental",
            "git",
            "deployment",
            "monitoring",
            "security",
        ]

        text_lower = text.lower()
        found_keywords = []

        for term in important_terms:
            if term in text_lower:
                found_keywords.append(term)

        return found_keywords

    def _find_relevant_principles(self, keywords: list[str]) -> list[Principle]:
        """Find principles relevant to given keywords."""
        relevant = []
        scores = {}

        for principle in self.loader.get_all_principles():
            score = 0
            content_lower = (principle.content or "").lower()

            for keyword in keywords:
                # Higher weight for keyword in title
                if keyword in principle.name:
                    score += 3
                # Medium weight for keyword in description
                if principle.description and keyword in principle.description.lower():
                    score += 2
                # Lower weight for keyword anywhere in content
                if keyword in content_lower:
                    score += 1

            if score > 0:
                scores[principle.number] = score
                relevant.append(principle)

        # Sort by relevance score
        relevant.sort(key=lambda p: scores[p.number], reverse=True)

        return relevant[:15]  # Return top 15 most relevant

    def _generate_recommendations(self, principles: list[Principle], context: str) -> list[str]:
        """Generate specific recommendations based on principles and context."""
        recommendations = []

        # Check for test-related context
        if "test" in context.lower():
            test_principles = [p for p in principles if p.number in [4, 9]]
            if test_principles:
                recommendations.append("Implement test-based verification (#4) with tests as quality gates (#9)")

        # Check for API/contract context
        if "api" in context.lower() or "contract" in context.lower():
            contract_principles = [p for p in principles if p.number == 8]
            if contract_principles:
                recommendations.append("Apply contract-first design (#8) to define clear interfaces")

        # Check for deployment context
        if "deploy" in context.lower():
            deploy_principles = [p for p in principles if p.number in [10, 34]]
            if deploy_principles:
                recommendations.append("Use git as safety net (#10) with feature flags (#34) for safe deployments")

        # Add general recommendations based on categories present
        categories = {p.category for p in principles}
        if "technology" in categories:
            recommendations.append("Focus on stateless design (#26) and idempotency (#31) for reliability")
        if "process" in categories:
            recommendations.append("Implement continuous validation (#11) with incremental processing (#12)")
        if "people" in categories:
            recommendations.append("Maintain strategic human touchpoints (#2) with human escape hatches (#6)")

        return recommendations[:5]  # Limit to 5 recommendations

    def _suggest_implementation_order(self, principles: list[Principle]) -> list[int]:
        """Suggest an order for implementing principles."""
        # Define priority order based on dependencies
        priority_order = [
            # Foundation
            1,
            2,
            3,  # People basics
            7,
            8,  # Process basics
            26,
            31,  # Technology basics
            # Core operations
            9,
            10,
            11,  # Testing and validation
            # Advanced features
            12,
            13,
            14,  # Optimization
        ]

        # Filter to only principles we have
        principle_numbers = {p.number for p in principles}
        ordered = [n for n in priority_order if n in principle_numbers]

        # Add remaining principles not in priority order
        remaining = [p.number for p in principles if p.number not in ordered]
        ordered.extend(sorted(remaining))

        return ordered

    def _get_phase_considerations(self, phase: str, principles: list[Principle]) -> list[str]:
        """Get key considerations for a project phase."""
        considerations = {
            "planning": [
                "Form small AI-first working groups",
                "Define strategic human touchpoints",
                "Establish prompt engineering practices",
            ],
            "design": [
                "Apply contract-first design principles",
                "Design for stateless operation",
                "Plan for idempotent operations",
            ],
            "implementation": [
                "Use regenerate-don't-edit approach",
                "Implement incremental processing",
                "Build with CLI-first interfaces",
            ],
            "testing": [
                "Establish tests as quality gates",
                "Implement continuous validation",
                "Use test-based verification",
            ],
            "deployment": [
                "Use feature flags for gradual rollout",
                "Implement graceful degradation",
                "Set up observability from the start",
            ],
            "maintenance": [
                "Monitor with metrics everywhere",
                "Maintain self-healing capabilities",
                "Keep documentation as specification",
            ],
        }

        return considerations.get(phase.lower(), ["Review relevant principles for this phase"])

    def _build_phase_checklist(self, principles: list[Principle]) -> list[str]:
        """Build a checklist from principle checklists."""
        checklist = []
        for principle in principles[:5]:  # Limit to top 5 principles
            if principle.checklist:
                # Add up to 2 items from each principle
                for item in principle.checklist[:2]:
                    checklist.append(f"[{principle.name}] {item}")

        return checklist

    def _analyze_dependencies(self, principles: list[Principle]) -> dict[str, list[int]]:
        """Analyze dependencies between principles."""
        dependencies = {}

        for principle in principles:
            deps = []
            # Find principles that this one references
            for related in principle.related_principles:
                if any(p.number == related for p in principles):
                    deps.append(related)

            if deps:
                dependencies[str(principle.number)] = deps

        return dependencies

    def _estimate_timeline(self, principles: list[Principle]) -> dict[str, Any]:
        """Estimate timeline for implementing principles."""
        # Simple estimation based on principle count and complexity
        weeks_per_principle = {
            "people": 1,  # People principles are quick to adopt
            "process": 2,  # Process changes take moderate time
            "technology": 3,  # Technology changes take longer
            "governance": 2,  # Governance is moderate
        }

        total_weeks = 0
        by_category = defaultdict(int)

        for principle in principles:
            weeks = weeks_per_principle.get(principle.category, 2)
            total_weeks += weeks
            by_category[principle.category] += weeks

        return {
            "total_weeks": total_weeks,
            "total_months": round(total_weeks / 4, 1),
            "by_category": dict(by_category),
            "parallel_potential": total_weeks // 2,  # Assume 50% can be done in parallel
        }

    def _get_phase_focus(self, phase_name: str) -> str:
        """Get the focus description for a roadmap phase."""
        focus = {
            "foundation": "Establish core team practices and basic AI-first mindset",
            "core": "Implement essential technical and process infrastructure",
            "optimization": "Improve efficiency, reliability, and performance",
            "advanced": "Add sophisticated capabilities and governance",
        }
        return focus.get(phase_name, "Implement selected principles")

    def _get_phase_criteria(self, phase_name: str) -> list[str]:
        """Get success criteria for a roadmap phase."""
        criteria = {
            "foundation": [
                "Team understands AI-first principles",
                "Basic practices are documented",
                "Initial tools are selected",
            ],
            "core": [
                "Core infrastructure is operational",
                "Key processes are automated",
                "Testing framework is in place",
            ],
            "optimization": [
                "Performance metrics are tracked",
                "Error rates are reduced",
                "Processing is efficient",
            ],
            "advanced": ["Governance processes are mature", "System is self-healing", "Full observability achieved"],
        }
        return criteria.get(phase_name, ["Phase objectives are met"])
