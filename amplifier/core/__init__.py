"""
Amplifier Core - Project context and session management.

Provides automatic project detection and persistent state management
for amplifier across multiple invocations.
"""

from .context import ProjectContext
from .context import detect_project_context

__all__ = ["ProjectContext", "detect_project_context"]
