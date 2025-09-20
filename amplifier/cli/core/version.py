"""Version module for Amplifier CLI.

Single source of truth for version information, reading from pyproject.toml.
"""

import tomllib
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_version() -> str:
    """Get the version from pyproject.toml.

    Caches the result after first read for performance.
    Falls back to "0.1.0" if unable to read pyproject.toml.

    Returns:
        Version string from pyproject.toml or fallback version.
    """
    try:
        # Find pyproject.toml by walking up from this file's location
        current_dir = Path(__file__).parent

        # Walk up to find project root (where pyproject.toml should be)
        for _ in range(5):  # Limit search depth to avoid infinite loop
            pyproject_path = current_dir / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "0.1.0")
            current_dir = current_dir.parent

        # If we can't find pyproject.toml, return fallback
        return "0.1.0"

    except Exception:
        # Any error reading the file, return fallback
        return "0.1.0"


# Module-level constant for convenience
__version__ = get_version()
