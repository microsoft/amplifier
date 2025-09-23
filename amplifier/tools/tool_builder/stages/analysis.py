"""
AI-powered metacognitive analysis for tool building.

This module performs deep analysis of implementation approaches and patterns
using AI intelligence instead of rule-based pattern matching.
"""

import logging
from typing import Any

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.ccsdk_toolkit.defensive.retry_patterns import retry_with_feedback

logger = logging.getLogger(__name__)


class MetacognitiveAnalyzer:
    """Pure AI-driven metacognitive analysis."""

    def __init__(self, timeout: int = 120):
        """Initialize with configurable timeout."""
        self.timeout = timeout
        self.session_options = SessionOptions(max_turns=1)

    async def analyze(self, requirements: dict[str, Any], tool_name: str) -> dict[str, Any]:
        """Perform metacognitive analysis of implementation approach.

        Args:
            requirements: Requirements from previous stage
            tool_name: Name of the tool

        Returns:
            Deep analysis of implementation strategy
        """
        prompt = self._build_prompt(requirements, tool_name)

        async with ClaudeSession(self.session_options) as session:
            response = await retry_with_feedback(func=session.query, prompt=prompt, max_retries=3)

            # Extract text from SessionResponse
            result = response.content if hasattr(response, "content") else str(response)

            parsed = parse_llm_json(result)
            if not parsed:
                raise ValueError("Failed to parse AI metacognitive analysis")

            if not isinstance(parsed, dict):
                # If parsing failed, return empty dict
                parsed = {}

            logger.info(f"Metacognitive analysis complete for '{tool_name}'")
            return parsed

    def _build_prompt(self, requirements: dict[str, Any], tool_name: str) -> str:
        """Build the metacognitive analysis prompt."""
        # Format requirements for context
        req_summary = self._format_requirements(requirements)

        return f"""Perform a metacognitive analysis for implementing this Claude Code tool.

Tool Name: {tool_name}

Requirements Summary:
{req_summary}

Analyze the implementation approach and provide insights in JSON format:

{{
  "implementation_strategy": {{
    "approach": "Overall approach to implementation",
    "key_decisions": ["Critical design decisions to make"],
    "architecture_pattern": "Recommended pattern (e.g., functional, class-based, async)",
    "modular_design": {{
      "main_module": "Core module structure",
      "supporting_modules": ["Additional modules if needed"],
      "separation_of_concerns": "How to separate responsibilities"
    }}
  }},
  "complexity_analysis": {{
    "cognitive_load": "high/medium/low - complexity for AI to implement",
    "implementation_risks": ["Potential challenges"],
    "simplification_opportunities": ["Ways to reduce complexity"]
  }},
  "integration_patterns": {{
    "claude_code_patterns": ["Specific Claude Code patterns to use"],
    "error_handling_strategy": "How to handle errors gracefully",
    "state_management": "If/how to manage state"
  }},
  "code_organization": {{
    "file_structure": ["Recommended file organization"],
    "naming_conventions": {{
      "functions": "Function naming pattern",
      "variables": "Variable naming pattern",
      "files": "File naming pattern"
    }},
    "documentation_needs": ["Key documentation points"]
  }},
  "testing_strategy": {{
    "test_categories": ["Types of tests needed"],
    "critical_test_cases": ["Must-have test scenarios"],
    "validation_approach": "How to validate correctness"
  }},
  "optimization_opportunities": {{
    "performance": ["Performance optimization points"],
    "usability": ["UX improvements"],
    "maintainability": ["Code maintainability aspects"]
  }},
  "ai_implementation_guidance": {{
    "implementation_order": ["Step-by-step implementation sequence"],
    "focus_areas": ["Areas requiring special attention"],
    "potential_pitfalls": ["Common mistakes to avoid"]
  }}
}}

Provide deep, actionable insights that will guide the code generation stage.
Return ONLY the JSON, no additional text."""

    def _format_requirements(self, requirements: dict[str, Any]) -> str:
        """Format requirements for prompt context."""
        lines = []
        lines.append(f"Purpose: {requirements.get('purpose', 'Not specified')}")

        if requirements.get("core_functionality"):
            lines.append("Core Functionality:")
            for func in requirements["core_functionality"]:
                lines.append(f"  - {func}")

        if requirements.get("inputs"):
            lines.append("Inputs:")
            for inp in requirements["inputs"]:
                lines.append(f"  - {inp.get('name')}: {inp.get('type')} - {inp.get('description')}")

        if requirements.get("outputs"):
            out = requirements["outputs"]
            lines.append(f"Output: {out.get('type')} - {out.get('description')}")

        return "\n".join(lines)
