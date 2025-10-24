#!/usr/bin/env python3
"""
Unit tests for the unified CLI launcher (amplify.py).

Tests cover backend selection, configuration precedence, command-line parsing,
and various operational modes.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add the project root to the path so we can import amplifier modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from amplify import (
    parse_args,
    validate_backend,
    launch_claude_code,
    launch_codex,
    list_backends,
    show_backend_info,
    show_version,
    main,
)
from amplifier.core.config import get_backend_config


class TestParseArgs:
    """Test command-line argument parsing."""

    def test_default_args(self):
        """Test parsing with no arguments."""
        with patch("sys.argv", ["amplify.py"]):
            args = parse_args()
        assert args.backend is None
        assert args.profile == "development"
        assert args.config is None
        assert args.list_backends is False
        assert args.info is None
        assert args.version is False
        assert args.args == []

    def test_backend_selection(self):
        """Test backend selection arguments."""
        with patch("sys.argv", ["amplify.py", "--backend", "codex"]):
            args = parse_args()
        assert args.backend == "codex"

        with patch("sys.argv", ["amplify.py", "--backend", "claude"]):
            args = parse_args()
        assert args.backend == "claude"

    def test_profile_selection(self):
        """Test profile selection arguments."""
        with patch("sys.argv", ["amplify.py", "--profile", "ci"]):
            args = parse_args()
        assert args.profile == "ci"

        with patch("sys.argv", ["amplify.py", "--profile", "review"]):
            args = parse_args()
        assert args.profile == "review"

    def test_config_flag(self):
        """Test config file specification."""
        with patch("sys.argv", ["amplify.py", "--config", ".env.production"]):
            args = parse_args()
        assert args.config == ".env.production"

    def test_info_flag(self):
        """Test info flag with backend."""
        with patch("sys.argv", ["amplify.py", "--info", "codex"]):
            args = parse_args()
        assert args.info == "codex"

    def test_list_backends_flag(self):
        """Test list backends flag."""
        with patch("sys.argv", ["amplify.py", "--list-backends"]):
            args = parse_args()
        assert args.list_backends is True

    def test_version_flag(self):
        """Test version flag."""
        with patch("sys.argv", ["amplify.py", "--version"]):
            args = parse_args()
        assert args.version is True

    def test_pass_through_args(self):
        """Test pass-through arguments to backend."""
        with patch("sys.argv", ["amplify.py", "--backend", "codex", "some", "args", "--here"]):
            args = parse_args()
        assert args.backend == "codex"
        assert args.args == ["some", "args", "--here"]


class TestValidateBackend:
    """Test backend validation."""

    @patch("amplify.is_backend_available")
    def test_valid_backend(self, mock_available):
        """Test validation of available backend."""
        mock_available.return_value = True
        assert validate_backend("claude") is True

    @patch("amplify.is_backend_available")
    def test_invalid_backend(self, mock_available, capsys):
        """Test validation of unavailable backend."""
        mock_available.return_value = False
        assert validate_backend("claude") is False
        captured = capsys.readouterr()
        assert "Backend 'claude' is not available" in captured.out


class TestLaunchClaudeCode:
    """Test Claude Code launching."""

    @patch("subprocess.run")
    def test_successful_launch(self, mock_run):
        """Test successful Claude Code launch."""
        mock_run.return_value.returncode = 0
        exit_code = launch_claude_code(["--help"])
        assert exit_code == 0
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["claude", "--help"]

    @patch("subprocess.run")
    @patch.dict(os.environ, {}, clear=True)
    def test_environment_setup(self, mock_run):
        """Test environment variable setup for Claude Code."""
        mock_run.return_value.returncode = 0
        launch_claude_code([])
        assert os.environ.get("AMPLIFIER_BACKEND") == "claude"

    @patch("subprocess.run")
    def test_file_not_found_error(self, mock_run):
        """Test handling of FileNotFoundError."""
        mock_run.side_effect = FileNotFoundError()
        exit_code = launch_claude_code([])
        assert exit_code == 1


class TestLaunchCodex:
    """Test Codex launching."""

    @patch("subprocess.run")
    @patch("amplify.Path.exists")
    def test_wrapper_launch(self, mock_exists, mock_run):
        """Test launching with wrapper script."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0

        exit_code = launch_codex([], "development")

        assert exit_code == 0
        mock_run.assert_called_once_with(
            ["./amplify-codex.sh", "--profile", "development"],
            check=False
        )

    @patch("subprocess.run")
    @patch("amplify.Path.exists")
    def test_direct_launch(self, mock_exists, mock_run):
        """Test direct launch when wrapper not found."""
        mock_exists.return_value = False
        mock_run.return_value.returncode = 0

        exit_code = launch_codex(["--help"], "ci")

        assert exit_code == 0
        mock_run.assert_called_once_with(
            ["codex", "--profile", "ci", "--config", ".codex/config.toml", "--help"],
            check=False
        )

    @patch("subprocess.run")
    @patch.dict(os.environ, {}, clear=True)
    def test_environment_setup(self, mock_run, mock_exists):
        """Test environment variable setup for Codex."""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0

        launch_codex([], "review")

        assert os.environ.get("AMPLIFIER_BACKEND") == "codex"
        assert os.environ.get("CODEX_PROFILE") == "review"


class TestListBackends:
    """Test backend listing functionality."""

    @patch("amplify.BackendFactory.get_available_backends")
    @patch("amplify.get_backend_config")
    def test_list_backends(self, mock_config, mock_get_available, capsys):
        """Test listing available backends."""
        mock_get_available.return_value = ["claude", "codex"]
        mock_config.return_value.amplifier_backend = "claude"

        list_backends()

        captured = capsys.readouterr()
        assert "Available backends:" in captured.out
        assert "claude" in captured.out
        assert "codex" in captured.out
        assert "Current configuration: claude" in captured.out


class TestShowBackendInfo:
    """Test backend information display."""

    @patch("amplify.get_backend_info")
    def test_show_backend_info(self, mock_get_info, capsys):
        """Test displaying backend information."""
        mock_get_info.return_value = {
            "backend": "codex",
            "available": True,
            "cli_path": "/usr/bin/codex",
            "version": "1.0.0",
        }

        show_backend_info("codex")

        captured = capsys.readouterr()
        assert "Backend Information: codex" in captured.out
        assert "Available: Yes" in captured.out
        assert "CLI Path: /usr/bin/codex" in captured.out


class TestShowVersion:
    """Test version information display."""

    @patch("amplify.get_backend_config")
    def test_show_version(self, mock_config, capsys):
        """Test displaying version information."""
        mock_config.return_value.amplifier_backend = "claude"

        show_version()

        captured = capsys.readouterr()
        assert "Amplifier v" in captured.out
        assert "Python" in captured.out
        assert "Configured Backend: claude" in captured.out


class TestMainFunction:
    """Test the main function."""

    @patch("amplify.parse_args")
    @patch("amplify.list_backends")
    def test_list_backends_mode(self, mock_list, mock_parse):
        """Test main function in list backends mode."""
        mock_parse.return_value.list_backends = True

        exit_code = main()

        assert exit_code == 0
        mock_list.assert_called_once()

    @patch("amplify.parse_args")
    @patch("amplify.show_backend_info")
    def test_info_mode(self, mock_show_info, mock_parse):
        """Test main function in info mode."""
        mock_parse.return_value.info = "codex"
        mock_parse.return_value.list_backends = False
        mock_parse.return_value.version = False

        exit_code = main()

        assert exit_code == 0
        mock_show_info.assert_called_once_with("codex")

    @patch("amplify.parse_args")
    @patch("amplify.show_version")
    def test_version_mode(self, mock_show_version, mock_parse):
        """Test main function in version mode."""
        mock_parse.return_value.version = True
        mock_parse.return_value.list_backends = False

        exit_code = main()

        assert exit_code == 0
        mock_show_version.assert_called_once()

    @patch("amplify.parse_args")
    @patch("amplify.get_backend_config")
    @patch("amplify.validate_backend")
    @patch("amplify.launch_claude_code")
    def test_launch_claude(self, mock_launch, mock_validate, mock_config, mock_parse):
        """Test launching Claude Code through main."""
        # Setup mocks
        mock_parse.return_value.backend = "claude"
        mock_parse.return_value.config = None
        mock_parse.return_value.list_backends = False
        mock_parse.return_value.version = False
        mock_parse.return_value.args = ["--help"]
        mock_config.return_value.amplifier_backend = "claude"
        mock_validate.return_value = True
        mock_launch.return_value = 0

        exit_code = main()

        assert exit_code == 0
        mock_launch.assert_called_once_with(["--help"])

    @patch("amplify.parse_args")
    @patch("amplify.get_backend_config")
    @patch("amplify.validate_backend")
    @patch("amplify.launch_codex")
    def test_launch_codex(self, mock_launch, mock_validate, mock_config, mock_parse):
        """Test launching Codex through main."""
        # Setup mocks
        mock_parse.return_value.backend = "codex"
        mock_parse.return_value.profile = "ci"
        mock_parse.return_value.config = None
        mock_parse.return_value.list_backends = False
        mock_parse.return_value.version = False
        mock_parse.return_value.args = []
        mock_config.return_value.amplifier_backend = "codex"
        mock_validate.return_value = True
        mock_launch.return_value = 0

        exit_code = main()

        assert exit_code == 0
        mock_launch.assert_called_once_with([], "ci")

    @patch("amplify.parse_args")
    @patch("amplify.get_backend_config")
    @patch("amplify.detect_backend")
    @patch("amplify.validate_backend")
    @patch("amplify.launch_claude_code")
    def test_auto_detect_backend(self, mock_launch, mock_validate, mock_detect,
                                mock_config, mock_parse):
        """Test automatic backend detection."""
        # Setup mocks
        mock_parse.return_value.backend = None
        mock_parse.return_value.config = None
        mock_parse.return_value.list_backends = False
        mock_parse.return_value.version = False
        mock_parse.return_value.args = []
        mock_config.return_value.amplifier_backend = None
        mock_config.return_value.amplifier_backend_auto_detect = True
        mock_detect.return_value = "claude"
        mock_validate.return_value = True
        mock_launch.return_value = 0

        exit_code = main()

        assert exit_code == 0
        mock_detect.assert_called_once()
        mock_launch.assert_called_once_with([])

    @patch("amplify.parse_args")
    @patch("amplify.get_backend_config")
    def test_config_precedence(self, mock_config, mock_parse):
        """Test configuration file precedence."""
        mock_parse.return_value.config = ".env.test"
        mock_parse.return_value.list_backends = True

        main()

        # Check that ENV_FILE was set
        assert os.environ.get("ENV_FILE") == ".env.test"


class TestConfigPrecedence:
    """Test configuration precedence rules."""

    @patch("amplify.get_backend_config")
    def test_config_flag_sets_env_file(self, mock_config, monkeypatch):
        """Test that --config flag sets ENV_FILE environment variable."""
        # Clear any existing ENV_FILE
        monkeypatch.delenv("ENV_FILE", raising=False)

        with patch("amplify.parse_args") as mock_parse:
            mock_parse.return_value.config = ".env.production"
            mock_parse.return_value.list_backends = True

            main()

            assert os.environ.get("ENV_FILE") == ".env.production"

    @patch("amplify.get_backend_config")
    def test_backend_config_uses_env_file(self, mock_config, monkeypatch):
        """Test that BackendConfig uses ENV_FILE when set."""
        # Set ENV_FILE
        monkeypatch.setenv("ENV_FILE", ".env.test")

        # Call get_backend_config which should use the ENV_FILE
        get_backend_config()

        # Verify it was called with the env file override
        mock_config.assert_called_with(".env.test")


if __name__ == "__main__":
    pytest.main([__file__])