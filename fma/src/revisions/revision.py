"""Revision management functions."""

from pathlib import Path

from fma.src.revisions.revision_state import RevisionState
from fma.src.utils.db_utils import write_state
from fma.src.utils.db_utils import write_xfma_state
from fma.src.utils.git_utils import create_worktree


def create_xfma_state(worktree_path: Path, prd_name: str, unique_id: str) -> RevisionState:
    """Create .xfma folder with state.json in the worktree.

    Args:
        worktree_path: Path to the worktree
        prd_name: The PRD name/number
        unique_id: The unique identifier for this worktree

    Returns:
        RevisionState instance
    """
    # Create RevisionState
    state = RevisionState.create_initial(unique_id, prd_name, worktree_path)

    # Write to .xfma/state.json
    state_file = write_xfma_state(worktree_path, state)

    print(f"✅ Created .xfma/state.json: {state_file}")

    return state


def create_database_record(state: RevisionState) -> Path:
    """Create database folder and state.json in $LAMP_DB_HOME/database.

    Args:
        state: RevisionState to write

    Returns:
        Path to the database record folder
    """
    # Write state to database
    state_file = write_state(state)

    print(f"✅ Created database record: {state_file.parent}")

    return state_file.parent


def setup_prd_worktree(prd_name: str, base_branch: str = "main") -> dict:
    """Complete setup for a PRD worktree.

    This is the main function that orchestrates all the steps:
    1. Create worktree
    2. Create RevisionState
    3. Write to .xfma state
    4. Write to database record

    Args:
        prd_name: The PRD name/number (e.g., "001_basic_functions")
        base_branch: Base branch to create worktree from (default: "main")

    Returns:
        Dictionary with worktree info
    """
    print(f"🚀 Setting up worktree for PRD: {prd_name}")

    # Create worktree
    worktree_path, unique_id = create_worktree(prd_name, base_branch)

    # Create RevisionState and write to .xfma
    state = create_xfma_state(worktree_path, prd_name, unique_id)

    # Write to database
    db_record = create_database_record(state)

    result = {
        "id": state.id,
        "prd_name": state.prd_name,
        "worktree_path": state.worktree_path,
        "xfma_dir": str(worktree_path / ".xfma"),
        "db_record": str(db_record),
    }

    print("\n✨ Worktree setup complete!")
    print(f"   Worktree: {worktree_path}")
    print(f"   ID: {unique_id}")

    return result
