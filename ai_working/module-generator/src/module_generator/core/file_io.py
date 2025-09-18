"""Resilient file I/O operations with retry logic for cloud sync issues."""

import json
import logging
import time
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def write_json(data: Any, path: Path | str, max_retries: int = 3) -> None:
    """Write JSON data to file with retry logic for cloud sync issues.

    Args:
        data: Data to serialize to JSON
        path: Path to write file to
        max_retries: Maximum number of retry attempts (default: 3)

    Raises:
        OSError: If write fails after all retries
        TypeError: If data is not JSON serializable
    """
    path = Path(path)
    content = json.dumps(data, indent=2, ensure_ascii=False)

    for attempt in range(max_retries):
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
            return

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                # Cloud sync issue - retry with exponential backoff
                delay = 0.5 * (2**attempt)  # 0.5, 1, 2 seconds

                if attempt == 0:
                    logger.warning(
                        f"File I/O error writing to {path} - retrying. "
                        "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                        "Consider enabling 'Always keep on this device' for better performance."
                    )

                time.sleep(delay)
            else:
                # Final attempt failed or different error
                raise OSError(f"Failed to write {path} after {max_retries} attempts. Error: {e}") from e


def write_yaml(data: Any, path: Path | str, max_retries: int = 3) -> None:
    """Write YAML data to file with retry logic for cloud sync issues.

    Args:
        data: Data to serialize to YAML
        path: Path to write file to
        max_retries: Maximum number of retry attempts (default: 3)

    Raises:
        OSError: If write fails after all retries
        yaml.YAMLError: If data cannot be serialized to YAML
    """
    path = Path(path)
    content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    for attempt in range(max_retries):
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
            return

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                # Cloud sync issue - retry with exponential backoff
                delay = 0.5 * (2**attempt)  # 0.5, 1, 2 seconds

                if attempt == 0:
                    logger.warning(
                        f"File I/O error writing to {path} - retrying. "
                        "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                        "Consider enabling 'Always keep on this device' for better performance."
                    )

                time.sleep(delay)
            else:
                # Final attempt failed or different error
                raise OSError(f"Failed to write {path} after {max_retries} attempts. Error: {e}") from e


def write_text(content: str, path: Path | str, max_retries: int = 3) -> None:
    """Write text content to file with retry logic for cloud sync issues.

    Args:
        content: Text content to write
        path: Path to write file to
        max_retries: Maximum number of retry attempts (default: 3)

    Raises:
        OSError: If write fails after all retries
    """
    path = Path(path)

    for attempt in range(max_retries):
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
            return

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                # Cloud sync issue - retry with exponential backoff
                delay = 0.5 * (2**attempt)  # 0.5, 1, 2 seconds

                if attempt == 0:
                    logger.warning(
                        f"File I/O error writing to {path} - retrying. "
                        "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                        "Consider enabling 'Always keep on this device' for better performance."
                    )

                time.sleep(delay)
            else:
                # Final attempt failed or different error
                raise OSError(f"Failed to write {path} after {max_retries} attempts. Error: {e}") from e


def read_yaml(path: Path | str) -> dict[str, Any]:
    """Read YAML file with basic error handling.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If file is not valid YAML
        OSError: If file cannot be read
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Return empty dict if file is empty
        if data is None:
            return {}

        return data

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in {path}: {e}") from e
    except OSError as e:
        raise OSError(f"Failed to read {path}: {e}") from e
