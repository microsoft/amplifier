"""
Path Configuration Module - Central path resolution for Amplifier

Purpose: Central path configuration and resolution for Amplifier project
Contract:
  - Resolve paths (relative, absolute, home) to absolute Path objects
  - Auto-create directories when accessed
  - Support multiple content directories
  - Backward compatibility with .data fallback

This module is a self-contained "brick" that other modules depend on
for consistent path resolution and directory management.
"""

import os
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class PathConfig:
    """Central path configuration and resolution for Amplifier.

    This class handles all path resolution and directory creation for the
    Amplifier project. It supports environment variables, resolves relative
    paths from the repo root, expands home directories, and auto-creates
    required directories.

    Environment Variables:
        AMPLIFIER_DATA_DIR: Data directory path (default: .data)
        AMPLIFIER_CONTENT_DIRS: Comma-separated content directories (default: .)

    Public Interface:
        data_dir: Path to data directory
        content_dirs: List of content directory Paths
        resolve_path(path_str): Resolve any path string to absolute Path
        get_all_content_paths(): Get existing content directories
        ensure_data_dirs(): Create all required directories
    """

    def __init__(self, repo_root: Path | None = None):
        """Initialize path configuration.

        Args:
            repo_root: Repository root directory. If None, uses current working directory.
        """
        # Set repo root - use provided path or current working directory
        self._repo_root = Path(repo_root) if repo_root else Path.cwd()

        # Load from environment variables with defaults
        self._load_paths()

        # Ensure essential directories exist
        self.ensure_data_dirs()

    def _load_paths(self) -> None:
        """Load paths from environment variables with defaults."""
        # Data directory - defaults to .data
        data_dir_env = os.getenv("AMPLIFIER_DATA_DIR", ".data")
        self._data_dir = self.resolve_path(data_dir_env)

        # Content directories - defaults to current directory
        content_dirs_env = os.getenv("AMPLIFIER_CONTENT_DIRS", ".")
        self._content_dirs = [self.resolve_path(p.strip()) for p in content_dirs_env.split(",")]

    def resolve_path(self, path_str: Union[str, Path]) -> Path:
        """Resolve a path string to an absolute Path object.

        Handles:
        - Relative paths (resolved from repo root)
        - Home directory paths (~/...)
        - Absolute paths

        Args:
            path_str: Path string to resolve

        Returns:
            Absolute Path object
        """
        path = Path(path_str)

        # Expand home directory
        path = path.expanduser()

        # If already absolute, return as is
        if path.is_absolute():
            return path

        # Otherwise, resolve relative to repo root
        return (self._repo_root / path).resolve()

    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self._data_dir

    @property
    def content_dirs(self) -> list[Path]:
        """Get the list of content directory paths."""
        return self._content_dirs

    def get_all_content_paths(self) -> list[Path]:
        """Get all existing content directories.

        Returns:
            List of Path objects for directories that actually exist
        """
        return [p for p in self._content_dirs if p.exists() and p.is_dir()]

    def ensure_data_dirs(self) -> None:
        """Create all required data directories if they don't exist."""
        # Data subdirectories to create
        data_subdirs = ["knowledge", "indexes", "state", "memories", "cache"]

        # Create data directory and subdirectories
        for subdir in data_subdirs:
            dir_path = self._data_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        """String representation of PathConfig."""
        return f"PathConfig(data_dir={self._data_dir}, content_dirs={self._content_dirs})"


# Create singleton instance for module-level access
paths = PathConfig()
