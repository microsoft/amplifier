"""
Plugin registration for UltraThink Tool

Registers the UltraThink workflow tool with the Amplifier kernel.
"""

from amplifier_core import AmplifierModule
from amplifier_core import Kernel
from .ultra_think import UltraThinkTool


class Plugin(AmplifierModule):
    """
    UltraThink tool plugin for Amplifier.

    This plugin registers the UltraThink workflow tool which provides
    deep multi-perspective analysis capabilities.
    """

    version = "0.1.0"
    description = "Multi-step reasoning workflow for deep analysis and brainstorming"

    def __init__(self, kernel):
        """Initialize the ultra think plugin."""
        super().__init__(kernel)
        self.name = "ultra_think_tool"
        self.tool = None

    async def initialize(self):
        """Initialize and register the ultra think tool."""
        self.tool = UltraThinkTool(self.kernel)
        self.kernel.register_tool(self.tool.name, self.tool)
        if hasattr(self.kernel, 'logger'):
            self.kernel.logger.info(f"UltraThink tool initialized as '{self.tool.name}'")

    async def shutdown(self):
        """Clean up resources."""
        # Remove the tool from the registry
        if self.tool and "ultra_think" in self.kernel.tools:
            # remove_tool doesn't exist in kernel, just delete from dict
            del self.kernel.tools["ultra_think"]
            if hasattr(self.kernel, 'logger'):
                self.kernel.logger.info("UltraThink tool shut down")

    async def register(self, kernel: Kernel) -> None:
        """
        Register the UltraThink tool in the kernel.

        This makes the tool available via the kernel's tool registry,
        allowing it to be invoked by agents, workflows, or directly via CLI.

        Args:
            kernel: The Amplifier kernel instance
        """
        # Create and register the tool
        tool = UltraThinkTool(kernel)
        kernel.register_tool(tool.name, tool)

        # Log successful registration
        if hasattr(kernel, 'logger'):
            kernel.logger.info(f"UltraThink tool registered successfully as '{tool.name}'")

    async def unregister(self, kernel: Kernel) -> None:
        """
        Unregister the UltraThink tool from the kernel.

        Args:
            kernel: The Amplifier kernel instance
        """
        # Remove the tool from the registry
        if "ultra_think" in kernel.tools:
            # remove_tool doesn't exist in kernel, just delete from dict
            del kernel.tools["ultra_think"]

            if hasattr(kernel, 'logger'):
                kernel.logger.info("UltraThink tool unregistered successfully")

    async def health_check(self) -> bool:
        """
        Check if the plugin is healthy and operational.

        Returns:
            True if the plugin is operational, False otherwise
        """
        # Basic health check - verify the tool class is importable
        try:
            from .ultra_think import UltraThinkTool
            return True
        except ImportError:
            return False