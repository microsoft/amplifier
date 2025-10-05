"""Plugin registration for Agent Registry module.

This plugin provides agent discovery and registration capabilities.
"""

from typing import Any, Dict
import logging
from amplifier_core import AmplifierModule

logger = logging.getLogger(__name__)


class Plugin(AmplifierModule):
    """Plugin that manages agent registration and discovery."""

    def __init__(self, kernel):
        """Initialize the agent registry plugin."""
        super().__init__(kernel)
        self.name = "agent_registry"
        self.agents = {}
        self.enabled = True

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent with the registry.

        Args:
            name: The agent's identifier
            agent: The agent instance
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")

    def get_agent(self, name: str) -> Any:
        """Retrieve an agent from the registry.

        Args:
            name: The agent's identifier

        Returns:
            The agent instance or None if not found
        """
        return self.agents.get(name)

    def list_agents(self) -> list:
        """List all registered agents.

        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def enable(self) -> None:
        """Enable the agent registry."""
        self.enabled = True
        logger.info("Agent registry enabled")

    def disable(self) -> None:
        """Disable the agent registry."""
        self.enabled = False
        logger.info("Agent registry disabled")

    async def initialize(self):
        """Initialize the agent registry plugin."""
        # No initialization needed for this module
        logger.info("Agent registry plugin initialized")
        pass

    async def shutdown(self):
        """Clean up resources."""
        # Clear agent references
        self.agents.clear()
        logger.info("Agent registry plugin shut down")


def register(kernel: Any) -> None:
    """Register the agent registry plugin with the kernel.

    This function is called by the Amplifier kernel to register
    the plugin and provide agent management capabilities.

    Args:
        kernel: The Amplifier kernel instance
    """
    plugin = Plugin()

    # Register the plugin instance for management
    kernel.register_plugin("agent_registry", plugin)

    logger.info("Agent registry plugin registered successfully")