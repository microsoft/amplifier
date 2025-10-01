"""
Session awareness for Claude Code sessions.

Enables multiple Claude sessions to be aware of each other's activity
in the same project directory.
"""

import json
import logging
import os
import time
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Configuration
STALE_THRESHOLD_SECONDS = 300  # 5 minutes
MAX_ACTIVITY_LOG_SIZE = 1000  # Keep last 1000 activities


@dataclass
class SessionActivity:
    """Represents a single activity from a Claude session."""

    session_id: str
    timestamp: float
    action: str
    details: str | None = None


@dataclass
class SessionInfo:
    """Information about an active Claude session."""

    session_id: str
    pid: int
    started: float
    last_seen: float
    activities: list[SessionActivity] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        """Check if session hasn't been seen recently."""
        return time.time() - self.last_seen > STALE_THRESHOLD_SECONDS


class SessionAwareness:
    """Manages awareness of multiple Claude Code sessions."""

    def __init__(self, project_root: Path | None = None):
        """Initialize session awareness.

        Args:
            project_root: Root directory for the project. Defaults to current directory.
        """
        self.project_root = project_root or Path.cwd()
        self.data_dir = self.project_root / ".data" / "session_awareness"
        self.sessions_file = self.data_dir / "sessions.json"
        self.activity_log = self.data_dir / "activity.jsonl"

        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Get session ID from environment or generate one
        self.session_id = os.environ.get("CLAUDE_SESSION_ID", f"session-{os.getpid()}")
        self.pid = os.getpid()

    def _load_sessions(self) -> dict[str, SessionInfo]:
        """Load active sessions from disk."""
        if not self.sessions_file.exists():
            return {}

        try:
            with open(self.sessions_file) as f:
                data = json.load(f)
                sessions = {}
                for sid, info in data.items():
                    # Convert activity dicts to SessionActivity objects
                    activities = [
                        SessionActivity(**act) if isinstance(act, dict) else act for act in info.get("activities", [])
                    ]
                    sessions[sid] = SessionInfo(
                        session_id=info["session_id"],
                        pid=info["pid"],
                        started=info["started"],
                        last_seen=info["last_seen"],
                        activities=activities,
                    )
                return sessions
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load sessions: {e}")
            return {}

    def _save_sessions(self, sessions: dict[str, SessionInfo]) -> None:
        """Save active sessions to disk."""
        try:
            data = {sid: asdict(info) for sid, info in sessions.items()}
            with open(self.sessions_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def _log_activity(self, activity: SessionActivity) -> None:
        """Append activity to the activity log."""
        try:
            with open(self.activity_log, "a") as f:
                f.write(json.dumps(asdict(activity)) + "\n")
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    def _trim_activity_log(self) -> None:
        """Keep only the last MAX_ACTIVITY_LOG_SIZE entries."""
        if not self.activity_log.exists():
            return

        try:
            with open(self.activity_log) as f:
                lines = f.readlines()

            if len(lines) > MAX_ACTIVITY_LOG_SIZE:
                with open(self.activity_log, "w") as f:
                    f.writelines(lines[-MAX_ACTIVITY_LOG_SIZE:])
        except Exception as e:
            logger.error(f"Failed to trim activity log: {e}")

    def register_activity(self, action: str, details: str | None = None) -> None:
        """Register an activity for the current session.

        Args:
            action: The action being performed (e.g., "Edit", "Read", "Test")
            details: Optional details about the action
        """
        sessions = self._load_sessions()

        # Clean up stale sessions
        active_sessions = {sid: info for sid, info in sessions.items() if not info.is_stale}

        # Update current session
        activity = SessionActivity(session_id=self.session_id, timestamp=time.time(), action=action, details=details)

        if self.session_id not in active_sessions:
            active_sessions[self.session_id] = SessionInfo(
                session_id=self.session_id, pid=self.pid, started=time.time(), last_seen=time.time(), activities=[]
            )

        session = active_sessions[self.session_id]
        session.last_seen = time.time()
        session.activities.append(activity)

        # Keep only recent activities per session
        if len(session.activities) > 10:
            session.activities = session.activities[-10:]

        # Save and log
        self._save_sessions(active_sessions)
        self._log_activity(activity)
        self._trim_activity_log()

        logger.debug(f"Session {self.session_id}: {action}")

    def get_active_sessions(self) -> list[SessionInfo]:
        """Get list of currently active sessions."""
        sessions = self._load_sessions()
        return [info for info in sessions.values() if not info.is_stale]

    def get_recent_activity(self, limit: int = 20) -> list[SessionActivity]:
        """Get recent activity across all sessions.

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of recent activities, newest first
        """
        if not self.activity_log.exists():
            return []

        activities = []
        try:
            with open(self.activity_log) as f:
                for line in f:
                    if line.strip():
                        activities.append(SessionActivity(**json.loads(line)))
        except Exception as e:
            logger.error(f"Failed to read activity log: {e}")

        # Sort by timestamp descending and return limited results
        activities.sort(key=lambda a: a.timestamp, reverse=True)
        return activities[:limit]

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of session awareness.

        Returns:
            Dictionary with status information
        """
        active_sessions = self.get_active_sessions()
        recent_activity = self.get_recent_activity(10)

        return {
            "current_session": self.session_id,
            "active_sessions": len(active_sessions),
            "sessions": [
                {
                    "id": s.session_id,
                    "pid": s.pid,
                    "duration_minutes": round((time.time() - s.started) / 60, 1),
                    "last_activity": (s.activities[-1].action if s.activities else None),
                }
                for s in active_sessions
            ],
            "recent_activity": [
                {
                    "session": a.session_id,
                    "action": a.action,
                    "ago_seconds": round(time.time() - a.timestamp),
                    "details": a.details,
                }
                for a in recent_activity
            ],
        }

    def broadcast_message(self, message: str) -> None:
        """Broadcast a message to all active sessions.

        Args:
            message: Message to broadcast
        """
        # For now, just log it as an activity
        # Future: Could write to a messages file that other sessions poll
        self.register_activity("Broadcast", message)
        logger.info(f"Broadcasting: {message}")
