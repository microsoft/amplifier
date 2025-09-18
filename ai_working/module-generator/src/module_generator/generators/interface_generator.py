"""Interface generator for creating module public interfaces from contracts.

This generator creates Python __init__.py files that define the public
interface of a module based on its contract specification.
"""

import json
import logging

from module_generator.generators.base import BaseGenerator
from module_generator.models import GeneratorContext

logger = logging.getLogger(__name__)


class InterfaceGenerator(BaseGenerator):
    """Generator for creating Python interface files (__init__.py) from contracts.

    This generator analyzes the module contract and produces:
    - Public exports (__all__ list)
    - Type definitions (dataclasses/TypedDicts)
    - Function stubs with proper type hints
    - Complete docstrings from contract descriptions
    """

    def __init__(self, timeout: int = 300):
        """Initialize the interface generator.

        Args:
            timeout: Timeout for Claude SDK operations (default: 300)
        """
        super().__init__(timeout=timeout)

    async def generate(self, context: GeneratorContext) -> str:
        """Generate a Python interface file from the module contract.

        Args:
            context: Generation context containing the contract and output path

        Returns:
            str: The generated Python interface code

        Raises:
            RuntimeError: If generation fails
        """
        self.validate_context(context)

        # Build the prompt for interface generation
        prompt = self._build_interface_prompt(context)

        # Query Claude with specialized system prompt
        system_prompt = self._get_interface_system_prompt()

        try:
            generated_code = await self.query_claude(prompt, system_prompt)

            # Clean up the response (remove markdown if present)
            generated_code = self._clean_generated_code(generated_code)

            # Save the interface file
            output_path = context.get_output_path("__init__.py")
            self.save_output(generated_code, output_path)

            logger.info(f"Successfully generated interface for module '{context.name}'")
            return generated_code

        except Exception as e:
            logger.error(f"Failed to generate interface: {e}")
            raise RuntimeError(f"Interface generation failed: {e}") from e

    def _build_interface_prompt(self, context: GeneratorContext) -> str:
        """Build the prompt for interface generation.

        Args:
            context: The generation context

        Returns:
            str: The formatted prompt for Claude
        """
        contract = context.contract

        # Extract key contract elements from nested structure
        module_info = contract.get("module", {})
        module_name = module_info.get("name", context.name)
        description = module_info.get("purpose", f"Module for {module_name}")
        inputs = contract.get("inputs", {})
        outputs = contract.get("outputs", {})
        side_effects = contract.get("side_effects", [])
        dependencies = contract.get("dependencies", [])

        prompt = f"""Generate a Python __init__.py interface file for the following module contract:

Module Name: {module_name}
Description: {description}

Contract Specification:
{json.dumps(contract, indent=2)}

Requirements:
1. Create a clean public interface with __all__ exports
2. Generate appropriate data classes/types for inputs and outputs
3. Create function stubs with proper type hints
4. Map contract types to Python types:
   - string → str
   - integer → int
   - number → float
   - boolean → bool
   - array → List[T]
   - object → dict or dataclass (prefer dataclass for structured data)
5. Include comprehensive docstrings from descriptions
6. Make functions async if they involve I/O or external calls
7. Use Optional[] for optional parameters
8. Follow Python best practices and PEP-8

Inputs:
{json.dumps(inputs, indent=2)}

Outputs:
{json.dumps(outputs, indent=2)}

Side Effects: {side_effects if side_effects else "None"}
Dependencies: {dependencies if dependencies else "None"}

Generate ONLY the Python code for __init__.py. Do not include markdown formatting or explanations.
The code should be complete, working, and ready to use."""

        return prompt

    def _get_interface_system_prompt(self) -> str:
        """Get the specialized system prompt for interface generation.

        Returns:
            str: System prompt for generating Python interfaces
        """
        return (
            "You are a Python code generator. Return ONLY valid Python code. "
            "Do not include any explanations, markdown formatting, or commentary. "
            "Generate clean, well-structured module interfaces following the 'bricks and studs' philosophy. "
            "Create Python interface code with proper type hints, dataclasses for structured data, and docstrings. "
            "The output must be a complete, valid Python file that can be executed immediately."
        )

    def _clean_generated_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting if present.

        Args:
            code: The generated code that might contain markdown

        Returns:
            str: Clean Python code without markdown
        """
        # Strip potential markdown code block markers
        code = code.strip()

        # Remove ```python or ``` markers
        if code.startswith("```python"):
            code = code[9:]  # len("```python") = 9
        elif code.startswith("```"):
            code = code[3:]  # len("```") = 3

        if code.endswith("```"):
            code = code[:-3]

        return code.strip()

    def validate_context(self, context: GeneratorContext) -> None:
        """Validate the context has required fields for interface generation.

        Args:
            context: The context to validate

        Raises:
            ValueError: If required fields are missing
        """
        super().validate_context(context)

        if not context.contract:
            raise ValueError("Contract is required for interface generation")

        # Validate contract has at least module name in correct location
        module_info = context.contract.get("module", {})
        if "name" not in module_info and not context.name:
            raise ValueError("Module name must be specified in contract.module.name or context")
