"""Data models for CCSDK Core module."""

from typing import Any

from pydantic import BaseModel
from pydantic import Field


class SessionOptions(BaseModel):
    """Configuration options for Claude sessions.

    Attributes:
        system_prompt: System prompt for the session
        max_turns: Maximum conversation turns (default: 1)
        timeout_seconds: Timeout for SDK operations (default: 120)
        retry_attempts: Number of retry attempts on failure (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
    """

    system_prompt: str = Field(default="You are a helpful assistant")
    max_turns: int = Field(default=1, gt=0, le=100)
    timeout_seconds: int = Field(default=120, gt=0, le=600)
    retry_attempts: int = Field(default=3, gt=0, le=10)
    retry_delay: float = Field(default=1.0, gt=0, le=10.0)

    class Config:
        json_schema_extra = {
            "example": {
                "system_prompt": "You are a code review assistant",
                "max_turns": 1,
                "timeout_seconds": 120,
                "retry_attempts": 3,
                "retry_delay": 1.0,
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Here's the code review...",
                "metadata": {"tokens": 150, "model": "claude-3"},
                "error": None,
            }
        }
