"""
Module: CCSDK Config

Configuration management for agents, tools, and environment.
See README.md for full contract specification.

Basic Usage:
    >>> from amplifier.ccsdk_toolkit.config import AgentDefinition, ToolkitConfig
    >>> agent = AgentDefinition.from_string(
    ...     "Review code for quality",
    ...     name="code-reviewer"
    ... )
"""

from .loader import ConfigLoader
from .models import AgentConfig
from .models import AgentDefinition
from .models import EnvironmentConfig
from .models import MCPServerConfig
from .models import ToolConfig
from .models import ToolkitConfig
from .models import ToolPermissions

__all__ = [
    "AgentConfig",
    "AgentDefinition",
    "ToolConfig",
    "ToolkitConfig",
    "ToolPermissions",
    "MCPServerConfig",
    "EnvironmentConfig",
    "ConfigLoader",
]
