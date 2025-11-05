"""
Module: CCSDK Core

Core wrapper around claude_code_sdk with robust error handling.
See README.md for full contract specification.

Basic Usage:
    >>> from amplifier.ccsdk_toolkit.core import CCSDKSession
    >>> async with CCSDKSession(system_prompt="You are a helpful assistant") as session:
    ...     response = await session.query("Hello!")
"""

from .models import SessionOptions
from .models import SessionResponse
from .session import ClaudeSession
from .session import ClaudeSession as CCSDKSession  # Alias for requested naming
from .session import SDKNotAvailableError
from .session import SessionError
from .utils import check_claude_cli
from .utils import query_with_retry

__all__ = [
    "CCSDKSession",
    "ClaudeSession",
    "SessionError",
    "SDKNotAvailableError",
    "SessionResponse",
    "SessionOptions",
    "check_claude_cli",
    "query_with_retry",
]
