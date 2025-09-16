"""Architecture design microtask for Tool Builder.

This module designs the modular architecture for tools based on requirements,
following the "bricks and studs" philosophy.
"""

import asyncio
import json
from typing import Any

from .exceptions import CCSDKRequiredError
from .exceptions import MicrotaskError


class ArchitectureDesigner:
    """Designs modular tool architecture using Claude Code SDK."""

    def __init__(self):
        """Initialize the designer and verify CC SDK availability."""
        self._verify_sdk_available()

    def _verify_sdk_available(self):
        """Verify Claude Code SDK is available - fail fast if not."""
        import importlib.util

        if importlib.util.find_spec("claude_code_sdk") is None:
            raise CCSDKRequiredError()

    async def design(self, tool_name: str, requirements: dict[str, Any]) -> dict[str, Any]:
        """Design the architecture for the tool.

        This microtask creates a modular architecture following our principles:
        - Bricks: Self-contained modules with single responsibilities
        - Studs: Clear interfaces/contracts between modules
        - Vertical slices: End-to-end functionality
        - Minimal abstractions: Direct, simple implementations

        Args:
            tool_name: Name of the tool being built
            requirements: Structured requirements from analysis phase

        Returns:
            Architecture specification with modules and interfaces
        """
        try:
            from claude_code_sdk import ClaudeCodeOptions
            from claude_code_sdk import ClaudeSDKClient
        except ImportError:
            raise CCSDKRequiredError()

        prompt = self._build_architecture_prompt(tool_name, requirements)
        response = ""

        try:
            # Architecture design may need time to think through module boundaries
            async with asyncio.timeout(300):  # 5 minutes max
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
            raise MicrotaskError("Architecture design timed out after 5 minutes")
        except Exception as e:
            raise MicrotaskError(f"Architecture design failed: {str(e)}")

        return self._parse_architecture(response)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for architecture design."""
        return """You are an architecture designer for the Amplifier Tool Builder.

Design modular architectures following our "bricks and studs" philosophy:

BRICKS (Modules):
- Self-contained directories with single responsibilities
- Include their own tests and documentation
- Expose only public contracts via __all__ or interfaces
- Can be regenerated independently

STUDS (Interfaces):
- Function signatures, CLI commands, API schemas
- Stable connection points between modules
- Minimal, clear contracts
- Enable module replacement without breaking the system

PRINCIPLES:
- Ruthless simplicity: Every abstraction must justify itself
- Vertical slices: Complete end-to-end functionality
- Direct implementations: Avoid unnecessary layers
- Minimal dependencies: Use libraries only when they add substantial value

Respond with JSON containing:
{
    "modules": [
        {
            "name": "module_name",
            "purpose": "What this module does",
            "contract": "Public interface description",
            "dependencies": ["other", "modules"],
            "files": ["main.py", "__init__.py", "tests.py"]
        }
    ],
    "entry_point": "How the tool is invoked",
    "data_flow": "How data moves through the system",
    "external_integrations": ["APIs", "services", "tools"],
    "testing_strategy": "How to validate the tool works"
}

Design for simplicity, testability, and regeneration."""

    def _build_architecture_prompt(self, tool_name: str, requirements: dict[str, Any]) -> str:
        """Build the prompt for architecture design."""
        return f"""Design the architecture for this Amplifier CLI tool:

Tool Name: {tool_name}

Requirements:
- Core Functionality: {requirements.get("core_functionality", "Not specified")}
- Inputs: {json.dumps(requirements.get("inputs", []))}
- Outputs: {json.dumps(requirements.get("outputs", []))}
- Key Features: {json.dumps(requirements.get("key_features", []))}
- Dependencies: {json.dumps(requirements.get("dependencies", []))}
- Integrations: {json.dumps(requirements.get("integrations", []))}
- Complexity: {requirements.get("complexity", "medium")}

Context:
- Will be invoked via Makefile as: make {tool_name}
- Should follow Amplifier patterns (CLI with Click, async where beneficial)
- Keep modules small and focused (single responsibility)
- Design for testability and future regeneration

Create a modular architecture that:
1. Breaks functionality into clear, independent bricks
2. Defines simple studs (interfaces) between them
3. Minimizes dependencies and abstractions
4. Enables vertical slice development

Focus on practical, working architecture that can be built incrementally."""

    def _parse_architecture(self, response: str) -> dict[str, Any]:
        """Parse the architecture from the AI response."""
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
            architecture = json.loads(cleaned)

            # Ensure required fields exist
            if "modules" not in architecture:
                architecture["modules"] = [self._create_default_module()]

            if "entry_point" not in architecture:
                architecture["entry_point"] = "CLI command via Click"

            if "data_flow" not in architecture:
                architecture["data_flow"] = "Input → Processing → Output"

            return architecture

        except json.JSONDecodeError as e:
            # Create minimal working architecture on parse failure
            return {
                "modules": [self._create_default_module()],
                "entry_point": "CLI command via Click",
                "data_flow": "Input → Processing → Output",
                "external_integrations": [],
                "testing_strategy": "Unit tests for each module",
                "parse_error": str(e),
                "raw_response": response[:500],
            }

    def _create_default_module(self) -> dict[str, Any]:
        """Create a default module structure."""
        return {
            "name": "core",
            "purpose": "Main processing logic",
            "contract": "process(input) -> output",
            "dependencies": [],
            "files": ["__init__.py", "main.py", "test_main.py"],
        }
