"""Git checkpoint management for Amplifier CLI Tool Builder.

This module provides git integration for creating checkpoint commits at stage
boundaries, enabling rollback on failures and tracking recovery points.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from amplifier_microtask.storage import save_json, load_json, ensure_directory


class GitCheckpointError(Exception):
    """Raised when git checkpoint operations fail."""


class GitCheckpoint:
    """Manages git checkpoints for session recovery and rollback.

    Creates meaningful commits at stage boundaries and supports rollback
    to previous checkpoints if tests fail.
    """

    def __init__(self, workspace: Path):
        """Initialize git checkpoint manager.

        Args:
            workspace: Path to the workspace directory
        """
        self.workspace = workspace
        self.checkpoints_dir = ensure_directory(workspace / ".checkpoints")

    def create_checkpoint(
        self, session_id: str, stage_name: str, files: List[str], task_data: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a git commit checkpoint for the current stage.

        Args:
            session_id: Session identifier for tracking
            stage_name: Name of the current stage
            files: List of file patterns to stage
            task_data: Optional task metadata for commit message

        Returns:
            Commit hash if successful, None otherwise
        """
        try:
            # Check if we're in a git repository
            if not self._is_git_repo():
                return None

            # Check git status to see if there are changes
            status = self._get_git_status()
            if not status:
                return None  # No changes to commit

            # Stage the specified files
            if not self._stage_files(files):
                return None

            # Generate commit message
            message = self._generate_commit_message(stage_name, task_data)

            # Create the commit
            commit_hash = self._create_commit(message)

            if commit_hash:
                # Save checkpoint info
                self._save_checkpoint_info(session_id, stage_name, commit_hash)

            return commit_hash

        except subprocess.SubprocessError as e:
            raise GitCheckpointError(f"Failed to create checkpoint: {e}")

    def rollback_to_checkpoint(self, commit_hash: str) -> bool:
        """Revert to a previous checkpoint.

        Args:
            commit_hash: Git commit hash to revert to

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Check for uncommitted changes
            if self._has_uncommitted_changes():
                # Stash changes first
                subprocess.run(
                    ["git", "stash", "push", "-m", f"Rollback stash {datetime.now().isoformat()}"],
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    check=True,
                )

            # Reset to the specified commit
            result = subprocess.run(
                ["git", "reset", "--hard", commit_hash], cwd=self.workspace, capture_output=True, text=True, check=True
            )

            return result.returncode == 0

        except subprocess.SubprocessError:
            return False

    def get_checkpoint_history(self, session_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of checkpoint dictionaries with commit info
        """
        checkpoints_file = self.checkpoints_dir / f"{session_id}_checkpoints.json"
        checkpoints = load_json(checkpoints_file)

        if not checkpoints:
            return []

        # Return checkpoints in reverse chronological order
        return sorted(checkpoints.get("checkpoints", []), key=lambda x: x.get("timestamp", ""), reverse=True)

    def stage_files(self, file_patterns: List[str]) -> bool:
        """Stage files for the next commit.

        Args:
            file_patterns: List of file paths or patterns to stage

        Returns:
            True if files staged successfully
        """
        return self._stage_files(file_patterns)

    def generate_commit_message(self, stage_name: str, task_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate a descriptive commit message from stage and task data.

        Args:
            stage_name: Name of the current stage
            task_data: Optional task metadata

        Returns:
            Formatted commit message
        """
        return self._generate_commit_message(stage_name, task_data)

    # Private helper methods

    def _is_git_repo(self) -> bool:
        """Check if workspace is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], cwd=self.workspace, capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _get_git_status(self) -> str:
        """Get current git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"], cwd=self.workspace, capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except subprocess.SubprocessError:
            return ""

    def _has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        status = self._get_git_status()
        return bool(status)

    def _stage_files(self, file_patterns: List[str]) -> bool:
        """Stage files for commit."""
        if not file_patterns:
            # If no specific files, stage all changes
            file_patterns = ["."]

        try:
            for pattern in file_patterns:
                # Resolve pattern relative to workspace
                file_path = self.workspace / pattern

                # Add the file or pattern
                result = subprocess.run(
                    ["git", "add", str(file_path)], cwd=self.workspace, capture_output=True, text=True, timeout=10
                )

                if result.returncode != 0:
                    # Try adding as a pattern if direct path fails
                    subprocess.run(
                        ["git", "add", pattern], cwd=self.workspace, capture_output=True, text=True, timeout=10
                    )

            return True

        except subprocess.SubprocessError:
            return False

    def _generate_commit_message(self, stage_name: str, task_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate descriptive commit message."""
        # Base message from stage name
        message_parts = [f"Checkpoint: {stage_name}"]

        # Add task information if available
        if task_data:
            if "task_id" in task_data:
                message_parts.append(f"Task: {task_data['task_id']}")

            if "description" in task_data:
                message_parts.append(f"\n\n{task_data['description']}")

            if "completed_tasks" in task_data:
                tasks = task_data["completed_tasks"]
                if tasks:
                    message_parts.append("\n\nCompleted:")
                    for task in tasks[:5]:  # Limit to first 5 tasks
                        message_parts.append(f"  - {task}")
                    if len(tasks) > 5:
                        message_parts.append(f"  ... and {len(tasks) - 5} more")

        # Add timestamp
        message_parts.append(f"\n\nTimestamp: {datetime.now().isoformat()}")

        return "\n".join(message_parts)

    def _create_commit(self, message: str) -> Optional[str]:
        """Create a git commit with the given message."""
        try:
            # Create commit using heredoc pattern from CLAUDE.md
            commit_cmd = f"""git commit -m "$(cat <<'EOF'
{message}
EOF
)"""

            result = subprocess.run(
                commit_cmd, shell=True, cwd=self.workspace, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                # Get the commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=self.workspace, capture_output=True, text=True, timeout=5
                )

                if hash_result.returncode == 0:
                    return hash_result.stdout.strip()

            return None

        except subprocess.SubprocessError:
            return None

    def _save_checkpoint_info(self, session_id: str, stage_name: str, commit_hash: str) -> bool:
        """Save checkpoint information to tracking file."""
        checkpoints_file = self.checkpoints_dir / f"{session_id}_checkpoints.json"

        # Load existing checkpoints
        data = load_json(checkpoints_file)
        if not data:
            data = {"session_id": session_id, "checkpoints": []}

        # Add new checkpoint
        checkpoint = {"commit_hash": commit_hash, "stage_name": stage_name, "timestamp": datetime.now().isoformat()}

        data["checkpoints"].append(checkpoint)

        # Save updated checkpoints
        return save_json(data, checkpoints_file)


def create_recovery_checkpoint(
    workspace: Path, session_id: str, stage_name: str, description: str = ""
) -> Optional[str]:
    """Convenience function to create a recovery checkpoint.

    Args:
        workspace: Path to workspace
        session_id: Session identifier
        stage_name: Current stage name
        description: Optional description for the checkpoint

    Returns:
        Commit hash if successful, None otherwise
    """
    checkpoint = GitCheckpoint(workspace)

    task_data = {"description": description} if description else None

    # Stage all changes in workspace
    return checkpoint.create_checkpoint(session_id=session_id, stage_name=stage_name, files=["."], task_data=task_data)


def rollback_session(workspace: Path, commit_hash: str) -> bool:
    """Convenience function to rollback to a checkpoint.

    Args:
        workspace: Path to workspace
        commit_hash: Git commit hash to rollback to

    Returns:
        True if rollback successful
    """
    checkpoint = GitCheckpoint(workspace)
    return checkpoint.rollback_to_checkpoint(commit_hash)
