"""Plugin registration for OpenAI provider."""

import logging

from amplifier_core.plugin import AmplifierModule

from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class Plugin(AmplifierModule):
    """OpenAI provider plugin for Amplifier."""

    async def initialize(self) -> None:
        """Register OpenAI model provider with the kernel."""
        try:
            # Create provider instance
            provider = OpenAIProvider()

            # Register with kernel
            self.kernel.register_model_provider("openai", provider)

            logger.info("OpenAI provider registered successfully")
        except ValueError as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
