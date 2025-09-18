"""Stage output evaluator for the module generation pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """Result of evaluating a stage output."""

    is_valid: bool
    score: float  # 0.0 to 1.0
    notes: str
    issues: list[str]
    suggestions: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "notes": self.notes,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluationResult:
        """Create from dictionary."""
        return cls(
            is_valid=data["is_valid"],
            score=data["score"],
            notes=data["notes"],
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
        )


class StageEvaluator:
    """Evaluates outputs at each pipeline stage."""

    def evaluate_parsing(self, contract: Any, impl: Any) -> EvaluationResult:
        """Evaluate parsed contract and implementation spec."""
        issues = []
        suggestions = []

        # Check contract has a name
        if not contract.name:
            issues.append("Contract missing module name")

        # Check contract has purpose
        if not contract.purpose:
            suggestions.append("Contract should include a Purpose section")

        # Check impl spec has overview
        if not impl.overview:
            suggestions.append("Implementation spec should include an Overview section")

        # Check name consistency
        if contract.name != impl.name:
            issues.append(f"Name mismatch: contract={contract.name}, impl={impl.name}")

        score = 1.0 - (len(issues) * 0.2)
        score = max(0.0, min(1.0, score))

        return EvaluationResult(
            is_valid=len(issues) == 0,
            score=score,
            notes=f"Parsed contract and spec for module: {contract.name}",
            issues=issues,
            suggestions=suggestions,
        )

    def evaluate_plan(self, plan_text: str, contract_text: str) -> EvaluationResult:
        """Evaluate a generated plan."""
        issues = []
        suggestions = []

        if not plan_text:
            issues.append("Plan is empty")
            return EvaluationResult(
                is_valid=False,
                score=0.0,
                notes="No plan generated",
                issues=issues,
                suggestions=suggestions,
            )

        # Check plan has key sections
        plan_lower = plan_text.lower()

        # Check for file structure
        if "file" not in plan_lower or "structure" not in plan_lower:
            suggestions.append("Plan should explicitly describe file structure")

        # Check for function/class mentions
        if "def " not in plan_text and "class " not in plan_text:
            issues.append("Plan doesn't mention specific functions or classes")

        # Check for test plan
        if "test" not in plan_lower:
            suggestions.append("Plan should include testing strategy")

        # Extract contract requirements
        contract_functions = re.findall(r"def\s+(\w+)", contract_text)
        contract_classes = re.findall(r"class\s+(\w+)", contract_text)

        # Check if plan mentions contract requirements
        missing_functions = [f for f in contract_functions if f not in plan_text]
        missing_classes = [c for c in contract_classes if c not in plan_text]

        if missing_functions:
            issues.append(f"Plan missing functions: {', '.join(missing_functions)}")
        if missing_classes:
            issues.append(f"Plan missing classes: {', '.join(missing_classes)}")

        # Calculate score
        score = 1.0
        score -= len(issues) * 0.15
        score -= len(suggestions) * 0.05
        score = max(0.0, min(1.0, score))

        return EvaluationResult(
            is_valid=len(issues) == 0,
            score=score,
            notes=f"Plan evaluation: {len(issues)} issues, {len(suggestions)} suggestions",
            issues=issues,
            suggestions=suggestions,
        )

    def evaluate_plan_comprehensive(self, plan_text: str, contract_text: str, spec_text: str) -> EvaluationResult:
        """Comprehensive evaluation of plan against contract and spec."""
        issues = []
        suggestions = []

        # Basic evaluation first
        basic_eval = self.evaluate_plan(plan_text, contract_text)
        issues.extend(basic_eval.issues)
        suggestions.extend(basic_eval.suggestions)

        if not plan_text:
            return basic_eval

        # Check plan completeness
        required_files = [
            "__init__.py",
            "core.py",
            "models.py",
            "README.md",
            "tests/",
        ]

        for req_file in required_files:
            if req_file not in plan_text:
                # Allow alternatives for core.py
                if req_file == "core.py":
                    if not any(alt in plan_text for alt in ["synthesizer.py", "engine.py", "processor.py"]):
                        suggestions.append(f"Plan should mention {req_file} or alternative implementation file")
                else:
                    suggestions.append(f"Plan should mention {req_file}")

        # Check for implementation details from spec
        if "Design Overview" in spec_text or "Overview" in spec_text:
            # Extract key terms from spec
            spec_keywords = re.findall(r"\b[A-Z][a-z]+[A-Z]\w*\b", spec_text)  # CamelCase terms
            missing_concepts = [kw for kw in spec_keywords if kw not in plan_text]
            if len(missing_concepts) > 3:
                suggestions.append(f"Plan may be missing concepts from spec: {', '.join(missing_concepts[:3])}...")

        # Check for modular design principles
        if "modular" not in plan_text.lower() and "module" not in plan_text.lower():
            suggestions.append("Plan should reflect modular design principles")

        # Calculate comprehensive score
        score = basic_eval.score
        score -= len(suggestions) * 0.02  # Additional penalty for new suggestions
        score = max(0.0, min(1.0, score))

        return EvaluationResult(
            is_valid=score >= 0.6,  # Threshold for proceeding
            score=score,
            notes=f"Comprehensive plan evaluation: score={score:.2f}",
            issues=issues,
            suggestions=suggestions,
        )

    def evaluate_generation(self, module_path: Any, contract_text: str) -> EvaluationResult:
        """Evaluate generated module."""
        from pathlib import Path

        issues = []
        suggestions = []

        module_path = Path(module_path) if not isinstance(module_path, Path) else module_path

        if not module_path.exists():
            issues.append(f"Module path does not exist: {module_path}")
            return EvaluationResult(
                is_valid=False,
                score=0.0,
                notes="Module generation failed",
                issues=issues,
                suggestions=suggestions,
            )

        # Check for required files
        required = {
            "__init__.py": "Module initialization file",
            "README.md": "Module documentation",
        }

        for file_name, desc in required.items():
            if not (module_path / file_name).exists():
                issues.append(f"Missing {desc}: {file_name}")

        # Check for implementation file (core.py or alternatives)
        impl_files = ["core.py", "synthesizer.py", "engine.py", "processor.py", "main.py"]
        if not any((module_path / f).exists() for f in impl_files):
            issues.append(f"Missing implementation file (expected one of: {', '.join(impl_files)})")

        # Check for tests
        test_dir = module_path / "tests"
        if not test_dir.exists():
            suggestions.append("Module should include tests directory")
        elif not list(test_dir.glob("test_*.py")):
            suggestions.append("Tests directory should contain test files")

        # Calculate score
        score = 1.0
        score -= len(issues) * 0.25
        score -= len(suggestions) * 0.05
        score = max(0.0, min(1.0, score))

        return EvaluationResult(
            is_valid=len(issues) == 0,
            score=score,
            notes=f"Module generation evaluation for {module_path.name}",
            issues=issues,
            suggestions=suggestions,
        )

    def evaluate_contract_compliance(self, module_path: Any, contract_text: str) -> EvaluationResult:
        """Evaluate if generated module complies with contract."""
        from pathlib import Path

        issues = []
        suggestions = []

        module_path = Path(module_path) if not isinstance(module_path, Path) else module_path

        # Extract contract requirements
        contract_functions = re.findall(r"def\s+(\w+)", contract_text)
        contract_classes = re.findall(r"class\s+(\w+)", contract_text)

        # Read module __init__.py to check exports
        init_file = module_path / "__init__.py"
        if init_file.exists():
            init_content = init_file.read_text()

            # Check for __all__ definition
            if "__all__" not in init_content:
                suggestions.append("__init__.py should define __all__ for clear exports")

            # Check if contract items are exported
            for func in contract_functions:
                if func not in init_content:
                    issues.append(f"Contract function not exported: {func}")

            for cls in contract_classes:
                if cls not in init_content:
                    issues.append(f"Contract class not exported: {cls}")
        else:
            issues.append("Missing __init__.py - cannot verify contract compliance")

        # Check implementation files for contract items
        impl_found = {}
        for py_file in module_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            for func in contract_functions:
                if f"def {func}" in content or f"async def {func}" in content:
                    impl_found[func] = py_file.name
            for cls in contract_classes:
                if f"class {cls}" in content:
                    impl_found[cls] = py_file.name

        # Report missing implementations
        for func in contract_functions:
            if func not in impl_found:
                issues.append(f"Contract function not implemented: {func}")

        for cls in contract_classes:
            if cls not in impl_found:
                issues.append(f"Contract class not implemented: {cls}")

        # Calculate score
        total_items = len(contract_functions) + len(contract_classes)
        if total_items > 0:
            implemented = len(impl_found)
            score = implemented / total_items
        else:
            score = 1.0 if not issues else 0.5

        return EvaluationResult(
            is_valid=len(issues) == 0,
            score=score,
            notes=f"Contract compliance: {len(impl_found)}/{total_items} items implemented",
            issues=issues,
            suggestions=suggestions,
        )
