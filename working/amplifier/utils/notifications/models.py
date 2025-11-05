"""
Data models for notification system.
"""

from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class Platform(str, Enum):
    """Supported notification platforms."""

    MACOS = "macos"
    LINUX = "linux"
    WSL = "wsl"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class NotificationRequest(BaseModel):
    """Request model for sending notifications."""

    message: str = Field(..., description="Main notification message")
    title: str = Field(default="Claude Code", description="Notification title")
    subtitle: str | None = Field(default=None, description="Optional subtitle (e.g., project name)")
    session_id: str | None = Field(default=None, description="Session ID for tracking")
    debug: bool = Field(default=False, description="Enable debug mode")


class NotificationResponse(BaseModel):
    """Response model after sending notification."""

    success: bool = Field(..., description="Whether notification was sent successfully")
    platform: Platform = Field(..., description="Platform where notification was sent")
    fallback_used: bool = Field(default=False, description="Whether console fallback was used")
    error: str | None = Field(default=None, description="Error message if failed")
    debug_log: str | None = Field(default=None, description="Debug information if debug mode enabled")


class ClaudeCodeHookInput(BaseModel):
    """Input model for Claude Code hook events."""

    session_id: str | None = Field(default=None, description="Session ID")
    transcript_path: str | None = Field(default=None, description="Path to transcript file")
    cwd: str | None = Field(default=None, description="Current working directory")
    hook_event_name: str | None = Field(default=None, description="Name of the hook event")
    message: str | None = Field(default=None, description="Notification message")
