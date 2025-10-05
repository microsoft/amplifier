"""Philosophy injection module for Amplifier.

This module automatically injects guiding principles and best practices
into AI prompts to ensure consistent behavior aligned with project philosophy.
"""

from .philosophy import PhilosophyModule
from .plugin import Plugin, register

__version__ = "0.1.0"

__all__ = [
    "PhilosophyModule",
    "Plugin",
    "register",
]