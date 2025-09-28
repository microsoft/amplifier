"""Git utilities for auto-healing."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def create_healing_branch(module_name: str) -> str:
    """Create a new branch for healing."""
    branch_name = f"auto-heal/{module_name}"
    try:
        subprocess.run(["git", "checkout", "-b", branch_name], capture_output=True, check=True)
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
