"""Core Claude session implementation with robust error handling."""

from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import Callable
from contextlib import suppress
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
        """Initialize session with options."""

        self.options = options or SessionOptions()
        self.client = None
        self._check_prerequisites()

    def _check_prerequisites(self) -> None:
        """Check if claude CLI is installed and accessible."""

        claude_path = shutil.which("claude")
        if claude_path:
            return

        known_locations = [
            Path.home() / ".local/share/reflex/bun/bin/claude",
            Path.home() / ".npm-global/bin/claude",
            Path("/usr/local/bin/claude"),
        ]

        for loc in known_locations:
            if loc.exists() and os.access(loc, os.X_OK):
                return

        raise SDKNotAvailableError(
            "Claude CLI not found. Install with one of:\n"
            "  - npm install -g @anthropic-ai/claude-code\n"
            "  - bun install -g @anthropic-ai/claude-code"
        )

    async def __aenter__(self) -> ClaudeSession:
        """Enter async context and initialize SDK client."""

        try:
            from claude_code_sdk import ClaudeCodeOptions
            from claude_code_sdk import ClaudeSDKClient
        except ImportError as exc:  # pragma: no cover - exercised in environments without SDK
            raise SDKNotAvailableError(
                "claude_code_sdk Python package not installed. Install with: pip install claude-code-sdk"
            ) from exc

        option_kwargs: dict[str, Any] = {
            "system_prompt": self.options.system_prompt,
            "permission_mode": self.options.permission_mode,
        }

        if self.options.max_turns is not None:
            option_kwargs["max_turns"] = self.options.max_turns

        allowed_tools = list(self.options.allowed_tools)
        if allowed_tools:
            option_kwargs["allowed_tools"] = allowed_tools

        if self.options.cwd:
            option_kwargs["cwd"] = str(self.options.cwd)

        if self.options.add_dirs:
            option_kwargs["add_dirs"] = [str(path) for path in self.options.add_dirs]

        if self.options.settings_path:
            option_kwargs["settings"] = str(self.options.settings_path)

        self.client = ClaudeSDKClient(options=ClaudeCodeOptions(**option_kwargs))
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context and cleanup."""

        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def query(
        self,
        prompt: str,
        *,
        stream: bool | None = None,
        message_callback: Callable[[dict[str, Any]], None] | None = None,
        todo_callback: Callable[[list[dict[str, Any]]], None] | None = None,
    ) -> SessionResponse:
        """Send a query to Claude with automatic retry."""

        if not self.client:
            return SessionResponse(error="Session not initialized. Use 'async with' context.")

        retry_delay = self.options.retry_delay
        last_error: str | Exception | None = None

        for attempt in range(self.options.retry_attempts):
            try:
                await self.client.query(prompt)

                response_segments: list[str] = []
                messages: list[dict[str, Any]] = []
                todos: list[dict[str, Any]] = []
                usage: dict[str, Any] | None = None
                session_id: str | None = None
                metadata: dict[str, Any] = {"attempt": attempt + 1}

                async for raw_message in self.client.receive_response():
                    normalized = _normalize_message(raw_message)
                    messages.append(normalized)

                    if message_callback:
                        message_callback(normalized)

                    segments = _extract_text(normalized)
                    if segments:
                        response_segments.extend(segments)
                        should_stream = stream if stream is not None else self.options.stream_output
                        for segment in segments:
                            if should_stream:
                                print(segment, end="", flush=True)
                            if self.options.progress_callback:
                                self.options.progress_callback(segment)

                    extracted_todos = _extract_todos(normalized)
                    if extracted_todos:
                        todos = extracted_todos
                        if todo_callback:
                            todo_callback(extracted_todos)

                    usage_block = normalized.get("usage")
                    if isinstance(usage_block, dict):
                        usage = usage_block

                    if normalized.get("session_id"):
                        session_id = str(normalized["session_id"])
                        metadata["session_id"] = session_id

                    if normalized.get("total_cost_usd") is not None:
                        metadata["total_cost_usd"] = normalized.get("total_cost_usd")
                    if normalized.get("duration_ms") is not None:
                        metadata["duration_ms"] = normalized.get("duration_ms")

                should_stream = stream if stream is not None else self.options.stream_output
                if should_stream and response_segments:
                    print()

                if response_segments:
                    content = "\n".join(response_segments).strip()
                    return SessionResponse(
                        content=content,
                        metadata=metadata,
                        todos=todos,
                        usage=usage,
                        session_id=session_id,
                        messages=messages,
                    )

                raise ValueError("Received empty response from SDK")

            except ValueError as exc:
                last_error = str(exc)
            except Exception as exc:  # pragma: no cover - network failures are environment specific
                last_error = exc

            if attempt < self.options.retry_attempts - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

        return SessionResponse(error=f"Failed after {self.options.retry_attempts} attempts: {last_error}")


def _normalize_message(message: Any) -> dict[str, Any]:
    """Convert SDK message objects into plain dictionaries."""

    if isinstance(message, dict):
        normalized = dict(message)
    else:
        normalized = {}
        for attribute in [
            "type",
            "content",
            "name",
            "input",
            "usage",
            "id",
            "result",
            "text",
            "session_id",
            "total_cost_usd",
            "duration_ms",
        ]:
            if hasattr(message, attribute):
                normalized[attribute] = getattr(message, attribute)

        if hasattr(message, "__dict__"):
            normalized.update({k: v for k, v in vars(message).items() if k not in normalized})

        if hasattr(message, "to_dict"):
            with suppress(Exception):  # pragma: no cover - defensive to avoid masking main failures
                normalized = {**message.to_dict(), **normalized}

    content = normalized.get("content")
    if isinstance(content, list):
        normalized["content"] = [_coerce_block(block) for block in content]
    else:
        normalized["content"] = []

    return normalized


def _coerce_block(block: Any) -> dict[str, Any]:
    """Ensure individual content blocks are dictionaries."""

    if isinstance(block, dict):
        return block

    block_dict: dict[str, Any] = {}
    for attr in ("type", "text", "id", "language", "data", "name", "tool_use_id"):
        if hasattr(block, attr):
            value = getattr(block, attr)
            if value is not None:
                block_dict[attr] = value

    if not block_dict and hasattr(block, "__dict__"):
        block_dict = dict(vars(block))

    return block_dict


def _extract_text(message: dict[str, Any]) -> list[str]:
    """Extract plain text segments from a normalized message."""

    segments: list[str] = []

    for block in message.get("content", []):
        if isinstance(block, dict):
            if block.get("tool_use_id"):
                continue
            text_value = block.get("text")
            if isinstance(text_value, str):
                stripped = text_value.strip()
                if stripped:
                    segments.append(stripped)
        elif isinstance(block, str):
            stripped = block.strip()
            if stripped:
                segments.append(stripped)

    inline_text = message.get("text")
    if isinstance(inline_text, str):
        stripped = inline_text.strip()
        if stripped:
            segments.append(stripped)

    result = message.get("result")
    if isinstance(result, dict):
        for key in ("text", "output_text"):
            value = result.get(key)
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    segments.append(stripped)

    return segments


def _extract_todos(message: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract TodoWrite payloads from a message if present."""

    if message.get("type") == "tool_use" and message.get("name") == "TodoWrite":
        tool_input = message.get("input")
        if isinstance(tool_input, dict):
            todos = tool_input.get("todos")
            if isinstance(todos, list):
                return todos
    return []
