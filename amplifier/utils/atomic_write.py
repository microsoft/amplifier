"""Atomic file writing utilities using temp file + rename pattern.

This module provides atomic write operations that ensure file writes are
either completely successful or leave the original file unchanged.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(filepath: Path | str, content: str) -> None:
    """Write text to file atomically using temp file + rename.

    Args:
        filepath: Target file path
        content: Text content to write
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory to ensure same filesystem
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=filepath.parent, delete=False, suffix=".tmp"
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        try:
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())  # Ensure data is written to disk

            # Atomic rename (on POSIX systems)
            os.replace(tmp_path, filepath)
        except Exception:
            # Clean up temp file on error
            if tmp_path.exists():
                tmp_path.unlink()
            raise


def atomic_write_json(filepath: Path | str, data: Any, indent: int = 2) -> None:
    """Write JSON to file atomically using temp file + rename.

    Args:
        filepath: Target file path
        data: Data to serialize as JSON
        indent: JSON indentation level
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write_text(filepath, content)


def atomic_append_jsonl(filepath: Path | str, record: dict) -> None:
    """Append a record to JSONL file atomically.

    This reads the existing file, appends the record, and writes atomically.
    For high-frequency appends, consider a different approach.

    Args:
        filepath: Target JSONL file path
        record: Dictionary to append as JSON line
    """
    filepath = Path(filepath)

    # Read existing content if file exists
    lines = []
    if filepath.exists():
        lines = filepath.read_text(encoding="utf-8").splitlines()

    # Append new record
    lines.append(json.dumps(record, ensure_ascii=False))

    # Write atomically
    content = "\n".join(lines) + "\n"
    atomic_write_text(filepath, content)
