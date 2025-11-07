"""Session Monitor Package

Provides automatic token usage tracking, session termination, and checkpoint/resume functionality
for Claude Code sessions to prevent context loss due to token limits.
"""

from .cli import cli
from .daemon import SessionMonitorDaemon
from .models import MonitorConfig
from .models import SessionState
from .models import TerminationRequest
from .models import TokenUsageSnapshot
from .token_tracker import TokenTracker

__all__ = [
    "TerminationRequest",
    "SessionState",
    "TokenUsageSnapshot",
    "MonitorConfig",
    "TokenTracker",
    "SessionMonitorDaemon",
    "cli",
]
