"""
AI Evaluator Module

Uses Anthropic API directly for simple test evaluation.
"""

import os


class AIEvaluator:
    """Evaluate command outputs using AI."""

    def __init__(self, model: str | None = None):
        """Initialize with optional model override."""
        if model is None:
            from amplifier.config.models import models

            from .config import config

            model = models.get_model(config.model_category)

        self.model = model
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if AI evaluation is available."""
        if not self.api_key:
            print("  ⚠ AI evaluation unavailable (no ANTHROPIC_API_KEY)")
            return False

        try:
            import anthropic  # noqa: F401

            return True
        except ImportError:
            print("  ⚠ AI evaluation unavailable (anthropic package not installed)")
            return False

    def evaluate(self, command: str, output: str, success_criteria: str, timeout: int = 30) -> tuple[bool, str]:
        """Evaluate command output against success criteria.

        Args:
            command: The command that was run
            output: Combined stdout and stderr output
            success_criteria: Human-readable success criteria
            timeout: Timeout for AI evaluation

        Returns:
            Tuple of (passed, reasoning)
        """
        if not self.available:
            # Skip evaluation when AI unavailable
            from .config import config

            if config.skip_on_ai_unavailable:
                return True, "AI unavailable - skipping evaluation"
            return False, "AI unavailable - cannot evaluate"

        try:
            import anthropic

            # Truncate output if needed
            from .config import config

            if len(output) > config.max_output_chars:
                output = output[: config.max_output_chars] + "\n... (truncated)"

            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = f"""You are evaluating the output of a command to determine if it meets the success criteria.

Command run: {command}

Success Criteria: {success_criteria}

Command Output:
{output}

Based on the output, does this command meet the success criteria?
Respond with PASS or FAIL followed by a brief explanation (1-2 sentences).

Format: PASS|FAIL: Brief explanation"""

            response = client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
            )

            result = response.content[0].text.strip()

            # Parse response
            if result.upper().startswith("PASS"):
                reasoning = result.split(":", 1)[1].strip() if ":" in result else "Criteria met"
                return True, reasoning
            reasoning = result.split(":", 1)[1].strip() if ":" in result else "Criteria not met"
            return False, reasoning

        except Exception as e:
            # On error, return skip if configured
            from .config import config

            if config.skip_on_ai_unavailable:
                return True, f"AI evaluation error: {e}"
            return False, f"AI evaluation failed: {e}"
