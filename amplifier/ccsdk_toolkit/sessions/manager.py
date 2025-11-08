"""Session management for CCSDK toolkit."""

import json
import time
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:  # pragma: no cover - type hint support
    from amplifier.session_monitor.models import TokenUsageSnapshot

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
        self.workspace_base_dir = Path(".codex/workspaces")

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

        # Ensure new optional fields exist for backward compatibility
        data.setdefault("checkpoint_data", None)
        data.setdefault("token_usage_history", [])
        data.setdefault("last_checkpoint_at", None)

        # Convert datetime strings back to datetime objects where necessary
        metadata = data.get("metadata") or {}
        created_at = metadata.get("created_at")
        updated_at = metadata.get("updated_at")
        last_checkpoint_at = data.get("last_checkpoint_at")

        if isinstance(created_at, str):
            metadata["created_at"] = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            metadata["updated_at"] = datetime.fromisoformat(updated_at)
        if isinstance(last_checkpoint_at, str):
            data["last_checkpoint_at"] = datetime.fromisoformat(last_checkpoint_at)

        return SessionState(**data)

    def save_session(self, session: SessionState) -> Path:
        """Save session to disk.

        Args:
            session: Session to save

        Returns:
            Path to saved session file
        """
        session_file = self.session_dir / f"{session.metadata.session_id}.json"

        data = session.model_dump(mode="json")

        with open(session_file, "w") as f:
            json.dump(data, f, indent=2)

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

    def save_checkpoint(self, session_id: str, checkpoint_data: dict[str, Any]) -> Path:
        """Save checkpoint data for a session.

        Args:
            session_id: Session identifier
            checkpoint_data: Data to checkpoint

        Returns:
            Path to checkpoint file
        """
        session = self.load_session(session_id)
        if not session:
            metadata = SessionMetadata(session_id=session_id, name=session_id)
            session = SessionState(metadata=metadata)

        session.create_checkpoint(checkpoint_data)
        self.save_session(session)

        checkpoint_dir = self.workspace_base_dir / session_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = checkpoint_dir / "checkpoint.json"

        checkpoint_content = {
            "session_id": session_id,
            "checkpoint_data": checkpoint_data,
            "timestamp": session.last_checkpoint_at.isoformat()
            if session.last_checkpoint_at
            else datetime.now().isoformat(),
        }

        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_content, f, indent=2)

        return checkpoint_file

    def load_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        """Load checkpoint data for a session.

        Args:
            session_id: Session identifier

        Returns:
            Checkpoint data if available, None otherwise
        """
        checkpoint_file = self.workspace_base_dir / session_id / "checkpoint.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file) as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError:
            return None

    def resume_session(self, session_id: str, continuation_command: str) -> SessionState:
        """Resume a session from checkpoint.

        Args:
            session_id: Session identifier
            continuation_command: Command to continue execution

        Returns:
            SessionState with restored checkpoint, None if not found
        """
        session = self.load_session(session_id)
        if not session:
            raise FileNotFoundError(f"Session '{session_id}' not found.")

        checkpoint = self.load_checkpoint(session_id)
        if checkpoint:
            session.checkpoint_data = checkpoint.get("checkpoint_data")
            timestamp = checkpoint.get("timestamp")
            if isinstance(timestamp, str):
                try:
                    session.last_checkpoint_at = datetime.fromisoformat(timestamp)
                except ValueError:
                    session.last_checkpoint_at = None

        session.context["continuation_command"] = continuation_command
        session.metadata.update()
        self.save_session(session)
        return session

    def get_session_token_usage(self, session_id: str) -> list["TokenUsageSnapshot"]:
        """Get token usage history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of token usage snapshots
        """
        session = self.load_session(session_id)
        if not session:
            return []
        return session.token_usage_history
