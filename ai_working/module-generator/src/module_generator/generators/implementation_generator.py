"""Implementation generator for creating full module implementations from specs.

This generator creates complete, working Python implementations based on
both the contract (interface) and specification (implementation details).
"""

import json
import logging

from module_generator.generators.base import BaseGenerator
from module_generator.models import GeneratorContext

logger = logging.getLogger(__name__)


class ImplementationGenerator(BaseGenerator):
    """Generator for creating full Python implementations from contracts and specs.

    This generator analyzes both the module contract AND specification to produce:
    - Complete working implementations of all functions
    - Claude SDK integration for AI operations
    - Proper error handling and retry logic
    - State management for checkpointing
    - All algorithms and behaviors from the spec
    """

    def __init__(self, timeout: int = 300):
        """Initialize the implementation generator.

        Args:
            timeout: Timeout for Claude SDK operations (default: 300)
        """
        super().__init__(timeout=timeout)

    async def generate(self, context: GeneratorContext) -> dict[str, str]:
        """Generate complete Python implementation files from contract and spec.

        Args:
            context: Generation context containing the contract, spec, and output path

        Returns:
            dict: Mapping of filename to generated code content

        Raises:
            RuntimeError: If generation fails
        """
        self.validate_context(context)

        if not context.spec:
            raise ValueError("Specification is required for implementation generation")

        # Check if Claude SDK is available - fail immediately if not
        if not await self._check_sdk_availability():
            raise RuntimeError(
                "Claude SDK is required for module generation.\n"
                "\n"
                "To fix:\n"
                "  1. Install Claude CLI: npm install -g @anthropic-ai/claude-code\n"
                "  2. Verify installation: which claude\n"
                "  3. Run inside Claude Code environment for best results\n"
            )

        # Generate multiple implementation files
        generated_files = {}

        try:
            # 1. Generate main implementation module
            logger.info("Generating main implementation module...")
            main_impl = await self._generate_main_implementation(context)
            generated_files["implementation.py"] = main_impl

            # 2. Generate Claude SDK integration if needed
            if self._needs_claude_sdk(context.spec):
                logger.info("Generating Claude SDK integration...")
                claude_impl = await self._generate_claude_integration(context)
                generated_files["claude_integration.py"] = claude_impl

            # 3. Generate state management if checkpointing is needed
            if self._needs_checkpointing(context.spec):
                logger.info("Generating state management...")
                state_impl = await self._generate_state_management(context)
                generated_files["state.py"] = state_impl

            # 4. Generate utilities if needed
            if self._needs_utilities(context.spec):
                logger.info("Generating utilities...")
                utils_impl = await self._generate_utilities(context)
                generated_files["utils.py"] = utils_impl

            logger.info(f"Successfully generated {len(generated_files)} implementation files")
            return generated_files

        except Exception as e:
            logger.error(f"Failed to generate implementation: {e}")
            raise RuntimeError(f"Implementation generation failed: {e}") from e

    async def _generate_main_implementation(self, context: GeneratorContext) -> str:
        """Generate the main implementation module with all functions.

        Args:
            context: The generation context

        Returns:
            str: Generated Python implementation code
        """
        prompt = self._build_implementation_prompt(context)
        system_prompt = self._get_implementation_system_prompt()

        generated_code = await self.query_claude(prompt, system_prompt)
        return self._clean_generated_code(generated_code)

    async def _generate_claude_integration(self, context: GeneratorContext) -> str:
        """Generate Claude SDK integration module.

        Args:
            context: The generation context

        Returns:
            str: Generated Python code for Claude integration
        """
        spec = context.spec
        prompting = spec.get("claude_prompting", {})

        prompt = f"""Generate a Python module for Claude SDK integration based on this specification:

Module: {context.name}

Claude Prompting Configuration:
{json.dumps(prompting, indent=2)}

Requirements:
1. Use claude_code_sdk with ClaudeSDKClient and ClaudeCodeOptions
2. Implement 120-second timeout for all SDK operations (critical!)
3. Handle markdown stripping from responses
4. Implement retry logic with exponential backoff
5. Create async functions using proper async/await patterns
6. Use this exact pattern for SDK calls:

async with asyncio.timeout(120):
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="...",
            max_turns=1,
        )
    ) as client:
        await client.query(prompt)
        response = ""
        async for message in client.receive_response():
            if hasattr(message, "content"):
                content = getattr(message, "content", [])
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text"):
                            response += getattr(block, "text", "")

Generate ONLY the Python code. Include proper imports and error handling."""

        system_prompt = (
            "You are a Python code generator. Output ONLY valid Python code. "
            "DO NOT include ANY explanatory text, markdown, or conversational responses. "
            "Start directly with 'import' or 'from' statements or Python code. "
            "Every function must be fully implemented with working logic."
        )

        generated_code = await self.query_claude(prompt, system_prompt)
        return self._clean_generated_code(generated_code)

    async def _generate_state_management(self, context: GeneratorContext) -> str:
        """Generate state management module for checkpointing.

        Args:
            context: The generation context

        Returns:
            str: Generated Python code for state management
        """
        spec = context.spec
        state_config = spec.get("state_management", {})

        prompt = f"""Generate a Python module for state management and checkpointing:

Module: {context.name}

State Management Configuration:
{json.dumps(state_config, indent=2)}

Requirements:
1. Implement checkpoint save/load functionality
2. Use file-based storage with immediate saves after each operation
3. Include file I/O retry logic for cloud-synced directories
4. Support resume capability from partial completion
5. Thread-safe operations with file locks if concurrent access is possible
6. JSON serialization for checkpoint data

Generate ONLY the Python code with all necessary imports."""

        system_prompt = (
            "You are a Python code generator. Output ONLY valid Python code. "
            "DO NOT include ANY explanatory text or conversational responses. "
            "Start directly with imports or Python code. "
            "Generate complete, working state management code."
        )

        generated_code = await self.query_claude(prompt, system_prompt)
        return self._clean_generated_code(generated_code)

    async def _generate_utilities(self, context: GeneratorContext) -> str:
        """Generate utilities module with helper functions.

        Args:
            context: The generation context

        Returns:
            str: Generated Python code for utilities
        """
        spec = context.spec
        algorithms = spec.get("algorithms", [])

        prompt = f"""Generate a Python utilities module with helper functions:

Module: {context.name}

Algorithms and Operations:
{json.dumps(algorithms, indent=2)}

Generate utility functions for:
1. Each algorithm/operation described in the spec
2. Common helper functions for data processing
3. Validation and sanitization functions
4. Any parsing or transformation functions needed

Generate ONLY the Python code with proper type hints and docstrings."""

        system_prompt = (
            "You are a Python code generator. Output ONLY valid Python code. "
            "DO NOT include ANY explanatory text or conversational responses. "
            "Start directly with imports or Python code. "
            "Generate complete utility functions with full implementations."
        )

        generated_code = await self.query_claude(prompt, system_prompt)
        return self._clean_generated_code(generated_code)

    def _build_implementation_prompt(self, context: GeneratorContext) -> str:
        """Build the main prompt for implementation generation.

        Args:
            context: The generation context

        Returns:
            str: The formatted prompt for Claude
        """
        contract = context.contract
        spec = context.spec

        # Extract module name for the prompt
        module_info = contract.get("module", {})
        module_name = module_info.get("name", context.name)

        prompt = f"""Generate a complete Python implementation for this module:

MODULE: {module_name}

CONTRACT (Interface):
{json.dumps(contract, indent=2)}

SPECIFICATION (Implementation):
{json.dumps(spec, indent=2)}

Requirements:
1. Implement ALL functions from the public_api section with full working code
2. NO stubs or NotImplementedError - everything must work
3. Follow the behaviors and data_flow from the specification
4. Integrate Claude SDK using the pattern specified in claude_prompting
5. Include proper error handling as specified in the errors section
6. Implement checkpointing/state management as described
7. Use async/await for I/O operations
8. Follow the 120-second timeout rule for Claude SDK operations
9. Include retry logic with exponential backoff where specified
10. Import necessary modules from other generated files (claude_integration, state, utils)

The implementation should:
- Actually perform the operations described, not just return stubs
- Use Claude SDK for AI operations as specified
- Save state immediately after each operation for resume capability
- Handle all error cases with proper exceptions
- Include comprehensive logging

Generate ONLY the Python implementation code. Make it complete and working."""

        return prompt

    def _get_implementation_system_prompt(self) -> str:
        """Get the system prompt for implementation generation.

        Returns:
            str: System prompt for generating full implementations
        """
        return (
            "You are a Python code generator. Output ONLY valid, executable Python code. "
            "DO NOT include ANY explanatory text, markdown, or conversational responses. "
            "DO NOT start with phrases like 'I'll generate' or 'Here is'. "
            "Start your response directly with Python code (imports, classes, or functions). "
            "Every function must be fully implemented and working - no stubs or placeholders. "
            "Follow the specification exactly, implementing all behaviors and algorithms described. "
            "Use proper async/await patterns, error handling, and include all necessary imports. "
            "The code must be immediately executable and functional."
        )

    def _needs_claude_sdk(self, spec: dict) -> bool:
        """Check if the module needs Claude SDK integration.

        Args:
            spec: The specification dictionary

        Returns:
            bool: True if Claude SDK is needed
        """
        return "claude_prompting" in spec or "claude" in str(spec).lower()

    def _needs_checkpointing(self, spec: dict) -> bool:
        """Check if the module needs checkpointing/state management.

        Args:
            spec: The specification dictionary

        Returns:
            bool: True if checkpointing is needed
        """
        return "state_management" in spec or "checkpoint" in str(spec).lower()

    def _needs_utilities(self, spec: dict) -> bool:
        """Check if the module needs utility functions.

        Args:
            spec: The specification dictionary

        Returns:
            bool: True if utilities are needed
        """
        return "algorithms" in spec or "data_flow" in spec

    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting if present.

        Args:
            code: The generated code that might contain markdown

        Returns:
            str: Clean Python code without markdown
        """
        code = code.strip()

        # Remove ```python or ``` markers
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]

        if code.endswith("```"):
            code = code[:-3]

        return code.strip()

    def validate_context(self, context: GeneratorContext) -> None:
        """Validate the context has required fields for implementation generation.

        Args:
            context: The context to validate

        Raises:
            ValueError: If required fields are missing
        """
        super().validate_context(context)

        if not context.contract:
            raise ValueError("Contract is required for implementation generation")

        if not context.spec:
            raise ValueError("Specification is required for implementation generation")

    async def _check_sdk_availability(self) -> bool:
        """Check if Claude SDK is available.

        Returns:
            bool: True if SDK is available, False otherwise
        """
        try:
            from module_generator.core import claude_sdk

            return await claude_sdk.check_sdk_available(timeout=10)
        except Exception as e:
            logger.error(f"SDK availability check failed: {e}")
            return False
