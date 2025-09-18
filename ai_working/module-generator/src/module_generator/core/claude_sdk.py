"""Claude SDK wrapper module for Module Generator.

This module provides a reliable interface to the Claude Code SDK with:
- CRITICAL 120-second timeout (never less!)
- Markdown stripping from responses
- CLI availability checking
- Clear error messages with installation instructions
"""

import asyncio
import contextlib
import shutil
import subprocess
import time
from pathlib import Path


def check_cli_available() -> bool:
    """Check if the claude CLI is available in the system.

    Returns:
        bool: True if claude CLI is found, False otherwise

    Raises:
        RuntimeError: If CLI is not found with installation instructions
    """
    # First try using shutil.which (most reliable)
    if shutil.which("claude"):
        return True

    # Check common installation locations as fallback
    known_locations = [
        Path.home() / ".local/share/reflex/bun/bin/claude",
        Path.home() / ".npm-global/bin/claude",
        Path("/usr/local/bin/claude"),
    ]

    # Also check NVM paths if NVM is installed
    nvm_dir = Path.home() / ".nvm/versions/node"
    if nvm_dir.exists():
        for node_version in nvm_dir.iterdir():
            claude_path = node_version / "bin/claude"
            if claude_path.exists() and claude_path.is_file():
                known_locations.append(claude_path)

    for location in known_locations:
        if location.exists() and location.is_file():
            try:
                # Verify it's executable
                subprocess.run([str(location), "--version"], capture_output=True, timeout=2, check=False)
                return True
            except (subprocess.TimeoutExpired, OSError):
                continue

    # CLI not found - raise error with clear instructions
    raise RuntimeError(
        "Claude CLI not found. Install with one of:\n"
        "  - npm install -g @anthropic-ai/claude-code\n"
        "  - bun install -g @anthropic-ai/claude-code\n"
        "\n"
        "Then verify installation: which claude"
    )


def strip_markdown(text: str) -> str:
    """Remove markdown code block formatting from text.

    Claude often wraps code in markdown blocks like:
    ```python
    code here
    ```

    This function strips those wrappers.

    Args:
        text: The text that may contain markdown code blocks

    Returns:
        str: The text with markdown code blocks removed
    """
    if not text:
        return text

    text = text.strip()

    # Remove opening markdown fence
    if text.startswith("```python"):
        text = text[9:]  # Remove ```python
    elif text.startswith("```py"):
        text = text[5:]  # Remove ```py
    elif text.startswith("```"):
        text = text[3:]  # Remove generic ```

    # Remove closing markdown fence
    if text.endswith("```"):
        text = text[:-3]

    # Final strip to remove any remaining whitespace
    return text.strip()


async def check_sdk_available(timeout: int = 10) -> bool:
    """Check if Claude SDK is available and working.

    Args:
        timeout: Timeout in seconds for the check (default: 10)

    Returns:
        bool: True if SDK is available and working, False otherwise
    """
    # First check if CLI is available - will raise if not found
    try:
        check_cli_available()
    except RuntimeError:
        return False

    # Try a simple SDK call with timeout
    try:
        from claude_code_sdk import ClaudeCodeOptions
        from claude_code_sdk import ClaudeSDKClient

        async with asyncio.timeout(timeout):
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt="Test",
                    max_turns=1,
                )
            ) as client:
                await client.query("Say 'test'")
                # If we get here without timeout, SDK is working
                return True
    except Exception:
        return False


async def query_claude(
    prompt: str, system_prompt: str | None = None, timeout: int = 300, show_progress: bool = True
) -> str:
    """Query Claude using the Claude Code SDK with proper timeout and response cleaning.

    CRITICAL: Default timeout is 300 seconds (5 minutes). This is necessary for
    complex code generation tasks. Can be adjusted via the timeout parameter.

    Args:
        prompt: The prompt to send to Claude
        system_prompt: Optional system prompt for context
        timeout: Timeout in seconds (default: 300, range: 30-600)
        show_progress: Whether to show real-time progress indicators (default: True)

    Returns:
        str: The cleaned response from Claude with markdown stripped

    Raises:
        RuntimeError: If Claude CLI is not available or if operation times out
        KeyboardInterrupt: If user interrupts with Ctrl+C
    """
    # Validate timeout range
    if not (30 <= timeout <= 600):
        raise ValueError(f"Timeout must be between 30 and 600 seconds, got {timeout}")

    # Check if CLI is available first - will raise with instructions if not found
    check_cli_available()

    # Import the SDK (do this after CLI check to avoid import errors)
    try:
        from claude_code_sdk import ClaudeCodeOptions
        from claude_code_sdk import ClaudeSDKClient
    except ImportError as e:
        raise RuntimeError(
            f"claude-code-sdk Python package not installed.\nInstall with: uv add claude-code-sdk\nError: {e}"
        )

    # Progress tracking variables
    start_time = time.time()
    last_activity = time.time()
    response = ""
    response_chunks = 0
    progress_task = None
    interrupted = False

    async def show_progress_indicator():
        """Show real-time progress with elapsed time and activity indicators."""
        nonlocal last_activity, interrupted
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        spinner_idx = 0
        no_activity_warned = False

        try:
            while not interrupted:
                elapsed = time.time() - start_time
                since_activity = time.time() - last_activity

                # Format elapsed time
                mins, secs = divmod(int(elapsed), 60)
                time_str = f"{mins:02d}:{secs:02d}"

                # Build status message
                status_parts = [
                    f"\r{spinner_chars[spinner_idx % len(spinner_chars)]}",
                    f"Waiting for Claude SDK... [{time_str}]",
                ]

                if response_chunks > 0:
                    status_parts.append(f"| {len(response)} chars received")
                    status_parts.append(f"| {response_chunks} chunks")

                # Warn if no activity for 30+ seconds
                if since_activity > 30 and not no_activity_warned:
                    status_parts.append(f"| ⚠️  No response for {int(since_activity)}s")
                    if since_activity > 60:
                        status_parts.append("(Ctrl+C to abort)")
                    no_activity_warned = True
                elif since_activity <= 30:
                    no_activity_warned = False

                # Print status (overwrite previous line)
                status = " ".join(status_parts)
                print(status + " " * 20, end="", flush=True)  # Extra spaces to clear line

                spinner_idx += 1
                await asyncio.sleep(0.1)  # Update 10 times per second

        except asyncio.CancelledError:
            # Clear the progress line when cancelled
            print("\r" + " " * 80 + "\r", end="", flush=True)
            return

    try:
        # Use configurable timeout (default 300 seconds)
        async with asyncio.timeout(timeout):
            # Start progress indicator if requested
            if show_progress:
                progress_task = asyncio.create_task(show_progress_indicator())
                print(f"\n🤖 Querying Claude SDK (timeout: {timeout}s, Ctrl+C to abort)...", flush=True)

            # Use ClaudeSDKClient with async context manager (correct pattern)
            async with ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=system_prompt
                    or "You are a helpful Python code generator. Generate clean, working Python code.",
                    max_turns=1,  # Single response, no conversation
                )
            ) as client:
                # Send the query
                await client.query(prompt)

                # Collect response from message stream
                async for message in client.receive_response():
                    # Update activity timestamp
                    last_activity = time.time()

                    # Extract text from message (handle different message types)
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    text = getattr(block, "text", "")
                                    if text:
                                        response += text
                                        response_chunks += 1
                        elif isinstance(content, str) and content:
                            response += content
                            response_chunks += 1

            # Stop progress indicator
            interrupted = True
            if progress_task:
                progress_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await progress_task

            # Clear progress line and show completion
            if show_progress:
                elapsed = time.time() - start_time
                mins, secs = divmod(int(elapsed), 60)
                print(
                    f"\r✅ Received {len(response)} chars in {mins:02d}:{secs:02d} ({response_chunks} chunks)"
                    + " " * 30,
                    flush=True,
                )

            # Strip markdown from the response
            cleaned_response = strip_markdown(response)

            # If we got an empty response after cleaning, it might indicate an issue
            if not cleaned_response:
                raise RuntimeError(
                    "Empty response from Claude SDK after markdown stripping.\n"
                    "This may indicate the SDK is not working properly.\n"
                    "Verify Claude CLI is working: claude --version"
                )

            return cleaned_response

    except asyncio.CancelledError:
        # Handle Ctrl+C gracefully
        interrupted = True
        if progress_task:
            progress_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await progress_task
        print("\n\n⛔ Operation cancelled by user (Ctrl+C)", flush=True)
        raise KeyboardInterrupt("User cancelled Claude SDK operation")

    except TimeoutError:
        interrupted = True
        if progress_task:
            progress_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await progress_task

        # Show what we received before timeout
        if show_progress and response:
            print(f"\n⏱️  Timeout after receiving {len(response)} chars", flush=True)

        raise RuntimeError(
            f"Claude SDK timeout after {timeout} seconds.\n"
            "This usually means:\n"
            "  1. Claude CLI is not properly installed\n"
            "  2. You're running outside Claude Code environment\n"
            "  3. The operation genuinely needs more time (rare)\n"
            "\n"
            "To fix:\n"
            "  - Install Claude CLI: npm install -g @anthropic-ai/claude-code\n"
            "  - Verify installation: which claude\n"
            "  - Try running inside Claude Code environment"
        )

    except Exception as e:
        interrupted = True
        if progress_task:
            progress_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await progress_task

        # Re-raise with more context
        raise RuntimeError(
            f"Claude SDK error: {e}\n"
            "\n"
            "Common causes:\n"
            "  - Claude CLI not installed (npm install -g @anthropic-ai/claude-code)\n"
            "  - Running outside Claude Code environment\n"
            "  - Network connectivity issues"
        )


# Convenience function for synchronous contexts
def query_claude_sync(
    prompt: str, system_prompt: str | None = None, timeout: int = 300, show_progress: bool = True
) -> str:
    """Synchronous wrapper for query_claude.

    Use this when you can't use async/await directly.

    Args:
        prompt: The prompt to send to Claude
        system_prompt: Optional system prompt for context
        timeout: Timeout in seconds (default: 300, range: 30-600)
        show_progress: Whether to show real-time progress indicators (default: True)

    Returns:
        str: The cleaned response from Claude

    Raises:
        RuntimeError: If Claude CLI is not available or if operation times out
        KeyboardInterrupt: If user interrupts with Ctrl+C
    """
    return asyncio.run(query_claude(prompt, system_prompt, timeout, show_progress))
