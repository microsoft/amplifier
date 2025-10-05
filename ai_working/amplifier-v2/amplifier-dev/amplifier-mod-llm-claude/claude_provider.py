"""Claude LLM provider implementation."""

import os

from amplifier_core.interfaces.model import BaseModelProvider
from anthropic import AsyncAnthropic


class ClaudeProvider(BaseModelProvider):
    """Provider for Anthropic's Claude models."""

    def __init__(self, model: str = "claude-3-opus-20240229", api_key: str | None = None):
        """Initialize the Claude provider.

        Args:
            model: The Claude model to use
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = AsyncAnthropic(api_key=self.api_key)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from Claude.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (max_tokens, temperature, etc.)

        Returns:
            The generated text response
        """
        # Extract common parameters with defaults
        max_tokens = kwargs.get("max_tokens", 1000)
        temperature = kwargs.get("temperature", 0.7)

        # Create the message
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from response
        return message.content[0].text
