"""
Claude integration module for Amplifier.

Provides session awareness and coordination capabilities for Claude Code.
"""

from .session_awareness import SessionActivity
from .session_awareness import SessionAwareness

__all__ = ["SessionAwareness", "SessionActivity"]
