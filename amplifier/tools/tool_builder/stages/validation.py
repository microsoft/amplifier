"""
AI-powered quality validation for generated tools.

This module validates generated code quality using AI assessment
instead of regex patterns and rule-based checks.
"""

import logging
from typing import Any

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.ccsdk_toolkit.defensive.retry_patterns import retry_with_feedback

logger = logging.getLogger(__name__)


class QualityValidator:
    """Pure AI-driven quality validation."""

    def __init__(self, timeout: int = 120):
        """Initialize with configurable timeout."""
        self.timeout = timeout
        self.session_options = SessionOptions(max_turns=1)

    async def validate(
        self, generated_code: dict[str, str], requirements: dict[str, Any], tool_name: str
    ) -> dict[str, Any]:
        """Validate generated code quality using AI assessment.

        Args:
            generated_code: Generated code files
            requirements: Original requirements
            tool_name: Name of the tool

        Returns:
            Validation results with issues and recommendations
        """
        validation_results = {
            "tool_name": tool_name,
            "files_validated": list(generated_code.keys()),
            "overall_quality": None,
            "issues": [],
            "recommendations": [],
            "requirements_coverage": {},
            "code_quality_metrics": {},
            "tokens_used": 0,
        }

        # Validate main code file
        if "tool.py" in generated_code:
            main_validation = await self._validate_code_file(
                code=generated_code["tool.py"], filename="tool.py", requirements=requirements, is_main=True
            )
            validation_results.update(self._merge_validation(validation_results, main_validation))

        # Validate test file if present
        if "test_tool.py" in generated_code:
            test_validation = await self._validate_code_file(
                code=generated_code["test_tool.py"], filename="test_tool.py", requirements=requirements, is_main=False
            )
            validation_results.update(self._merge_validation(validation_results, test_validation))

        # Determine overall quality
        validation_results["overall_quality"] = self._calculate_overall_quality(validation_results)

        logger.info(f"Quality validation complete for '{tool_name}'")
        return validation_results

    async def _validate_code_file(
        self, code: str, filename: str, requirements: dict[str, Any], is_main: bool
    ) -> dict[str, Any]:
        """Validate a single code file."""
        prompt = self._build_validation_prompt(code, filename, requirements, is_main)

        async with ClaudeSession(self.session_options) as session:
            response = await retry_with_feedback(func=session.query, prompt=prompt, max_retries=3)

            # Extract text from SessionResponse
            result = response.content if hasattr(response, "content") else str(response)

            parsed = parse_llm_json(result)
            if not parsed:
                raise ValueError(f"Failed to parse validation results for {filename}")

            # Ensure we return a dict
            if not isinstance(parsed, dict):
                return {}
            return parsed

    def _build_validation_prompt(self, code: str, filename: str, requirements: dict[str, Any], is_main: bool) -> str:
        """Build the validation prompt."""
        req_summary = self._format_requirements_for_validation(requirements)
        file_type = "main implementation" if is_main else "test file"

        return f"""Perform quality validation of this generated Claude Code tool {file_type}.

Filename: {filename}

Code to Validate:
```python
{code}
```

Requirements to Check Against:
{req_summary}

Provide a comprehensive validation assessment in JSON format:

{{
  "syntax_valid": true/false,
  "imports_correct": true/false,
  "requirements_met": {{
    "core_functionality_implemented": ["list of implemented features"],
    "missing_functionality": ["list of missing features"],
    "coverage_percentage": 0-100
  }},
  "code_quality": {{
    "readability": "excellent/good/fair/poor",
    "documentation": "complete/adequate/minimal/missing",
    "error_handling": "robust/adequate/basic/insufficient",
    "type_hints": "complete/partial/missing",
    "naming_conventions": "consistent/mostly_consistent/inconsistent"
  }},
  "security_assessment": {{
    "issues_found": ["list any security concerns"],
    "risk_level": "none/low/medium/high"
  }},
  "performance_assessment": {{
    "potential_bottlenecks": ["list any performance concerns"],
    "optimization_needed": true/false
  }},
  "critical_issues": [
    {{"severity": "high/medium/low", "description": "issue description", "line": "approximate line number if applicable"}}
  ],
  "recommendations": [
    "Specific improvement suggestions"
  ],
  "claude_code_compliance": {{
    "follows_patterns": true/false,
    "uses_decorators_correctly": true/false,
    "error_handling_appropriate": true/false
  }},
  "ready_for_use": true/false,
  "quality_score": 0-100
}}

Be thorough but constructive. Focus on actual problems rather than style preferences.
Return ONLY the JSON, no additional text."""

    def _format_requirements_for_validation(self, requirements: dict[str, Any]) -> str:
        """Format requirements for validation context."""
        lines = []

        if requirements.get("core_functionality"):
            lines.append("Core Functionality to Implement:")
            for func in requirements["core_functionality"]:
                lines.append(f"  - {func}")

        if requirements.get("inputs"):
            lines.append("\nExpected Inputs:")
            for inp in requirements["inputs"]:
                lines.append(f"  - {inp.get('name')} ({inp.get('type')}): {inp.get('description')}")

        if requirements.get("outputs"):
            out = requirements["outputs"]
            lines.append(f"\nExpected Output: {out.get('type')} - {out.get('description')}")

        if requirements.get("error_handling"):
            lines.append("\nError Handling Required:")
            for err in requirements["error_handling"]:
                lines.append(f"  - {err}")

        return "\n".join(lines)

    def _merge_validation(self, results: dict[str, Any], new_validation: dict[str, Any]) -> dict[str, Any]:
        """Merge validation results from a file into overall results."""
        # Add issues
        if new_validation.get("critical_issues"):
            results["issues"].extend(new_validation["critical_issues"])

        # Add recommendations
        if new_validation.get("recommendations"):
            results["recommendations"].extend(new_validation["recommendations"])

        # Update requirements coverage
        if new_validation.get("requirements_met"):
            results["requirements_coverage"].update(
                {
                    "implemented": new_validation["requirements_met"].get("core_functionality_implemented", []),
                    "missing": new_validation["requirements_met"].get("missing_functionality", []),
                    "coverage": new_validation["requirements_met"].get("coverage_percentage", 0),
                }
            )

        # Update code quality metrics
        if new_validation.get("code_quality"):
            results["code_quality_metrics"].update(new_validation["code_quality"])

        return results

    def _calculate_overall_quality(self, results: dict[str, Any]) -> str:
        """Calculate overall quality rating based on validation results."""
        # Count critical issues by severity
        high_issues = sum(1 for issue in results["issues"] if issue.get("severity") == "high")
        medium_issues = sum(1 for issue in results["issues"] if issue.get("severity") == "medium")

        # Check requirements coverage
        coverage = results.get("requirements_coverage", {}).get("coverage", 0)

        # Determine overall quality
        if high_issues > 0:
            return "needs_work"
        if medium_issues > 2 or coverage < 70:
            return "acceptable_with_improvements"
        if coverage >= 90 and medium_issues == 0:
            return "excellent"
        return "good"
