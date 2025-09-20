"""Unit tests for list command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from amplifier.cli.commands import list as list_cmd
from tests.fixtures.mocks import MockManifest
from tests.fixtures.mocks import MockOutputManager


class TestListCommand:
    """Test list command functionality."""

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
                "sha": "sha_123",
                "installed_at": "2024-01-01T00:00:00",
            },
            {
                "name": "bug-hunter",
                "type": "agents",
                "source": "github",
                "ref": "main",
                "sha": "sha_456",
                "installed_at": "2024-01-01T12:00:00",
            },
            {
                "name": "amplifier-tool",
                "type": "tools",
                "source": "github",
                "ref": "feature",
                "sha": "sha_789",
                "installed_at": "2024-01-02T00:00:00",
            },
            {
                "name": "local-agent",
                "type": "agents",
                "source": "local",
                "path": "/path/to/agent",
                "installed_at": "2024-01-03T00:00:00",
            },
        ]
        return manifest

    @pytest.fixture
    def github_resources(self):
        """Mock available GitHub resources."""
        return {
            "agents": ["zen-architect", "bug-hunter", "test-coverage"],
            "tools": ["amplifier-tool", "another-tool"],
            "commands": ["custom-cmd"],
            "mcp-servers": [],
        }

    def test_list_installed_resources(self, runner, mock_manifest):
        """Test listing all installed resources."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, [])

            assert result.exit_code == 0
            assert "Installed Resources" in result.output
            assert "zen-architect" in result.output
            assert "bug-hunter" in result.output
            assert "amplifier-tool" in result.output
            assert "local-agent" in result.output
            # Should show counts
            assert "3 agents" in result.output
            assert "1 tool" in result.output

    def test_list_installed_by_type(self, runner, mock_manifest):
        """Test listing installed resources of specific type."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, ["agents"])

            assert result.exit_code == 0
            assert "zen-architect" in result.output
            assert "bug-hunter" in result.output
            assert "local-agent" in result.output
            # Should not show tools
            assert "amplifier-tool" not in result.output

    def test_list_available_resources(self, runner, github_resources):
        """Test listing available resources from GitHub."""

        async def mock_list_resources(resource_type, ref):
            return github_resources.get(resource_type, [])

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=MockManifest()),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_resources),
        ):
            result = runner.invoke(list_cmd.cmd, ["--available"])

            assert result.exit_code == 0
            assert "Available Resources" in result.output
            assert "test-coverage" in result.output  # Available but not installed
            assert "another-tool" in result.output

    def test_list_available_by_type(self, runner, github_resources):
        """Test listing available resources of specific type."""

        async def mock_list_resources(resource_type, ref):
            return github_resources.get(resource_type, [])

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=MockManifest()),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_resources),
        ):
            result = runner.invoke(list_cmd.cmd, ["agents", "--available"])

            assert result.exit_code == 0
            assert "zen-architect" in result.output
            assert "bug-hunter" in result.output
            assert "test-coverage" in result.output
            # Should not show tools
            assert "amplifier-tool" not in result.output

    def test_list_with_details_flag(self, runner, mock_manifest):
        """Test listing with --details flag shows more information."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, ["--details"])

            assert result.exit_code == 0
            # Should show SHA and dates
            assert "sha_123" in result.output
            assert "2024-01-01" in result.output
            # Should show source info
            assert "github:main" in result.output
            assert "local:" in result.output

    def test_list_empty_manifest(self, runner):
        """Test listing with empty manifest."""
        empty_manifest = MockManifest(resources=[])

        with patch("amplifier.cli.commands.list.load_manifest", return_value=empty_manifest):
            result = runner.invoke(list_cmd.cmd, [])

            assert result.exit_code == 0
            assert "No resources installed" in result.output

    def test_list_both_installed_and_available(self, runner, mock_manifest, github_resources):
        """Test listing both installed and available resources."""

        async def mock_list_resources(resource_type, ref):
            return github_resources.get(resource_type, [])

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_resources),
        ):
            result = runner.invoke(list_cmd.cmd, ["--all"])

            assert result.exit_code == 0
            assert "Installed Resources" in result.output
            assert "Available Resources" in result.output
            # Should show installed
            assert "zen-architect" in result.output
            # Should show available but not installed
            assert "test-coverage" in result.output

    def test_list_with_source_flag(self, runner, mock_manifest, github_resources):
        """Test listing available resources from different branch."""
        call_count = 0

        async def mock_list_resources(resource_type, ref):
            nonlocal call_count
            call_count += 1
            assert ref == "feature-branch"  # Should use specified ref
            return github_resources.get(resource_type, [])

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_resources),
        ):
            result = runner.invoke(list_cmd.cmd, ["--available", "--source", "feature-branch"])

            assert result.exit_code == 0
            assert call_count > 0  # Should have called with feature-branch

    def test_list_json_output(self, runner, mock_manifest):
        """Test JSON output format."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, ["--json"])

            assert result.exit_code == 0
            # Should be valid JSON
            import json

            data = json.loads(result.output)
            assert "installed" in data
            assert len(data["installed"]) == 4
            assert data["installed"][0]["name"] == "zen-architect"

    def test_list_json_with_available(self, runner, mock_manifest, github_resources):
        """Test JSON output with available resources."""

        async def mock_list_resources(resource_type, ref):
            return github_resources.get(resource_type, [])

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_resources),
        ):
            result = runner.invoke(list_cmd.cmd, ["--json", "--all"])

            assert result.exit_code == 0
            import json

            data = json.loads(result.output)
            assert "installed" in data
            assert "available" in data
            assert len(data["available"]["agents"]) == 3

    def test_list_quiet_mode(self, runner, mock_manifest):
        """Test list in quiet mode shows minimal output."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, [], obj={"quiet": True})

            assert result.exit_code == 0
            # Should just list names, one per line
            lines = result.output.strip().split("\n")
            assert "zen-architect" in lines
            assert "bug-hunter" in lines
            assert "amplifier-tool" in lines
            assert "local-agent" in lines
            # No headers or decorations
            assert "Installed Resources" not in result.output

    def test_list_updates_available_flag(self, runner, mock_manifest, github_resources):
        """Test showing which resources have updates available."""

        async def mock_fetch(resource_type, name, ref):
            # Return new SHA for some resources
            if name == "zen-architect":
                return "content", "new_sha_999"  # Update available
            return "content", mock_manifest.find_resource(name, resource_type)["sha"]

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.commands.list.fetch_from_github", new=mock_fetch),
        ):
            result = runner.invoke(list_cmd.cmd, ["--check-updates"])

            assert result.exit_code == 0
            assert "Update available" in result.output
            assert "zen-architect" in result.output

    def test_list_invalid_resource_type(self, runner):
        """Test list with invalid resource type."""
        result = runner.invoke(list_cmd.cmd, ["invalid-type"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value" in result.output

    def test_list_filter_by_source(self, runner, mock_manifest):
        """Test filtering resources by source."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            # List only GitHub resources
            result = runner.invoke(list_cmd.cmd, ["--filter-source", "github"])

            assert result.exit_code == 0
            assert "zen-architect" in result.output
            assert "bug-hunter" in result.output
            assert "amplifier-tool" in result.output
            assert "local-agent" not in result.output  # Local resource excluded

    def test_list_filter_by_ref(self, runner, mock_manifest):
        """Test filtering resources by ref/branch."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            # List only resources from feature branch
            result = runner.invoke(list_cmd.cmd, ["--filter-ref", "feature"])

            assert result.exit_code == 0
            assert "amplifier-tool" in result.output  # From feature branch
            assert "zen-architect" not in result.output  # From main branch

    def test_list_with_output_manager(self, runner, mock_manifest, mock_output):
        """Test list uses output manager."""
        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest),
            patch("amplifier.cli.core.output.get_output_manager", return_value=mock_output),
        ):
            result = runner.invoke(list_cmd.cmd, [], obj={"output": mock_output})

            assert result.exit_code == 0
            assert any("Installed Resources" in msg for _, msg in mock_output.messages)

    def test_list_handles_github_error(self, runner):
        """Test handling GitHub API errors when listing available."""

        async def mock_list_error(*args):
            raise Exception("GitHub API error")

        with (
            patch("amplifier.cli.commands.list.load_manifest", return_value=MockManifest()),
            patch("amplifier.cli.commands.list.list_github_resources", new=mock_list_error),
        ):
            result = runner.invoke(list_cmd.cmd, ["--available"])

            assert result.exit_code != 0
            assert "error" in result.output.lower()

    def test_list_groups_by_type(self, runner, mock_manifest):
        """Test that resources are grouped by type in output."""
        with patch("amplifier.cli.commands.list.load_manifest", return_value=mock_manifest):
            result = runner.invoke(list_cmd.cmd, [])

            assert result.exit_code == 0
            # Check that agents are grouped together
            output_lines = result.output.split("\n")
            agents_section_found = False
            tools_section_found = False

            for i, line in enumerate(output_lines):
                if "agents" in line.lower():
                    agents_section_found = True
                    # Check next lines have agent names
                    assert any(
                        "zen-architect" in output_lines[j] or "bug-hunter" in output_lines[j]
                        for j in range(i + 1, min(i + 5, len(output_lines)))
                    )
                if "tools" in line.lower():
                    tools_section_found = True
                    # Check next lines have tool names
                    assert any("amplifier-tool" in output_lines[j] for j in range(i + 1, min(i + 5, len(output_lines))))

            assert agents_section_found
            assert tools_section_found
