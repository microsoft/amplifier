"""Data models for session monitoring and token tracking."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field


class TerminationReason(str, Enum):
    """Reasons for requesting session termination."""

    TOKEN_LIMIT_APPROACHING = "token_limit_approaching"
    PHASE_COMPLETE = "phase_complete"
    ERROR = "error"
    MANUAL = "manual"


class TerminationPriority(str, Enum):
    """Priority levels for termination requests."""

    IMMEDIATE = "immediate"
    GRACEFUL = "graceful"


class TerminationRequest(BaseModel):
    """Request for session termination with continuation details.

    Attributes:
        timestamp: When the request was created
        reason: Why termination is requested
        phase: Current workflow phase (optional)
        issue: Specific issue description (optional)
        continuation_command: Command to restart the session
        priority: How urgently to terminate
        token_usage_pct: Current token usage percentage
        pid: Process ID of the session to terminate
        workspace_id: Identifier for the workspace
    """

    timestamp: datetime = Field(default_factory=datetime.now)
    reason: TerminationReason
    phase: str | None = None
    issue: str | None = None
    continuation_command: str
    priority: TerminationPriority = TerminationPriority.GRACEFUL
    token_usage_pct: float
    pid: int
    workspace_id: str = Field(default_factory=lambda: str(uuid4()))

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-01T10:00:00",
                "reason": "token_limit_approaching",
                "phase": "code_review",
                "issue": "Approaching 90% token limit",
                "continuation_command": "claude --continue-session",
                "priority": "graceful",
                "token_usage_pct": 85.5,
                "pid": 12345,
                "workspace_id": "workspace-123",
            }
        }


class TokenUsageSnapshot(BaseModel):
    """Snapshot of token usage at a specific point in time.

    Attributes:
        timestamp: When the snapshot was taken
        estimated_tokens: Estimated token count
        usage_pct: Percentage of token limit used
        source: How the estimate was calculated
    """

    timestamp: datetime = Field(default_factory=datetime.now)
    estimated_tokens: int
    usage_pct: float
    source: str = Field(description="Source of estimation: session_log, api_response, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-01T10:00:00",
                "estimated_tokens": 85000,
                "usage_pct": 85.0,
                "source": "session_log",
            }
        }


class MonitorConfig(BaseModel):
    """Configuration for the session monitor daemon.

    Attributes:
        workspace_base_dir: Base directory for workspace files
        check_interval_seconds: How often to check for termination requests
        token_warning_threshold: Percentage at which to warn about token usage
        token_critical_threshold: Percentage at which to request termination
        max_restart_attempts: Maximum number of restart attempts
        restart_backoff_seconds: Base backoff time between restart attempts
    """

    workspace_base_dir: Path = Field(default=Path(".codex/workspaces"))
    check_interval_seconds: int = Field(default=5)
    token_warning_threshold: float = Field(default=80.0)
    token_critical_threshold: float = Field(default=90.0)
    max_restart_attempts: int = Field(default=3)
    restart_backoff_seconds: int = Field(default=2)

    class Config:
        json_schema_extra = {
            "example": {
                "workspace_base_dir": ".codex/workspaces",
                "check_interval_seconds": 5,
                "token_warning_threshold": 80.0,
                "token_critical_threshold": 90.0,
                "max_restart_attempts": 3,
                "restart_backoff_seconds": 2,
            }
        }
