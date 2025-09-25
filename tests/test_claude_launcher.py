#!/usr/bin/env python3
"""
Test suite for the amplifier claude command launcher.

Tests the new unified CLI command integration with Claude.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

# Add amplifier to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from amplifier.claude_launcher import detect_project_type
from amplifier.claude_launcher import find_amplifier_root
from amplifier.claude_launcher import launch_claude


class TestAmplifierRootDetection:
    """Test Amplifier root directory detection."""

    def test_find_amplifier_root_from_module(self):
        """Test finding Amplifier root from the module location."""
        root = find_amplifier_root()
        assert root.exists()
        assert (root / "pyproject.toml").exists()
        assert (root / "AGENTS.md").exists()
        assert (root / "amplifier").exists()

    def test_find_amplifier_root_returns_consistent_path(self):
        """Test that find_amplifier_root returns the same path consistently."""
        root1 = find_amplifier_root()
        root2 = find_amplifier_root()
        assert root1 == root2


class TestProjectTypeDetection:
    """Test project type detection (Amplifier vs external)."""

    def test_detect_amplifier_project(self):
        """Test detection when inside Amplifier project."""
        amplifier_root = find_amplifier_root()
        # Test from amplifier root
        is_amp, proj = detect_project_type(amplifier_root, amplifier_root)
        assert is_amp is True
        assert proj == amplifier_root

        # Test from subdirectory
        subdir = amplifier_root / "amplifier"
        is_amp, proj = detect_project_type(subdir, amplifier_root)
        assert is_amp is True
        assert proj == amplifier_root

    def test_detect_external_project(self):
        """Test detection when outside Amplifier project."""
        amplifier_root = find_amplifier_root()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            is_amp, proj = detect_project_type(tmppath, amplifier_root)
            assert is_amp is False
            assert proj == tmppath


class TestClaudeLauncher:
    """Test the launch_claude function."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_launch_claude_missing_cli(self, mock_which, mock_run):
        """Test error when Claude CLI is not found."""
        mock_which.return_value = None

        with pytest.raises(RuntimeError) as exc_info:
            launch_claude()

        assert "Claude CLI not found" in str(exc_info.value)
        assert "npm install -g @anthropic-ai/claude-code" in str(exc_info.value)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_launch_claude_in_amplifier_directory(self, mock_which, mock_run):
        """Test launching Claude within Amplifier project."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = MagicMock(returncode=0)

        amplifier_root = find_amplifier_root()
        launch_claude(amplifier_root)

        # Verify subprocess was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # Check that amplifier-anywhere.sh is used
        assert "amplifier-anywhere.sh" in str(call_args[0][0][0])

        # Check environment doesn't have EXTERNAL_PROJECT_MODE
        env = call_args[1].get("env", {})
        assert "EXTERNAL_PROJECT_MODE" not in env

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_launch_claude_in_external_directory(self, mock_which, mock_run):
        """Test launching Claude in external project."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            launch_claude(tmppath)

            # Verify subprocess was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args

            # Check environment has EXTERNAL_PROJECT_MODE
            env = call_args[1].get("env", {})
            assert env.get("EXTERNAL_PROJECT_MODE") == "1"
            assert env.get("AMPLIFIER_EXTERNAL_MODE") == "1"
            # Use resolve() to handle symlink differences
            assert Path(env.get("AMPLIFIER_WORKING_DIR")).resolve() == tmppath.resolve()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_launch_claude_with_extra_args(self, mock_which, mock_run):
        """Test passing extra arguments to Claude."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = MagicMock(returncode=0)

        extra_args = ["--model", "sonnet", "--help"]
        launch_claude(None, extra_args)

        # Verify extra args were passed
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        for arg in extra_args:
            assert arg in call_args

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_launch_claude_fallback_without_script(self, mock_which, mock_run):
        """Test fallback when amplifier-anywhere.sh doesn't exist."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = MagicMock(returncode=0)

        # Temporarily rename the script to simulate it missing
        amplifier_root = find_amplifier_root()

        # Patch the script path directly
        with patch.object(Path, "exists") as mock_exists:

            def exists_side_effect():
                # Check the actual path being tested
                import inspect

                frame = inspect.currentframe()
                if frame is None:
                    return True
                self_obj = frame.f_locals.get("self")
                return not (self_obj and str(self_obj).endswith("amplifier-anywhere.sh"))

            mock_exists.side_effect = lambda: exists_side_effect()

            # Mock script doesn't exist but other files do
            with patch("amplifier.claude_launcher.find_amplifier_root") as mock_find_root:
                mock_find_root.return_value = amplifier_root

                # Patch script existence check specifically
                original_exists = Path.exists

                def patched_exists(self):
                    if str(self).endswith("amplifier-anywhere.sh"):
                        return False
                    return original_exists(self)

                with patch.object(Path, "exists", patched_exists):
                    # Should fall back to direct claude launch
                    launch_claude()

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            # Should use claude directly, not the script
            assert call_args[0] == "/usr/local/bin/claude"


class TestCLIIntegration:
    """Test integration with the main CLI."""

    def test_claude_command_exists(self):
        """Test that amplifier claude command exists."""
        result = subprocess.run(["amplifier", "claude", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Launch Claude with Amplifier context" in result.stdout

    def test_claude_command_help_examples(self):
        """Test that help text includes usage examples."""
        result = subprocess.run(["amplifier", "claude", "--help"], capture_output=True, text=True)
        assert "amplifier claude" in result.stdout
        assert "~/myproject" in result.stdout
        assert "Examples:" in result.stdout


class TestBackwardCompatibility:
    """Test backward compatibility with existing scripts."""

    def test_amplifier_anywhere_script_exists(self):
        """Test that amplifier-anywhere.sh still exists."""
        amplifier_root = find_amplifier_root()
        script_path = amplifier_root / "amplifier-anywhere.sh"
        assert script_path.exists()
        assert script_path.is_file()
        assert os.access(script_path, os.X_OK)  # Check it's executable

    def test_amplifier_anywhere_help_works(self):
        """Test that amplifier-anywhere.sh --help still works."""
        result = subprocess.run(
            ["./amplifier-anywhere.sh", "--help"], capture_output=True, text=True, cwd=find_amplifier_root()
        )
        assert result.returncode == 0
        assert "Amplifier Universal Access Script" in result.stdout


class TestErrorHandling:
    """Test error handling and user feedback."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_subprocess_error_handling(self, mock_which, mock_run):
        """Test handling of subprocess failures."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.side_effect = subprocess.CalledProcessError(1, "claude")

        with pytest.raises(SystemExit):
            launch_claude()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_keyboard_interrupt_handling(self, mock_which, mock_run):
        """Test graceful handling of Ctrl+C."""
        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.side_effect = KeyboardInterrupt()

        # Should exit cleanly without error
        with pytest.raises(SystemExit) as exc_info:
            launch_claude()
        assert exc_info.value.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
