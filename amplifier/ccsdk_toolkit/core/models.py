"""Data models for CCSDK Core module."""

from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class SessionOptions(BaseModel):
    """Configuration options for Claude sessions.

    Attributes:
        system_prompt: System prompt for the session
        max_turns: Maximum conversation turns (default: unlimited)
        retry_attempts: Number of retry attempts on failure (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
        stream_output: Enable real-time streaming output (default: False)
        progress_callback: Optional callback for progress updates
    """

    system_prompt: str = Field(default="You are a helpful assistant")
    max_turns: int | None = Field(default=None)
    retry_attempts: int = Field(default=3, gt=0, le=10)
    retry_delay: float = Field(default=1.0, gt=0, le=10.0)
    stream_output: bool = Field(default=False, description="Enable real-time streaming output")
    progress_callback: Callable[[str], None] | None = Field(
        default=None,
        description="Optional callback for progress updates",
        exclude=True,  # Exclude from serialization since callables can't be serialized
    )
    permission_mode: Literal["default", "acceptEdits", "plan", "bypassPermissions"] = Field(
        default="acceptEdits",
        description="Claude Code permission mode to use for the session",
    )
    allowed_tools: list[str] = Field(
        default_factory=list,
        description="Explicit list of allowed tools; empty list uses Claude defaults",
    )
    cwd: Path | None = Field(default=None, description="Working directory for Claude Code CLI")
    add_dirs: list[Path] = Field(default_factory=list, description="Additional directories to mount into the session")
    settings_path: Path | None = Field(default=None, description="Optional path to Claude Code settings JSON")

    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "You are a code review assistant",
                "max_turns": 1,
                "retry_attempts": 3,
                "retry_delay": 1.0,
                "stream_output": False,  # Streaming disabled by default
            }
        }

    @field_validator("max_turns")
    @classmethod
    def validate_max_turns(cls, value: int | None) -> int | None:
        """Ensure max_turns is at least 1 when provided."""

        if value is not None and value < 1:
            raise ValueError("max_turns must be >= 1 when provided")
        return value


class SessionResponse(BaseModel):
    """Response from a Claude session query.

    Attributes:
        content: The response text content
        metadata: Additional metadata about the response
        error: Error message if the query failed
    """

    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    todos: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] | None = Field(default=None)
    session_id: str | None = Field(default=None)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if the response was successful."""
        return self.error is None and bool(self.content)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Here's the code review...",
                "metadata": {"tokens": 150, "model": "claude-3"},
                "error": None,
            }
        }
