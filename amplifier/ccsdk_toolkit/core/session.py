"""Core Claude session implementation with robust error handling."""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .models import SessionOptions
from .models import SessionResponse

try:  # pragma: no cover - optional dependency handled gracefully
    from claude_code_sdk import AssistantMessage
    from claude_code_sdk import ClaudeCodeOptions
    from claude_code_sdk import ClaudeSDKClient
    from claude_code_sdk import ClaudeSDKError
    from claude_code_sdk import ProcessError
    from claude_code_sdk import ResultMessage
    from claude_code_sdk import TextBlock
except Exception:  # pragma: no cover - import errors handled at runtime
    AssistantMessage = None  # type: ignore[assignment]
    ClaudeCodeOptions = None  # type: ignore[assignment]
    ClaudeSDKClient = None  # type: ignore[assignment]
    ClaudeSDKError = Exception  # type: ignore[assignment]
    ProcessError = Exception  # type: ignore[assignment]
    ResultMessage = None  # type: ignore[assignment]
    TextBlock = None  # type: ignore[assignment]


class SessionError(Exception):
    """Base exception for session errors."""


class SDKNotAvailableError(SessionError):
    """Raised when Claude CLI/SDK is not available."""


class ClaudeSession:
    """Async context manager for Claude Code SDK sessions.

    This provides a robust wrapper around the claude_code_sdk with:
    - Prerequisite checking for the claude CLI
    - Automatic retry with exponential backoff
    - Clean timeout handling
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
            if ClaudeSDKClient is None or ClaudeCodeOptions is None:  # pragma: no cover - runtime guard
                raise ImportError("claude_code_sdk is not available")

            option_kwargs: dict[str, Any] = {
                "system_prompt": self.options.system_prompt,
                "max_turns": self.options.max_turns,
            }

            if self.options.max_thinking_tokens is not None:
                option_kwargs["max_thinking_tokens"] = self.options.max_thinking_tokens
            if self.options.append_system_prompt:
                option_kwargs["append_system_prompt"] = self.options.append_system_prompt
            if self.options.allowed_tools is not None:
                option_kwargs["allowed_tools"] = list(self.options.allowed_tools)
            if self.options.disallowed_tools is not None:
                option_kwargs["disallowed_tools"] = list(self.options.disallowed_tools)
            if self.options.permission_mode is not None:
                option_kwargs["permission_mode"] = self.options.permission_mode
            if self.options.resume:
                option_kwargs["resume"] = self.options.resume
            if self.options.model:
                option_kwargs["model"] = self.options.model
            if self.options.permission_prompt_tool_name:
                option_kwargs["permission_prompt_tool_name"] = self.options.permission_prompt_tool_name
            if self.options.cwd:
                option_kwargs["cwd"] = str(self.options.cwd)
            if self.options.settings:
                option_kwargs["settings"] = self.options.settings
            if self.options.add_dirs:
                option_kwargs["add_dirs"] = [str(path) for path in self.options.add_dirs]
            if self.options.extra_args:
                option_kwargs["extra_args"] = self.options.extra_args

            self.client = ClaudeSDKClient(options=ClaudeCodeOptions(**option_kwargs))
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

    async def query(
        self,
        prompt: str,
        *,
        stream: bool | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> SessionResponse:
        """Send a query to Claude with automatic retry."""
        if not self.client:
            return SessionResponse(error="Session not initialized. Use 'async with' context.")

        retry_delay = self.options.retry_delay
        last_error = None

        use_stream = stream if stream is not None else self.options.stream_output
        callback = progress_callback or self.options.progress_callback

        for attempt in range(self.options.retry_attempts):
            try:
                # Query with timeout
                async with asyncio.timeout(self.options.timeout_seconds):
                    await self.client.query(prompt)

                    # Collect response
                    response_text = ""
                    session_id: str | None = None
                    total_cost = 0.0
                    duration_ms = 0
                    usage: dict[str, Any] | None = None

                    async for message in self.client.receive_response():
                        if AssistantMessage is not None and isinstance(message, AssistantMessage):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if TextBlock is not None and isinstance(block, TextBlock):
                                        chunk = getattr(block, "text", "")
                                        if chunk:
                                            response_text += chunk
                                            if callback:
                                                callback(chunk)
                                            if use_stream:
                                                print(chunk, end="", flush=True)
                        elif ResultMessage is not None and isinstance(message, ResultMessage):
                            session_id = getattr(message, "session_id", session_id)
                            total_cost = getattr(message, "total_cost_usd", total_cost) or 0.0
                            duration_ms = getattr(message, "duration_ms", duration_ms) or 0
                            usage = getattr(message, "usage", usage) or usage

                    if response_text:
                        metadata: dict[str, Any] = {
                            "attempt": attempt + 1,
                            "session_id": session_id,
                            "total_cost_usd": total_cost,
                            "duration_ms": duration_ms,
                        }
                        if usage:
                            metadata["usage"] = usage
                        return SessionResponse(content=response_text, metadata=metadata)

                    # Empty response, retry
                    last_error = "Received empty response from SDK"

            except TimeoutError:
                last_error = f"SDK timeout after {self.options.timeout_seconds} seconds"
            except (ClaudeSDKError, ProcessError) as exc:  # pragma: no cover - passthrough
                last_error = str(exc)
            except Exception as e:
                last_error = str(e)

            # Wait before retry (except on last attempt)
            if attempt < self.options.retry_attempts - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        # All retries exhausted
        return SessionResponse(error=f"Failed after {self.options.retry_attempts} attempts: {last_error}")
