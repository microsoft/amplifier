"""
Basic tests for the Amplifier CLI.
"""

import pytest
from click.testing import CliRunner

from amplifier.cli import cli


def test_cli_version():
    """Test that --version works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "Amplifier CLI" in result.output


def test_cli_help():
    """Test that help text is displayed."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Amplifier - Modular AI-powered development assistant" in result.output


def test_list_modes_command():
    """Test the list-modes command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list-modes"])
    assert result.exit_code == 0
    # Should at least show the built-in modes
    assert "default" in result.output or "Available Modes" in result.output


def test_list_modules_command():
    """Test the list-modules command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list-modules"])
    assert result.exit_code == 0
    assert "Available Modules" in result.output or "amplifier_mod" in result.output