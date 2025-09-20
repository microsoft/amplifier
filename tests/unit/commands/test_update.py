"""Unit tests for update command."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amplifier.cli.commands import update
from tests.fixtures.mocks import MockManifest
from tests.fixtures.mocks import MockOutputManager


class TestUpdateCommand:
    """Test update command functionality."""

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
                "ref": "main",
                "sha": "old_sha_123",
                "installed_at": "2024-01-01T00:00:00",
            },
            {
                "name": "amplifier-tool",
                "type": "tools",
                "source": "github",
                "ref": "main",
                "sha": "old_sha_456",
                "installed_at": "2024-01-01T00:00:00",
            },
            {
                "name": "local-agent",
                "type": "agents",
                "source": "local",
                "path": "/path/to/local/agent",
                "installed_at": "2024-01-01T00:00:00",
            },
        ]
        return manifest

    def test_update_specific_resources(self, runner, mock_manifest):
        """Test updating specific resources."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Setup mocks
            mock_fetch.return_value = AsyncMock(return_value=("new_content", "new_sha_789"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect"])

            assert result.exit_code == 0
            assert "Updated 1 resource" in result.output

    def test_update_all_resources(self, runner, mock_manifest):
        """Test updating all resources."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Setup mocks - return different SHA for updates
            mock_fetch.return_value = AsyncMock(return_value=("new_content", "new_sha_999"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, [])

            assert result.exit_code == 0
            # Should update 2 GitHub resources (not local)
            assert "Updated 2 resource" in result.output

    def test_update_no_updates_available(self, runner, mock_manifest):
        """Test when no updates are available (same SHA)."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Return same SHA - no update needed
            mock_fetch.return_value = AsyncMock(return_value=("content", "old_sha_123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect"])

            assert result.exit_code == 0
            assert "already up-to-date" in result.output.lower()
            # Should not call install
            mock_install.assert_not_called()

    def test_update_force_flag(self, runner, mock_manifest):
        """Test force updating even when SHA matches."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Return same SHA
            mock_fetch.return_value = AsyncMock(return_value=("content", "old_sha_123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect", "--force"])

            assert result.exit_code == 0
            # Should install even with same SHA
            mock_install.assert_called()
            assert "Updated 1 resource" in result.output

    def test_update_check_only_flag(self, runner, mock_manifest):
        """Test check-only mode doesn't actually update."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest") as mock_save,
        ):
            # New version available
            mock_fetch.return_value = AsyncMock(return_value=("content", "new_sha"))()

            result = runner.invoke(update.cmd, ["--check-only"])

            assert result.exit_code == 0
            assert "Updates available" in result.output
            # Should not install or save
            mock_install.assert_not_called()
            mock_save.assert_not_called()

    def test_update_no_updates_check_only(self, runner, mock_manifest):
        """Test check-only mode when no updates available."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
        ):
            # Same SHA - no updates
            mock_fetch.side_effect = [
                AsyncMock(return_value=("content", "old_sha_123"))(),
                AsyncMock(return_value=("content", "old_sha_456"))(),
            ]

            result = runner.invoke(update.cmd, ["--check-only"])

            assert result.exit_code == 0
            assert "All resources are up-to-date" in result.output

    def test_update_resource_not_found(self, runner, mock_manifest):
        """Test updating non-existent resource."""
        with patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest):
            result = runner.invoke(update.cmd, ["nonexistent-resource"])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_update_local_resource_skipped(self, runner, mock_manifest):
        """Test that local resources are skipped during update."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            result = runner.invoke(update.cmd, ["local-agent"])

            assert result.exit_code == 0
            assert "local resource" in result.output.lower()
            # Should not fetch or install
            mock_fetch.assert_not_called()
            mock_install.assert_not_called()

    def test_update_fetch_error(self, runner, mock_manifest):
        """Test handling fetch errors during update."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource"),
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Fetch fails
            mock_fetch.return_value = AsyncMock(return_value=(None, None))()

            result = runner.invoke(update.cmd, ["zen-architect"])

            assert result.exit_code == 1
            assert "Failed to fetch" in result.output

    def test_update_install_error(self, runner, mock_manifest):
        """Test handling install errors during update."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            # Fetch succeeds but install fails
            mock_fetch.return_value = AsyncMock(return_value=("content", "new_sha"))()
            mock_install.return_value = AsyncMock(return_value=False)()

            result = runner.invoke(update.cmd, ["zen-architect"])

            assert result.exit_code == 1
            assert "Failed to install" in result.output

    def test_update_source_flag(self, runner, mock_manifest):
        """Test updating from different source/ref."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            mock_fetch.return_value = AsyncMock(return_value=("content", "feature_sha"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect", "--source", "feature-branch"])

            assert result.exit_code == 0
            # Should fetch from feature branch
            calls = mock_fetch.call_args_list
            assert any("feature-branch" in str(call) for call in calls)

    def test_update_quiet_mode(self, runner, mock_manifest):
        """Test update in quiet mode."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            mock_fetch.return_value = AsyncMock(return_value=("content", "new_sha"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect"], obj={"quiet": True})

            assert result.exit_code == 0
            # Minimal output in quiet mode
            lines = result.output.strip().split("\n")
            assert len(lines) < 3

    def test_update_with_output_manager(self, runner, mock_manifest, mock_output):
        """Test update uses output manager."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
            patch("amplifier.cli.core.output.get_output_manager", return_value=mock_output),
        ):
            mock_fetch.return_value = AsyncMock(return_value=("content", "new_sha"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect"], obj={"output": mock_output})

            assert result.exit_code == 0
            assert any("Updating" in msg for _, msg in mock_output.messages)

    def test_update_empty_manifest(self, runner):
        """Test update with empty manifest."""
        empty_manifest = MockManifest(resources=[])

        with patch("amplifier.cli.commands.update.load_manifest", return_value=empty_manifest):
            result = runner.invoke(update.cmd, [])

            assert result.exit_code == 0
            assert "No resources to update" in result.output

    def test_update_multiple_resources(self, runner, mock_manifest):
        """Test updating multiple specific resources."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.update.install_resource") as mock_install,
            patch("amplifier.cli.commands.update.save_manifest"),
        ):
            mock_fetch.return_value = AsyncMock(return_value=("content", "new_sha"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            result = runner.invoke(update.cmd, ["zen-architect", "amplifier-tool"])

            assert result.exit_code == 0
            assert "Updated 2 resource" in result.output

    def test_update_handles_network_timeout(self, runner, mock_manifest):
        """Test handling network timeout during update."""
        with (
            patch("amplifier.cli.commands.update.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.update.fetch_from_github") as mock_fetch,
        ):
            mock_fetch.side_effect = TimeoutError("Request timed out")

            result = runner.invoke(update.cmd, ["zen-architect"])

            assert result.exit_code == 1
            assert "timeout" in result.output.lower() or "error" in result.output.lower()
