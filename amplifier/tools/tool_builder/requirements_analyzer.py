"""Requirements analysis microtask for Tool Builder.

This module implements the first AI microtask that analyzes tool requirements
using Claude Code SDK.
"""

import asyncio
import json
import re
from typing import Any

from .exceptions import CCSDKRequiredError
from .exceptions import MicrotaskError


class RequirementsAnalyzer:
    """Analyzes tool requirements using Claude Code SDK."""

    # AI-related keywords to detect
    AI_KEYWORDS = {
        "ai",
        "llm",
        "claude",
        "gpt",
        "openai",
        "anthropic",
        "summarize",
        "synthesize",
        "analyze",
        "extract",
        "generate",
        "transform",
        "process with ai",
        "language model",
        "machine learning",
        "ml",
        "natural language",
        "nlp",
        "understand",
        "intelligent",
        "smart",
        "cognitive",
    }

    def __init__(self):
        """Initialize the analyzer and verify CC SDK availability."""
        self._verify_sdk_available()

    def _verify_sdk_available(self):
        """Verify Claude Code SDK is available - fail fast if not."""
        import importlib.util

        if importlib.util.find_spec("claude_code_sdk") is None:
            raise CCSDKRequiredError()

    async def analyze(self, tool_name: str, description: str) -> dict[str, Any]:
        """Analyze requirements for the tool.

        This is a focused microtask that extracts:
        - Core functionality requirements
        - Input/output specifications
        - Dependencies and integrations
        - Complexity assessment

        Args:
            tool_name: Name of the tool to create
            description: User's description of what the tool should do

        Returns:
            Structured requirements analysis
        """
        try:
            from claude_code_sdk import ClaudeCodeOptions
            from claude_code_sdk import ClaudeSDKClient
        except ImportError:
            raise CCSDKRequiredError()

        # Prepare focused prompt for requirements analysis
        prompt = self._build_requirements_prompt(tool_name, description)

        response = ""
        try:
            # Execute focused CC SDK call
            # Note: While we aim for short operations, complex requirements
            # may legitimately take longer to analyze properly
            async with asyncio.timeout(300):  # 5 minutes max for complex tools
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt=self._get_system_prompt(),
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

        except TimeoutError:
            raise MicrotaskError("Requirements analysis timed out after 5 minutes")
        except Exception as e:
            raise MicrotaskError(f"Requirements analysis failed: {str(e)}")

        # Parse and return the structured response
        return self._parse_requirements(response, description)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for requirements analysis."""
        return """You are a requirements analyst for the Amplifier Tool Builder.

Your task is to analyze tool requirements and extract structured information.
Pay special attention to:
1. Multi-step processes and workflows
2. AI/LLM integration needs (summarization, analysis, synthesis, etc.)
3. Complex natural language requirements
4. Numbered lists or bullet points in the description
5. Input/output transformations

When the user mentions AI processes like "summarize", "analyze", "synthesize", or references
AI/LLM/Claude, set requires_ai to true and detail the AI requirements.

Respond with JSON containing these fields:
{
    "core_functionality": "Preserve the ACTUAL requirements from the description, don't generalize",
    "inputs": ["specific input types mentioned or implied"],
    "outputs": ["specific output types mentioned or implied"],
    "dependencies": ["required", "libraries"],
    "integrations": ["systems", "to", "integrate", "with"],
    "complexity": "simple|medium|complex",
    "key_features": ["extract from description, preserve user's language"],
    "constraints": ["technical", "constraints"],
    "success_criteria": ["how", "to", "validate", "success"],
    "requires_ai": true/false,
    "ai_requirements": ["if requires_ai, list specific AI tasks needed"],
    "workflow_steps": ["if multi-step process, list the steps"]
}

IMPORTANT: Preserve the user's actual requirements. Don't replace them with generic placeholders.
Extract and maintain the specific details from the description."""

    def _build_requirements_prompt(self, tool_name: str, description: str) -> str:
        """Build the prompt for requirements analysis."""
        return f"""Analyze the requirements for this Amplifier CLI tool:

Tool Name: {tool_name}
Description: {description}

Context: This will be an Amplifier CLI tool that follows our patterns:
- Invoked via Makefile targets
- Follows modular design philosophy
- Uses Python with async support
- Integrates with existing Amplifier ecosystem

Extract structured requirements following the JSON format.
Focus on what's needed to build a working tool."""

    def _extract_ai_requirements(self, description: str) -> tuple[bool, list[str]]:
        """Extract AI-related requirements from the description.

        Args:
            description: The tool description

        Returns:
            Tuple of (requires_ai, list of AI requirements)
        """
        description_lower = description.lower()
        requires_ai = False
        ai_requirements = []

        # Check for AI keywords
        for keyword in self.AI_KEYWORDS:
            if keyword in description_lower:
                requires_ai = True
                break

        # Extract specific AI tasks mentioned
        if requires_ai:
            # Look for common AI task patterns
            patterns = [
                r"summarize?\s+(\w+(?:\s+\w+)*)",
                r"analyze?\s+(\w+(?:\s+\w+)*)",
                r"synthesize?\s+(\w+(?:\s+\w+)*)",
                r"extract\s+(\w+(?:\s+\w+)*)",
                r"generate\s+(\w+(?:\s+\w+)*)",
                r"process\s+(?:through|with|using)\s+(?:ai|llm|claude)",
                r"ai\s+(?:process|analysis|summary|synthesis)",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, description_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str) and match:
                        ai_requirements.append(f"AI task: {match.strip()}")

        return requires_ai, ai_requirements

    def _extract_workflow_steps(self, description: str) -> list[str]:
        """Extract workflow steps from numbered lists or multi-step descriptions.

        Args:
            description: The tool description

        Returns:
            List of workflow steps
        """
        steps = []

        # Look for numbered lists (1., 2., etc. or 1), 2), etc.)
        numbered_pattern = r"(?:^|\n)\s*(?:\d+[.)]\s*(.+?)(?=\n\s*\d+[.)]|\n\n|$))"
        matches = re.findall(numbered_pattern, description, re.MULTILINE | re.DOTALL)
        if matches:
            steps.extend([m.strip() for m in matches if m.strip()])

        # Look for bullet points
        bullet_pattern = r"(?:^|\n)\s*[•·\-*]\s*(.+?)(?=\n\s*[•·\-*]|\n\n|$)"
        matches = re.findall(bullet_pattern, description, re.MULTILINE | re.DOTALL)
        if matches and not steps:  # Only use if no numbered steps found
            steps.extend([m.strip() for m in matches if m.strip()])

        # Look for "then" or "and then" patterns
        if not steps:
            then_pattern = r"(?:^|[,.])\s*(?:and\s+)?then\s+(.+?)(?=[,.]|$)"
            matches = re.findall(then_pattern, description, re.IGNORECASE)
            if matches:
                steps.extend([m.strip() for m in matches if m.strip()])

        # Look for "For each" patterns indicating iteration
        foreach_pattern = r"for\s+each\s+(\w+(?:\s+\w+)*)[,:]?\s*(.+?)(?=[.]|$)"
        matches = re.findall(foreach_pattern, description, re.IGNORECASE)
        for item, action in matches:
            steps.append(f"For each {item}: {action.strip()}")

        return steps

    def _parse_requirements(self, response: str, original_description: str = "") -> dict[str, Any]:
        """Parse the requirements from the AI response.

        Args:
            response: The AI's JSON response
            original_description: The original description for fallback parsing
        """
        # Clean response if wrapped in markdown
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            requirements = json.loads(cleaned)

            # Validate and enhance required fields
            required_fields = [
                "core_functionality",
                "inputs",
                "outputs",
                "complexity",
                "key_features",
            ]

            for field in required_fields:
                if field not in requirements:
                    requirements[field] = self._get_default_value(field)

            # Add AI requirements if not present but detected
            if "requires_ai" not in requirements and original_description:
                requires_ai, ai_reqs = self._extract_ai_requirements(original_description)
                requirements["requires_ai"] = requires_ai
                if "ai_requirements" not in requirements:
                    requirements["ai_requirements"] = ai_reqs

            # Add workflow steps if not present
            if "workflow_steps" not in requirements and original_description:
                steps = self._extract_workflow_steps(original_description)
                if steps:
                    requirements["workflow_steps"] = steps

            # Add metacognitive analysis for input type detection
            from .metacognitive_analyzer import MetacognitiveAnalyzer

            meta_analyzer = MetacognitiveAnalyzer()
            input_analysis = meta_analyzer.analyze_input_type(original_description)

            # Enhance requirements based on analysis
            if input_analysis["primary_type"] == "directory":
                requirements["cli_type"] = "directory_processor"
                requirements["batch_processing"] = input_analysis["is_batch"]
                requirements["file_pattern"] = input_analysis.get("file_pattern", "*.txt")
                requirements["file_limit"] = input_analysis.get("count_limit", 5)
                # Update inputs to reflect directory processing
                if not requirements.get("inputs"):
                    requirements["inputs"] = []
                requirements["inputs"].insert(
                    0, f"source_directory: Path to directory containing {input_analysis.get('file_pattern', 'files')}"
                )
            elif input_analysis["primary_type"] == "file":
                requirements["cli_type"] = "file_processor"
                if not requirements.get("inputs"):
                    requirements["inputs"] = ["input_file: Path to single file"]
            else:
                requirements["cli_type"] = "text_processor"

            return requirements

        except json.JSONDecodeError as e:
            # If parsing fails, try to extract from original description
            requires_ai, ai_reqs = self._extract_ai_requirements(original_description)
            workflow_steps = self._extract_workflow_steps(original_description)

            # Preserve the original description in core_functionality
            core_functionality = original_description if original_description else "Tool functionality to be determined"

            # Add metacognitive analysis even on parse error
            from .metacognitive_analyzer import MetacognitiveAnalyzer

            meta_analyzer = MetacognitiveAnalyzer()
            input_analysis = meta_analyzer.analyze_input_type(original_description)

            base_requirements = {
                "core_functionality": core_functionality,
                "inputs": self._extract_inputs_outputs(original_description, "input"),
                "outputs": self._extract_inputs_outputs(original_description, "output"),
                "dependencies": [],
                "integrations": [],
                "complexity": "complex" if requires_ai else "medium",
                "key_features": self._extract_key_features(original_description),
                "constraints": [],
                "success_criteria": ["tool runs without errors"],
                "requires_ai": requires_ai,
                "ai_requirements": ai_reqs,
                "workflow_steps": workflow_steps,
                "parse_error": str(e),
                "raw_response": response[:500],  # Keep first 500 chars for debugging
            }

            # Enhance with metacognitive analysis
            if input_analysis["primary_type"] == "directory":
                base_requirements["cli_type"] = "directory_processor"
                base_requirements["batch_processing"] = input_analysis["is_batch"]
                base_requirements["file_pattern"] = input_analysis.get("file_pattern", "*.txt")
                base_requirements["file_limit"] = input_analysis.get("count_limit", 5)
                if not base_requirements["inputs"]:
                    base_requirements["inputs"] = [
                        f"source_directory: Path to directory containing {input_analysis.get('file_pattern', 'files')}"
                    ]
            elif input_analysis["primary_type"] == "file":
                base_requirements["cli_type"] = "file_processor"
                if not base_requirements["inputs"]:
                    base_requirements["inputs"] = ["input_file: Path to single file"]
            else:
                base_requirements["cli_type"] = "text_processor"

            return base_requirements

    def _extract_inputs_outputs(self, description: str, io_type: str) -> list[str]:
        """Extract likely inputs or outputs from description.

        Args:
            description: The tool description
            io_type: "input" or "output"

        Returns:
            List of likely inputs or outputs
        """
        items = []
        description_lower = description.lower()

        if io_type == "input":
            patterns = [
                r"(?:input|read|load|fetch|get|take)\s+(?:from\s+)?(\w+(?:\s+\w+)*)",
                r"process(?:es|ing)?\s+(\w+(?:\s+\w+)*)",
                r"(?:given|with)\s+(\w+(?:\s+\w+)*)",
            ]
        else:
            patterns = [
                r"(?:output|write|save|store|generate|create|produce)\s+(\w+(?:\s+\w+)*)",
                r"(?:return|result|yield)s?\s+(\w+(?:\s+\w+)*)",
                r"(?:to|into)\s+(\w+(?:\s+file|\s+format)?)",
            ]

        for pattern in patterns:
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and match and len(match) < 50:
                    items.append(match.strip())

        # Remove duplicates while preserving order
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique_items.append(item)

        return unique_items if unique_items else [f"user {io_type}"]

    def _extract_key_features(self, description: str) -> list[str]:
        """Extract key features from the description.

        Args:
            description: The tool description

        Returns:
            List of key features
        """
        features = []

        # Extract verb-based features
        verb_pattern = r"\b(?:will|should|must|can)\s+(\w+(?:\s+\w+){0,3})"
        matches = re.findall(verb_pattern, description, re.IGNORECASE)
        for match in matches:
            if match and len(match) < 50:
                features.append(match.strip())

        # Look for feature keywords
        feature_keywords = ["support", "provide", "enable", "allow", "include", "feature"]
        for keyword in feature_keywords:
            pattern = rf"{keyword}s?\s+(\w+(?:\s+\w+){{0,3}})"
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if match and len(match) < 50:
                    features.append(f"{keyword} {match.strip()}")

        # Remove duplicates
        seen = set()
        unique_features = []
        for feature in features:
            if feature not in seen:
                seen.add(feature)
                unique_features.append(feature)

        return unique_features if unique_features else ["core processing"]

    def _get_default_value(self, field: str) -> Any:
        """Get default value for a missing field."""
        defaults = {
            "core_functionality": "Functionality to be specified",
            "inputs": [],
            "outputs": [],
            "dependencies": [],
            "integrations": [],
            "complexity": "medium",
            "key_features": [],
            "constraints": [],
            "success_criteria": [],
        }
        return defaults.get(field, [])
