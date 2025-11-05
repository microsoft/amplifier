"""Simple file I/O utilities with retry logic for cloud sync issues.

This module provides drop-in replacements for common file operations that can
handle transient I/O errors (errno 5) typically caused by OneDrive/cloud sync.
"""

import errno
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Track if we've shown the cloud sync warning this session
_cloud_sync_warning_shown = False


def _handle_io_error(attempt: int, max_retries: int = 3) -> bool:
    """Handle I/O error with exponential backoff.

    Returns True if we should retry, False otherwise.
    """
    global _cloud_sync_warning_shown

    if attempt >= max_retries:
        return False

    # Show warning once per session
    if not _cloud_sync_warning_shown:
        logger.warning(
            "File I/O error detected (likely OneDrive/cloud sync interference). "
            "Consider pausing cloud sync or excluding this directory from sync."
        )
        _cloud_sync_warning_shown = True

    # Exponential backoff: 0.1s, 0.2s, 0.4s
    wait_time = 0.1 * (2**attempt)
    logger.debug(f"Retrying file operation in {wait_time}s (attempt {attempt + 1}/{max_retries})")
    time.sleep(wait_time)
    return True


def write_json_with_retry(data: Any, filepath: Path | str, indent: int = 2, max_retries: int = 3) -> None:
    """Write JSON to file with retry logic for cloud sync issues."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return
        except OSError as e:
            if e.errno == errno.EIO and _handle_io_error(attempt, max_retries):
                continue
            raise


def read_json_with_retry(filepath: Path | str, max_retries: int = 3) -> Any:
    """Read JSON from file with retry logic for cloud sync issues."""
    filepath = Path(filepath)

    for attempt in range(max_retries + 1):
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:
            if e.errno == errno.EIO and _handle_io_error(attempt, max_retries):
                continue
            raise
    # Should never reach here, but satisfy linter
    raise OSError(f"Failed to read {filepath} after {max_retries} retries")


def write_text_with_retry(text: str, filepath: Path | str, max_retries: int = 3) -> None:
    """Write text to file with retry logic for cloud sync issues."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries + 1):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            return
        except OSError as e:
            if e.errno == errno.EIO and _handle_io_error(attempt, max_retries):
                continue
            raise


def read_text_with_retry(filepath: Path | str, max_retries: int = 3) -> str:
    """Read text from file with retry logic for cloud sync issues."""
    filepath = Path(filepath)

    for attempt in range(max_retries + 1):
        try:
            with open(filepath, encoding="utf-8") as f:
                return f.read()
        except OSError as e:
            if e.errno == errno.EIO and _handle_io_error(attempt, max_retries):
                continue
            raise
    # Should never reach here, but satisfy linter
    raise OSError(f"Failed to read {filepath} after {max_retries} retries")


def append_line_with_retry(line: str, filepath: Path | str, max_retries: int = 3) -> None:
    """Append a line to file with retry logic for cloud sync issues."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Ensure line ends with newline
    if not line.endswith("\n"):
        line += "\n"

    for attempt in range(max_retries + 1):
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(line)
            return
        except OSError as e:
            if e.errno == errno.EIO and _handle_io_error(attempt, max_retries):
                continue
            raise


# Convenience aliases for simpler imports
write_json = write_json_with_retry
read_json = read_json_with_retry
write_text = write_text_with_retry
read_text = read_text_with_retry
append_line = append_line_with_retry
