"""
AI-powered requirements analysis for tool building.

This module uses pure AI understanding to analyze tool requirements
instead of rule-based keyword matching.
"""

import logging
from typing import Any

from amplifier.ccsdk_toolkit.core.models import SessionOptions
from amplifier.ccsdk_toolkit.core.session import ClaudeSession
from amplifier.ccsdk_toolkit.defensive.llm_parsing import parse_llm_json
from amplifier.ccsdk_toolkit.defensive.retry_patterns import retry_with_feedback

logger = logging.getLogger(__name__)


class RequirementsAnalyzer:
    """Pure AI-driven requirements analysis."""

    def __init__(self, timeout: int = 120):
        """Initialize with configurable timeout."""
        self.timeout = timeout
        self.session_options = SessionOptions(max_turns=1)

    async def analyze(self, tool_name: str, description: str) -> dict[str, Any]:
        """Analyze tool requirements using AI understanding.

        Args:
            tool_name: Name of the tool
            description: Natural language description

        Returns:
            Structured requirements analysis
        """
        prompt = self._build_prompt(tool_name, description)

        async with ClaudeSession(self.session_options) as session:
            response = await retry_with_feedback(func=session.query, prompt=prompt, max_retries=3)

            # Extract text from SessionResponse
            result = response.content if hasattr(response, "content") else str(response)

            parsed = parse_llm_json(result)
            if not parsed:
                raise ValueError("Failed to parse AI requirements analysis")

            # Ensure required fields
            if isinstance(parsed, dict):
                parsed.setdefault("tool_name", tool_name)
                parsed.setdefault("description", description)
            else:
                # If parsing failed, create basic structure
                parsed = {"tool_name": tool_name, "description": description}

            logger.info(f"Requirements analysis complete for '{tool_name}'")
            return parsed

    def _build_prompt(self, tool_name: str, description: str) -> str:
        """Build the requirements analysis prompt."""
        return f"""Analyze the requirements for building a Claude Code tool.

Tool Name: {tool_name}
Description: {description}

Provide a comprehensive requirements analysis in JSON format with these fields:

{{
  "purpose": "Clear statement of what the tool does",
  "core_functionality": ["List of main features"],
  "inputs": [
    {{"name": "param_name", "type": "type", "description": "what it's for", "required": true/false}}
  ],
  "outputs": {{
    "type": "return type",
    "description": "what it returns",
    "format": "specific format if applicable"
  }},
  "dependencies": ["External libraries or services needed"],
  "error_handling": ["Types of errors to handle"],
  "edge_cases": ["Special cases to consider"],
  "performance_requirements": {{
    "timeout": "recommended timeout in seconds",
    "complexity": "O(n) notation if applicable"
  }},
  "integration_points": ["Where this tool connects with other systems"],
  "security_considerations": ["Any security aspects to consider"],
  "usage_examples": ["Example use cases or command patterns"]
}}

Focus on practical, implementable requirements. Be specific about data types, formats, and constraints.
Return ONLY the JSON, no additional text."""
