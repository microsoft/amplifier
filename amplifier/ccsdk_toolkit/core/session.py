"""Core Claude session implementation with robust error handling."""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any

from .models import SessionOptions
from .models import SessionResponse


class SessionError(Exception):
    """Base exception for session errors."""


class SDKNotAvailableError(SessionError):
    """Raised when Claude CLI/SDK is not available."""


class ClaudeSession:
    """Async context manager for Claude Code SDK sessions.

    This provides a robust wrapper around the claude_code_sdk with:
    - Prerequisite checking for the claude CLI
    - Automatic retry with exponential backoff
    - Graceful degradation when SDK unavailable
    """

    def __init__(self, options: SessionOptions | None = None):
        """Initialize session with options.

        Args:
            options: Session configuration options
        """
        self.options = options or SessionOptions()
        self.client = None
        self._check_prerequisites()

    def _check_prerequisites(self):
        """Check if claude CLI is installed and accessible."""
        # Check if claude CLI is available
        claude_path = shutil.which("claude")
        if not claude_path:
            # Check common installation locations
            known_locations = [
                Path.home() / ".local/share/reflex/bun/bin/claude",
                Path.home() / ".npm-global/bin/claude",
                Path("/usr/local/bin/claude"),
            ]

            for loc in known_locations:
                if loc.exists() and os.access(loc, os.X_OK):
                    claude_path = str(loc)
                    break

            if not claude_path:
                raise SDKNotAvailableError(
                    "Claude CLI not found. Install with one of:\n"
                    "  - npm install -g @anthropic-ai/claude-code\n"
                    "  - bun install -g @anthropic-ai/claude-code"
                )

    async def __aenter__(self):
        """Enter async context and initialize SDK client."""
        try:
            # Import SDK only when actually using it
            from claude_code_sdk import ClaudeCodeOptions
            from claude_code_sdk import ClaudeSDKClient

            self.client = ClaudeSDKClient(
                options=ClaudeCodeOptions(
                    system_prompt=self.options.system_prompt,
                    max_turns=self.options.max_turns,
                )
            )
            await self.client.__aenter__()
            return self

        except ImportError:
            raise SDKNotAvailableError(
                "claude_code_sdk Python package not installed. Install with: pip install claude-code-sdk"
            )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and cleanup."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def query(self, prompt: str, stream: bool | None = None) -> SessionResponse:
        """Send a query to Claude with automatic retry.

        Args:
            prompt: The prompt to send to Claude
            stream: Override the session's stream_output setting

        Returns:
            SessionResponse with the result or error
        """
        if not self.client:
            return SessionResponse(error="Session not initialized. Use 'async with' context.")

        retry_delay = self.options.retry_delay
        last_error = None

        for attempt in range(self.options.retry_attempts):
            try:
                # Execute query directly
                assert self.client is not None  # Type guard for pyright
                await self.client.query(prompt)

                # Collect response with streaming support
                response_text = ""
                metadata: dict[str, Any] = {"attempt": attempt + 1}

                async for message in self.client.receive_response():
                    if hasattr(message, "content"):
                        content = getattr(message, "content", [])
                        if isinstance(content, list):
                            for block in content:
                                if hasattr(block, "text"):
                                    text = getattr(block, "text", "")
                                    if text:
                                        response_text += text

                                        # Stream output if enabled
                                        should_stream = stream if stream is not None else self.options.stream_output
                                        if should_stream:
                                            print(text, end="", flush=True)

                                        # Call progress callback if provided
                                        if self.options.progress_callback:
                                            self.options.progress_callback(text)

                    # Collect metadata from ResultMessage if available
                    if hasattr(message, "__class__") and message.__class__.__name__ == "ResultMessage":
                        if hasattr(message, "session_id"):
                            metadata["session_id"] = getattr(message, "session_id", None)
                        if hasattr(message, "total_cost_usd"):
                            metadata["total_cost_usd"] = getattr(message, "total_cost_usd", 0.0)
                        if hasattr(message, "duration_ms"):
                            metadata["duration_ms"] = getattr(message, "duration_ms", 0)

                # Add newline after streaming if enabled
                should_stream = stream if stream is not None else self.options.stream_output
                if should_stream and response_text:
                    print()  # Final newline after streaming

                if response_text:
                    return SessionResponse(content=response_text, metadata=metadata)

                # Empty response, will retry
                raise ValueError("Received empty response from SDK")
            except ValueError as e:
                last_error = str(e)
            except Exception as e:
                last_error = str(e)

            # Wait before retry (except on last attempt)
            if attempt < self.options.retry_attempts - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        # All retries exhausted
        return SessionResponse(error=f"Failed after {self.options.retry_attempts} attempts: {last_error}")
