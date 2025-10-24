"""
Codex tools wrapper - imports from .codex/tools/agent_context_bridge.py

This module provides a clean import path for agent context bridge utilities.
"""

import sys
from pathlib import Path

# Add .codex/tools to path
codex_tools_path = Path(__file__).parent.parent / ".codex" / "tools"
if str(codex_tools_path) not in sys.path:
    sys.path.insert(0, str(codex_tools_path))

# Import and re-export functions
try:
    from agent_context_bridge import cleanup_context_files
    from agent_context_bridge import extract_agent_result
    from agent_context_bridge import inject_context_to_agent
    from agent_context_bridge import serialize_context
    from agent_context_bridge import AgentContextBridge

    __all__ = [
        "AgentContextBridge",
        "serialize_context",
        "inject_context_to_agent",
        "extract_agent_result",
        "cleanup_context_files",
    ]
except ImportError as e:
    # Raise ImportError with helpful message
    raise ImportError(
        f"Failed to import agent context bridge: {e}. "
        "Ensure .codex/tools/agent_context_bridge.py exists."
    ) from e
