"""Plugin registration for philosophy injection module.

This plugin subscribes to prompt:before_send events and automatically
injects philosophy guidance into prompts.
"""

from typing import Any, Dict
import logging
from amplifier_core import AmplifierModule
from .philosophy import PhilosophyModule

logger = logging.getLogger(__name__)


class Plugin(AmplifierModule):
    """Plugin that injects philosophy guidance into AI prompts."""

    def __init__(self, kernel):
        """Initialize the philosophy plugin."""
        super().__init__(kernel)
        self.name = "philosophy"
        self.philosophy_module = PhilosophyModule()
        self.enabled = True

    def handle_prompt_before_send(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt:before_send events to inject philosophy.

        Args:
            event_data: Event data containing the prompt

        Returns:
            Modified event data with philosophy-enhanced prompt
        """
        if not self.enabled:
            return event_data

        try:
            # Extract the prompt from event data
            prompt = event_data.get("prompt", "")

            if prompt:
                # Inject philosophy guidance
                enhanced_prompt = self.philosophy_module.inject_guidance(prompt)
                event_data["prompt"] = enhanced_prompt
                logger.debug("Successfully injected philosophy guidance into prompt")

        except Exception as e:
            logger.error(f"Failed to inject philosophy guidance: {e}")
            # Return original event data on error

        return event_data

    def enable(self) -> None:
        """Enable philosophy injection."""
        self.enabled = True
        logger.info("Philosophy injection enabled")

    def disable(self) -> None:
        """Disable philosophy injection."""
        self.enabled = False
        logger.info("Philosophy injection disabled")

    def reload_documents(self) -> None:
        """Reload philosophy documents from disk."""
        self.philosophy_module.reload()

    async def initialize(self):
        """Initialize the philosophy plugin."""
        # Subscribe to prompt:before_send events
        self.kernel.message_bus.subscribe(
            "prompt:before_send",
            self.handle_prompt_before_send
        )
        logger.info("Philosophy plugin initialized successfully")

    async def shutdown(self):
        """Clean up resources."""
        # No cleanup needed for this module
        pass


def register(kernel: Any) -> None:
    """Register the philosophy plugin with the kernel.

    This function is called by the Amplifier kernel to register
    the plugin and subscribe to events.

    Args:
        kernel: The Amplifier kernel instance
    """
    plugin = Plugin()

    # Subscribe to prompt:before_send events
    kernel.message_bus.subscribe(
        "prompt:before_send",
        plugin.handle_prompt_before_send
    )

    # Register the plugin instance for management
    kernel.register_plugin("philosophy", plugin)

    logger.info("Philosophy plugin registered successfully")