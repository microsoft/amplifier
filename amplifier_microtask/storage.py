"""Storage module for handling file operations with atomic writes and recovery support.

This module provides simple, reliable file operations with atomic writes to prevent
data corruption and graceful error handling for resilience.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any


def save_json(data: dict, filepath: Path) -> bool:
    """Save data to JSON file using atomic write pattern.

    Args:
        data: Dictionary to save as JSON
        filepath: Target file path

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        ensure_directory(filepath.parent)

        # Write to temp file first (atomic write pattern)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp", delete=False
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp_file.name)

        # Atomic rename (replaces existing file if present)
        tmp_path.replace(filepath)
        return True

    except (IOError, OSError, TypeError, ValueError):
        # Clean up temp file if it exists
        if "tmp_path" in locals() and tmp_path.exists():
            try:
                tmp_path.unlink()
            except (IOError, OSError):
                pass
        return False


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load JSON data from file with error handling.

    Args:
        filepath: Path to JSON file

    Returns:
        Loaded data dictionary, or empty dict if file doesn't exist or error occurs
    """
    try:
        if not filepath.exists():
            return {}

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    except (IOError, OSError, json.JSONDecodeError):
        return {}


def append_jsonl(record: dict, filepath: Path) -> bool:
    """Append a record to a JSON Lines file.

    Args:
        record: Dictionary to append as a JSON line
        filepath: Path to JSONL file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        ensure_directory(filepath.parent)

        # Append to file (create if doesn't exist)
        with open(filepath, "a", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)
            f.write("\n")

        return True

    except (IOError, OSError, TypeError, ValueError):
        return False


def ensure_directory(path: Path) -> Path:
    """Create directory if it doesn't exist.

    Args:
        path: Directory path to create

    Returns:
        The path that was passed in
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except (IOError, OSError):
        # If we can't create it, at least return the path
        pass

    return path
