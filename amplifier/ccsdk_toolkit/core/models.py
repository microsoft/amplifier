"""Data models for CCSDK Core module."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SessionOptions(BaseModel):
    """Configuration options for Claude sessions.

    Attributes:
        system_prompt: System prompt for the session
        max_turns: Maximum conversation turns (default: 1)
        timeout_seconds: Timeout for SDK operations (default: 120)
        retry_attempts: Number of retry attempts on failure (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
        cwd: Working directory passed to the Claude Code SDK
        add_dirs: Additional directories exposed to the SDK
        allowed_tools: Explicitly allowed tool names
        disallowed_tools: Explicitly disallowed tool names
        permission_mode: Claude SDK permission mode
        settings: Path to Claude configuration file
        resume: Session ID to resume a previous conversation
        append_system_prompt: Additional system prompt content
        max_thinking_tokens: Override for model thinking tokens
        model: Model identifier override
        permission_prompt_tool_name: Tool used when prompting for permissions
        extra_args: Extra keyword arguments forwarded to ClaudeCodeOptions
    """

    system_prompt: str = Field(default="You are a helpful assistant")
    max_turns: int = Field(default=1, gt=0, le=100)
    timeout_seconds: int = Field(default=120, gt=0, le=7200)
    retry_attempts: int = Field(default=3, gt=0, le=10)
    retry_delay: float = Field(default=1.0, gt=0, le=10.0)
    cwd: Path | None = Field(default=None)
    add_dirs: list[str | Path] = Field(default_factory=list)
    allowed_tools: list[str] | None = Field(default=None)
    disallowed_tools: list[str] | None = Field(default=None)
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] | None = Field(default=None)
    settings: str | None = Field(default=None)
    resume: str | None = Field(default=None)
    append_system_prompt: str | None = Field(default=None)
    max_thinking_tokens: int | None = Field(default=None, ge=0)
    model: str | None = Field(default=None)
    permission_prompt_tool_name: str | None = Field(default=None)
    extra_args: dict[str, str | None] = Field(default_factory=dict)
    stream_output: bool = Field(default=False)
    progress_callback: Callable[[str], None] | None = Field(default=None)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "system_prompt": "You are a code review assistant",
                "max_turns": 1,
                "timeout_seconds": 120,
                "retry_attempts": 3,
                "retry_delay": 1.0,
                "cwd": "/workspace",
                "add_dirs": ["ai_context"],
                "allowed_tools": ["Read", "Grep"],
                "permission_mode": "default",
                "stream_output": True,
            }
        },
    )


class SessionResponse(BaseModel):
    """Response from a Claude session query.

    Attributes:
        content: The response text content
        metadata: Additional metadata about the response
        error: Error message if the query failed
    """

    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None and bool(self.content)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Here's the code review...",
                "metadata": {
                    "tokens": 150,
                    "model": "claude-3",
                    "session_id": "session-123",
                    "total_cost_usd": 0.12,
                    "duration_ms": 4200,
                },
                "error": None,
            }
        }
    )
