"""Stream handler for Claude Code SDK responses with activity detection and progress feedback.

This module provides a simple, robust way to handle streaming responses from the Claude Code SDK
with visibility into progress and automatic timeout handling for idle connections.
"""

import asyncio
import time
from collections.abc import AsyncIterator
from collections.abc import Callable
from typing import Any


async def handle_streaming_response(
    response_iterator: AsyncIterator,
    timeout_seconds: int = 300,
    idle_timeout: int = 30,
    progress_callback: Callable[[int, int], None] | None = None,
) -> str:
    """Handle streaming response from Claude Code SDK with activity detection.

    Args:
        response_iterator: Async iterator from SDK client.receive_response()
        timeout_seconds: Maximum total time to wait for complete response
        idle_timeout: Maximum time to wait between chunks before timeout
        progress_callback: Optional callback(chunks, total_chars) for progress updates

    Returns:
        Complete response string assembled from all chunks

    Raises:
        asyncio.TimeoutError: If idle_timeout or timeout_seconds exceeded

    Example:
        >>> async with ClaudeSDKClient(options) as client:
        ...     await client.query(prompt)
        ...     response = await handle_streaming_response(
        ...         client.receive_response(),
        ...         timeout_seconds=120,
        ...         idle_timeout=30
        ...     )
    """
    response = ""
    chunks_received = 0
    last_activity = time.time()
    last_progress_report = time.time()
    start_time = time.time()

    # Default progress callback - print dots
    if progress_callback is None:

        def default_progress(chunks: int, chars: int) -> None:
            print(".", end="", flush=True)

        progress_callback = default_progress

    try:
        async with asyncio.timeout(timeout_seconds):
            async for message in response_iterator:
                # Check idle timeout
                current_time = time.time()
                if current_time - last_activity > idle_timeout:
                    raise TimeoutError(f"No response chunks for {idle_timeout} seconds - connection may be stalled")

                # Extract text from message structure
                if hasattr(message, "content"):
                    content = getattr(message, "content", [])
                    if isinstance(content, list):
                        for block in content:
                            if hasattr(block, "text"):
                                chunk = getattr(block, "text", "")
                                if chunk:
                                    response += chunk
                                    chunks_received += 1
                                    last_activity = current_time

                                    # Report progress every 5 seconds or on each chunk if small response
                                    if current_time - last_progress_report > 5 or chunks_received < 10:
                                        progress_callback(chunks_received, len(response))
                                        last_progress_report = current_time

                # Also check total timeout within loop
                if current_time - start_time > timeout_seconds:
                    raise TimeoutError(f"Total timeout of {timeout_seconds} seconds exceeded")

    except TimeoutError as e:
        # Distinguish between idle and total timeout
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            error_msg = f"Response timed out after {timeout_seconds} seconds (received {len(response)} chars in {chunks_received} chunks)"
        else:
            error_msg = f"Response stalled - no chunks for {idle_timeout} seconds (received {len(response)} chars in {chunks_received} chunks)"

        # Save partial results if any
        if response:
            error_msg += f"\nPartial response saved: {len(response)} characters"

        raise TimeoutError(error_msg) from e

    except Exception as e:
        # Include diagnostic info in any other errors
        error_msg = f"Streaming error after {chunks_received} chunks, {len(response)} chars: {str(e)}"
        raise RuntimeError(error_msg) from e

    finally:
        # Always print newline after progress dots
        if chunks_received > 0:
            print()  # Newline after progress indicators

    return response


async def handle_claude_sdk_response(
    client: Any, prompt: str, timeout_seconds: int = 300, idle_timeout: int = 30, verbose: bool = False
) -> str:
    """Convenience wrapper that handles the full SDK interaction pattern.

    Args:
        client: ClaudeSDKClient instance (already initialized)
        prompt: Prompt to send to Claude
        timeout_seconds: Maximum total time for response
        idle_timeout: Maximum idle time between chunks
        verbose: If True, print detailed progress info

    Returns:
        Complete response string from Claude

    Example:
        >>> async with ClaudeSDKClient(options) as client:
        ...     response = await handle_claude_sdk_response(
        ...         client,
        ...         "Generate a Python function",
        ...         timeout_seconds=120
        ...     )
    """
    # Define progress callback based on verbosity
    if verbose:

        def verbose_progress(chunks: int, chars: int) -> None:
            print(f"\rReceived {chunks} chunks, {chars} characters...", end="", flush=True)
    else:

        def verbose_progress(chunks: int, chars: int) -> None:
            print(".", end="", flush=True)

    # Send query
    await client.query(prompt)

    # Handle streaming response
    response = await handle_streaming_response(
        client.receive_response(),
        timeout_seconds=timeout_seconds,
        idle_timeout=idle_timeout,
        progress_callback=verbose_progress if verbose else None,
    )

    return response
