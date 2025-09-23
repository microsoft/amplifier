"""
File utilities for copying with proper permission preservation.

This module provides utilities for copying files while preserving
important attributes like executable permissions.
"""

import os
import shutil
import stat
from pathlib import Path


def copy_with_permissions(src: Path, dst: Path, follow_symlinks: bool = True) -> None:
    """Copy file with full permission preservation.

    Automatically makes files executable if they're being copied to .claude/tools/
    directory, as these are expected to be scripts that need execution permissions.

    Args:
        src: Source file path
        dst: Destination file path
        follow_symlinks: Whether to follow symbolic links

    Raises:
        FileNotFoundError: If source file doesn't exist
        PermissionError: If unable to set permissions
    """
    if not src.exists():
        raise FileNotFoundError(f"Source file does not exist: {src}")

    # Copy file content and basic metadata
    shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

    # Check if destination is in .claude/tools/ directory
    # These files should always be executable (scripts, Python files, etc.)
    if ".claude/tools" in str(dst) or ".claude\\tools" in str(dst):
        # Make it executable for owner (user)
        current_mode = dst.stat().st_mode
        new_mode = current_mode | stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR
        os.chmod(dst, new_mode)
    else:
        # For other files, preserve source permissions
        src_stat = src.stat() if follow_symlinks else src.lstat()
        os.chmod(dst, src_stat.st_mode)


def copy_tree_with_permissions(src_dir: Path, dst_dir: Path, ignore_patterns: list[str] | None = None) -> None:
    """Recursively copy directory tree preserving permissions.

    Args:
        src_dir: Source directory
        dst_dir: Destination directory
        ignore_patterns: List of patterns to ignore (e.g., ['*.pyc', '__pycache__'])
    """
    if not src_dir.exists():
        raise FileNotFoundError(f"Source directory does not exist: {src_dir}")

    # Create destination directory if it doesn't exist
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Setup ignore function if patterns provided
    ignore_func = None
    if ignore_patterns:
        ignore_func = shutil.ignore_patterns(*ignore_patterns)
        ignored = ignore_func(str(src_dir), os.listdir(src_dir)) if ignore_func else set()
    else:
        ignored = set()

    # Walk through source directory
    for item in src_dir.iterdir():
        if item.name in ignored:
            continue

        src_path = src_dir / item.name
        dst_path = dst_dir / item.name

        if src_path.is_dir():
            # Recursively copy subdirectory
            copy_tree_with_permissions(src_path, dst_path, ignore_patterns)
        else:
            # Copy file with permissions
            copy_with_permissions(src_path, dst_path)


def ensure_executable(file_path: Path) -> None:
    """Ensure a file has executable permissions for the owner.

    Args:
        file_path: Path to the file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    # Get current permissions
    current_mode = file_path.stat().st_mode

    # Add owner execute permission
    new_mode = current_mode | stat.S_IXUSR

    # Apply new permissions
    os.chmod(file_path, new_mode)


def is_executable(file_path: Path) -> bool:
    """Check if a file has executable permissions.

    Args:
        file_path: Path to the file

    Returns:
        True if file is executable by owner, False otherwise
    """
    if not file_path.exists():
        return False

    mode = file_path.stat().st_mode
    return bool(mode & stat.S_IXUSR)


def get_package_data_path(relative_path: str = "") -> Path:
    """Get path to files in the amplifier-cli-v3 repository.

    This function finds files from the actual repository rather than
    package data, preventing duplication and drift.

    Args:
        relative_path: Optional relative path within repo

    Returns:
        Path to the repo file or directory
    """
    import amplifier

    # Get the package installation directory
    package_dir = Path(amplifier.__file__).parent

    # Go up to find the repo root (amplifier-cli-v3)
    # Package is at amplifier-cli-v3/amplifier/
    repo_root = package_dir.parent

    # Check if we're in the expected structure
    if repo_root.name != "amplifier-cli-v3":
        # If not in dev environment, look for the repo in a standard location
        # or fall back to package location
        possible_locations = [
            Path.home() / "Source" / "amplifier-cli-v3",
            Path.home() / "src" / "amplifier-cli-v3",
            Path.home() / "projects" / "amplifier-cli-v3",
            Path.home() / "code" / "amplifier-cli-v3",
            Path("/Users/robotdad/Source/amplifier-cli-v3"),  # Known location
        ]

        for location in possible_locations:
            if location.exists() and (location / "CLAUDE.md").exists():
                repo_root = location
                break
        else:
            # Fall back to package directory if repo not found
            repo_root = package_dir.parent

    if relative_path:
        return repo_root / relative_path
    return repo_root
