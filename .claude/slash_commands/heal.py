#!/usr/bin/env python3
"""Simplified slash command that delegates to the amplifier CLI heal command."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run amplifier heal command with provided arguments."""
    # Get the project root (2 levels up from this script)
    project_root = Path(__file__).resolve().parents[2]

    # Build the command: python -m amplifier.cli heal [args]
    cmd = [sys.executable, "-m", "amplifier.cli", "heal"] + sys.argv[1:]

    # Run the command in the project root directory
    result = subprocess.run(cmd, cwd=project_root)

    # Exit with the same code as the subprocess
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
