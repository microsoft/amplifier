"""Claude SDK helper with streaming, no-timeout, and progress tracking capabilities.

This example showcases best practices using the CCSDK defensive utilities for
robust LLM response handling.
"""

from collections.abc import Callable
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json


async def query_claude_with_timeout(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    parse_json: bool = False,
    stream_output: bool = False,
    progress_callback: Callable[[str], None] | None = None,
    max_turns: int = 1,
    verbose: bool = False,
) -> Any:
    """Query Claude with streaming support.

    Args:
        prompt: The user prompt
        system_prompt: System prompt for context
        parse_json: Whether to parse response as JSON
        stream_output: Enable real-time streaming output
        progress_callback: Optional callback for progress updates
        max_turns: Maximum conversation turns
        verbose: Enable verbose output for debugging

    Returns:
        SessionResponse or parsed JSON dict
    """
    if verbose:
        print(f"[Claude Query] Max turns: {max_turns}")
        print(f"[Claude Query] Streaming: {stream_output}, Has callback: {progress_callback is not None}")

    options = SessionOptions(
        system_prompt=system_prompt,
        retry_attempts=2,
        max_turns=max_turns,
        stream_output=stream_output,
        progress_callback=progress_callback,
    )

    async with ClaudeSession(options) as session:
        # Query with optional streaming
        response = await session.query(prompt, stream=stream_output)

        if response.error:
            raise RuntimeError(f"Claude query failed: {response.error}")

        if not response.content:
            raise RuntimeError("Received empty response from Claude")

        # Include metadata if available (for cost tracking, etc.)
        if verbose and response.metadata:
            print(f"[Claude Query] Metadata: {response.metadata}")

        if parse_json:
            # Use defensive parsing with graceful fallback
            # This handles markdown blocks, mixed text, and various JSON formats automatically
            return parse_llm_json(response.content, default=[], verbose=verbose)

        return response


# New helper function for complex multi-stage operations
async def query_claude_streaming(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """Simplified streaming query helper for real-time visibility.

    Args:
        prompt: The user prompt
        system_prompt: System prompt for context
        on_chunk: Optional callback for each chunk of text

    Returns:
        Complete response text
    """
    options = SessionOptions(
        system_prompt=system_prompt,
        stream_output=True,  # Always stream
        progress_callback=on_chunk,  # Handle chunks
        max_turns=1,
    )

    async with ClaudeSession(options) as session:
        response = await session.query(prompt)
        if response.error:
            raise RuntimeError(f"Claude query failed: {response.error}")
        return response.content
