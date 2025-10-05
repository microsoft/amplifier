"""Claude LLM provider module for Amplifier.

Provides integration with Anthropic's Claude models as a model provider
for the Amplifier kernel.
"""

from .claude_provider import ClaudeProvider
from .plugin import Plugin

__all__ = ["ClaudeProvider", "Plugin"]

__version__ = "0.1.0"
