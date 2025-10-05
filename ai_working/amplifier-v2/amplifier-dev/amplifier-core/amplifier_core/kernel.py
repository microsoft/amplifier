"""Core kernel for the Amplifier system.

Manages plugin lifecycle, registries, and message bus integration.
Simple, direct implementation following ruthless simplicity principle.
"""

import logging

from .interfaces.model import BaseModelProvider
from .interfaces.tool import BaseTool
from .message_bus import Event
from .message_bus import MessageBus
from .plugin import AmplifierModule
from .plugin import discover_modules

logger = logging.getLogger(__name__)


class Kernel:
    """Core kernel that manages plugins, providers, and system lifecycle."""

    def __init__(self) -> None:
        """Initialize the kernel with empty registries."""
        self.message_bus = MessageBus()
        self.model_providers: dict[str, BaseModelProvider] = {}
        self.tools: dict[str, BaseTool] = {}
        self.modules: list[AmplifierModule] = []
        self._running = False

    async def load_modules(self) -> None:
        """Discover and load all available modules via entry points."""
        discovered = discover_modules()

        for module_class in discovered:
            try:
                module = module_class(self)
                await module.initialize()
                self.modules.append(module)
                logger.info(f"Loaded module: {module.name}")
            except Exception as e:
                logger.error(f"Failed to load module {module_class.__name__}: {e}")

    async def load_modules_by_name(self, module_names: list[str]) -> None:
        """Load specific modules by their entry point names.

        Args:
            module_names: List of module entry point names to load
        """
        from importlib.metadata import entry_points

        # Get all entry points in the amplifier.modules group
        eps = entry_points(group="amplifier.modules")

        # Track which modules were requested
        requested = set(module_names)
        loaded = set()

        for ep in eps:
            if ep.name not in requested:
                continue

            try:
                # Load the module class
                module_class = ep.load()

                # Verify it's a subclass of AmplifierModule
                if not issubclass(module_class, AmplifierModule):
                    logger.warning(f"Entry point {ep.name} does not inherit from AmplifierModule")
                    continue

                # Check if already loaded
                if any(isinstance(m, module_class) for m in self.modules):
                    logger.debug(f"Module {ep.name} already loaded, skipping")
                    loaded.add(ep.name)
                    continue

                # Create and initialize the module
                module = module_class(self)
                await module.initialize()
                self.modules.append(module)
                loaded.add(ep.name)
                logger.info(f"Loaded module: {ep.name}")

            except Exception as e:
                logger.error(f"Failed to load module {ep.name}: {e}")

        # Warn about requested modules that weren't found
        not_found = requested - loaded
        if not_found:
            logger.warning(f"Modules not found: {', '.join(not_found)}")

    def register_model_provider(self, name: str, provider: BaseModelProvider) -> None:
        """Register a model provider."""
        self.model_providers[name] = provider
        logger.debug(f"Registered model provider: {name}")

    def register_tool(self, name: str, tool: BaseTool) -> None:
        """Register a tool."""
        self.tools[name] = tool
        logger.debug(f"Registered tool: {name}")

    async def start(self) -> None:
        """Start the kernel and all modules."""
        if self._running:
            return

        logger.info("Starting kernel...")
        self._running = True

        # Load modules
        await self.load_modules()

        # Publish start event
        await self.message_bus.publish(Event(type="kernel.started", data={}, source="kernel"))

        logger.info("Kernel started successfully")

    async def shutdown(self) -> None:
        """Shutdown the kernel and all modules."""
        if not self._running:
            return

        logger.info("Shutting down kernel...")

        # Publish shutdown event
        await self.message_bus.publish(Event(type="kernel.shutdown", data={}, source="kernel"))

        # Shutdown modules in reverse order
        for module in reversed(self.modules):
            try:
                await module.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down module {module.name}: {e}")

        self._running = False
        logger.info("Kernel shutdown complete")

    def get_model_provider(self, name: str) -> BaseModelProvider | None:
        """Get a registered model provider by name."""
        return self.model_providers.get(name)

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a registered tool by name."""
        return self.tools.get(name)
