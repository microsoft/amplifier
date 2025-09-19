"""Claude SDK helper with streaming, no-timeout, and progress tracking capabilities."""

import json
from collections.abc import Callable
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions


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
            # Strip markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]

            if content.endswith("```"):
                content = content[:-3]

            content = content.strip()

            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from content if it's mixed with other text
                import re

                json_match = re.search(r"\[.*?\]", content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                # Return empty list for synthesizer to handle gracefully
                if verbose:
                    print(f"Warning: Failed to parse JSON response: {e}")
                return []

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
