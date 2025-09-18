"""Session management module for tracking and recovering microtask workflow state.

This module provides session state management with full recovery support,
allowing workflows to be interrupted and resumed from saved checkpoints.
"""

import uuid
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from amplifier_microtask.storage import save_json, load_json, ensure_directory


class SessionNotFoundError(Exception):
    """Raised when attempting to load a non-existent session."""


@dataclass
class Session:
    """Session state container for microtask workflows.

    Attributes:
        id: Unique session identifier
        created_at: Session creation timestamp
        status: Current status ("active", "completed", "failed")
        current_stage: Name of the current processing stage
        completed_tasks: List of completed task identifiers
        data: Arbitrary task-specific data
        workspace: Path to the workspace directory
    """

    id: str
    created_at: datetime
    status: str  # "active", "completed", "failed"
    current_stage: str
    completed_tasks: List[str]
    data: Dict[str, Any]
    workspace: Path

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "current_stage": self.current_stage,
            "completed_tasks": self.completed_tasks,
            "data": self.data,
            "workspace": str(self.workspace),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        return cls(
            id=data["id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            status=data["status"],
            current_stage=data["current_stage"],
            completed_tasks=data["completed_tasks"],
            data=data["data"],
            workspace=Path(data["workspace"]),
        )


@dataclass
class SessionInfo:
    """Lightweight session information for listing."""

    id: str
    created_at: datetime
    status: str
    current_stage: str
    workspace: Path


def create_session(workspace: Path) -> Session:
    """Create a new session with unique ID.

    Args:
        workspace: Path to the workspace directory

    Returns:
        New Session instance with initial state
    """
    session = Session(
        id=str(uuid.uuid4()),
        created_at=datetime.now(),
        status="active",
        current_stage="initialization",
        completed_tasks=[],
        data={},
        workspace=workspace,
    )

    # Save initial state
    save_checkpoint(session)

    return session


def load_session(session_id: str, workspace: Path) -> Session:
    """Load existing session from saved state.

    Args:
        session_id: Session identifier to load
        workspace: Path to the workspace directory

    Returns:
        Loaded Session instance

    Raises:
        SessionNotFoundError: If session file doesn't exist
    """
    session_file = _get_session_file(session_id, workspace)

    if not session_file.exists():
        raise SessionNotFoundError(f"Session {session_id} not found in {workspace}")

    data = load_json(session_file)

    if not data:
        raise SessionNotFoundError(f"Session {session_id} file exists but is empty or corrupted")

    return Session.from_dict(data)


def save_checkpoint(session: Session) -> bool:
    """Save current session state to disk.

    Args:
        session: Session to save

    Returns:
        True if saved successfully, False otherwise
    """
    session_file = _get_session_file(session.id, session.workspace)
    return save_json(session.to_dict(), session_file)


def list_sessions(workspace: Path) -> List[SessionInfo]:
    """Find all existing sessions in workspace.

    Args:
        workspace: Path to the workspace directory

    Returns:
        List of SessionInfo objects for all found sessions
    """
    sessions_dir = workspace / ".sessions"

    if not sessions_dir.exists():
        return []

    sessions = []

    # Look for all session JSON files
    for session_file in sessions_dir.glob("*.json"):
        try:
            data = load_json(session_file)
            if data:
                sessions.append(
                    SessionInfo(
                        id=data["id"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        status=data["status"],
                        current_stage=data["current_stage"],
                        workspace=Path(data["workspace"]),
                    )
                )
        except (KeyError, ValueError):
            # Skip corrupted session files
            continue

    # Sort by creation time, newest first
    sessions.sort(key=lambda s: s.created_at, reverse=True)

    return sessions


def update_session_status(session: Session, status: str) -> bool:
    """Update session status and save.

    Args:
        session: Session to update
        status: New status value

    Returns:
        True if saved successfully
    """
    session.status = status
    return save_checkpoint(session)


def update_session_stage(session: Session, stage: str) -> bool:
    """Update current stage and save.

    Args:
        session: Session to update
        stage: New stage name

    Returns:
        True if saved successfully
    """
    session.current_stage = stage
    return save_checkpoint(session)


def add_completed_task(session: Session, task_id: str) -> bool:
    """Add task to completed list and save.

    Args:
        session: Session to update
        task_id: Task identifier to add

    Returns:
        True if saved successfully
    """
    if task_id not in session.completed_tasks:
        session.completed_tasks.append(task_id)
        return save_checkpoint(session)
    return True


def update_session_data(session: Session, key: str, value: Any) -> bool:
    """Update session data dictionary and save.

    Args:
        session: Session to update
        key: Data key to set
        value: Value to store

    Returns:
        True if saved successfully
    """
    session.data[key] = value
    return save_checkpoint(session)


def get_latest_session(workspace: Path) -> Optional[Session]:
    """Get the most recently created active session.

    Args:
        workspace: Path to the workspace directory

    Returns:
        Latest active Session or None if no active sessions
    """
    sessions = list_sessions(workspace)

    for session_info in sessions:
        if session_info.status == "active":
            try:
                return load_session(session_info.id, workspace)
            except SessionNotFoundError:
                continue

    return None


def cleanup_old_sessions(workspace: Path, keep_count: int = 10) -> int:
    """Remove old completed/failed sessions keeping most recent.

    Args:
        workspace: Path to the workspace directory
        keep_count: Number of recent sessions to keep

    Returns:
        Number of sessions removed
    """
    sessions = list_sessions(workspace)
    removed_count = 0

    # Keep all active sessions and most recent inactive ones
    inactive_sessions = [s for s in sessions if s.status != "active"]

    # Remove old inactive sessions beyond keep_count
    if len(inactive_sessions) > keep_count:
        for session_info in inactive_sessions[keep_count:]:
            session_file = _get_session_file(session_info.id, workspace)
            try:
                if session_file.exists():
                    session_file.unlink()
                    removed_count += 1
            except (IOError, OSError):
                # Skip files we can't delete
                pass

    return removed_count


def _get_session_file(session_id: str, workspace: Path) -> Path:
    """Get the path to a session file.

    Args:
        session_id: Session identifier
        workspace: Workspace directory

    Returns:
        Path to the session JSON file
    """
    sessions_dir = ensure_directory(workspace / ".sessions")
    return sessions_dir / f"{session_id}.json"
