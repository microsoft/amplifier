"""Clarification handling for multi-turn interactions.

This module provides different strategies for handling clarification requests
from the Claude SDK during module generation.
"""

import json
import sys
from typing import Any
from typing import Protocol

from .response_parser import ParsedQuestion


class ClarificationStrategy(Protocol):
    """Protocol for clarification handling strategies."""

    async def get_clarification(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Get clarification for a question.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            The clarification response
        """
        ...


class AutoClarificationHandler:
    """Handles clarification automatically using Claude SDK.

    This handler uses a nested Claude SDK call to automatically
    answer clarification questions based on the module spec and context.
    """

    def __init__(self, claude_sdk=None):
        """Initialize auto clarification handler.

        Args:
            claude_sdk: Claude SDK instance for nested calls
        """
        self.claude_sdk = claude_sdk

    async def get_clarification(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Get automatic clarification using Claude SDK.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            The clarification response
        """
        if not self.claude_sdk:
            # Fallback to reasonable defaults
            return self._get_default_answer(question, context)

        # Build prompt for clarification
        prompt = self._build_clarification_prompt(question, context)

        # Use nested SDK call to get answer
        try:
            response = await self.claude_sdk.query(prompt, max_turns=1)
            return self._extract_answer(response) or self._get_default_answer(question, context)
        except Exception as e:
            # Fallback to defaults on error
            print(f"Auto-clarification failed: {e}", file=sys.stderr)
            return self._get_default_answer(question, context)

    def _build_clarification_prompt(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Build prompt for clarification request.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            Prompt for Claude SDK
        """
        module_spec = context.get("module_spec", {})

        prompt = f"""You are helping to generate a software module.
The module implementer has asked a clarification question while working on the implementation.

Module Specification:
{json.dumps(module_spec, indent=2)}

Question: {question.question}

Context: {question.context}
"""

        if question.options:
            prompt += "\nOptions provided:\n"
            for i, option in enumerate(question.options, 1):
                prompt += f"{i}. {option}\n"
            prompt += "\nSelect the most appropriate option or provide a specific answer."

        prompt += """
Provide a clear, concise answer to help the implementation proceed.
Focus on practical choices that align with the module specification.
If options are provided, select the most appropriate one.
Answer directly without explanation unless necessary.
"""

        return prompt

    def _extract_answer(self, response: str) -> str | None:
        """Extract answer from Claude SDK response.

        Args:
            response: Raw response from Claude SDK

        Returns:
            Extracted answer or None
        """
        if not response:
            return None

        # Clean response
        answer = response.strip()

        # If it's a numbered choice, extract it
        if answer.startswith(("1", "2", "3", "4", "5")):
            # Extract just the choice text
            parts = answer.split(".", 1)
            if len(parts) > 1:
                answer = parts[1].strip()

        return answer

    def _get_default_answer(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Get default answer based on common patterns.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            Default answer
        """
        question_lower = question.question.lower()

        # Common implementation decisions
        if "async" in question_lower or "sync" in question_lower:
            return "Use async/await pattern for better scalability"

        if "error handling" in question_lower:
            return "Raise specific exceptions with clear messages"

        if "logging" in question_lower:
            return "Use Python's logging module with appropriate levels"

        if "configuration" in question_lower:
            return "Use environment variables with sensible defaults"

        if "test" in question_lower:
            return "Include comprehensive unit tests with pytest"

        # If options provided, pick first reasonable one
        if question.options and len(question.options) > 0:
            return question.options[0]

        # Generic default
        return "Proceed with the simplest working implementation"


class InteractiveClarificationHandler:
    """Handles clarification through interactive user input.

    This handler prompts the user directly for clarification
    when questions arise during module generation.
    """

    def __init__(self, input_func=None, output_func=None):
        """Initialize interactive clarification handler.

        Args:
            input_func: Function for getting user input (default: input)
            output_func: Function for displaying output (default: print)
        """
        self.input_func = input_func or input
        self.output_func = output_func or print

    async def get_clarification(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Get clarification through user interaction.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            The clarification response from user
        """
        # Display question
        self.output_func("\n" + "=" * 60)
        self.output_func("CLARIFICATION NEEDED")
        self.output_func("=" * 60)
        self.output_func(f"\nQuestion: {question.question}\n")

        if question.context:
            self.output_func(f"Context: {question.context}\n")

        # Display options if available
        if question.options:
            self.output_func("Options:")
            for i, option in enumerate(question.options, 1):
                self.output_func(f"  {i}. {option}")
            self.output_func("\nEnter option number or custom answer:")
        else:
            self.output_func("Please provide an answer:")

        # Get user input
        answer = self.input_func().strip()

        # Handle numbered option selection
        if answer.isdigit() and question.options:
            option_num = int(answer) - 1
            if 0 <= option_num < len(question.options):
                answer = question.options[option_num]

        self.output_func("=" * 60 + "\n")

        return answer


class HybridClarificationHandler:
    """Hybrid handler that tries auto-clarification first, falls back to interactive.

    This handler attempts automatic clarification but can fall back
    to interactive mode if confidence is low or auto-clarification fails.
    """

    def __init__(
        self,
        auto_handler: AutoClarificationHandler,
        interactive_handler: InteractiveClarificationHandler,
        confidence_threshold: float = 0.7,
    ):
        """Initialize hybrid clarification handler.

        Args:
            auto_handler: Automatic clarification handler
            interactive_handler: Interactive clarification handler
            confidence_threshold: Minimum confidence for auto-clarification
        """
        self.auto_handler = auto_handler
        self.interactive_handler = interactive_handler
        self.confidence_threshold = confidence_threshold

    async def get_clarification(self, question: ParsedQuestion, context: dict[str, Any]) -> str:
        """Get clarification using hybrid approach.

        Args:
            question: The question requiring clarification
            context: Current conversation context

        Returns:
            The clarification response
        """
        # Try auto-clarification first
        try:
            auto_answer = await self.auto_handler.get_clarification(question, context)

            # Check if we should confirm with user
            if self._should_confirm(question, auto_answer):
                print(f"\nSuggested answer: {auto_answer}")
                confirm = input("Accept this answer? (y/n): ").strip().lower()

                if confirm == "y":
                    return auto_answer
                # Fall back to interactive
                return await self.interactive_handler.get_clarification(question, context)

            return auto_answer

        except Exception:
            # Fall back to interactive on any error
            return await self.interactive_handler.get_clarification(question, context)

    def _should_confirm(self, question: ParsedQuestion, answer: str) -> bool:
        """Determine if auto-answer should be confirmed.

        Args:
            question: The original question
            answer: The auto-generated answer

        Returns:
            True if confirmation needed
        """
        # Confirm for critical decisions
        critical_keywords = ["security", "authentication", "database", "api", "production"]
        question_lower = question.question.lower()

        return any(keyword in question_lower for keyword in critical_keywords)
