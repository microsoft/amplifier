"""Base interface for workflows.

Simple contract for multi-step processes.
"""

from abc import ABC
from abc import abstractmethod
from typing import Any


class BaseWorkflow(ABC):
    """Abstract base class for workflows."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Workflow name."""
        pass

    @property
    @abstractmethod
    def steps(self) -> list[str]:
        """List of step names in execution order."""
        pass

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the workflow with given context.

        Args:
            context: Initial workflow context

        Returns:
            Final workflow result
        """
        pass

    async def execute_step(self, step: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single workflow step. Override for custom behavior.

        Args:
            step: Step name
            context: Current workflow context

        Returns:
            Updated context
        """
        return context
