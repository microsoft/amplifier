"""Unit tests for worktree command."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from git.exc import GitCommandError

from amplifier.cli.commands import worktree
from amplifier.cli.core.errors import ConfigurationError
from tests.fixtures.mocks import MockOutputManager


class TestWorktreeCommand:
    """Test worktree command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_output(self):
        """Create mock output manager."""
        return MockOutputManager()

    @pytest.fixture
    def mock_repo(self):
        """Create mock git repository."""
        repo = MagicMock()
        repo.working_dir = "/test/repo"
        repo.git = MagicMock()
        repo.refs = []
        return repo

    @pytest.fixture
    def temp_repo(self, tmp_path):
        """Create temporary repository directory."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        return repo_dir

    def test_get_repo_success(self, mock_repo):
        """Test getting repository when in a git repo."""
        with patch("git.Repo", return_value=mock_repo):
            result = worktree.get_repo()
            assert result == mock_repo

    def test_get_repo_not_in_git(self):
        """Test get_repo raises error when not in a git repository."""
        with (
            patch("git.Repo", side_effect=Exception("Not a git repo")),
            pytest.raises(ConfigurationError, match="Not in a git repository"),
        ):
            worktree.get_repo()

    def test_get_worktrees_dir(self, mock_repo, tmp_path):
        """Test getting worktrees directory path."""
        mock_repo.working_dir = str(tmp_path / "repo")

        with patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo):
            result = worktree.get_worktrees_dir()
            assert result == tmp_path / ".amplifier-worktrees"

    def test_copy_data_directory(self, tmp_path):
        """Test copying .data directory from source to worktree."""
        source = tmp_path / "source"
        source.mkdir()
        source_data = source / ".data"
        source_data.mkdir()
        (source_data / "file.txt").write_text("test content")
        (source_data / "subdir").mkdir()
        (source_data / "subdir" / "nested.txt").write_text("nested content")

        target = tmp_path / "target"
        target.mkdir()

        worktree.copy_data_directory(source, target)

        # Verify copy
        assert (target / ".data").exists()
        assert (target / ".data" / "file.txt").read_text() == "test content"
        assert (target / ".data" / "subdir" / "nested.txt").read_text() == "nested content"

    def test_copy_data_directory_replaces_existing(self, tmp_path):
        """Test copying .data directory replaces existing data."""
        source = tmp_path / "source"
        source.mkdir()
        source_data = source / ".data"
        source_data.mkdir()
        (source_data / "new.txt").write_text("new content")

        target = tmp_path / "target"
        target.mkdir()
        target_data = target / ".data"
        target_data.mkdir()
        (target_data / "old.txt").write_text("old content")

        worktree.copy_data_directory(source, target)

        # Old file should be gone
        assert not (target / ".data" / "old.txt").exists()
        # New file should exist
        assert (target / ".data" / "new.txt").read_text() == "new content"

    def test_copy_data_directory_no_source(self, tmp_path):
        """Test copy_data_directory when source doesn't have .data."""
        source = tmp_path / "source"
        source.mkdir()
        target = tmp_path / "target"
        target.mkdir()

        # Should not raise error
        worktree.copy_data_directory(source, target)

        # No .data directory should be created
        assert not (target / ".data").exists()

    def test_create_worktree_new_branch(self, runner, mock_repo, tmp_path):
        """Test creating worktree with new branch."""
        mock_repo.working_dir = str(tmp_path / "repo")
        mock_repo.refs = []  # No existing branches

        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
            patch("amplifier.cli.commands.worktree.copy_data_directory") as mock_copy,
        ):
            result = runner.invoke(worktree.cmd, ["create", "feature"])

            assert result.exit_code == 0
            # Should create worktree with new branch
            mock_repo.git.worktree.assert_called_once_with("add", "-b", "feature", str(worktrees_dir / "feature"))
            # Should copy data directory
            mock_copy.assert_called_once()
            assert "Created worktree with new branch 'feature'" in result.output

    def test_create_worktree_existing_branch(self, runner, mock_repo, tmp_path):
        """Test creating worktree with existing branch."""
        mock_repo.working_dir = str(tmp_path / "repo")
        # Mock existing branch
        mock_ref = Mock()
        mock_ref.name = "existing-branch"
        mock_repo.refs = [mock_ref]

        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
            patch("amplifier.cli.commands.worktree.copy_data_directory"),
        ):
            result = runner.invoke(worktree.cmd, ["create", "test", "--branch", "existing-branch"])

            assert result.exit_code == 0
            # Should create worktree with existing branch
            mock_repo.git.worktree.assert_called_once_with("add", str(worktrees_dir / "test"), "existing-branch")
            assert "Created worktree with existing branch 'existing-branch'" in result.output

    def test_create_worktree_no_copy_data(self, runner, mock_repo, tmp_path):
        """Test creating worktree without copying .data directory."""
        mock_repo.working_dir = str(tmp_path / "repo")
        mock_repo.refs = []

        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
            patch("amplifier.cli.commands.worktree.copy_data_directory") as mock_copy,
        ):
            result = runner.invoke(worktree.cmd, ["create", "feature", "--no-copy-data"])

            assert result.exit_code == 0
            # Should NOT copy data directory
            mock_copy.assert_not_called()

    def test_create_worktree_already_exists(self, runner, mock_repo, tmp_path):
        """Test error when worktree already exists."""
        mock_repo.working_dir = str(tmp_path / "repo")

        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        existing_worktree = worktrees_dir / "feature"
        existing_worktree.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["create", "feature"])

            assert result.exit_code != 0
            assert "already exists" in result.output

    def test_create_worktree_git_error(self, runner, mock_repo, tmp_path):
        """Test handling git command error during creation."""
        mock_repo.working_dir = str(tmp_path / "repo")
        mock_repo.refs = []
        mock_repo.git.worktree.side_effect = GitCommandError("git", "error message")

        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["create", "feature"])

            assert result.exit_code != 0
            assert "Failed to create worktree" in result.output

    def test_list_worktrees_none_found(self, runner, mock_repo):
        """Test listing worktrees when none exist."""
        mock_repo.git.worktree.return_value = ""

        with patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo):
            result = runner.invoke(worktree.cmd, ["list"])

            assert result.exit_code == 0
            assert "No worktrees found" in result.output

    def test_list_worktrees_success(self, runner, mock_repo, tmp_path):
        """Test listing existing worktrees."""
        worktree_output = """worktree /test/repo
HEAD abc123def456
branch refs/heads/main

worktree /test/.amplifier-worktrees/feature
HEAD 123456abc789
branch refs/heads/feature

worktree /test/.amplifier-worktrees/bugfix
HEAD 789def123456
branch refs/heads/bugfix
detached
"""
        mock_repo.git.worktree.return_value = worktree_output
        mock_repo.working_dir = "/test/repo"

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=Path("/test/.amplifier-worktrees")),
        ):
            result = runner.invoke(worktree.cmd, ["list"])

            assert result.exit_code == 0
            assert "3 worktree(s)" in result.output
            assert "main" in result.output
            assert "feature" in result.output
            assert "bugfix" in result.output
            assert "detached" in result.output

    def test_list_worktrees_with_locked(self, runner, mock_repo):
        """Test listing worktrees with locked status."""
        worktree_output = """worktree /test/repo
HEAD abc123def456
branch refs/heads/main

worktree /test/worktrees/feature
HEAD 123456abc789
branch refs/heads/feature
locked Locked for testing
"""
        mock_repo.git.worktree.return_value = worktree_output
        mock_repo.working_dir = "/test/repo"

        with patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo):
            result = runner.invoke(worktree.cmd, ["list"])

            assert result.exit_code == 0
            assert "locked" in result.output

    def test_list_worktrees_git_error(self, runner, mock_repo):
        """Test handling git error when listing worktrees."""
        mock_repo.git.worktree.side_effect = GitCommandError("git", "error")

        with patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo):
            result = runner.invoke(worktree.cmd, ["list"])

            assert result.exit_code != 0
            assert "Failed to list worktrees" in result.output

    def test_remove_worktree_success(self, runner, mock_repo, tmp_path):
        """Test removing a worktree."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        worktree_path = worktrees_dir / "feature"
        worktree_path.mkdir()

        mock_repo.git.worktree.return_value = None  # Success

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature"])

            assert result.exit_code == 0
            mock_repo.git.worktree.assert_called_once_with("remove", str(worktree_path))
            assert "Removed worktree" in result.output

    def test_remove_worktree_force(self, runner, mock_repo, tmp_path):
        """Test force removing a worktree."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        worktree_path = worktrees_dir / "feature"
        worktree_path.mkdir()

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature", "--force"])

            assert result.exit_code == 0
            mock_repo.git.worktree.assert_called_once_with("remove", str(worktree_path), "--force")
            assert "Force removed worktree" in result.output

    def test_remove_worktree_not_found(self, runner, mock_repo, tmp_path):
        """Test error when worktree doesn't exist."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        # Worktree doesn't exist

        mock_repo.git.worktree.return_value = ""  # Empty list

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "nonexistent"])

            assert result.exit_code != 0
            assert "not found" in result.output

    def test_remove_worktree_find_by_name(self, runner, mock_repo, tmp_path):
        """Test finding worktree by name in git worktree list."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        other_path = tmp_path / "other" / "feature"

        # Worktree not in expected location
        worktree_list = f"worktree {other_path}\nHEAD abc123\nbranch feature"
        mock_repo.git.worktree.side_effect = [worktree_list, None]  # First for list, then for remove

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature"])

            assert result.exit_code == 0
            # Should find and remove the worktree
            calls = mock_repo.git.worktree.call_args_list
            assert calls[1][0] == ("remove", str(other_path))

    def test_remove_worktree_with_uncommitted_changes(self, runner, mock_repo, tmp_path):
        """Test error when worktree has uncommitted changes."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        worktree_path = worktrees_dir / "feature"
        worktree_path.mkdir()

        error = GitCommandError("git", "contains modified or untracked files")
        mock_repo.git.worktree.side_effect = error

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature"])

            assert result.exit_code != 0
            assert "uncommitted changes" in result.output
            assert "Use --force" in result.output

    def test_remove_worktree_cleans_up_directory(self, runner, mock_repo, tmp_path):
        """Test that remove cleans up directory if it still exists."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        worktree_path = worktrees_dir / "feature"
        worktree_path.mkdir()
        (worktree_path / "leftover.txt").write_text("leftover file")

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
            patch("shutil.rmtree") as mock_rmtree,
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature"])

            assert result.exit_code == 0
            # Should clean up the directory
            mock_rmtree.assert_called_once_with(worktree_path)

    def test_remove_worktree_git_error(self, runner, mock_repo, tmp_path):
        """Test handling other git errors during removal."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()
        worktree_path = worktrees_dir / "feature"
        worktree_path.mkdir()

        mock_repo.git.worktree.side_effect = GitCommandError("git", "unexpected error")

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
        ):
            result = runner.invoke(worktree.cmd, ["remove", "feature"])

            assert result.exit_code != 0
            assert "Failed to remove worktree" in result.output

    def test_worktree_with_output_manager(self, runner, mock_repo, mock_output, tmp_path):
        """Test worktree commands use output manager."""
        worktrees_dir = tmp_path / ".amplifier-worktrees"
        worktrees_dir.mkdir()

        mock_repo.refs = []
        mock_repo.working_dir = str(tmp_path / "repo")

        with (
            patch("amplifier.cli.commands.worktree.get_repo", return_value=mock_repo),
            patch("amplifier.cli.commands.worktree.get_worktrees_dir", return_value=worktrees_dir),
            patch("amplifier.cli.core.output.get_output_manager", return_value=mock_output),
        ):
            result = runner.invoke(worktree.cmd, ["create", "test"], obj={"output": mock_output})

            assert result.exit_code == 0
            # Should have used output manager
            assert any("Creating worktree" in msg for _, msg in mock_output.messages)
            assert any("success" in method for method, _ in mock_output.messages)
