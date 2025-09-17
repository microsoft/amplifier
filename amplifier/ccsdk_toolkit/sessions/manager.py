"""Session management for CCSDK toolkit."""

import json
import time
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from .models import SessionMetadata
from .models import SessionState


class SessionManager:
    """Manager for creating, loading, and persisting sessions.

    Handles session lifecycle including:
    - Creating new sessions with unique IDs
    - Loading existing sessions for re-entrancy
    - Saving session state to disk
    - Cleaning up old sessions
    """

    def __init__(self, session_dir: Path | None = None):
        """Initialize session manager.

        Args:
            session_dir: Directory to store sessions.
                        Defaults to ~/.ccsdk/sessions
        """
        self.session_dir = session_dir or (Path.home() / ".ccsdk" / "sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create_session(self, name: str = "unnamed", tags: list[str] | None = None) -> SessionState:
        """Create a new session.

        Args:
            name: Human-readable session name
            tags: Optional tags for categorization

        Returns:
            New SessionState instance
        """
        metadata = SessionMetadata(name=name, tags=tags or [])
        return SessionState(metadata=metadata)

    def load_session(self, session_id: str) -> SessionState | None:
        """Load an existing session.

        Args:
            session_id: Session identifier

        Returns:
            SessionState if found, None otherwise
        """
        session_file = self.session_dir / f"{session_id}.json"
        if not session_file.exists():
            return None

        with open(session_file) as f:
            data = json.load(f)

        # Convert datetime strings back to datetime objects
        if "metadata" in data:
            if "created_at" in data["metadata"]:
                data["metadata"]["created_at"] = datetime.fromisoformat(data["metadata"]["created_at"])
            if "updated_at" in data["metadata"]:
                data["metadata"]["updated_at"] = datetime.fromisoformat(data["metadata"]["updated_at"])

        return SessionState(**data)

    def save_session(self, session: SessionState) -> Path:
        """Save session to disk.

        Args:
            session: Session to save

        Returns:
            Path to saved session file
        """
        session_file = self.session_dir / f"{session.metadata.session_id}.json"

        # Convert to JSON-serializable format
        data = session.model_dump()

        # Convert datetime objects to ISO format strings
        if "metadata" in data:
            if "created_at" in data["metadata"]:
                data["metadata"]["created_at"] = data["metadata"]["created_at"].isoformat()
            if "updated_at" in data["metadata"]:
                data["metadata"]["updated_at"] = data["metadata"]["updated_at"].isoformat()

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return session_file

    def list_sessions(self, days_back: int = 7) -> list[SessionMetadata]:
        """List recent sessions.

        Args:
            days_back: How many days back to look

        Returns:
            List of session metadata
        """
        sessions = []
        cutoff = datetime.now(UTC) - timedelta(days=days_back)

        for session_file in self.session_dir.glob("*.json"):
            # Check file modification time
            mtime = datetime.fromtimestamp(session_file.stat().st_mtime, tz=UTC)
            if mtime < cutoff:
                continue

            try:
                session = self.load_session(session_file.stem)
                if session:
                    sessions.append(session.metadata)
            except Exception:
                # Skip corrupted sessions
                continue

        # Sort by updated time, newest first
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        return sessions

    def cleanup_old_sessions(self, days_to_keep: int = 30) -> int:
        """Remove sessions older than specified days.

        Args:
            days_to_keep: Keep sessions newer than this many days

        Returns:
            Number of sessions removed
        """
        cutoff = time.time() - (days_to_keep * 86400)
        removed = 0

        for session_file in self.session_dir.glob("*.json"):
            if session_file.stat().st_mtime < cutoff:
                session_file.unlink()
                removed += 1

        return removed

    def get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session.

        Args:
            session_id: Session identifier

        Returns:
            Path to session file
        """
        return self.session_dir / f"{session_id}.json"
