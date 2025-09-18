"""Utility functions for CCSDK Core module."""

import asyncio
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import TypeVar

T = TypeVar("T")


def check_claude_cli() -> tuple[bool, str]:
    """Check if Claude CLI is installed and accessible.

    Returns:
        Tuple of (is_available, path_or_error_message)

    Example:
        >>> available, info = check_claude_cli()
        >>> if available:
        ...     print(f"Claude CLI found at: {info}")
        ... else:
        ...     print(f"Claude CLI not available: {info}")
    """
    # Check if claude CLI is available in PATH
    claude_path = shutil.which("claude")
    if claude_path:
        return True, claude_path

    # Check common installation locations
    known_locations = [
        Path.home() / ".local/share/reflex/bun/bin/claude",
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
        Path.home() / ".nvm/versions/node" / "*" / "bin/claude",  # Pattern for nvm
    ]

    for loc in known_locations:
        # Handle glob patterns
        if "*" in str(loc):
            import glob

            matches = glob.glob(str(loc))
            for match in matches:
                match_path = Path(match)
                if match_path.exists() and os.access(match_path, os.X_OK):
                    return True, str(match_path)
        else:
            if loc.exists() and os.access(loc, os.X_OK):
                return True, str(loc)

    return False, (
        "Claude CLI not found. Install with one of:\n"
        "  - npm install -g @anthropic-ai/claude-code\n"
        "  - bun install -g @anthropic-ai/claude-code"
    )


async def query_with_retry(
    func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    **kwargs,
) -> Any:
    """Execute an async function with exponential backoff retry.

    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay between retries in seconds (default: 1.0)
        **kwargs: Keyword arguments for the function

    Returns:
        Result from the function

    Raises:
        The last exception if all retries fail

    Example:
        >>> async def flaky_operation():
        ...     # Some operation that might fail
        ...     return "success"
        >>> result = await query_with_retry(flaky_operation, max_attempts=5)
    """
    delay = initial_delay
    last_error = None

    for attempt in range(max_attempts):
        try:
            # Execute function directly - trust in natural completion
            result = await func(*args, **kwargs)
            return result

        except Exception as e:
            last_error = e

        # Wait before retry (except on last attempt)
        if attempt < max_attempts - 1:
            await asyncio.sleep(delay)
            delay *= 2  # Exponential backoff

    # All retries exhausted
    if last_error:
        raise last_error
    raise RuntimeError(f"Failed after {max_attempts} attempts")
