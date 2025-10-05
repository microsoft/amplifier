"""Plugin registration for Claude LLM provider."""

from amplifier_core.kernel import AmplifierKernel
from amplifier_core.plugin import AmplifierModule

from .claude_provider import ClaudeProvider


class Plugin(AmplifierModule):
    """Claude provider plugin for Amplifier."""

    async def register(self, kernel: AmplifierKernel) -> None:
        """Register Claude model provider with the kernel.

        Args:
            kernel: The Amplifier kernel to register with
        """
        provider = ClaudeProvider()
        await kernel.add_model_provider("claude", provider)
