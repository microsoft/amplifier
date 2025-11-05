"""
Module: CCSDK Sessions

Session state management and persistence.
See README.md for full contract specification.

Basic Usage:
    >>> from amplifier.ccsdk_toolkit.sessions import SessionManager
    >>> manager = SessionManager()
    >>> session = manager.create_session("my-task")
    >>> session.save()
"""

from .manager import SessionManager
from .models import SessionMetadata
from .models import SessionState

__all__ = ["SessionManager", "SessionState", "SessionMetadata"]
