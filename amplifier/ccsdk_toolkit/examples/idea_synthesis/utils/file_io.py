"""File I/O utilities with retry logic for cloud-synced files."""

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def write_json_with_retry(data: Any, filepath: Path, max_retries: int = 3, initial_delay: float = 0.5) -> None:
    """Write JSON to file with retry logic for cloud-synced directories.

    Handles OSError errno 5 that can occur with OneDrive/Dropbox synced files.
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
    """Read JSON from file with retry logic for cloud-synced directories."""
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
