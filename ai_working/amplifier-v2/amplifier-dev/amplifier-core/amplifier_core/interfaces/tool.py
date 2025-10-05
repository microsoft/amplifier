"""Base interface for tools.

Simple contract for executable tools.
"""

from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name used for registration and invocation."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass

    @abstractmethod
    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Result dictionary
        """
        pass
