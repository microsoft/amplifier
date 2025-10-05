"""Base interface for model providers.

Simple contract for LLM integration.
"""

from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseModelProvider(ABC):
    """Abstract base class for model providers."""

    @abstractmethod
    async def generate(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> str:
        """Generate a response from the model.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            **kwargs: Provider-specific parameters

        Returns:
            The generated text response
        """
        pass

    @abstractmethod
    def get_config(self) -> dict[str, Any]:
        """Get provider configuration.

        Returns:
            Configuration dictionary
        """
        pass
