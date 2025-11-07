"""Session Monitor Package

Provides automatic token usage tracking, session termination, and checkpoint/resume functionality
for Claude Code sessions to prevent context loss due to token limits.
"""

from .cli import cli
from .daemon import SessionMonitorDaemon
from .models import MonitorConfig
from .models import TerminationRequest
from .models import TokenUsageSnapshot
from .token_tracker import TokenTracker

# Import SessionState from ccsdk_toolkit for compatibility
try:
    from ..ccsdk_toolkit.sessions.models import SessionState
except ImportError:
    SessionState = None  # Fallback if not available

__all__ = [
    "TerminationRequest",
    "TokenUsageSnapshot",
    "MonitorConfig",
    "TokenTracker",
    "SessionMonitorDaemon",
    "cli",
]

# Add SessionState if available
if SessionState is not None:
    __all__.append("SessionState")
