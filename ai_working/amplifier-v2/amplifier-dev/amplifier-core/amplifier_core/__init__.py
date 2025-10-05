"""Amplifier Core - Kernel infrastructure for plugin-based system.

Simple, direct implementation providing:
- Plugin discovery and lifecycle management
- Message bus for async pub/sub
- Model provider and tool registries
- Clean interface contracts
"""

from .interfaces import BaseModelProvider
from .interfaces import BaseTool
from .interfaces import BaseWorkflow
from .kernel import Kernel
from .message_bus import Event
from .message_bus import MessageBus
from .plugin import AmplifierModule
from .plugin import discover_modules

__version__ = "0.1.0"

__all__ = [
    # Core kernel
    "Kernel",
    # Plugin system
    "AmplifierModule",
    "discover_modules",
    # Message bus
    "MessageBus",
    "Event",
    # Interfaces
    "BaseModelProvider",
    "BaseTool",
    "BaseWorkflow",
]
