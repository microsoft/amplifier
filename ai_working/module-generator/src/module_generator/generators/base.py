"""Base generator class providing common functionality for all module generators.

This module provides the abstract base class that all generators inherit from.
It handles:
- Interaction with Claude SDK for code generation
- Template formatting for prompts
- File saving with resilient I/O
- Error handling and reporting
"""

import logging
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any

from module_generator.core import claude_sdk
from module_generator.core import file_io
from module_generator.models import GeneratorContext

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for all module generators.

    Provides common functionality for prompt building, generation, and output saving.
    Subclasses must implement the generate() method to define their specific behavior.
    """

    def __init__(self, timeout: int = 300):
        """Initialize the base generator.

        Args:
            timeout: Timeout for Claude SDK operations in seconds (default: 300)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout

    @abstractmethod
    async def generate(self, context: GeneratorContext) -> str:
        """Generate module content based on the provided context.

        This method must be implemented by each specific generator subclass.

        Args:
            context: The generation context containing module specification and metadata

        Returns:
            str: The generated content (code, documentation, etc.)

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def _is_valid_python_code(self, text: str) -> bool:
        """Check if the generated text is likely valid Python code.

        Args:
            text: The text to validate

        Returns:
            bool: True if text appears to be Python code, False otherwise
        """
        if not text or not text.strip():
            return False

        # Check for common conversational patterns that indicate it's not code
        conversational_patterns = [
            "I'll generate",
            "I'll create",
            "Here is",
            "Here's",
            "Let me",
            "This module",
            "This code",
            "The following",
            "I will",
            "I can",
        ]

        first_line = text.strip().split("\n")[0].lower()
        for pattern in conversational_patterns:
            if pattern.lower() in first_line:
                return False

        # Check for Python-like patterns
        python_patterns = [
            "import ",
            "from ",
            "def ",
            "class ",
            '"""',
            "'''",
            "#",
            "@",
        ]

        # Check if it starts with something Python-like
        for pattern in python_patterns:
            if text.strip().startswith(pattern):
                return True

        # Try to compile it as a basic check
        try:
            compile(text, "<string>", "exec")
            return True
        except SyntaxError:
            # Might still be valid if it has imports at the top
            # Check if first non-empty lines look like Python
            lines = [line for line in text.strip().split("\n") if line.strip()]
            if lines:
                first_code_line = lines[0]
                for pattern in python_patterns:
                    if pattern in first_code_line:
                        return True
            return False

    async def query_claude(
        self, prompt: str, system_prompt: str | None = None, timeout: int | None = None, show_progress: bool = True
    ) -> str:
        """Query Claude for generation with proper error handling.

        Args:
            prompt: The main prompt for Claude
            system_prompt: Optional system prompt for context (defaults to code generation)
            timeout: Timeout in seconds (default: uses instance timeout)
            show_progress: Whether to show real-time progress indicators (default: True)

        Returns:
            str: The generated response from Claude, cleaned and ready to use

        Raises:
            RuntimeError: If Claude SDK is not available or operation fails
            KeyboardInterrupt: If user interrupts with Ctrl+C
        """
        max_retries = 3
        enforced_system_prompt = system_prompt or self._default_system_prompt()
        enforced_prompt = prompt

        for attempt in range(max_retries):
            try:
                # Use the battle-tested claude_sdk module with progress indicators
                response = await claude_sdk.query_claude(
                    prompt=enforced_prompt,
                    system_prompt=enforced_system_prompt,
                    timeout=timeout or self.timeout,
                    show_progress=show_progress,
                )

                # Validate that we got Python code, not conversational text
                if self._is_valid_python_code(response):
                    self.logger.debug(f"Successfully generated {len(response)} characters of valid Python code")
                    return response

                # If not valid Python, retry with stronger prompt
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1}: Response was not valid Python code, retrying...")
                    # Add enforcement to the prompt
                    enforced_prompt = f"OUTPUT ONLY PYTHON CODE. NO EXPLANATIONS.\n\n{prompt}"
                    enforced_system_prompt = (
                        "You are a Python code generator. Output ONLY valid, executable Python code. "
                        "DO NOT include ANY explanatory text or markdown. Start directly with imports or code."
                    )
                else:
                    raise RuntimeError(
                        "Claude SDK returned conversational text instead of Python code.\n"
                        "Response started with: " + response[:100] + "...\n"
                        "This is a known issue with the Claude SDK. Try running inside Claude Code environment."
                    )

            except KeyboardInterrupt:
                # Re-raise keyboard interrupt as-is for clean shutdown
                self.logger.info("Generation cancelled by user")
                raise
            except RuntimeError as e:
                if "instead of Python code" in str(e) or attempt == max_retries - 1:
                    # Re-raise with generator context
                    self.logger.error(f"Generation failed: {e}")
                    raise RuntimeError(f"{self.__class__.__name__} generation failed: {e}") from e
                # Otherwise, let it retry

        raise RuntimeError(f"Failed to generate valid Python code after {max_retries} attempts")

    def query_claude_sync(
        self, prompt: str, system_prompt: str | None = None, timeout: int | None = None, show_progress: bool = True
    ) -> str:
        """Synchronous wrapper for query_claude for non-async contexts.

        Args:
            prompt: The main prompt for Claude
            system_prompt: Optional system prompt for context
            timeout: Timeout in seconds (default: uses instance timeout)
            show_progress: Whether to show real-time progress indicators (default: True)

        Returns:
            str: The generated response from Claude

        Raises:
            RuntimeError: If Claude SDK is not available or operation fails
            KeyboardInterrupt: If user interrupts with Ctrl+C
        """
        return claude_sdk.query_claude_sync(
            prompt=prompt,
            system_prompt=system_prompt or self._default_system_prompt(),
            timeout=timeout or self.timeout,
            show_progress=show_progress,
        )

    def format_prompt(self, template: str, **kwargs: Any) -> str:
        """Format a prompt template with provided values.

        Uses simple Python string formatting with {key} placeholders.

        Args:
            template: Template string with {key} placeholders
            **kwargs: Values to substitute into the template

        Returns:
            str: Formatted prompt ready for Claude

        Example:
            >>> generator.format_prompt(
            ...     "Generate a {type} for {name}",
            ...     type="class",
            ...     name="UserService"
            ... )
            "Generate a class for UserService"
        """
        try:
            formatted = template.format(**kwargs)
            self.logger.debug(f"Formatted prompt: {len(formatted)} characters")
            return formatted
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to format prompt template: {e}") from e

    def save_output(self, content: str, path: Path | str) -> None:
        """Save generated content to file with resilient I/O.

        Handles cloud sync issues (OneDrive, Dropbox) with automatic retry.
        Creates parent directories as needed.

        Args:
            content: The content to save
            path: Path to save the file to

        Raises:
            OSError: If save fails after retries
        """
        path = Path(path)

        try:
            # Use file_io for resilient writing
            file_io.write_text(content, path)
            self.logger.info(f"Saved output to {path}")

        except OSError as e:
            self.logger.error(f"Failed to save output to {path}: {e}")
            raise

    def save_json(self, data: dict[str, Any], path: Path | str) -> None:
        """Save data as JSON with resilient I/O.

        Args:
            data: Dictionary to save as JSON
            path: Path to save the file to

        Raises:
            OSError: If save fails after retries
            TypeError: If data is not JSON serializable
        """
        path = Path(path)

        try:
            file_io.write_json(data, path)
            self.logger.info(f"Saved JSON to {path}")

        except (OSError, TypeError) as e:
            self.logger.error(f"Failed to save JSON to {path}: {e}")
            raise

    def save_yaml(self, data: dict[str, Any], path: Path | str) -> None:
        """Save data as YAML with resilient I/O.

        Args:
            data: Dictionary to save as YAML
            path: Path to save the file to

        Raises:
            OSError: If save fails after retries
            yaml.YAMLError: If data cannot be serialized to YAML
        """
        path = Path(path)

        try:
            file_io.write_yaml(data, path)
            self.logger.info(f"Saved YAML to {path}")

        except (OSError, Exception) as e:
            self.logger.error(f"Failed to save YAML to {path}: {e}")
            raise

    def _default_system_prompt(self) -> str:
        """Get the default system prompt for this generator.

        Subclasses can override to provide specialized prompts.

        Returns:
            str: Default system prompt for code generation
        """
        return (
            "You are a Python code generator. You MUST output ONLY valid Python code. "
            "DO NOT include any explanatory text, markdown, or conversational responses. "
            "DO NOT start with phrases like 'I'll generate' or 'Here is'. "
            "Output ONLY the raw Python code with proper imports, classes, and functions. "
            "The response must be immediately executable Python code. "
            "Every function must be fully implemented - no stubs or placeholders."
        )

    def validate_context(self, context: GeneratorContext) -> None:
        """Validate the generation context before processing.

        Subclasses can override to add specific validation.

        Args:
            context: The context to validate

        Raises:
            ValueError: If context is invalid
        """
        if not context.name:
            raise ValueError("Module name is required")

        if not context.output_dir:
            raise ValueError("Output directory is required")

        # Ensure output directory exists
        Path(context.output_dir).mkdir(parents=True, exist_ok=True)
