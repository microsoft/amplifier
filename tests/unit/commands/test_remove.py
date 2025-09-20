"""Unit tests for remove command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amplifier.cli.commands import remove
from tests.fixtures.mocks import MockManifest
from tests.fixtures.mocks import MockOutputManager


class TestRemoveCommand:
    """Test remove command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_output(self):
        """Create mock output manager."""
        return MockOutputManager()

    @pytest.fixture
    def mock_manifest(self):
        """Create mock manifest with resources."""
        manifest = MockManifest()
        manifest.resources = [
            {
                "name": "zen-architect",
                "type": "agents",
                "source": "github",
                "sha": "sha_123",
                "installed_at": "2024-01-01T00:00:00",
            },
            {
                "name": "bug-hunter",
                "type": "agents",
                "source": "github",
                "sha": "sha_456",
                "installed_at": "2024-01-01T00:00:00",
            },
            {
                "name": "amplifier-tool",
                "type": "tools",
                "source": "github",
                "sha": "sha_789",
                "installed_at": "2024-01-01T00:00:00",
            },
        ]
        return manifest

    @pytest.fixture
    def temp_claude_dir(self, tmp_path):
        """Create temporary .claude directory structure."""
        claude_dir = tmp_path / ".claude"
        (claude_dir / "agents").mkdir(parents=True)
        (claude_dir / "tools").mkdir(parents=True)
        (claude_dir / "commands").mkdir(parents=True)
        (claude_dir / "mcp-servers").mkdir(parents=True)

        # Create some resource files
        (claude_dir / "agents" / "zen-architect.md").write_text("Agent content")
        (claude_dir / "agents" / "bug-hunter.md").write_text("Bug hunter content")
        (claude_dir / "tools" / "amplifier-tool.md").write_text("Tool content")

        return claude_dir

    def test_remove_single_resource(self, runner, mock_manifest, temp_claude_dir):
        """Test removing a single resource."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest") as mock_save,
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"])

            assert result.exit_code == 0
            assert "Removed zen-architect" in result.output
            # File should be deleted
            assert not (temp_claude_dir / "agents" / "zen-architect.md").exists()
            # Manifest should be saved
            mock_save.assert_called_once()
            # Resource should be removed from manifest
            assert len(mock_manifest.resources) == 2

    def test_remove_multiple_resources(self, runner, mock_manifest, temp_claude_dir):
        """Test removing multiple resources."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect", "bug-hunter"])

            assert result.exit_code == 0
            assert "Removed 2 resource" in result.output
            assert not (temp_claude_dir / "agents" / "zen-architect.md").exists()
            assert not (temp_claude_dir / "agents" / "bug-hunter.md").exists()
            assert len(mock_manifest.resources) == 1  # Only tool left

    def test_remove_all_of_type(self, runner, mock_manifest, temp_claude_dir):
        """Test removing all resources of a type."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
            patch("click.confirm", return_value=True),  # Confirm removal
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents"])

            assert result.exit_code == 0
            assert "Removed 2 resource" in result.output
            # All agents should be removed
            assert not (temp_claude_dir / "agents" / "zen-architect.md").exists()
            assert not (temp_claude_dir / "agents" / "bug-hunter.md").exists()
            # Only tool should remain in manifest
            assert len(mock_manifest.resources) == 1
            assert mock_manifest.resources[0]["type"] == "tools"

    def test_remove_all_cancelled(self, runner, mock_manifest):
        """Test cancelling removal of all resources of a type."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("click.confirm", return_value=False),  # Cancel
        ):
            result = runner.invoke(remove.cmd, ["agents"])

            assert result.exit_code == 0
            assert "Cancelled" in result.output
            # Manifest should not change
            assert len(mock_manifest.resources) == 3

    def test_remove_all_with_force(self, runner, mock_manifest, temp_claude_dir):
        """Test removing all with --force flag (no confirmation)."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "--force"])

            assert result.exit_code == 0
            assert "Removed 2 resource" in result.output
            # Should not ask for confirmation with --force

    def test_remove_resource_not_found(self, runner, mock_manifest):
        """Test removing non-existent resource."""
        with patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest):
            result = runner.invoke(remove.cmd, ["agents", "nonexistent"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_remove_file_not_found(self, runner, mock_manifest, temp_claude_dir):
        """Test removing resource when file doesn't exist."""
        # Delete the file first
        (temp_claude_dir / "agents" / "zen-architect.md").unlink()

        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"])

            assert result.exit_code == 0
            # Should still remove from manifest even if file doesn't exist
            assert "Removed zen-architect" in result.output
            assert len(mock_manifest.resources) == 2

    def test_remove_invalid_resource_type(self, runner):
        """Test remove with invalid resource type."""
        result = runner.invoke(remove.cmd, ["invalid-type", "resource"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    def test_remove_empty_manifest(self, runner):
        """Test remove with empty manifest."""
        empty_manifest = MockManifest(resources=[])

        with patch("amplifier.cli.commands.remove.load_manifest", return_value=empty_manifest):
            result = runner.invoke(remove.cmd, ["agents", "test"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_remove_directory_with_subdirs(self, runner, mock_manifest, temp_claude_dir):
        """Test removing resource with subdirectories."""
        # Create resource with subdirectories
        resource_dir = temp_claude_dir / "agents" / "complex-agent"
        resource_dir.mkdir()
        (resource_dir / "config").mkdir()
        (resource_dir / "config" / "settings.yaml").write_text("settings")
        (resource_dir / "README.md").write_text("readme")

        # Add to manifest
        mock_manifest.resources.append(
            {"name": "complex-agent", "type": "agents", "source": "github", "sha": "sha_999"}
        )

        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
            patch("shutil.rmtree") as mock_rmtree,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "complex-agent"])

            assert result.exit_code == 0
            # Should use rmtree for directory
            mock_rmtree.assert_called_once()

    def test_remove_permission_error(self, runner, mock_manifest, temp_claude_dir):
        """Test handling permission errors during removal."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
            patch("pathlib.Path.unlink", side_effect=PermissionError("No permission")),
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"])

            assert result.exit_code == 1
            assert "permission" in result.output.lower() or "error" in result.output.lower()

    def test_remove_quiet_mode(self, runner, mock_manifest, temp_claude_dir):
        """Test remove in quiet mode."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"], obj={"quiet": True})

            assert result.exit_code == 0
            # Minimal output
            lines = result.output.strip().split("\n")
            assert len(lines) < 3

    def test_remove_with_output_manager(self, runner, mock_manifest, mock_output, temp_claude_dir):
        """Test remove uses output manager."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
            patch("amplifier.cli.core.output.get_output_manager", return_value=mock_output),
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"], obj={"output": mock_output})

            assert result.exit_code == 0
            assert any("Removing" in msg for _, msg in mock_output.messages)

    def test_remove_dry_run(self, runner, mock_manifest, temp_claude_dir):
        """Test remove with --dry-run flag."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest") as mock_save,
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect", "--dry-run"])

            assert result.exit_code == 0
            assert "DRY RUN" in result.output
            # File should still exist
            assert (temp_claude_dir / "agents" / "zen-architect.md").exists()
            # Manifest should not be saved
            mock_save.assert_not_called()
            # Resources should not be removed from manifest
            assert len(mock_manifest.resources) == 3

    def test_remove_updates_manifest_correctly(self, runner, mock_manifest, temp_claude_dir):
        """Test that manifest is correctly updated after removal."""
        with (
            patch("amplifier.cli.commands.remove.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.remove.save_manifest"),
            patch("amplifier.cli.commands.remove.get_resource_target_dir") as mock_get_dir,
        ):
            mock_get_dir.return_value = temp_claude_dir / "agents"

            result = runner.invoke(remove.cmd, ["agents", "zen-architect"])

            assert result.exit_code == 0
            # Check that the right resource was removed
            remaining_names = [r["name"] for r in mock_manifest.resources]
            assert "zen-architect" not in remaining_names
            assert "bug-hunter" in remaining_names
            assert "amplifier-tool" in remaining_names
