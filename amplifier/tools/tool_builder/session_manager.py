"""Session management for Tool Builder with persistence and recovery."""

import json
import uuid
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any

from .exceptions import SessionError


@dataclass
class ToolBuilderSession:
    """Represents a tool creation session with full state tracking."""

    id: str
    tool_name: str
    description: str
    created_at: datetime
    updated_at: datetime
    current_stage: str
    completed_stages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Pipeline state
    requirements: dict[str, Any] | None = None
    architecture: dict[str, Any] | None = None
    generated_modules: list[str] = field(default_factory=list)
    quality_checks: list[dict[str, Any]] = field(default_factory=list)

    # Configuration
    output_dir: str = "./amplifier/tools"
    template: str | None = None

    def save(self):
        """Persist session to disk."""
        session_dir = self._get_session_dir()
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / f"{self.id}.json"

        # Serialize with datetime handling
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()

        session_file.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, session_id: str) -> "ToolBuilderSession":
        """Load session from disk."""
        session_file = cls._get_session_dir() / f"{session_id}.json"

        if not session_file.exists():
            raise SessionError(f"Session not found: {session_id}")

        try:
            data = json.loads(session_file.read_text())

            # Deserialize datetime fields
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            return cls(**data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise SessionError(f"Failed to load session {session_id}: {e}")

    @staticmethod
    def _get_session_dir() -> Path:
        """Get the session storage directory."""
        return Path.home() / ".amplifier" / "tool_builder" / "sessions"

    def update_stage(self, stage: str):
        """Update the current stage and track completion."""
        if self.current_stage and self.current_stage not in self.completed_stages:
            self.completed_stages.append(self.current_stage)

        self.current_stage = stage
        self.updated_at = datetime.now()
        self.save()

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the session."""
        self.metadata[key] = value
        self.updated_at = datetime.now()
        self.save()


@dataclass
class SessionSummary:
    """Lightweight session summary for listing."""

    id: str
    tool_name: str
    description: str
    created_at: datetime
    current_stage: str


class SessionManager:
    """Manages tool creation sessions with lifecycle operations."""

    def __init__(self):
        """Initialize the session manager."""
        self.session_dir = Path.home() / ".amplifier" / "tool_builder" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, tool_name: str, description: str) -> ToolBuilderSession:
        """Create a new tool creation session."""
        session = ToolBuilderSession(
            id=str(uuid.uuid4())[:8],  # Short ID for usability
            tool_name=tool_name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            current_stage="initializing",
            completed_stages=[],
            metadata={
                "version": "0.1.0",
                "sdk_version": self._get_sdk_version(),
            },
        )
        session.save()
        return session

    def load_session(self, session_id: str) -> ToolBuilderSession:
        """Load an existing session."""
        return ToolBuilderSession.load(session_id)

    def save_session(self, session: ToolBuilderSession):
        """Save session state."""
        session.save()

    def list_sessions(self) -> list[SessionSummary]:
        """List all available sessions."""
        sessions = []

        for session_file in self.session_dir.glob("*.json"):
            try:
                data = json.loads(session_file.read_text())
                sessions.append(
                    SessionSummary(
                        id=data["id"],
                        tool_name=data["tool_name"],
                        description=data["description"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        current_stage=data["current_stage"],
                    )
                )
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted sessions
                continue

        # Sort by creation date, newest first
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Remove sessions older than max_age_days."""
        cutoff = datetime.now().timestamp() - (max_age_days * 86400)
        removed = 0

        for session_file in self.session_dir.glob("*.json"):
            if session_file.stat().st_mtime < cutoff:
                session_file.unlink()
                removed += 1

        return removed

    def get_session_analytics(self, session_id: str) -> dict[str, Any]:
        """Get analytics for a specific session."""
        session = self.load_session(session_id)

        duration = (session.updated_at - session.created_at).total_seconds()
        completion_rate = len(session.completed_stages) / max(len(session.completed_stages) + 1, 1)

        return {
            "session_id": session.id,
            "tool_name": session.tool_name,
            "duration_seconds": duration,
            "stages_completed": len(session.completed_stages),
            "current_stage": session.current_stage,
            "completion_rate": completion_rate,
            "has_requirements": session.requirements is not None,
            "has_architecture": session.architecture is not None,
            "modules_generated": len(session.generated_modules),
            "quality_checks_passed": len([c for c in session.quality_checks if c.get("passed", False)]),
        }

    def _get_sdk_version(self) -> str:
        """Get Claude Code SDK version if available."""
        try:
            import subprocess

            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "unknown"
