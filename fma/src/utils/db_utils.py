"""Database utilities for reading and writing revision state."""

import json
import os
from pathlib import Path

from fma.src.revisions.revision_state import RevisionState


def get_database_dir() -> Path:
    """Get the database directory path.

    Returns:
        Path to the database directory

    Raises:
        RuntimeError: If neither LAMP_DB_HOME nor LAMP_HOME is set
    """
    lamp_db_home = os.getenv("LAMP_DB_HOME")
    if lamp_db_home:
        return Path(lamp_db_home)

    lamp_home = os.getenv("LAMP_HOME")
    if not lamp_home:
        raise RuntimeError("Neither LAMP_DB_HOME nor LAMP_HOME environment variable is set")

    return Path(lamp_home) / "database"


def get_record_dir(revision_id: str) -> Path:
    """Get the database record directory for a revision.

    Args:
        revision_id: The unique revision ID

    Returns:
        Path to the record directory
    """
    database_dir = get_database_dir()
    return database_dir / revision_id


def write_state(state: RevisionState) -> Path:
    """Write revision state to database.

    Args:
        state: RevisionState to write

    Returns:
        Path to the written state.json file
    """
    record_dir = get_record_dir(state.id)
    record_dir.mkdir(parents=True, exist_ok=True)

    state_file = record_dir / "state.json"
    with open(state_file, "w") as f:
        json.dump(state.to_dict(), f, indent=2)

    return state_file


def read_state(revision_id: str) -> RevisionState:
    """Read revision state from database.

    Args:
        revision_id: The unique revision ID

    Returns:
        RevisionState instance

    Raises:
        FileNotFoundError: If state file doesn't exist
        ValueError: If state file is invalid
    """
    record_dir = get_record_dir(revision_id)
    state_file = record_dir / "state.json"

    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file) as f:
        data = json.load(f)

    return RevisionState.from_dict(data)


def write_xfma_state(worktree_path: Path, state: RevisionState) -> Path:
    """Write revision state to worktree .xfma/state.json.

    Args:
        worktree_path: Path to the worktree
        state: RevisionState to write

    Returns:
        Path to the written state.json file
    """
    xfma_dir = worktree_path / ".xfma"
    xfma_dir.mkdir(exist_ok=True)

    state_file = xfma_dir / "state.json"
    with open(state_file, "w") as f:
        json.dump(state.to_dict(), f, indent=2)

    return state_file


def read_xfma_state(worktree_path: Path) -> RevisionState:
    """Read revision state from worktree .xfma/state.json.

    Args:
        worktree_path: Path to the worktree

    Returns:
        RevisionState instance

    Raises:
        FileNotFoundError: If state file doesn't exist
        ValueError: If state file is invalid
    """
    state_file = worktree_path / ".xfma" / "state.json"

    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")

    with open(state_file) as f:
        data = json.load(f)

    return RevisionState.from_dict(data)


def update_state(revision_id: str, updates: dict) -> RevisionState:
    """Update specific fields in a revision state.

    Args:
        revision_id: The unique revision ID
        updates: Dictionary of field updates

    Returns:
        Updated RevisionState

    Raises:
        FileNotFoundError: If state doesn't exist
    """
    state = read_state(revision_id)

    # Update fields
    for key, value in updates.items():
        if hasattr(state, key):
            setattr(state, key, value)

    # Write back to database
    write_state(state)

    # Also update worktree if path exists
    worktree_path = Path(state.worktree_path)
    if worktree_path.exists():
        write_xfma_state(worktree_path, state)

    return state


def list_all_states() -> list[RevisionState]:
    """List all revision states in the database.

    Returns:
        List of RevisionState instances
    """
    database_dir = get_database_dir()
    if not database_dir.exists():
        return []

    states = []
    for record_dir in database_dir.iterdir():
        if not record_dir.is_dir():
            continue

        state_file = record_dir / "state.json"
        if not state_file.exists():
            continue

        try:
            with open(state_file) as f:
                data = json.load(f)
            states.append(RevisionState.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            # Skip invalid state files
            continue

    return states


def delete_state(revision_id: str) -> None:
    """Delete a revision state from the database.

    Args:
        revision_id: The unique revision ID
    """
    record_dir = get_record_dir(revision_id)
    if record_dir.exists():
        import shutil

        shutil.rmtree(record_dir)
