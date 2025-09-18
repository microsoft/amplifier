"""Tests for git checkpoint management."""

from pathlib import Path
from unittest.mock import Mock, patch


from amplifier_microtask.git_checkpoint import (
    GitCheckpoint,
    create_recovery_checkpoint,
    rollback_session,
)


class TestGitCheckpoint:
    """Test git checkpoint functionality."""

    def test_init(self):
        """Test GitCheckpoint initialization."""
        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        assert checkpoint.workspace == workspace
        assert checkpoint.checkpoints_dir == workspace / ".checkpoints"

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    def test_is_git_repo_true(self, mock_run):
        """Test checking if directory is a git repo."""
        mock_run.return_value = Mock(returncode=0)

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        assert checkpoint._is_git_repo() is True
        mock_run.assert_called_once()

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    def test_is_git_repo_false(self, mock_run):
        """Test checking non-git directory."""
        mock_run.return_value = Mock(returncode=1)

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        assert checkpoint._is_git_repo() is False

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    def test_get_git_status(self, mock_run):
        """Test getting git status."""
        mock_run.return_value = Mock(returncode=0, stdout="M  file1.py\nA  file2.py\n")

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        status = checkpoint._get_git_status()
        assert status == "M  file1.py\nA  file2.py"

    def test_generate_commit_message_basic(self):
        """Test basic commit message generation."""
        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        message = checkpoint._generate_commit_message("test_stage")

        assert "Checkpoint: test_stage" in message
        assert "Timestamp:" in message

    def test_generate_commit_message_with_task_data(self):
        """Test commit message with task metadata."""
        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        task_data = {
            "task_id": "task_123",
            "description": "Implementing feature X",
            "completed_tasks": ["subtask_1", "subtask_2", "subtask_3"],
        }

        message = checkpoint._generate_commit_message("test_stage", task_data)

        assert "Checkpoint: test_stage" in message
        assert "Task: task_123" in message
        assert "Implementing feature X" in message
        assert "subtask_1" in message
        assert "subtask_2" in message

    def test_generate_commit_message_truncates_tasks(self):
        """Test that commit message truncates long task lists."""
        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        task_data = {"completed_tasks": [f"task_{i}" for i in range(10)]}

        message = checkpoint._generate_commit_message("test_stage", task_data)

        # Should only show first 5 tasks
        assert "task_0" in message
        assert "task_4" in message
        assert "task_5" not in message
        assert "and 5 more" in message

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    @patch("amplifier_microtask.git_checkpoint.save_json")
    def test_create_checkpoint_success(self, mock_save, mock_run):
        """Test successful checkpoint creation."""
        # Setup mock responses
        mock_run.side_effect = [
            Mock(returncode=0),  # is_git_repo
            Mock(returncode=0, stdout="M  file.py"),  # get_status
            Mock(returncode=0),  # stage files
            Mock(returncode=0),  # create commit
            Mock(returncode=0, stdout="abc123def"),  # get commit hash
        ]
        mock_save.return_value = True

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        commit_hash = checkpoint.create_checkpoint(session_id="session_123", stage_name="test_stage", files=["file.py"])

        assert commit_hash == "abc123def"
        assert mock_save.called

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    def test_create_checkpoint_no_changes(self, mock_run):
        """Test checkpoint creation with no changes."""
        mock_run.side_effect = [
            Mock(returncode=0),  # is_git_repo
            Mock(returncode=0, stdout=""),  # get_status (empty)
        ]

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        commit_hash = checkpoint.create_checkpoint(session_id="session_123", stage_name="test_stage", files=["file.py"])

        assert commit_hash is None

    @patch("amplifier_microtask.git_checkpoint.subprocess.run")
    def test_rollback_with_uncommitted_changes(self, mock_run):
        """Test rollback stashes uncommitted changes."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="M  file.py"),  # has changes
            Mock(returncode=0),  # stash
            Mock(returncode=0),  # reset
        ]

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        result = checkpoint.rollback_to_checkpoint("abc123")

        assert result is True
        # Check that stash was called
        assert any("stash" in str(call) for call in mock_run.call_args_list)

    @patch("amplifier_microtask.git_checkpoint.load_json")
    def test_get_checkpoint_history(self, mock_load):
        """Test retrieving checkpoint history."""
        mock_load.return_value = {
            "session_id": "session_123",
            "checkpoints": [
                {"commit_hash": "abc123", "stage_name": "stage1", "timestamp": "2024-01-01T10:00:00"},
                {"commit_hash": "def456", "stage_name": "stage2", "timestamp": "2024-01-01T11:00:00"},
            ],
        }

        workspace = Path("/tmp/test_workspace")
        checkpoint = GitCheckpoint(workspace)

        history = checkpoint.get_checkpoint_history("session_123")

        assert len(history) == 2
        # Should be reverse chronological
        assert history[0]["stage_name"] == "stage2"
        assert history[1]["stage_name"] == "stage1"

    @patch("amplifier_microtask.git_checkpoint.GitCheckpoint.create_checkpoint")
    def test_create_recovery_checkpoint(self, mock_create):
        """Test convenience function for recovery checkpoint."""
        mock_create.return_value = "abc123"

        result = create_recovery_checkpoint(
            workspace=Path("/tmp/test"),
            session_id="session_123",
            stage_name="test_stage",
            description="Test description",
        )

        assert result == "abc123"
        mock_create.assert_called_once()

    @patch("amplifier_microtask.git_checkpoint.GitCheckpoint.rollback_to_checkpoint")
    def test_rollback_session(self, mock_rollback):
        """Test convenience function for rollback."""
        mock_rollback.return_value = True

        result = rollback_session(workspace=Path("/tmp/test"), commit_hash="abc123")

        assert result is True
        mock_rollback.assert_called_once_with("abc123")
