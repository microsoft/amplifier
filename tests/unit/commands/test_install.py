"""Unit tests for install command."""

from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amplifier.cli.commands import install
from tests.fixtures.mocks import MockOutputManager


class TestInstallCommand:
    """Test install command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_output(self):
        """Create mock output manager."""
        return MockOutputManager()

    @pytest.fixture
    def mock_github_resources(self):
        """Mock GitHub resources."""
        return {
            "agents": ["zen-architect", "bug-hunter", "test-coverage"],
            "tools": ["amplifier-tool", "test-tool"],
            "commands": ["custom-cmd"],
            "mcp-servers": ["server1", "server2"],
        }

    async def async_return(self, value):
        """Helper to return async value."""
        return value

    @pytest.mark.asyncio
    async def test_install_single_type_specific_resources(self):
        """Test installing specific resources of a single type."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["zen-architect", "bug-hunter", "test-coverage"])()
            mock_installed.return_value = False
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            # Test install specific resources
            installed, skipped, failed = await install._install_single_type(
                "agents", ("zen-architect", "bug-hunter"), force=False, dry_run=False, ref="main"
            )

            assert installed == 2
            assert skipped == 0
            assert failed == 0

    @pytest.mark.asyncio
    async def test_install_single_type_all_resources(self):
        """Test installing all resources of a type."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["tool1", "tool2"])()
            mock_installed.return_value = False
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            # Test install all resources (empty names tuple)
            installed, skipped, failed = await install._install_single_type(
                "tools", (), force=False, dry_run=False, ref="main"
            )

            assert installed == 2
            assert skipped == 0
            assert failed == 0

    @pytest.mark.asyncio
    async def test_install_single_type_skip_installed(self):
        """Test skipping already installed resources."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1"])()
            mock_installed.return_value = True  # Already installed
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            # Test without force
            installed, skipped, failed = await install._install_single_type(
                "agents", ("agent1",), force=False, dry_run=False, ref="main"
            )

            assert installed == 0
            assert skipped == 1
            assert failed == 0
            # Should not fetch or install
            mock_fetch.assert_not_called()
            mock_install.assert_not_called()

    @pytest.mark.asyncio
    async def test_install_single_type_force_reinstall(self):
        """Test force reinstalling already installed resources."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1"])()
            mock_installed.return_value = True  # Already installed
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            # Test with force
            installed, skipped, failed = await install._install_single_type(
                "agents", ("agent1",), force=True, dry_run=False, ref="main"
            )

            assert installed == 1
            assert skipped == 0
            assert failed == 0
            # Should fetch and install despite being installed
            mock_fetch.assert_called_once()
            mock_install.assert_called_once()

    @pytest.mark.asyncio
    async def test_install_single_type_dry_run(self):
        """Test dry run mode doesn't actually install."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1"])()
            mock_installed.return_value = False
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=True)()

            # Test dry run
            installed, skipped, failed = await install._install_single_type(
                "agents", ("agent1",), force=False, dry_run=True, ref="main"
            )

            assert installed == 0
            assert skipped == 0
            assert failed == 0
            # Should fetch but not install
            mock_fetch.assert_called_once()
            mock_install.assert_not_called()

    @pytest.mark.asyncio
    async def test_install_single_type_invalid_resource(self):
        """Test installing non-existent resource."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github"),
            patch("amplifier.cli.commands.install.install_resource"),
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1", "agent2"])()
            mock_installed.return_value = False

            # Test invalid resource name
            installed, skipped, failed = await install._install_single_type(
                "agents", ("invalid-agent",), force=False, dry_run=False, ref="main"
            )

            assert installed == 0
            assert skipped == 1  # Skipped as not available
            assert failed == 0

    @pytest.mark.asyncio
    async def test_install_single_type_fetch_failure(self):
        """Test handling fetch failure."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource"),
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1"])()
            mock_installed.return_value = False
            mock_fetch.return_value = AsyncMock(return_value=(None, None))()  # Fetch failed

            # Test fetch failure
            installed, skipped, failed = await install._install_single_type(
                "agents", ("agent1",), force=False, dry_run=False, ref="main"
            )

            assert installed == 0
            assert skipped == 0
            assert failed == 1

    @pytest.mark.asyncio
    async def test_install_single_type_install_failure(self):
        """Test handling install failure."""
        with (
            patch("amplifier.cli.commands.install.list_github_resources") as mock_list,
            patch("amplifier.cli.commands.install.is_resource_installed") as mock_installed,
            patch("amplifier.cli.commands.install.fetch_from_github") as mock_fetch,
            patch("amplifier.cli.commands.install.install_resource") as mock_install,
        ):
            # Setup mocks
            mock_list.return_value = AsyncMock(return_value=["agent1"])()
            mock_installed.return_value = False
            mock_fetch.return_value = AsyncMock(return_value=("content", "sha123"))()
            mock_install.return_value = AsyncMock(return_value=False)()  # Install failed

            # Test install failure
            installed, skipped, failed = await install._install_single_type(
                "agents", ("agent1",), force=False, dry_run=False, ref="main"
            )

            assert installed == 0
            assert skipped == 0
            assert failed == 1

    def test_install_command_specific_resources(self, runner):
        """Test install command with specific resources."""

        async def mock_install_single_type(*args, **kwargs):
            return 2, 0, 0  # 2 installed

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "zen-architect", "bug-hunter"])

            assert result.exit_code == 0
            assert "Successfully installed 2" in result.output

    def test_install_command_all_of_type(self, runner):
        """Test install command for all resources of a type."""

        async def mock_install_single_type(*args, **kwargs):
            return 3, 0, 0  # 3 installed

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents"])

            assert result.exit_code == 0
            assert "Successfully installed 3" in result.output

    def test_install_command_all_types(self, runner):
        """Test install command for all resource types."""
        call_count = 0

        async def mock_install_single_type(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return different counts for each type
            if call_count == 1:
                return 2, 0, 0  # agents
            if call_count == 2:
                return 1, 0, 0  # tools
            if call_count == 3:
                return 1, 0, 0  # commands
            return 1, 0, 0  # mcp-servers

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["all"])

            assert result.exit_code == 0
            assert "Successfully installed 5" in result.output  # 2+1+1+1

    def test_install_command_with_source_flag(self, runner):
        """Test install command with --source flag."""

        async def mock_install_single_type(resource_type, names, force, dry_run, ref):
            assert ref == "feature-branch"
            return 1, 0, 0

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "test", "--source", "feature-branch"])

            assert result.exit_code == 0

    def test_install_command_with_force_flag(self, runner):
        """Test install command with --force flag."""

        async def mock_install_single_type(resource_type, names, force, dry_run, ref):
            assert force is True
            return 1, 0, 0

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "test", "--force"])

            assert result.exit_code == 0

    def test_install_command_with_dry_run_flag(self, runner):
        """Test install command with --dry-run flag."""

        async def mock_install_single_type(resource_type, names, force, dry_run, ref):
            assert dry_run is True
            return 0, 0, 0  # Dry run doesn't install

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "test", "--dry-run"])

            assert result.exit_code == 0
            assert "DRY RUN" in result.output

    def test_install_command_with_failures(self, runner):
        """Test install command handling failures."""

        async def mock_install_single_type(*args, **kwargs):
            return 1, 2, 3  # 1 installed, 2 skipped, 3 failed

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "test"])

            assert result.exit_code == 1  # Exit code 1 for failures
            assert "3 failed" in result.output
            assert "2 skipped" in result.output

    def test_install_command_invalid_resource_type(self, runner):
        """Test install command with invalid resource type."""
        result = runner.invoke(install.cmd, ["invalid-type"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    def test_install_command_quiet_mode(self, runner):
        """Test install command in quiet mode."""

        async def mock_install_single_type(*args, **kwargs):
            return 2, 0, 0

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
        ):
            result = runner.invoke(install.cmd, ["agents", "test"], obj={"quiet": True})

            assert result.exit_code == 0
            # Output should be minimal in quiet mode
            lines = result.output.strip().split("\n")
            assert len(lines) < 3

    def test_install_command_with_output_manager(self, runner, mock_output):
        """Test install command uses output manager."""

        async def mock_install_single_type(*args, **kwargs):
            return 1, 0, 0

        with (
            patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type),
            patch("amplifier.cli.commands.install.update_manifest_from_installed"),
            patch("amplifier.cli.core.output.get_output_manager", return_value=mock_output),
        ):
            result = runner.invoke(install.cmd, ["agents", "test"], obj={"output": mock_output})

            assert result.exit_code == 0
            # Should have used output manager
            assert any("Installing" in msg for _, msg in mock_output.messages)

    def test_install_command_handles_exception(self, runner):
        """Test install command handles exceptions gracefully."""

        async def mock_install_single_type(*args, **kwargs):
            raise Exception("Network error")

        with patch("amplifier.cli.commands.install._install_single_type", new=mock_install_single_type):
            result = runner.invoke(install.cmd, ["agents", "test"])

            # Should handle error without crashing
            assert result.exit_code != 0
            assert "error" in result.output.lower()
