"""Unit tests for config command."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from amplifier.cli.commands import config
from tests.fixtures.mocks import MockOutputManager


class TestConfigCommand:
    """Test config command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def mock_output(self):
        """Create mock output manager."""
        return MockOutputManager()

    @pytest.fixture
    def temp_config(self, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / ".amplifier"
        config_dir.mkdir()
        return config_dir

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "default_source": "github",
            "auto_update_check": True,
            "github_repo": "microsoft/amplifier",
        }

    def test_load_config_with_defaults(self):
        """Test loading config returns defaults when file doesn't exist."""
        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/config.yaml")

            result = config.load_config()

            assert result["default_source"] == "github"
            assert result["auto_update_check"] is True
            assert result["github_repo"] == "microsoft/amplifier"

    def test_load_config_from_file(self, temp_config, sample_config):
        """Test loading config from existing file."""
        config_file = temp_config / "config.yaml"
        custom_config = {"default_source": "local", "custom_key": "custom_value"}
        config_file.write_text(yaml.dump(custom_config))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = config.load_config()

            # Should have custom values
            assert result["default_source"] == "local"
            assert result["custom_key"] == "custom_value"
            # Should have defaults for missing keys
            assert result["auto_update_check"] is True
            assert result["github_repo"] == "microsoft/amplifier"

    def test_save_config(self, temp_config):
        """Test saving configuration to file."""
        config_file = temp_config / "config.yaml"
        test_config = {"test_key": "test_value", "number": 42}

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            config.save_config(test_config)

            # Verify file was created
            assert config_file.exists()

            # Verify content
            saved_data = yaml.safe_load(config_file.read_text())
            assert saved_data["test_key"] == "test_value"
            assert saved_data["number"] == 42

    def test_save_config_creates_directory(self, tmp_path):
        """Test save_config creates directory if it doesn't exist."""
        config_file = tmp_path / "new_dir" / ".amplifier" / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            config.save_config({"key": "value"})

            assert config_file.parent.exists()
            assert config_file.exists()

    def test_get_config_value(self, runner, temp_config):
        """Test getting a configuration value."""
        config_file = temp_config / "config.yaml"
        config_file.write_text(yaml.dump({"test_key": "test_value"}))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["get", "test_key"])

            assert result.exit_code == 0
            assert "test_value" in result.output

    def test_get_config_unknown_key(self, runner, temp_config):
        """Test getting an unknown configuration key."""
        config_file = temp_config / "config.yaml"
        config_file.write_text(yaml.dump({"known_key": "value"}))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["get", "unknown_key"])

            assert result.exit_code == 1
            assert "Unknown configuration key" in result.output
            assert "Available keys" in result.output

    def test_get_config_quiet_mode(self, runner, temp_config):
        """Test getting config value in quiet mode."""
        config_file = temp_config / "config.yaml"
        config_file.write_text(yaml.dump({"test_key": "test_value"}))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            # Pass quiet flag in context
            result = runner.invoke(config.cmd, ["get", "test_key"], obj={"quiet": True})

            assert result.exit_code == 0
            assert result.output.strip() == "test_value"

    def test_set_config_value(self, runner, temp_config):
        """Test setting a configuration value."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "default_source", "local"])

            assert result.exit_code == 0
            assert "default_source" in result.output

            # Verify value was saved
            saved_config = yaml.safe_load(config_file.read_text())
            assert saved_config["default_source"] == "local"

    def test_set_config_boolean_values(self, runner, temp_config):
        """Test setting boolean configuration values."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            # Test various boolean representations
            for value, expected in [
                ("true", True),
                ("false", False),
                ("yes", True),
                ("no", False),
                ("1", True),
                ("0", False),
                ("on", True),
                ("off", False),
            ]:
                result = runner.invoke(config.cmd, ["set", "auto_update_check", value])
                assert result.exit_code == 0

                saved_config = yaml.safe_load(config_file.read_text())
                assert saved_config["auto_update_check"] == expected

    def test_set_config_invalid_boolean(self, runner, temp_config):
        """Test setting invalid boolean value."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "auto_update_check", "invalid"])

            assert result.exit_code == 1
            assert "Invalid boolean value" in result.output

    def test_set_config_invalid_source(self, runner, temp_config):
        """Test setting invalid source value."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "default_source", "invalid"])

            assert result.exit_code == 1
            assert "Invalid source" in result.output
            assert "github, local" in result.output

    def test_set_config_github_repo_validation(self, runner, temp_config):
        """Test github_repo format validation."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            # Invalid format (no slash)
            result = runner.invoke(config.cmd, ["set", "github_repo", "invalid"])
            assert result.exit_code == 1
            assert "Invalid repository format" in result.output

            # Valid format
            result = runner.invoke(config.cmd, ["set", "github_repo", "owner/repo"])
            assert result.exit_code == 0

    def test_set_config_custom_key_warning(self, runner, temp_config):
        """Test setting a custom configuration key shows warning."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "custom_key", "custom_value"])

            assert result.exit_code == 0
            assert "custom configuration key" in result.output

            # Verify it was still saved
            saved_config = yaml.safe_load(config_file.read_text())
            assert saved_config["custom_key"] == "custom_value"

    def test_set_config_updates_existing_value(self, runner, temp_config):
        """Test updating an existing configuration value."""
        config_file = temp_config / "config.yaml"
        config_file.write_text(yaml.dump({"test_key": "old_value"}))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "test_key", "new_value"])

            assert result.exit_code == 0
            assert "old_value → new_value" in result.output

    def test_set_config_quiet_mode(self, runner, temp_config):
        """Test setting config value in quiet mode."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["set", "default_source", "local"], obj={"quiet": True})

            assert result.exit_code == 0
            assert result.output.strip() == ""

            # Verify value was still saved
            saved_config = yaml.safe_load(config_file.read_text())
            assert saved_config["default_source"] == "local"

    def test_list_config(self, runner, temp_config):
        """Test listing all configuration settings."""
        config_file = temp_config / "config.yaml"
        custom_config = {
            "default_source": "github",  # default value
            "auto_update_check": False,  # modified value
            "custom_key": "custom_value",  # custom key
        }
        config_file.write_text(yaml.dump(custom_config))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["list"])

            assert result.exit_code == 0
            assert "Configuration Settings" in result.output
            assert "default_source" in result.output
            assert "auto_update_check" in result.output
            assert "(modified)" in result.output
            assert str(config_file) in result.output

    def test_list_config_quiet_mode(self, runner, temp_config):
        """Test listing config in quiet mode."""
        config_file = temp_config / "config.yaml"
        config_data = {"key1": "value1", "key2": 42}
        config_file.write_text(yaml.dump(config_data))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = runner.invoke(config.cmd, ["list"], obj={"quiet": True})

            assert result.exit_code == 0
            # Should be simple key=value format
            lines = result.output.strip().split("\n")
            assert any("key1=value1" in line for line in lines)
            assert any("key2=42" in line for line in lines)

    def test_config_with_output_manager(self, runner, temp_config, mock_output):
        """Test config commands use output manager."""
        config_file = temp_config / "config.yaml"

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            with patch("amplifier.cli.core.output.get_output_manager") as mock_get_output:
                mock_get_output.return_value = mock_output

                # Test get command
                result = runner.invoke(config.cmd, ["get", "default_source"], obj={"output": mock_output})

                assert result.exit_code == 0
                assert any("default_source" in msg for _, msg in mock_output.messages)

    def test_config_handles_corrupted_yaml(self, runner, temp_config):
        """Test config handles corrupted YAML gracefully."""
        config_file = temp_config / "config.yaml"
        config_file.write_text("invalid: yaml: content:")  # Invalid YAML

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            # Should still load with defaults
            result = config.load_config()
            assert result["default_source"] == "github"

    def test_config_handles_permission_error(self, runner):
        """Test config handles permission errors."""
        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = Path("/readonly/config.yaml")

            with (
                patch("builtins.open", side_effect=PermissionError("No permission")),
                patch("amplifier.cli.core.output.get_output_manager") as mock_output,
            ):
                mock_manager = MagicMock()
                mock_output.return_value = mock_manager

                result = runner.invoke(config.cmd, ["set", "test_key", "value"])

                # Should handle error without crashing
                assert result.exit_code != 0

    def test_config_empty_file_handling(self, temp_config):
        """Test handling of empty config file."""
        config_file = temp_config / "config.yaml"
        config_file.write_text("")  # Empty file

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            result = config.load_config()

            # Should return defaults
            assert result["default_source"] == "github"
            assert result["auto_update_check"] is True
            assert result["github_repo"] == "microsoft/amplifier"

    def test_config_preserves_extra_keys(self, runner, temp_config):
        """Test that unrecognized keys are preserved when saving."""
        config_file = temp_config / "config.yaml"
        initial_config = {
            "default_source": "github",
            "custom_key": "should_be_preserved",
            "another_custom": {"nested": "value"},
        }
        config_file.write_text(yaml.dump(initial_config))

        with patch("amplifier.cli.commands.config.get_config_path") as mock_path:
            mock_path.return_value = config_file

            # Modify a standard key
            result = runner.invoke(config.cmd, ["set", "default_source", "local"])
            assert result.exit_code == 0

            # Check that custom keys are preserved
            saved_config = yaml.safe_load(config_file.read_text())
            assert saved_config["default_source"] == "local"
            assert saved_config["custom_key"] == "should_be_preserved"
            assert saved_config["another_custom"]["nested"] == "value"
