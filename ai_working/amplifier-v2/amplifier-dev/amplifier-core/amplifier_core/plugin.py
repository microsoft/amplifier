"""Plugin discovery and base class for Amplifier modules.

Simple plugin system using Python entry points for discovery.
"""

import logging
from abc import ABC
from abc import abstractmethod
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .kernel import Kernel

logger = logging.getLogger(__name__)


class AmplifierModule(ABC):
    """Abstract base class for all Amplifier modules."""

    def __init__(self, kernel: "Kernel") -> None:
        """Initialize module with kernel reference."""
        self.kernel = kernel
        self.name = self.__class__.__name__

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the module. Register providers, tools, subscriptions."""
        pass

    async def shutdown(self) -> None:  # noqa: B027
        """Cleanup when module is shutting down. Override if needed."""


def discover_modules() -> list[type[AmplifierModule]]:
    """Discover all installed modules via entry points.

    Looks for entry points in the 'amplifier.modules' group.
    Each entry point should reference a class that inherits from AmplifierModule.

    Returns:
        List of module classes ready to be instantiated.
    """
    modules: list[type[AmplifierModule]] = []

    # Get all entry points in the amplifier.modules group
    eps = entry_points(group="amplifier.modules")

    for ep in eps:
        try:
            # Load the module class
            module_class = ep.load()

            # Verify it's a subclass of AmplifierModule
            if not issubclass(module_class, AmplifierModule):
                logger.warning(f"Entry point {ep.name} does not inherit from AmplifierModule")
                continue

            modules.append(module_class)
            logger.debug(f"Discovered module: {ep.name}")

        except Exception as e:
            logger.error(f"Failed to load entry point {ep.name}: {e}")

    return modules
