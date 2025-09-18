# Module: validation
# Purpose: Validate stage outputs against DESC requirements

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    stage: str
    passed: bool
    score: float  # 0.0 to 1.0
    issues: list[str]
    suggestions: list[str]


class RequirementsValidator:
    """Validate outputs against original DESC requirements."""

    def __init__(self, original_desc: str):
        self.original_desc = original_desc
        self.requirements = self.extract_requirements(original_desc)

    def extract_requirements(self, desc: str) -> dict[str, str]:
        """Extract measurable requirements from DESC."""
        requirements = {}

        # Look for numbered items (1. 2. 3. etc)
        numbered_items = re.findall(r"\d+\.\s*([^.]+(?:\.[^.]+)*?)(?=\d+\.|$)", desc)
        for i, item in enumerate(numbered_items, 1):
            requirements[f"req_{i}"] = item.strip()

        # Look for key action words
        if "read" in desc.lower():
            requirements["input_handling"] = "Must handle input file/directory reading"
        if "ai process" in desc.lower() or "ai" in desc.lower():
            requirements["ai_integration"] = "Must integrate AI processing"
        if "resume" in desc.lower() or "incremental" in desc.lower():
            requirements["resume_capability"] = "Must support resume/incremental processing"
        if "save" in desc.lower() or "store" in desc.lower():
            requirements["persistence"] = "Must save/store results persistently"

        return requirements

    def validate_stage(self, stage_name: str, output: Any) -> ValidationResult:
        """Validate a stage output against requirements."""

        # Convert output to string for analysis
        output_str = str(output) if not isinstance(output, str) else output

        validators = {
            "requirements_analysis": self._validate_requirements,
            "system_design": self._validate_design,
            "code_generation": self._validate_code,
            "test_generation": self._validate_tests,
        }

        validator = validators.get(stage_name, self._validate_generic)
        return validator(stage_name, output_str)

    def _validate_requirements(self, stage: str, output: str) -> ValidationResult:
        """Validate requirements analysis covers DESC."""
        issues = []
        suggestions = []
        matched = 0

        for req_id, req_text in self.requirements.items():
            # Check if requirement is addressed
            if any(word in output.lower() for word in req_text.lower().split()[:3]):
                matched += 1
            else:
                issues.append(f"Missing requirement: {req_text[:50]}...")
                suggestions.append(f"Add requirement covering: {req_text[:50]}...")

        score = matched / len(self.requirements) if self.requirements else 0.5
        passed = score >= 0.7

        return ValidationResult(stage, passed, score, issues, suggestions)

    def _validate_design(self, stage: str, output: str) -> ValidationResult:
        """Validate design addresses requirements."""
        issues = []
        suggestions = []

        # Check for key design elements
        checks = [
            ("components" in output.lower() or "modules" in output.lower(), "No clear component/module design"),
            ("data flow" in output.lower() or "flow" in output.lower(), "No data flow specification"),
            ("interface" in output.lower() or "api" in output.lower(), "No interface definitions"),
        ]

        passed_checks = sum(1 for check, _ in checks if check)
        for check, issue in checks:
            if not check:
                issues.append(issue)

        score = passed_checks / len(checks)
        passed = score >= 0.6

        if not passed:
            suggestions.append("Include clear component breakdown and data flow")

        return ValidationResult(stage, passed, score, issues, suggestions)

    def _validate_code(self, stage: str, output: str) -> ValidationResult:
        """Validate generated code meets requirements."""
        issues = []
        suggestions = []

        # Check for implementation of key requirements
        has_cli = "click" in output or "argparse" in output or "def main" in output
        has_ai = "claude" in output.lower() or "llm" in output.lower() or "ai" in output.lower()
        has_incremental = "save" in output and ("exists" in output or "resume" in output)
        has_no_stubs = "NotImplementedError" not in output and "TODO" not in output

        checks = [
            (has_cli, "No CLI interface found"),
            (has_ai, "No AI integration found"),
            (has_incremental, "No incremental save/resume capability"),
            (has_no_stubs, "Contains stub/placeholder code"),
        ]

        passed_checks = sum(1 for check, _ in checks if check)
        for check, issue in checks:
            if not check:
                issues.append(issue)

        score = passed_checks / len(checks)
        passed = score >= 0.75

        return ValidationResult(stage, passed, score, issues, suggestions)

    def _validate_tests(self, stage: str, output: str) -> ValidationResult:
        """Validate test coverage."""
        issues = []

        has_unit = "test_" in output
        has_validation = "validate" in output.lower() or "assert" in output

        checks = [
            (has_unit, "No unit tests found"),
            (has_validation, "No validation/assertions found"),
        ]

        passed_checks = sum(1 for check, _ in checks if check)
        for check, issue in checks:
            if not check:
                issues.append(issue)

        score = passed_checks / len(checks)
        passed = score >= 0.5  # Lower bar for tests

        return ValidationResult(stage, passed, score, issues, [])

    def _validate_generic(self, stage: str, output: str) -> ValidationResult:
        """Generic validation for other stages."""
        # Basic check - did we get substantive output?
        has_content = len(output) > 100
        score = 1.0 if has_content else 0.0
        issues = [] if has_content else ["Output appears too short or empty"]

        return ValidationResult(stage, has_content, score, issues, [])

    def generate_report(self, validations: list[ValidationResult]) -> str:
        """Generate validation report."""
        report = ["=== VALIDATION REPORT ===\n"]

        total_score = sum(v.score for v in validations) / len(validations)
        passed = sum(1 for v in validations if v.passed)

        report.append(f"Overall Score: {total_score:.1%}")
        report.append(f"Stages Passed: {passed}/{len(validations)}\n")

        for v in validations:
            status = "✅" if v.passed else "❌"
            report.append(f"{status} {v.stage}: {v.score:.1%}")

            if v.issues:
                report.append("  Issues:")
                for issue in v.issues:
                    report.append(f"    - {issue}")

            if v.suggestions:
                report.append("  Suggestions:")
                for suggestion in v.suggestions:
                    report.append(f"    - {suggestion}")

        return "\n".join(report)
