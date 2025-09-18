"""
Module: agent

Purpose: Execute microtasks via Claude SDK

This module provides functionality to execute microtasks using the Claude Code SDK.
It handles SDK availability checking, context formatting, and proper timeout management.
"""

import asyncio
import json
import shutil
from typing import Optional, Dict, Any


class SDKNotAvailableError(Exception):
    """Raised when Claude SDK is not available"""

    def __init__(self, message: str = "Claude SDK is not available"):
        super().__init__(message)
        self.message = message


def check_sdk_available() -> bool:
    """Verify Claude CLI is present and accessible.

    Returns:
        bool: True if Claude CLI is available, False otherwise
    """
    # Check if claude CLI is available in PATH
    claude_path = shutil.which("claude")
    if claude_path:
        return True

    # Check common installation locations
    import os

    known_locations = [
        os.path.expanduser("~/.local/share/reflex/bun/bin/claude"),
        os.path.expanduser("~/.npm-global/bin/claude"),
        "/usr/local/bin/claude",
    ]

    for loc in known_locations:
        if os.path.exists(loc) and os.access(loc, os.X_OK):
            return True

    return False


def format_context(context: Dict[str, Any]) -> str:
    """Prepare context dictionary for inclusion in prompt.

    Args:
        context: Dictionary containing context information

    Returns:
        str: Formatted context string ready for prompt inclusion
    """
    if not context:
        return ""

    formatted_parts = []
    for key, value in context.items():
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)
        formatted_parts.append(f"**{key}**:\n{value_str}")

    return "\n\n".join(formatted_parts)


async def execute_task(prompt: str, context: Optional[Dict[str, Any]] = None, timeout: int = 120) -> str:
    """Execute a microtask using Claude SDK with progress monitoring.

    Args:
        prompt: The task prompt to execute
        context: Optional context dictionary to include with the prompt
        timeout: Timeout in seconds (default: 120)

    Returns:
        str: Task execution result

    Raises:
        SDKNotAvailableError: If Claude SDK is not available
        TimeoutError: If task execution exceeds timeout
        Exception: For other execution errors
    """
    # Check SDK availability first
    if not check_sdk_available():
        raise SDKNotAvailableError("Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code")

    # Try to import the SDK
    try:
        from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
    except ImportError:
        raise SDKNotAvailableError(
            "claude_code_sdk Python package not installed. Install with: pip install claude-code-sdk"
        )

    # Create progress monitor if context provides task_id and stage_name
    monitor = None
    monitor_task = None
    if context and "task_id" in context and "stage_name" in context:
        try:
            from amplifier_microtask.progress_monitor import ProgressMonitor

            monitor = ProgressMonitor(context["task_id"], context["stage_name"])
            monitor.start()
            # Start monitoring in background
            monitor_task = asyncio.create_task(monitor.monitor_heartbeat())
        except Exception:
            # Silently ignore if progress monitoring fails
            monitor = None

    # Format the full prompt with context
    full_prompt = prompt
    if context:
        context_str = format_context(context)
        if context_str:
            full_prompt = f"{context_str}\n\n{prompt}"

    # Add progress file path to prompt if monitor is active
    if monitor:
        full_prompt = f"{full_prompt}\n\n[System: You may write progress updates to {monitor.progress_file}]"

    try:
        # Execute with proper timeout
        async with asyncio.timeout(timeout):
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="You are an AI assistant executing a specific microtask. Focus on the task at hand and provide clear, actionable results.",
                    max_turns=1,
                )
            ) as client:
                # Send the query
                await client.query(full_prompt)

                # Collect the response
                response = ""
                async for message in client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    response += getattr(block, "text", "")

                # Clean up response if it contains markdown code blocks
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]  # Remove ```json
                elif response.startswith("```"):
                    response = response[3:]  # Remove ```

                if response.endswith("```"):
                    response = response[:-3]  # Remove trailing ```

                # Always return a string (even if empty)
                return response.strip() if response else ""

    except asyncio.TimeoutError:
        raise TimeoutError(
            f"Task execution timed out after {timeout} seconds. "
            "This may indicate the task is too complex or the SDK is not responding."
        )
    except Exception as e:
        # Re-raise with more context
        raise Exception(f"Task execution failed: {str(e)}") from e
    finally:
        # Stop monitoring and cleanup
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        # Keep progress file for debugging, clean up in post-processing

    # This should never be reached, but satisfies type checker
    return ""


# Convenience function for synchronous usage
def execute_task_sync(prompt: str, context: Optional[Dict[str, Any]] = None, timeout: int = 120) -> str:
    """Synchronous wrapper for execute_task.

    Args:
        prompt: The task prompt to execute
        context: Optional context dictionary to include with the prompt
        timeout: Timeout in seconds (default: 120)

    Returns:
        str: Task execution result

    Raises:
        SDKNotAvailableError: If Claude SDK is not available
        TimeoutError: If task execution exceeds timeout
        Exception: For other execution errors
    """
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we are, we can't use asyncio.run()
        raise RuntimeError(
            "execute_task_sync cannot be called from an async context. Use execute_task directly instead."
        )
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(execute_task(prompt, context, timeout))


# Module initialization - check SDK availability on import
_sdk_available = check_sdk_available()
if not _sdk_available:
    import warnings

    warnings.warn(
        "Claude CLI not detected. The agent module requires the Claude CLI to be installed. "
        "Install with: npm install -g @anthropic-ai/claude-code",
        RuntimeWarning,
        stacklevel=2,
    )
