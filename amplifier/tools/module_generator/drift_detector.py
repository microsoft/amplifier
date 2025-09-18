"""Drift detector for measuring deviation from requirements."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path


class DriftDetector:
    """Detects and measures drift from original requirements."""

    def measure_plan_drift(self, plan_text: str, contract_text: str, spec_text: str) -> float:
        """Measure how much the plan drifts from contract and spec.

        Returns:
            Float between 0.0 (no drift) and 1.0 (complete drift)
        """
        if not plan_text:
            return 1.0  # Empty plan = complete drift

        # Extract key requirements from contract
        contract_requirements = self._extract_requirements(contract_text)

        # Extract design elements from spec
        spec_requirements = self._extract_requirements(spec_text)

        # Check presence in plan
        total_requirements = contract_requirements + spec_requirements
        if not total_requirements:
            return 0.0  # No requirements to drift from

        missing_count = 0
        for req in total_requirements:
            if req.lower() not in plan_text.lower():
                missing_count += 1

        drift_score = missing_count / len(total_requirements)
        return min(1.0, drift_score)

    def measure_implementation_drift(self, module_path: Path, contract_text: str) -> float:
        """Measure how much the implementation drifts from contract.

        Returns:
            Float between 0.0 (no drift) and 1.0 (complete drift)
        """
        if not module_path.exists():
            return 1.0  # No implementation = complete drift

        # Extract contract requirements
        contract_functions = re.findall(r"def\s+(\w+)", contract_text)
        contract_classes = re.findall(r"class\s+(\w+)", contract_text)
        total_items = len(contract_functions) + len(contract_classes)

        if total_items == 0:
            return 0.0  # No requirements to drift from

        # Check implementation
        implemented = set()
        for py_file in module_path.glob("**/*.py"):
            if py_file.is_file():
                content = py_file.read_text()
                for func in contract_functions:
                    if f"def {func}" in content or f"async def {func}" in content:
                        implemented.add(func)
                for cls in contract_classes:
                    if f"class {cls}" in content:
                        implemented.add(cls)

        missing_count = total_items - len(implemented)
        drift_score = missing_count / total_items
        return min(1.0, drift_score)

    def measure_text_similarity(self, text1: str, text2: str) -> float:
        """Measure similarity between two texts.

        Returns:
            Float between 0.0 (completely different) and 1.0 (identical)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize texts
        text1_normalized = self._normalize_text(text1)
        text2_normalized = self._normalize_text(text2)

        # Use sequence matcher for similarity
        matcher = SequenceMatcher(None, text1_normalized, text2_normalized)
        return matcher.ratio()

    def detect_missing_concepts(self, implementation: str, requirements: str) -> list[str]:
        """Detect concepts from requirements missing in implementation."""
        # Extract important terms from requirements
        req_concepts = self._extract_concepts(requirements)

        # Check which are missing from implementation
        impl_lower = implementation.lower()
        missing = []
        for concept in req_concepts:
            if concept.lower() not in impl_lower:
                missing.append(concept)

        return missing

    def _extract_requirements(self, text: str) -> list[str]:
        """Extract key requirements from a contract or spec."""
        requirements = []

        # Extract function names
        functions = re.findall(r"def\s+(\w+)", text)
        requirements.extend(functions)

        # Extract class names
        classes = re.findall(r"class\s+(\w+)", text)
        requirements.extend(classes)

        # Extract CamelCase concepts
        concepts = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b", text)
        # Filter out common words
        filtered_concepts = [
            c for c in concepts if c not in ["The", "This", "That", "These", "Those", "None", "True", "False"]
        ]
        requirements.extend(filtered_concepts[:10])  # Limit to top 10 concepts

        return requirements

    def _extract_concepts(self, text: str) -> list[str]:
        """Extract important concepts from text."""
        concepts = []

        # Extract CamelCase terms
        camel_case = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b", text)
        concepts.extend(camel_case)

        # Extract terms in quotes
        quoted = re.findall(r"[\"']([^\"']+)[\"']", text)
        concepts.extend(quoted)

        # Extract terms after "implements", "creates", "generates", etc.
        action_terms = re.findall(r"(?:implements?|creates?|generates?|builds?)\s+(\w+)", text, re.I)
        concepts.extend(action_terms)

        # Deduplicate while preserving order
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept.lower() not in seen:
                seen.add(concept.lower())
                unique_concepts.append(concept)

        return unique_concepts[:20]  # Limit to top 20 concepts

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        # Convert to lowercase
        text = text.lower()
        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "is",
            "are",
            "was",
            "were",
        }
        words = text.split()
        words = [w for w in words if w not in stop_words]
        return " ".join(words)

    def calculate_drift_report(
        self, plan_text: str, implementation_path: Path, contract_text: str, spec_text: str
    ) -> dict:
        """Generate comprehensive drift report."""
        report = {
            "plan_drift": self.measure_plan_drift(plan_text, contract_text, spec_text),
            "implementation_drift": self.measure_implementation_drift(implementation_path, contract_text),
            "plan_implementation_similarity": 0.0,
            "missing_concepts": [],
            "summary": "",
        }

        # Check plan-implementation similarity if both exist
        if plan_text and implementation_path.exists():
            impl_text = self._read_implementation(implementation_path)
            report["plan_implementation_similarity"] = self.measure_text_similarity(plan_text, impl_text)

        # Find missing concepts
        if implementation_path.exists():
            impl_text = self._read_implementation(implementation_path)
            report["missing_concepts"] = self.detect_missing_concepts(impl_text, contract_text)

        # Generate summary
        avg_drift = (report["plan_drift"] + report["implementation_drift"]) / 2
        if avg_drift < 0.2:
            report["summary"] = "Excellent alignment with requirements"
        elif avg_drift < 0.4:
            report["summary"] = "Good alignment with minor deviations"
        elif avg_drift < 0.6:
            report["summary"] = "Moderate drift from requirements"
        else:
            report["summary"] = "Significant drift from requirements"

        return report

    def _read_implementation(self, module_path: Path) -> str:
        """Read all Python files from module for analysis."""
        impl_text = ""
        for py_file in module_path.glob("**/*.py"):
            if py_file.is_file() and not py_file.name.startswith("test_"):
                impl_text += py_file.read_text() + "\n"
        return impl_text
