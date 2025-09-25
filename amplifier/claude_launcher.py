#!/usr/bin/env python3
"""
Claude launcher module for Amplifier.

Launches Claude with appropriate context depending on whether working
on Amplifier itself or an external project.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def find_amplifier_root() -> Path:
    """Find the Amplifier project root directory.

    Returns:
        Path to Amplifier root directory

    Raises:
        RuntimeError: If Amplifier root cannot be found
    """
    # Start from this file's location
    current_file = Path(__file__).resolve()

    # Go up from amplifier/claude_launcher.py to find root
    # This file is in amplifier/, so parent is the project root
    amplifier_root = current_file.parent.parent

    # Verify it's actually the Amplifier root by checking for marker files
    markers = ["pyproject.toml", "AGENTS.md", "amplifier"]
    if all((amplifier_root / marker).exists() for marker in markers):
        return amplifier_root

    # If not found, raise error
    raise RuntimeError(
        f"Could not find Amplifier root. Expected to find it at {amplifier_root} with markers: {markers}"
    )


def detect_project_type(working_dir: Path, amplifier_root: Path) -> tuple[bool, Path]:
    """Detect if we're working on Amplifier or an external project.

    Args:
        working_dir: Current working directory
        amplifier_root: Path to Amplifier root

    Returns:
        Tuple of (is_amplifier_project, project_root)
    """
    # Check if current dir is within Amplifier
    try:
        working_dir.relative_to(amplifier_root)
        # We're inside Amplifier
        return True, amplifier_root
    except ValueError:
        # We're outside Amplifier - external project
        return False, working_dir


def launch_claude(project_dir: Path | None = None, extra_args: list[str] | None = None) -> None:
    """Launch Claude with appropriate context.

    Args:
        project_dir: Optional project directory to work in (defaults to current dir)
        extra_args: Additional arguments to pass to claude CLI

    Raises:
        RuntimeError: If claude CLI is not found or amplifier-anywhere.sh is missing
        subprocess.CalledProcessError: If claude launch fails
    """
    import os

    # Check if claude CLI is available
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError(
            "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code\n"
            "Or run 'amplifier doctor' to check your environment."
        )

    # Determine working directory
    working_dir = Path(project_dir).resolve() if project_dir else Path.cwd()

    # Find Amplifier root
    try:
        amplifier_root = find_amplifier_root()
    except RuntimeError as e:
        print(f"Warning: {e}", file=sys.stderr)
        print("Launching Claude without Amplifier context.", file=sys.stderr)
        # Launch claude in the working directory without Amplifier context
        cmd = [claude_path, str(working_dir)]
        if extra_args:
            cmd.extend(extra_args)
        subprocess.run(cmd, check=True)
        return

    # Use the amplifier-anywhere.sh script for full agent support
    script_path = amplifier_root / "amplifier-anywhere.sh"
    if not script_path.exists():
        # Fallback to direct claude launch if script doesn't exist
        print(f"Warning: amplifier-anywhere.sh not found at {script_path}", file=sys.stderr)
        print("Launching Claude directly without full Amplifier integration.", file=sys.stderr)
        cmd = [claude_path, str(working_dir)]
        if extra_args:
            cmd.extend(extra_args)
        subprocess.run(cmd, check=True)
        return

    # Detect project type
    is_amplifier, project_root = detect_project_type(working_dir, amplifier_root)

    # Set up environment variables
    env = os.environ.copy()
    env["ORIGINAL_PWD"] = str(Path.cwd())

    if not is_amplifier:
        # Working on external project - enable external mode
        print("🔍 Detected non-Amplifier project - using external mode")
        env["EXTERNAL_PROJECT_MODE"] = "1"
        env["AMPLIFIER_EXTERNAL_MODE"] = "1"
        env["AMPLIFIER_WORKING_DIR"] = str(project_root)

    # Build command using amplifier-anywhere.sh for full agent support
    cmd = [str(script_path), str(project_root)]

    # Add any extra arguments
    if extra_args:
        cmd.extend(extra_args)

    # Launch using the script
    print(f"🚀 Starting Amplifier for project: {project_root}")
    print(f"📁 Amplifier location: {amplifier_root}")

    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch Claude: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nClaude session terminated by user.", file=sys.stderr)
        sys.exit(0)


def main() -> None:
    """Main entry point for the claude launcher."""
    # Parse simple arguments (we don't need full argparse for this)
    import sys

    args = sys.argv[1:]

    # Extract project directory if provided as first positional argument
    project_dir = None
    extra_args = []

    if args and not args[0].startswith("-"):
        # First arg is project directory
        project_dir = args[0]
        extra_args = args[1:] if len(args) > 1 else []
    else:
        # All args are extra args for claude
        extra_args = args

    try:
        # Convert string to Path if provided
        path_obj = Path(project_dir) if project_dir else None
        result = launch_claude(path_obj, extra_args)
        sys.exit(result)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
