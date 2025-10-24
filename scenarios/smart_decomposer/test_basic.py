#!/usr/bin/env python3
"""Basic test to verify the smart_decomposer CLI works."""

import subprocess
import sys


def run_command(args):
    """Run a command and return the result."""
    cmd = [sys.executable, "-m", "scenarios.smart_decomposer"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_help():
    """Test help command."""
    code, stdout, stderr = run_command(["--help"])
    assert code == 0, f"Help failed: {stderr}"
    assert "decompose" in stdout
    assert "assign" in stdout
    assert "execute" in stdout
    assert "status" in stdout
    print("✓ Help command works")


def test_status_non_existent():
    """Test status with non-existent project."""
    code, stdout, stderr = run_command(["status", "--project-id", "test-xyz-999"])
    assert code == 1, "Should fail for non-existent project"
    assert "Project not found" in stderr
    print("✓ Status correctly reports missing project")


def test_decompose_help():
    """Test decompose help."""
    code, stdout, stderr = run_command(["decompose", "--help"])
    assert code == 0, f"Decompose help failed: {stderr}"
    assert "--goal" in stdout
    assert "--project-id" in stdout
    print("✓ Decompose help works")


def main():
    """Run all tests."""
    print("Testing smart_decomposer CLI...")
    test_help()
    test_status_non_existent()
    test_decompose_help()
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    main()
