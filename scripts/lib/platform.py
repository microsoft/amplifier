"""Amplifier platform detection — Python equivalent of scripts/lib/platform.sh.

Usage:
    from scripts.lib.platform import get_amplifier_home, get_project_dir, get_platform, PLATFORM

Or as standalone:
    python scripts/lib/platform.py  # prints platform.json to stdout
"""

import json
import os
import sys
from pathlib import Path


def get_platform() -> str:
    """Detect current platform: 'linux', 'windows', or 'macos'."""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    return "linux"


def get_amplifier_home() -> Path:
    """Find the Amplifier repo root directory."""
    env = os.environ.get("AMPLIFIER_HOME")
    if env:
        return Path(env)

    candidates = [
        Path("/opt/amplifier"),
        Path("C:/claude/amplifier"),
        Path("/c/claude/amplifier"),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "CLAUDE.md").exists():
            return candidate

    this_file = Path(__file__).resolve()
    repo_root = this_file.parent.parent.parent
    if (repo_root / "CLAUDE.md").exists():
        return repo_root

    raise RuntimeError("Cannot detect AMPLIFIER_HOME. Set the environment variable.")


def get_claude_projects_dir() -> Path:
    """Find the Claude Code projects directory (~/.claude/projects/)."""
    return Path.home() / ".claude" / "projects"


def get_project_dir(project_hint: str = "amplifier") -> Path:
    """Find a Claude Code project directory by name hint.

    Claude Code encodes project paths differently per platform:
    - Windows: C--claude-amplifier (C:\\claude\\amplifier -> C--claude-amplifier)
    - Linux: -opt-amplifier (/opt/amplifier -> -opt-amplifier)

    This function finds the correct directory regardless of platform.
    """
    projects = get_claude_projects_dir()
    if not projects.is_dir():
        return projects / project_hint

    for candidate in projects.iterdir():
        if candidate.is_dir() and project_hint in candidate.name:
            return candidate

    return projects / project_hint


def get_memory_dir(project_hint: str = "amplifier") -> Path:
    """Find the memory directory for a Claude Code project."""
    return get_project_dir(project_hint) / "memory"


def get_workspace_root() -> Path:
    """Find the workspace root containing multiple project repos."""
    platform = get_platform()
    env = os.environ.get("AMPLIFIER_WORKSPACE")
    if env:
        return Path(env)
    if platform == "windows":
        return Path("C:/claude")
    return Path("/opt")


PLATFORM = get_platform()


def generate_platform_json() -> dict:
    """Generate platform.json content for the current machine."""
    home = get_amplifier_home()
    return {
        "os": PLATFORM,
        "amplifier_root": str(home),
        "claude_project_dir": str(get_project_dir("amplifier")),
        "workspace_root": str(get_workspace_root()),
        "memory_dir": str(get_memory_dir("amplifier")),
    }


if __name__ == "__main__":
    print(json.dumps(generate_platform_json(), indent=2))
