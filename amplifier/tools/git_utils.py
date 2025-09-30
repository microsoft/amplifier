"""Git utilities for auto-healing."""

import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def check_clean_working_tree() -> bool:
    """Check if working tree is clean (no uncommitted changes).

    Returns:
        True if clean, False if there are uncommitted changes
    """
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        return not result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check git status: {e}")
        return False


def create_healing_branch(module_name: str) -> str:
    """Create a new branch for healing."""
    # Check for uncommitted changes first
    if not check_clean_working_tree():
        logger.warning("Working tree has uncommitted changes - creating branch anyway")

    # Add timestamp to ensure uniqueness
    timestamp = int(time.time())
    branch_name = f"auto-heal/{module_name}/{timestamp}"

    try:
        # First check if we need to switch from existing branch
        current_branch = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
        ).stdout.strip()

        # If on another auto-heal branch, stash changes and switch to main first
        if current_branch.startswith("auto-heal/"):
            # Stash any uncommitted changes
            subprocess.run(["git", "stash"], capture_output=True, check=False)
            # Switch to main
            subprocess.run(["git", "checkout", "main"], capture_output=True, check=True)
            # Pop stash if there were changes
            stash_list = subprocess.run(
                ["git", "stash", "list"], capture_output=True, text=True, check=True
            ).stdout.strip()
            if stash_list:
                subprocess.run(["git", "stash", "pop"], capture_output=True, check=False)

        # Now create the new branch
        subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True, check=True)
        logger.info(f"Created healing branch: {branch_name}")
        return branch_name
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create branch: {e}")
        raise


def cleanup_branch(branch_name: str) -> None:
    """Clean up healing branch."""
    try:
        subprocess.run(["git", "checkout", "main"], capture_output=True, check=True)
        subprocess.run(["git", "branch", "-D", branch_name], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to cleanup branch: {e}")


def commit_and_merge(module_path: Path, branch_name: str, health_before: float, health_after: float) -> bool:
    """Commit changes and merge to main."""
    try:
        # Add and commit
        subprocess.run(["git", "add", str(module_path)], capture_output=True, check=True)
        commit_msg = f"Auto-heal: {module_path.name} (health {health_before:.1f} → {health_after:.1f})"
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, check=True)

        # Merge to main
        subprocess.run(["git", "checkout", "main"], capture_output=True, check=True)
        subprocess.run(["git", "merge", branch_name, "--no-ff"], capture_output=True, check=True)

        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operations failed: {e}")
        return False
