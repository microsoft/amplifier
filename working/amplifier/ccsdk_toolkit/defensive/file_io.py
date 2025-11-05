"""
File I/O utilities with retry logic for cloud-synced files.

This module provides the standard file I/O operations for the CCSDK toolkit.
It handles common issues with cloud-synced directories (OneDrive, Dropbox, etc.)
by implementing automatic retry with exponential backoff.

Use these utilities for all file operations to ensure reliability across
different environments, especially when working with cloud-synced directories.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def write_json_with_retry(data: Any, filepath: Path, max_retries: int = 3, initial_delay: float = 0.5) -> None:
    """
    Write JSON to file with retry logic for cloud-synced directories.

    Handles OSError errno 5 that can occur with OneDrive/Dropbox synced files.
    This is the standard way to write JSON files in the CCSDK toolkit.

    Args:
        data: Data to serialize to JSON
        filepath: Path to write the JSON file
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before retry (default: 0.5)

    Raises:
        OSError: If write fails after all retry attempts

    Example:
        >>> from pathlib import Path
        >>> from amplifier.ccsdk_toolkit.defensive import write_json_with_retry
        >>> data = {"key": "value"}
        >>> write_json_with_retry(data, Path("output.json"))
    """
    retry_delay = initial_delay

    for attempt in range(max_retries):
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                f.flush()
            return
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logger.warning(
                        f"File I/O error writing to {filepath} - retrying. "
                        "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                        f"Consider enabling 'Always keep on this device' for: {filepath.parent}"
                    )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise


def read_json_with_retry(filepath: Path, max_retries: int = 3, initial_delay: float = 0.5, default: Any = None) -> Any:
    """
    Read JSON from file with retry logic for cloud-synced directories.

    Handles OSError errno 5 that can occur with OneDrive/Dropbox synced files.
    This is the standard way to read JSON files in the CCSDK toolkit.

    Args:
        filepath: Path to read the JSON file from
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before retry (default: 0.5)
        default: Default value to return if file doesn't exist or JSON is invalid

    Returns:
        Parsed JSON data or default value if file doesn't exist/is invalid

    Raises:
        OSError: If read fails after all retry attempts (except for missing files)

    Example:
        >>> from pathlib import Path
        >>> from amplifier.ccsdk_toolkit.defensive import read_json_with_retry
        >>> data = read_json_with_retry(Path("input.json"), default={})
    """
    if not filepath.exists():
        return default

    retry_delay = initial_delay

    for attempt in range(max_retries):
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logger.warning(
                        f"File I/O error reading {filepath} - retrying. This may be due to cloud-synced files."
                    )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {filepath}")
            return default

    return default
