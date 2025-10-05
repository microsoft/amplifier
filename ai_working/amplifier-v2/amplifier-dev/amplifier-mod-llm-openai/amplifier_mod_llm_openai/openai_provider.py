"""OpenAI model provider implementation."""

import os
from typing import Any

from amplifier_core.interfaces.model import BaseModelProvider
from openai import AsyncOpenAI


class OpenAIProvider(BaseModelProvider):
    """Provider for OpenAI GPT models."""

    def __init__(self, model_name: str = "gpt-4", api_key: str | None = None):
        """Initialize OpenAI provider.

        Args:
            model_name: Model to use (default: gpt-4)
            api_key: API key (default: from OPENAI_API_KEY env var)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")

        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> str:
        """Generate a response using OpenAI's API.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Additional parameters for OpenAI API

        Returns:
            The generated text response
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        # Call OpenAI API
        response = await self.client.chat.completions.create(model=self.model_name, messages=messages, **kwargs)

        return response.choices[0].message.content

    def get_config(self) -> dict[str, Any]:
        """Get provider configuration.

        Returns:
            Configuration dictionary
        """
        return {"provider": "openai", "model": self.model_name, "api_key_configured": bool(self.api_key)}
